# Iteration 6: free email copy, paid email copy, background email non-blocking, free+discount no-consume, rejected resubmit guard
import os
import sys
import time
import uuid
import asyncio
import pytest
import requests
from pymongo import MongoClient
from dotenv import dotenv_values

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
_env = dotenv_values("/app/backend/.env")
db = MongoClient(_env["MONGO_URL"])[_env["DB_NAME"]]
EMAIL = "delivered@resend.dev"
SESSIONS = []


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    orig = db.discounts.find_one({"code": "EARLY20"}, {"_id": 0})
    yield
    db.discounts.update_one({"code": "EARLY20"}, {"$set": {"uses": orig["uses"], "active": orig["active"], "featured": orig["featured"]}})
    if SESSIONS:
        db.orders.delete_many({"session_id": {"$in": SESSIONS}})


def checkout(pid, code="", headers=None):
    r = requests.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": pid, "customer_email": f"delivered+{uuid.uuid4().hex[:8]}@resend.dev", "discount_code": code}, headers=headers or {})
    if r.status_code == 200:
        SESSIONS.append(r.json()["session_id"])
    return r


@pytest.fixture(scope="module")
def es():
    sys.path.insert(0, "/app/backend")
    import email_service
    return email_service


# ---- email copy ----
def test_free_email_copy(es):
    subj, html = es.approval_email({"product_name": "A Calmer Week", "amount": 0, "session_id": "x"}, "https://shop.example.com/payment/success?session_id=x")
    assert "FREE TEMPLATE READY" in html
    assert "free" in subj.lower()
    assert "GPay" not in html and "PAYMENT CONFIRMED" not in html
    es._assert_safe_email(subj, html)


def test_paid_email_copy(es):
    subj, html = es.approval_email({"product_name": "The Weekly Reset", "amount": 399, "session_id": "x"}, "https://shop.example.com/payment/success?session_id=x")
    assert "PAYMENT CONFIRMED" in html and "GPay" in html
    assert "FREE TEMPLATE" not in html
    es._assert_safe_email(subj, html)


# ---- free checkout with discount ----
@pytest.mark.parametrize("pid", ["free-planner", "free-moodboard"])
def test_free_with_code_no_consume(pid):
    before = db.discounts.find_one({"code": "EARLY20"})["uses"]
    r = checkout(pid, code="EARLY20")
    assert r.status_code == 200 and r.json()["free"] is True
    st = requests.get(f"{BASE_URL}/api/payments/status/{r.json()['session_id']}").json()
    assert st["discount_code"] == "" and st["amount"] == 0 and st["payment_status"] == "paid"
    assert db.discounts.find_one({"code": "EARLY20"})["uses"] == before


def test_free_with_invalid_code_still_ok():
    r = checkout("free-planner", code="NOPE_BOGUS")
    assert r.status_code == 200 and r.json()["free"] is True


# ---- background email: response must not wait on email provider ----
def test_free_checkout_with_origin_is_fast_and_records_status():
    origin = BASE_URL
    t = time.time()
    r = checkout("free-moodboard", headers={"Origin": origin})
    elapsed = time.time() - t
    assert r.status_code == 200
    assert elapsed < 5, f"checkout took {elapsed:.1f}s"
    sid = r.json()["session_id"]
    status = None
    for _ in range(40):
        status = db.orders.find_one({"session_id": sid}).get("email_status")
        if status: break
        time.sleep(0.5)
    assert status in ("sent", "failed"), status
    print("email_status:", status, db.orders.find_one({"session_id": sid}).get("email_error"))


# ---- paid regression + rejected resubmit guard ----
def test_rejected_resubmit_guard():
    before = db.discounts.find_one({"code": "EARLY20"})["uses"]
    r = checkout("weekly-reset", code="EARLY20")
    sid = r.json()["session_id"]
    assert db.discounts.find_one({"code": "EARLY20"})["uses"] == before + 1
    assert requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TEST654321"}).status_code == 200
    # simulate owner rejection (same as review_order reject)
    db.orders.update_one({"session_id": sid}, {"$set": {"payment_status": "rejected"}})
    db.discounts.update_one({"code": "EARLY20", "uses": {"$gt": 0}}, {"$inc": {"uses": -1}})
    # exhaust code -> resubmit must be blocked
    orig = db.discounts.find_one({"code": "EARLY20"})
    db.discounts.update_one({"code": "EARLY20"}, {"$set": {"uses": orig["max_uses"]}})
    s = requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TEST654322"})
    assert s.status_code == 400
    db.discounts.update_one({"code": "EARLY20"}, {"$set": {"uses": orig["uses"]}})
    s = requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TEST654323"})
    assert s.status_code == 200 and s.json()["payment_status"] == "pending_review"
    assert db.discounts.find_one({"code": "EARLY20"})["uses"] == orig["uses"] + 1


def test_promo_endpoint():
    r = requests.get(f"{BASE_URL}/api/store/promo")
    assert r.status_code == 200
    d = r.json()
    assert d["code"] == "EARLY20" and d["percent"] == 20


@pytest.mark.parametrize("method,path", [("post", "/api/admin/orders/x/approve"), ("post", "/api/admin/orders/x/reject"),
                                         ("post", "/api/admin/discounts"), ("put", "/api/admin/settings"), ("post", "/api/admin/products")])
def test_admin_mutations_401(method, path):
    assert getattr(requests, method)(f"{BASE_URL}{path}", json={}).status_code == 401
