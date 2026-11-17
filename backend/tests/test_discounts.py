# Regression tests: Morrow Market percentage discount codes (validate, checkout, max_uses, admin auth)
import os
import uuid
import concurrent.futures as cf
import pytest
import requests
from pymongo import MongoClient
from dotenv import dotenv_values

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
_env = dotenv_values("/app/backend/.env")
db = MongoClient(_env["MONGO_URL"])[_env["DB_NAME"]]
EMAIL = "TEST_disc@example.com"


def seed(code, percent, max_uses=None, active=True, uses=0):
    db.discounts.insert_one({"id": str(uuid.uuid4()), "code": code, "percent": percent, "max_uses": max_uses,
                             "uses": uses, "active": active, "created_at": "2026-01-01T00:00:00+00:00"})


@pytest.fixture(scope="module", autouse=True)
def data():
    db.discounts.delete_many({"code": {"$regex": "^TEST"}})
    seed("TESTTWENTY", 20)
    seed("TESTONCE", 10, max_uses=1)
    seed("TESTPAUSED", 30, active=False)
    seed("TESTUSEDUP", 15, max_uses=2, uses=2)
    seed("TESTRACE", 50, max_uses=3)
    yield
    db.discounts.delete_many({"code": {"$regex": "^TEST"}})
    db.orders.delete_many({"customer_email": {"$regex": "^test_disc", "$options": "i"}})


@pytest.fixture
def s():
    with requests.Session() as sess:
        yield sess


def uses(code): return db.discounts.find_one({"code": code})["uses"]


# Admin auth
@pytest.mark.parametrize("method,path,body", [
    ("get", "/api/admin/discounts", None),
    ("post", "/api/admin/discounts", {"code": "TESTX", "percent": 10}),
    ("patch", "/api/admin/discounts/abc", {"active": False}),
])
def test_admin_requires_auth(s, method, path, body):
    r = getattr(s, method)(f"{BASE_URL}{path}", json=body)
    assert r.status_code == 401, r.text
    r2 = getattr(s, method)(f"{BASE_URL}{path}", json=body, headers={"Authorization": "Bearer bad.token.here"})
    assert r2.status_code == 401, r2.text


# Validate
def test_validate_case_insensitive(s):
    r = s.post(f"{BASE_URL}/api/discounts/validate", json={"code": "  testtwenty ", "product_id": "weekly-reset"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d == {"code": "TESTTWENTY", "percent": 20, "original": 499, "final": 399}
    assert uses("TESTTWENTY") == 0  # validate does not consume


@pytest.mark.parametrize("code", ["NOPE123", "TESTPAUSED", "TESTUSEDUP", ""])
def test_validate_invalid(s, code):
    r = s.post(f"{BASE_URL}/api/discounts/validate", json={"code": code, "product_id": "weekly-reset"})
    assert r.status_code == 400, r.text
    assert "detail" in r.json()


def test_validate_bad_product(s):
    r = s.post(f"{BASE_URL}/api/discounts/validate", json={"code": "TESTTWENTY", "product_id": "nope"})
    assert r.status_code == 404


# Checkout
def test_checkout_with_code(s):
    r = s.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "quiet-brand", "customer_email": EMAIL, "discount_code": "testtwenty"})
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    o = s.get(f"{BASE_URL}/api/payments/status/{sid}").json()
    assert o["amount"] == 719 and o["original_amount"] == 899
    assert o["discount_code"] == "TESTTWENTY" and o["discount_percent"] == 20
    assert o["payment_status"] == "awaiting_payment"
    assert uses("TESTTWENTY") == 0  # abandoned checkout does not consume a use
    # A submitted payment reference consumes the use.
    r = s.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TESTUTR123456"})
    assert r.status_code == 200 and r.json()["payment_status"] == "pending_review"
    assert uses("TESTTWENTY") == 1


def test_checkout_without_code(s):
    r = s.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "slow-content", "customer_email": EMAIL})
    assert r.status_code == 200
    o = s.get(f"{BASE_URL}/api/payments/status/{r.json()['session_id']}").json()
    assert o["amount"] == 299 and o["discount_code"] == "" and o["discount_percent"] == 0


def test_max_uses_enforced_when_payment_is_submitted(s):
    body = {"product_id": "weekly-reset", "customer_email": EMAIL, "discount_code": "TESTONCE"}
    first = s.post(f"{BASE_URL}/api/payments/checkout", json=body)
    second = s.post(f"{BASE_URL}/api/payments/checkout", json=body)
    assert first.status_code == second.status_code == 200
    assert uses("TESTONCE") == 0
    sid1, sid2 = first.json()["session_id"], second.json()["session_id"]
    assert s.post(f"{BASE_URL}/api/payments/{sid1}/submit", json={"transaction_id": "TESTONCE11111"}).status_code == 200
    assert uses("TESTONCE") == 1
    assert s.post(f"{BASE_URL}/api/payments/{sid2}/submit", json={"transaction_id": "TESTONCE22222"}).status_code == 400
    v = s.post(f"{BASE_URL}/api/discounts/validate", json={"code": "TESTONCE", "product_id": "weekly-reset"})
    assert v.status_code == 400


@pytest.mark.parametrize("code", ["TESTPAUSED", "TESTUSEDUP", "BOGUS99"])
def test_checkout_rejects_bad_code(s, code):
    before = db.orders.count_documents({})
    r = s.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "weekly-reset", "customer_email": EMAIL, "discount_code": code})
    assert r.status_code == 400
    assert db.orders.count_documents({}) == before


def test_concurrent_checkout_does_not_consume_until_payment_submission():
    body = {"product_id": "weekly-reset", "customer_email": EMAIL, "discount_code": "TESTRACE"}
    with cf.ThreadPoolExecutor(8) as ex:
        responses = list(ex.map(lambda _: requests.post(f"{BASE_URL}/api/payments/checkout", json=body), range(8)))
    assert all(r.status_code == 200 for r in responses), [r.status_code for r in responses]
    assert uses("TESTRACE") == 0
    sessions = [r.json()["session_id"] for r in responses]
    def submit(i):
        return requests.post(f"{BASE_URL}/api/payments/{sessions[i]}/submit", json={"transaction_id": f"TESTRACEUTR{i:04d}"})
    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(submit, range(8)))
    assert [r.status_code for r in results].count(200) == 3, [r.status_code for r in results]
    assert [r.status_code for r in results].count(400) == 5, [r.status_code for r in results]
    assert uses("TESTRACE") == 3
