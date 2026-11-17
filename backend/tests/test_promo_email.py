# Regression tests: Festive promo banner API (/api/store/promo), featured auto-apply, admin auth on toggle/resend, approval email helper
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
EMAIL = "TEST_promo@example.com"


def early(**changes):
    db.discounts.update_one({"code": "EARLY20"}, {"$set": changes})


@pytest.fixture(scope="module", autouse=True)
def restore():
    orig = db.discounts.find_one({"code": "EARLY20"}, {"_id": 0})
    assert orig, "EARLY20 seed missing"
    yield
    db.discounts.update_one({"code": "EARLY20"}, {"$set": {"featured": True, "active": True, "uses": 0, "max_uses": orig.get("max_uses", 50)}})
    db.discounts.delete_many({"code": {"$regex": "^TESTP"}})
    db.orders.delete_many({"customer_email": {"$regex": "^test_promo", "$options": "i"}})


@pytest.fixture(autouse=True)
def reset_early():
    early(featured=True, active=True, uses=0, max_uses=50)
    yield


# ---- /api/store/promo ----
def test_promo_featured():
    r = requests.get(f"{BASE_URL}/api/store/promo")
    assert r.status_code == 200
    assert r.json() == {"code": "EARLY20", "percent": 20, "remaining": 50}


def test_promo_remaining_reflects_uses():
    early(uses=7)
    assert requests.get(f"{BASE_URL}/api/store/promo").json()["remaining"] == 43


@pytest.mark.parametrize("changes", [{"featured": False}, {"active": False}, {"uses": 50}])
def test_promo_null(changes):
    early(**changes)
    r = requests.get(f"{BASE_URL}/api/store/promo")
    assert r.status_code == 200
    assert r.json() is None


def test_promo_unlimited_remaining_null():
    early(featured=False)
    db.discounts.delete_many({"code": "TESTPUNL"})
    db.discounts.insert_one({"id": str(uuid.uuid4()), "code": "TESTPUNL", "percent": 10, "max_uses": None, "uses": 3,
                             "active": True, "featured": True, "created_at": "2026-01-01T00:00:00+00:00"})
    try:
        assert requests.get(f"{BASE_URL}/api/store/promo").json() == {"code": "TESTPUNL", "percent": 10, "remaining": None}
    finally:
        db.discounts.delete_many({"code": "TESTPUNL"})


# ---- validate/checkout with featured code ----
def test_validate_and_checkout_early20():
    v = requests.post(f"{BASE_URL}/api/discounts/validate", json={"code": "EARLY20", "product_id": "weekly-reset"})
    assert v.status_code == 200 and v.json() == {"code": "EARLY20", "percent": 20, "original": 499, "final": 399}
    r = requests.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "weekly-reset", "customer_email": EMAIL, "discount_code": "EARLY20"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    o = requests.get(f"{BASE_URL}/api/payments/status/{sid}").json()
    assert o["amount"] == 399 and o["original_amount"] == 499 and o["discount_code"] == "EARLY20"
    assert db.discounts.find_one({"code": "EARLY20"})["uses"] == 1
    assert requests.get(f"{BASE_URL}/api/store/promo").json()["remaining"] == 49
    s = requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TESTUTR998877"})
    assert s.status_code == 200 and s.json()["payment_status"] == "pending_review"


# ---- admin auth ----
@pytest.mark.parametrize("method,path,body", [
    ("patch", "/api/admin/discounts/abc", {"featured": True}),
    ("patch", "/api/admin/discounts/abc", {"active": False}),
    ("post", "/api/admin/orders/abc/resend-email", {}),
    ("post", "/api/admin/orders/abc/approve", {}),
])
def test_admin_requires_auth(method, path, body):
    for h in ({}, {"Authorization": "Bearer bad.token.here"}):
        r = getattr(requests, method)(f"{BASE_URL}{path}", json=body, headers=h)
        assert r.status_code == 401, r.text
    assert db.discounts.find_one({"code": "EARLY20"})["featured"] is True


# ---- email helper (in-process, send_email mocked; no real mail sent) ----
class FakeReq:
    def __init__(self, origin): self.headers = {"origin": origin} if origin else {}


@pytest.fixture(scope="module")
def server_mod():
    sys.path.insert(0, "/app/backend")
    import server
    import email_service
    return server, email_service


@pytest.mark.parametrize("origin,expect", [
    ("https://shop.example.com", "sent"), ("http://shop.example.com", "failed"), ("", "failed")])
def test_email_customer(server_mod, origin, expect):
    server, es = server_mod
    sent = []

    async def fake_send(*, to, subject, html):
        es._assert_safe_email(subject, html)
        sent.append((to, subject, html)); return "id1"
    server.send_email = fake_send
    oid, sid = str(uuid.uuid4()), uuid.uuid4().hex
    db.orders.insert_one({"id": oid, "session_id": sid, "product_id": "weekly-reset", "product_name": "The Weekly Reset",
                          "customer_email": EMAIL, "payment_status": "paid", "amount": 399})

    async def run():
        from motor.motor_asyncio import AsyncIOMotorClient
        server.db = AsyncIOMotorClient(_env["MONGO_URL"])[_env["DB_NAME"]]
        return await server.email_customer(db.orders.find_one({"id": oid}, {"_id": 0}), FakeReq(origin))
    out = asyncio.run(run())
    assert out["email_status"] == expect
    assert "_id" not in out
    if expect == "sent":
        assert sent[0][0] == EMAIL
        assert f"https://shop.example.com/payment/success?session_id={sid}" in sent[0][2]
    else:
        assert not sent and out["email_error"]
