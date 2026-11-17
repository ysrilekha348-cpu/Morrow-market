# Iteration 10: reports, exports (zip/xlsx), report settings, morning summary email, cron endpoint
import asyncio
import io
import json
import os
import sys
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import requests
from dotenv import dotenv_values, load_dotenv
from openpyxl import load_workbook
from pymongo import MongoClient

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")
sys.path.insert(0, "/app/backend")
import server  # noqa: E402
import reports  # noqa: E402
import email_service as es  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
_env = dotenv_values("/app/backend/.env")
SECRET = _env["WEBHOOK_CRON_SECRET"]
pdb = MongoClient(_env["MONGO_URL"])[_env["DB_NAME"]]
LOOP = asyncio.new_event_loop()
TEST_ORDER_IDS, CRON_IDS, SENT = [], [], []


def run(coro):
    return LOOP.run_until_complete(coro)


async def fake_send(*, to, subject, html):
    es._assert_safe_email(subject, html)
    SENT.append((to, subject, html))
    return "fake"


@pytest.fixture(scope="module", autouse=True)
def setup_module_state():
    orig = pdb.settings.find_one({"id": "store"}, {"_id": 0, "summary_hour": 1, "summary_sent_on": 1, "site_url": 1}) or {}
    server.send_email = fake_send  # never send real emails
    server.app.dependency_overrides[server.admin_user] = lambda: {"user_id": "test"}
    yield
    server.app.dependency_overrides.clear()
    restore = {"summary_hour": orig.get("summary_hour", 8), "summary_sent_on": orig.get("summary_sent_on", "")}
    unset = {}
    if "site_url" in orig:
        restore["site_url"] = orig["site_url"]
    else:
        unset["site_url"] = ""
    upd = {"$set": restore}
    if unset:
        upd["$unset"] = unset
    pdb.settings.update_one({"id": "store"}, upd)
    for oid in TEST_ORDER_IDS:
        pdb.orders.delete_one({"id": oid})
    for rid in CRON_IDS:
        pdb.cron_runs.delete_one({"run_id": rid})


def asgi():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://t")


def mk_order(**kw):
    o = {"id": f"TEST_{uuid.uuid4()}", "session_id": f"TEST_{uuid.uuid4()}", "product_id": "weekly-reset",
         "product_name": "TEST_Product", "customer_email": "TEST_r@example.com", "amount": 499.0,
         "original_amount": 499.0, "payment_status": "awaiting_payment", "payment_method": "gpay",
         "transaction_id": "", "created_at": datetime.now(timezone.utc).isoformat()}
    o.update(kw)
    return o


# ---- Auth walls (public URL) ----
@pytest.mark.parametrize("method,path", [
    ("get", "/api/admin/export"), ("get", "/api/admin/orders/spreadsheet"),
    ("get", "/api/admin/reports/settings"), ("put", "/api/admin/reports/settings"),
    ("post", "/api/admin/reports/send-summary")])
def test_admin_endpoints_401(method, path):
    r = getattr(requests, method)(f"{BASE_URL}{path}", json={"summary_hour": 8})
    assert r.status_code == 401


# ---- Export zip & spreadsheet (in-process, admin overridden) ----
def test_export_zip_contents():
    async def go():
        async with asgi() as c:
            return await c.get("/api/admin/export")
    r = run(go())
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/zip")
    assert "morrow-market-export-" in r.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert set(z.namelist()) == {"products.json", "orders.json", "discounts.json", "settings.json", "orders.xlsx"}
    products = json.loads(z.read("products.json"))
    assert len(products) == pdb.products.count_documents({})
    assert all("_id" not in p for p in products)
    assert len(json.loads(z.read("orders.json"))) == pdb.orders.count_documents({})
    load_workbook(io.BytesIO(z.read("orders.xlsx")))


def test_spreadsheet_endpoint():
    async def go():
        async with asgi() as c:
            return await c.get("/api/admin/orders/spreadsheet")
    r = run(go())
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    ws = load_workbook(io.BytesIO(r.content)).active
    assert ws.cell(1, 1).value == "Order date (IST)"
    n = pdb.orders.count_documents({})
    assert ws.max_row == n + 3  # header + orders + blank + totals


