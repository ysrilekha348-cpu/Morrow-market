# Iteration 9: refactor regression - email safety validator, storage _request, download of stored files
import os
import sys
import pytest
import requests
from pymongo import MongoClient
from dotenv import dotenv_values, load_dotenv

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")
import email_service as es  # noqa: E402
import storage  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
_env = dotenv_values("/app/backend/.env")
db = MongoClient(_env["MONGO_URL"])[_env["DB_NAME"]]
created = []


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    for sid in created:
        db.orders.delete_one({"session_id": sid})


# _assert_safe_email
@pytest.mark.parametrize("html", [
    '<form><input name="x"></form>',
    '<textarea></textarea>',
    '<a href="http://example.com">x</a>',
    '<img src="/relative.png">',
    '<a href="https://bit.ly/abc">x</a>',
    '<a href="https://sub.tinyurl.com/a">x</a>',
    '<a href="https://192.168.1.1/a">x</a>',
    '<a href="https://user@example.com/a">x</a>',
    '<a href="https://xn--pple-43d.com">x</a>',
    '<a href="https://evil.com/login">paypal.com</a>',
    '<p>Please reply with your password</p>',
])
def test_unsafe_rejected(html):
    with pytest.raises(ValueError):
        es._assert_safe_email("Hello", html)


def test_cred_ask_in_subject_rejected():
    with pytest.raises(ValueError):
        es._assert_safe_email("Verify your card now", "<p>hi</p>")


@pytest.mark.parametrize("html", [
    '<a href="mailto:a@b.com">mail</a><a href="#top">top</a><a href="tel:123">t</a>',
    '<a href="https://shop.example.com/x">example.com</a>',
    '<a href="https://example.com/x">Open my download</a>',
])
def test_safe_accepted(html):
    es._assert_safe_email("Your download", html)


@pytest.mark.parametrize("amount", [0, 299])
def test_approval_email_passes(amount):
    subj, html = es.approval_email({"product_name": "Quiet Brand Kit <b>", "amount": amount},
                                   f"{BASE_URL}/payment/success?session_id=abc&x=1")
    es._assert_safe_email(subj, html)
    assert "Open my download" in html
    if amount:
        assert "&lt;b&gt;" in html and "<b>" not in html


# storage get/put via refactored _request
def test_storage_roundtrip():
    path = f"{storage.APP_NAME}/tests/TEST_iter9.txt"
    storage.put_object(path, b"hello-iter9", "text/plain")
    data, ctype = storage.get_object(path)
    assert data == b"hello-iter9"


def test_storage_missing_raises():
    with pytest.raises(requests.HTTPError):
        storage.get_object(f"{storage.APP_NAME}/tests/does-not-exist-iter9.bin")


# Paid product with storage_path downloads the stored file
def test_paid_download_serves_stored_file():
    prod = db.products.find_one({"id": "money-map"}, {"_id": 0})
    assert prod and prod.get("storage_path")
    r = requests.post(f"{BASE_URL}/api/payments/checkout",
                      json={"product_id": "money-map", "customer_email": "TEST_iter9@example.com"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    created.append(sid)
    db.orders.update_one({"session_id": sid}, {"$set": {"payment_status": "paid"}})
    d = requests.get(f"{BASE_URL}/api/downloads/{sid}")
    assert d.status_code == 200
    stored, _ = storage.get_object(prod["storage_path"])
    assert d.content == stored
