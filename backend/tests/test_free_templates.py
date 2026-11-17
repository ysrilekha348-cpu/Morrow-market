# Iteration 5: free downloadable templates, free checkout instant flow, EARLY20 interplay, approval email helper (mocked)
import os
import sys
import uuid
import asyncio
import pytest
import requests
from pymongo import MongoClient
from dotenv import dotenv_values

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
_env = dotenv_values("/app/backend/.env")
db = MongoClient(_env["MONGO_URL"])[_env["DB_NAME"]]
EMAIL = "TEST_free5@example.com"
FREE_IDS = ["free-planner", "free-moodboard"]
CREATED_SESSIONS = []


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    orig = db.discounts.find_one({"code": "EARLY20"}, {"_id": 0})
    yield
    db.discounts.update_one({"code": "EARLY20"}, {"$set": {"uses": orig["uses"], "active": orig["active"], "featured": orig["featured"]}})
    if CREATED_SESSIONS:
        db.orders.delete_many({"session_id": {"$in": CREATED_SESSIONS}})


def checkout(pid, code="", headers=None):
    r = requests.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": pid, "customer_email": f"test_free5_{uuid.uuid4().hex[:8]}@example.com", "discount_code": code}, headers=headers or {})
    if r.status_code == 200:
        CREATED_SESSIONS.append(r.json()["session_id"])
    return r


# ---- catalogue ----
def test_products_include_free_and_paid():
    r = requests.get(f"{BASE_URL}/api/products")
    assert r.status_code == 200
    items = {p["id"]: p for p in r.json()}
    for pid in ["weekly-reset", "quiet-brand", "slow-content", *FREE_IDS]:
        assert pid in items, pid
    assert items["weekly-reset"]["price"] == 499
    for pid, name in [("free-planner", "A Calmer Week"), ("free-moodboard", "Brand Moodboard")]:
        assert items[pid]["name"] == name
        assert items[pid]["price"] == 0
        assert items[pid]["category"] == "Free templates"
        assert "storage_path" not in items[pid]


@pytest.mark.parametrize("pid", FREE_IDS)
def test_free_pdf_uploaded_to_storage(pid):
    doc = db.products.find_one({"id": pid})
    assert doc.get("storage_path"), f"{pid} has no storage_path"
    assert doc.get("file_content_type") == "application/pdf"


# ---- free checkout ----
@pytest.mark.parametrize("pid", FREE_IDS)
def test_free_checkout_instant_and_download(pid):
    before = db.discounts.find_one({"code": "EARLY20"})["uses"]
    r = checkout(pid)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["free"] is True and isinstance(d["session_id"], str)
    st = requests.get(f"{BASE_URL}/api/payments/status/{d['session_id']}").json()
    assert st["payment_status"] == "paid" and st["amount"] == 0 and st["discount_code"] == ""
    import time
    for _ in range(20):
        order = db.orders.find_one({"session_id": d["session_id"]})
        if order.get("email_status"): break
        time.sleep(0.25)
    assert order["payment_method"] == "free"
    assert order.get("email_status") in ("failed", "sent")  # no Origin header -> not sent, but status saved
    dl = requests.get(f"{BASE_URL}/api/downloads/{d['session_id']}")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("application/pdf")
    assert dl.content[:4] == b"%PDF"
    assert ".pdf" in dl.headers.get("content-disposition", "")
    assert db.discounts.find_one({"code": "EARLY20"})["uses"] == before


def test_free_checkout_with_early20_does_not_burn_use():
    """Spec: free product does not use EARLY20. If a client sends the code anyway, a use should not be consumed."""
    before = db.discounts.find_one({"code": "EARLY20"})["uses"]
    r = checkout("free-planner", code="EARLY20")
    assert r.status_code == 200
    after = db.discounts.find_one({"code": "EARLY20"})["uses"]
    assert after == before, f"EARLY20 use burned on a free product ({before}->{after})"