def test_orders_xlsx_builder_totals_and_ist():
    orders = [
        {"created_at": "2026-01-10T20:00:00+00:00", "reviewed_at": "2026-01-10T21:00:00+00:00", "product_name": "A", "amount": 499.0, "payment_status": "paid", "id": "1", "discount_percent": 0},
        {"created_at": "2026-01-10T20:00:00+00:00", "product_name": "B", "amount": 299.0, "payment_status": "pending_review", "id": "2"},
        {"created_at": "2026-01-10T20:00:00+00:00", "product_name": "C", "amount": 199.0, "payment_status": "paid", "id": "3", "discount_percent": 20},
        {"created_at": "2026-01-10T20:00:00+00:00", "product_name": "D", "amount": 99.0, "payment_status": "rejected", "id": "4"},
    ]
    ws = load_workbook(io.BytesIO(reports.orders_xlsx(orders))).active
    assert ws.max_row == 1 + 4 + 2
    assert ws.cell(2, 1).value == "11 Jan 2026, 01:30 AM"  # 20:00 UTC -> 01:30 IST next day
    assert ws.cell(2, 11).value == "11 Jan 2026, 02:30 AM"
    assert ws.cell(2, 4).value == "Paid" and ws.cell(3, 4).value == "Needs review"
    last = ws.max_row
    assert ws.cell(last, 1).value == "Confirmed revenue"
    assert ws.cell(last, 4).value == "2 paid orders"
    assert ws.cell(last, 8).value == 698


def test_orders_xlsx_empty():
    ws = load_workbook(io.BytesIO(reports.orders_xlsx([]))).active
    assert ws.cell(ws.max_row, 4).value == "0 paid orders"


# ---- Report settings ----
@pytest.mark.parametrize("hour", [0, 7, 9, 8])
def test_put_settings_valid(hour):
    async def go():
        async with asgi() as c:
            return await c.put("/api/admin/reports/settings", json={"summary_hour": hour})
    r = run(go())
    assert r.status_code == 200
    assert r.json()["summary_hour"] == hour
    assert r.json()["recipient"].lower() == server.owner_email().lower()
    assert pdb.settings.find_one({"id": "store"})["summary_hour"] == hour


@pytest.mark.parametrize("hour", [6, 10, 12, -1, "8", None])
def test_put_settings_invalid(hour):
    async def go():
        async with asgi() as c:
            return await c.put("/api/admin/reports/settings", json={"summary_hour": hour})
    assert run(go()).status_code == 422


def test_get_settings_records_https_origin():
    async def go():
        async with asgi() as c:
            return await c.get("/api/admin/reports/settings", headers={"origin": "https://shop.example.com"})
    r = run(go())
    assert r.status_code == 200 and set(r.json()) == {"summary_hour", "last_sent_on", "recipient"}
    assert pdb.settings.find_one({"id": "store"})["site_url"] == "https://shop.example.com"


def test_send_summary_now_mocked():
    SENT.clear()
    async def go():
        async with asgi() as c:
            return await c.post("/api/admin/reports/send-summary")
    r = run(go())
    assert r.status_code == 200
    assert len(SENT) == 1 and "morning summary" in SENT[0][1]
    assert "https://shop.example.com/admin" in SENT[0][2]
    assert r.json()["last_sent_on"] == server.stamp()


# ---- Scheduled summary gating ----
def _set(hour, sent_on):
    pdb.settings.update_one({"id": "store"}, {"$set": {"summary_hour": hour, "summary_sent_on": sent_on}})


def test_scheduled_sends_only_at_chosen_hour_once():
    hour = datetime.now(reports.IST).hour
    SENT.clear()
    _set(hour, "")
    run(server.run_scheduled_summary())
    assert len(SENT) == 1
    run(server.run_scheduled_summary())  # same day again
    assert len(SENT) == 1
    _set((hour + 1) % 24 or 7, "")
    run(server.run_scheduled_summary())
    assert len(SENT) == 1
    _set(0, "")
    if hour != 0:
        run(server.run_scheduled_summary())
        assert len(SENT) == 1


def test_scheduled_sent_yesterday_sends_again():
    SENT.clear()
    _set(datetime.now(reports.IST).hour, (datetime.now(reports.IST) - timedelta(days=1)).strftime("%Y-%m-%d"))
    run(server.run_scheduled_summary())
    assert len(SENT) == 1


# ---- summary_email safety ----
def _stats(**kw):
    s = {"date": "Monday, 12 January", "confirmed_count": 0, "revenue": 0, "new_orders": 0, "free_downloads": 0, "waiting": []}
    s.update(kw)
    return s


@pytest.mark.parametrize("url", [None, f"{BASE_URL}/admin"])
def test_summary_email_quiet(url):
    subj, html = es.summary_email(_stats(), url)
    es._assert_safe_email(subj, html)
    assert "quiet night" in html and ("Open owner space" in html) == bool(url)


