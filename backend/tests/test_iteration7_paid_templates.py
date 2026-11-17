# Iteration 7: 15 new paid templates - catalog, detail, downloads (PDF/ZIP), unchanged flows
import io
import os
import uuid
import zipfile
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
mongo = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]

NEW = {
    "money-map": (299, "Financial tracker", "money-map-bundle.zip"),
    "monthly-budget": (199, "Budgeting", "monthly-budget-bundle.zip"),
    "debt-payoff": (249, "Finance", "debt-payoff-bundle.zip"),
    "savings-goals": (149, "Finance", "savings-goals.pdf"),
    "subscription-audit": (99, "Finance", "subscription-audit.pdf"),
    "income-invoice": (199, "Business", "income-invoice-bundle.zip"),
    "freelancer-finance": (499, "Business", "freelancer-finance-bundle.zip"),
    "content-batch": (199, "Planning", "content-batch-bundle.zip"),
    "client-onboarding": (299, "Business", "client-onboarding.pdf"),
    "project-scope": (249, "Business", "project-scope.pdf"),
    "meeting-notes": (129, "Planning", "meeting-notes.pdf"),
    "job-search": (199, "Career", "job-search-bundle.zip"),
    "meal-grocery": (149, "Home", "meal-grocery.pdf"),
    "home-reset": (99, "Home", "home-reset.pdf"),
    "self-care": (129, "Wellbeing", "self-care.pdf"),
}
OLD = {"weekly-reset": 499, "quiet-brand": 899, "slow-content": 299, "free-planner": 0, "free-moodboard": 0}
CREATED_SESSIONS = []


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    early = mongo.discounts.find_one({"code": "EARLY20"})
    yield
    if CREATED_SESSIONS:
        mongo.orders.delete_many({"session_id": {"$in": CREATED_SESSIONS}})
    if early is not None:
        mongo.discounts.update_one({"code": "EARLY20"}, {"$set": {"uses": early["uses"]}})


def make_order(pid, discount=""):
    r = requests.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": pid, "customer_email": f"test_{uuid.uuid4().hex[:6]}@example.com", "discount_code": discount})
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    CREATED_SESSIONS.append(sid)
    return r.json()


class TestCatalog:
    def test_products_total_and_prices(self):
        r = requests.get(f"{BASE_URL}/api/products")
        assert r.status_code == 200
        data = {p["id"]: p for p in r.json()}
        assert len(r.json()) == 30, [p["id"] for p in r.json()]  # iteration 8 added 10 more
        for pid, (price, cat, fname) in NEW.items():
            assert pid in data, pid
            assert data[pid]["price"] == price and data[pid]["price"] > 0
            assert data[pid]["category"] == cat
            assert data[pid]["file_name"] == fname
            assert "_id" not in data[pid]
        for pid, price in OLD.items():
            assert data[pid]["price"] == price

    @pytest.mark.parametrize("pid", list(NEW))
    def test_detail(self, pid):
        r = requests.get(f"{BASE_URL}/api/products/{pid}")
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == pid and d["price"] == NEW[pid][0] and d["name"]

    def test_storage_paths_in_db(self):
        for pid in NEW:
            p = mongo.products.find_one({"id": pid})
            assert p.get("storage_path"), pid
            assert p.get("file_size", 0) > 1000


class TestDownloads:
    def test_unpaid_download_blocked(self):
        sid = make_order("money-map")["session_id"]
        assert requests.get(f"{BASE_URL}/api/downloads/{sid}").status_code == 404
        st = requests.get(f"{BASE_URL}/api/payments/status/{sid}").json()
        assert st["payment_status"] == "awaiting_payment" and st["amount"] == 299

    @pytest.mark.parametrize("pid", list(NEW))
    def test_paid_download(self, pid):
        res = make_order(pid)
        assert res["free"] is False
        sid = res["session_id"]
        mongo.orders.update_one({"session_id": sid}, {"$set": {"payment_status": "paid"}})
        r = requests.get(f"{BASE_URL}/api/downloads/{sid}")
        assert r.status_code == 200, r.text
        fname = NEW[pid][2]
        assert fname in r.headers.get("content-disposition", "")
        if fname.endswith(".pdf"):
            assert r.headers["content-type"].startswith("application/pdf")
            assert r.content[:4] == b"%PDF"
        else:
            assert r.headers["content-type"].startswith("application/zip")
            names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
            assert any(n.endswith(".pdf") for n in names), names
            assert any(n.endswith(".xlsx") for n in names), names
            z = zipfile.ZipFile(io.BytesIO(r.content))
            for n in names:
                if n.endswith(".xlsx"):
                    inner = zipfile.ZipFile(io.BytesIO(z.read(n)))
                    assert "xl/workbook.xml" in inner.namelist()
                if n.endswith(".pdf"):
                    assert z.read(n)[:4] == b"%PDF"


class TestUnchangedFlows:
    def test_early20_on_new_product(self):
        v = requests.post(f"{BASE_URL}/api/discounts/validate", json={"code": "early20", "product_id": "freelancer-finance"})
        assert v.status_code == 200 and v.json()["final"] == 399
        res = make_order("freelancer-finance", "EARLY20")
        st = requests.get(f"{BASE_URL}/api/payments/status/{res['session_id']}").json()
        assert st["amount"] == 399 and st["discount_code"] == "EARLY20"

    def test_gpay_submit_on_new_product(self):
        sid = make_order("job-search")["session_id"]
        r = requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TEST123456"})
        assert r.status_code == 200 and r.json()["payment_status"] == "pending_review"
        assert requests.get(f"{BASE_URL}/api/downloads/{sid}").status_code == 404

    def test_free_still_free(self):
        r = requests.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "free-planner", "customer_email": "test_free7@example.com", "discount_code": ""},
                          headers={"Origin": "http://localhost"})
        assert r.status_code == 200 and r.json()["free"] is True
        CREATED_SESSIONS.append(r.json()["session_id"])
        d = requests.get(f"{BASE_URL}/api/downloads/{r.json()['session_id']}")
        assert d.status_code == 200 and d.content[:4] == b"%PDF"

    def test_promo_and_payment_info(self):
        assert requests.get(f"{BASE_URL}/api/store/promo").json()["code"] == "EARLY20"
        assert requests.get(f"{BASE_URL}/api/store/payment-info").status_code == 200

    @pytest.mark.parametrize("method,path", [("get", "/api/admin/products"), ("get", "/api/admin/orders"), ("get", "/api/admin/discounts"),
                                             ("get", "/api/admin/settings"), ("post", "/api/admin/products"), ("post", "/api/admin/orders/x/approve")])
    def test_admin_protected(self, method, path):
        r = getattr(requests, method)(f"{BASE_URL}{path}", json={})
        assert r.status_code in (401, 403), r.status_code
