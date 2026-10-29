# Regression tests: Morrow Market manual GPay checkout + owner approval flow
import os
import pytest
import requests
from pymongo import MongoClient
from dotenv import dotenv_values

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
_env = dotenv_values("/app/backend/.env")
db = MongoClient(_env["MONGO_URL"])[_env["DB_NAME"]]


@pytest.fixture(scope="module")
def s():
    with requests.Session() as sess:
        yield sess
    db.orders.delete_many({"customer_email": {"$regex": "^test_gpay", "$options": "i"}})


def new_order(s, pid="weekly-reset"):
    r = s.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": pid, "customer_email": "TEST_gpay@example.com"})
    assert r.status_code == 200, r.text
    return r.json()["session_id"]


# Storefront products
def test_seed_products_inr(s):
    r = s.get(f"{BASE_URL}/api/products")
    assert r.status_code == 200
    prices = {p["id"]: p["price"] for p in r.json()}
    assert prices.get("weekly-reset") == 499
    assert prices.get("quiet-brand") == 899
    assert prices.get("slow-content") == 299


def test_product_404(s):
    assert s.get(f"{BASE_URL}/api/products/nope").status_code == 404


# Payment info
def test_payment_info(s):
    r = s.get(f"{BASE_URL}/api/store/payment-info")
    assert r.status_code == 200
    d = r.json()
    assert d["gpay_number"] == "9337939011"
    assert isinstance(d["has_qr"], bool)
    q = s.get(f"{BASE_URL}/api/store/qr")
    assert q.status_code == (200 if d["has_qr"] else 404)


# Checkout validation
def test_checkout_invalid_email(s):
    r = s.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "weekly-reset", "customer_email": "bad"})
    assert r.status_code == 422


def test_checkout_unknown_product(s):
    r = s.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "nope", "customer_email": "TEST_gpay@example.com"})
    assert r.status_code == 404


# Checkout -> status -> submit -> download gating
def test_full_flow(s):
    sid = new_order(s, "quiet-brand")
    st = s.get(f"{BASE_URL}/api/payments/status/{sid}").json()
    assert st["payment_status"] == "awaiting_payment"
    assert st["amount"] == 899 and st["product_name"] == "Quiet Brand Kit"
    assert "transaction_id" not in st
    assert s.get(f"{BASE_URL}/api/downloads/{sid}").status_code == 404

    assert s.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "123"}).status_code == 422
    assert s.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "x" * 41}).status_code == 422
    r = s.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "412345678901"})
    assert r.status_code == 200 and r.json()["payment_status"] == "pending_review"
    assert db.orders.find_one({"session_id": sid})["transaction_id"] == "412345678901"
    # Second submit while pending is rejected
    assert s.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "999999999"}).status_code == 400
    assert s.get(f"{BASE_URL}/api/downloads/{sid}").status_code == 404

    # Simulate owner approve
    db.orders.update_one({"session_id": sid}, {"$set": {"payment_status": "paid"}})
    d = s.get(f"{BASE_URL}/api/downloads/{sid}")
    assert d.status_code == 200
    assert "attachment" in d.headers["content-disposition"]
    assert "Quiet Brand Kit" in d.text or len(d.content) > 0
    # Paid order can't be resubmitted
    assert s.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "999999999"}).status_code == 400


def test_rejected_can_resubmit(s):
    sid = new_order(s)
    db.orders.update_one({"session_id": sid}, {"$set": {"payment_status": "rejected"}})
    r = s.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "NEWUTR123456"})
    assert r.status_code == 200 and r.json()["payment_status"] == "pending_review"


def test_status_unknown(s):
    assert s.get(f"{BASE_URL}/api/payments/status/nope").status_code == 404
    assert s.post(f"{BASE_URL}/api/payments/nope/submit", json={"transaction_id": "123456"}).status_code == 400


# Admin auth protection
@pytest.mark.parametrize("method,path", [
    ("get", "/api/admin/products"), ("post", "/api/admin/products"), ("get", "/api/admin/orders"),
    ("get", "/api/admin/settings"), ("put", "/api/admin/settings"), ("post", "/api/admin/settings/qr"),
    ("post", "/api/admin/orders/x/approve"), ("post", "/api/admin/orders/x/reject"),
    ("post", "/api/admin/products/weekly-reset/file"), ("patch", "/api/admin/products/weekly-reset"),
])
def test_admin_requires_auth(s, method, path):
    r = getattr(s, method)(f"{BASE_URL}{path}")
    assert r.status_code == 401, f"{path} -> {r.status_code}"
    r2 = getattr(s, method)(f"{BASE_URL}{path}", headers={"Authorization": "Bearer invalid.token.here"})
    assert r2.status_code in (401, 403), f"{path} bad token -> {r2.status_code}"