def test_free_pay_submit_rejected():
    r = checkout("free-moodboard")
    sid = r.json()["session_id"]
    s = requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "123456789"})
    assert s.status_code == 400


# ---- paid checkout regression ----
def test_paid_checkout_early20():
    before = db.discounts.find_one({"code": "EARLY20"})["uses"]
    v = requests.post(f"{BASE_URL}/api/discounts/validate", json={"code": "EARLY20", "product_id": "weekly-reset"})
    assert v.json() == {"code": "EARLY20", "percent": 20, "original": 499, "final": 399}
    r = checkout("weekly-reset", code="EARLY20")
    assert r.status_code == 200 and r.json()["free"] is False
    sid = r.json()["session_id"]
    st = requests.get(f"{BASE_URL}/api/payments/status/{sid}").json()
    assert st["payment_status"] == "awaiting_payment" and st["amount"] == 399
    assert db.discounts.find_one({"code": "EARLY20"})["uses"] == before + 1
    assert requests.get(f"{BASE_URL}/api/downloads/{sid}").status_code == 404
    s = requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TEST123456"})
    assert s.status_code == 200 and s.json()["payment_status"] == "pending_review"


@pytest.mark.parametrize("path", ["/api/admin/orders", "/api/admin/products", "/api/admin/discounts", "/api/admin/settings"])
def test_admin_401(path):
    assert requests.get(f"{BASE_URL}{path}").status_code == 401


# ---- email helper in-process (send_email mocked) ----
class FakeReq:
    def __init__(self, origin): self.headers = {"origin": origin} if origin else {}


@pytest.fixture(scope="module")
def srv():
    sys.path.insert(0, "/app/backend")
    import server
    import email_service
    return server, email_service


def _run(server, coro_fn):
    async def run():
        from motor.motor_asyncio import AsyncIOMotorClient
        server.db = AsyncIOMotorClient(_env["MONGO_URL"])[_env["DB_NAME"]]
        return await coro_fn()
    return asyncio.run(run())


def test_free_checkout_calls_email_service(srv):
    server, es = srv
    sent = []

    async def fake_send(*, to, subject, html):
        es._assert_safe_email(subject, html); sent.append((to, subject, html)); return "id"
    server.send_email = fake_send
    body = server.CheckoutIn(product_id="free-planner", customer_email=EMAIL)
    from fastapi import BackgroundTasks
    bt = BackgroundTasks()

    async def go():
        o = await server.checkout(body, FakeReq("https://shop.example.com"), bt)
        assert not sent, "email should be deferred to background task"
        await bt()
        return o
    out = _run(server, go)
    CREATED_SESSIONS.append(out["session_id"])
    assert out["free"] is True
    assert sent and sent[0][0].lower() == EMAIL.lower()
    assert f"https://shop.example.com/payment/success?session_id={out['session_id']}" in sent[0][2]
    assert db.orders.find_one({"session_id": out["session_id"]})["email_status"] == "sent"


def test_approve_calls_email_service(srv):
    server, es = srv
    sent = []

    async def fake_send(*, to, subject, html):
        es._assert_safe_email(subject, html); sent.append((to, html)); return "id"
    server.send_email = fake_send
    oid, sid = str(uuid.uuid4()), uuid.uuid4().hex
    CREATED_SESSIONS.append(sid)
    db.orders.insert_one({"id": oid, "session_id": sid, "product_id": "weekly-reset", "product_name": "The Weekly Reset",
                          "customer_email": EMAIL, "payment_status": "pending_review", "amount": 399, "discount_code": ""})
    from fastapi import BackgroundTasks
    bt = BackgroundTasks()

    async def go():
        o = await server.review_order(oid, "approve", FakeReq("https://shop.example.com"), bt, {})
        await bt()
        return o
    out = _run(server, go)
    assert out["payment_status"] == "paid"
    assert f"https://shop.example.com/payment/success?session_id={sid}" in sent[0][1]
    assert db.orders.find_one({"id": oid})["email_status"] == "sent"