@pytest.mark.parametrize("url", [None, f"{BASE_URL}/admin"])
def test_summary_email_busy(url):
    waiting = [{"product_name": "<b>X</b>", "customer_email": "a@b.com", "transaction_id": "UTR123456", "amount": 1299}]
    subj, html = es.summary_email(_stats(confirmed_count=2, revenue=1500, new_orders=3, free_downloads=1, waiting=waiting), url)
    es._assert_safe_email(subj, html)
    assert "₹1,500 confirmed" in subj and "1 to review" in subj
    assert "&lt;b&gt;X" in html and "₹1,299" in html


# ---- daily_stats ----
def test_daily_stats_counts():
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=2)).isoformat()
    old = (now - timedelta(hours=30)).isoformat()
    orders = [
        {"payment_status": "paid", "amount": 499, "reviewed_at": recent, "created_at": old},
        {"payment_status": "paid", "amount": 299, "reviewed_at": old, "created_at": old},
        {"payment_status": "paid", "amount": 0, "reviewed_at": recent, "created_at": recent},
        {"payment_status": "pending_review", "amount": 199, "created_at": recent},
        {"payment_status": "pending_review", "amount": 99, "created_at": old},
        {"payment_status": "awaiting_payment", "amount": 149, "created_at": recent},
    ]
    s = reports.daily_stats(orders, now)
    assert s["confirmed_count"] == 1 and s["revenue"] == 499
    assert s["new_orders"] == 2
    assert s["free_downloads"] == 1
    assert len(s["waiting"]) == 2


# ---- Cron endpoint (public URL); settings guarded so no real email can go out ----
@pytest.fixture
def guard_no_send():
    _set(8, datetime.now(reports.IST).strftime("%Y-%m-%d"))
    yield


def test_cron_no_bearer():
    assert requests.post(f"{BASE_URL}/api/cron/daily-summary", json={}).status_code == 401


def test_cron_wrong_bearer():
    r = requests.post(f"{BASE_URL}/api/cron/daily-summary", json={}, headers={"Authorization": "Bearer nope", "X-Webhook-Id": "x"})
    assert r.status_code == 401


def test_cron_invalid_json():
    r = requests.post(f"{BASE_URL}/api/cron/daily-summary", data="not-json",
                      headers={"Authorization": f"Bearer {SECRET}", "Content-Type": "application/json", "X-Webhook-Id": "x"})
    assert r.status_code == 400


def test_cron_missing_run_id():
    r = requests.post(f"{BASE_URL}/api/cron/daily-summary", json={}, headers={"Authorization": f"Bearer {SECRET}"})
    assert r.status_code == 400


def test_cron_non_object_body():
    r = requests.post(f"{BASE_URL}/api/cron/daily-summary", json=[1, 2], headers={"Authorization": f"Bearer {SECRET}"})
    assert r.status_code == 400, f"got {r.status_code}"


def test_cron_accept_and_duplicate(guard_no_send):
    rid = f"TEST_{uuid.uuid4()}"
    CRON_IDS.append(rid)
    h = {"Authorization": f"Bearer {SECRET}", "X-Webhook-Id": rid}
    r1 = requests.post(f"{BASE_URL}/api/cron/daily-summary", json={}, headers=h)
    assert r1.status_code == 200 and r1.json() == {"status": "accepted"}
    assert pdb.cron_runs.find_one({"run_id": rid})
    r2 = requests.post(f"{BASE_URL}/api/cron/daily-summary", json={}, headers=h)
    assert r2.status_code == 200 and r2.json() == {"status": "duplicate"}


def test_cron_run_id_in_body(guard_no_send):
    rid = f"TEST_{uuid.uuid4()}"
    CRON_IDS.append(rid)
    r = requests.post(f"{BASE_URL}/api/cron/daily-summary", json={"run_id": rid}, headers={"Authorization": f"Bearer {SECRET}"})
    assert r.status_code == 200 and r.json()["status"] == "accepted"


# ---- crons.yml contract ----
def test_crons_yml():
    import yaml
    data = yaml.safe_load(open("/app/.emergent/crons.yml"))
    crons = data["crons"]
    assert len(crons) == 3
    assert sorted(c["cron"] for c in crons) == ["0 7 * * *", "0 8 * * *", "0 9 * * *"]
    for c in crons:
        assert c["timezone"] == "Asia/Kolkata" and c["method"] == "POST" and c["enabled"] is True
        assert c["endpoint"] == "{{BASE_URL}}/api/cron/daily-summary"
        assert c["name"] and c["description"]
