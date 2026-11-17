# Iteration 8: 10 more paid templates - catalog (30 total), detail, downloads, distinct content, regressions
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
    "study-planner": (149, "Education", "study-planner.pdf"),
    "reading-journal": (99, "Lifestyle", "reading-journal.pdf"),
    "wedding-planner": (299, "Finance", "wedding-planner-bundle.zip"),
    "travel-planner": (199, "Travel", "travel-planner.pdf"),
    "moving-home": (149, "Home", "moving-home.pdf"),
    "pet-care": (129, "Home", "pet-care.pdf"),
    "fitness-log": (149, "Wellbeing", "fitness-log.pdf"),
    "digital-detox": (99, "Wellbeing", "digital-detox.pdf"),
    "gift-planner": (99, "Lifestyle", "gift-planner.pdf"),
    "course-launch": (299, "Business", "course-launch-bundle.zip"),
}
CREATED_SESSIONS = []
CONTENT = {}


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
    CREATED_SESSIONS.append(r.json()["session_id"])
    return r.json()


def paid_download(pid):
    sid = make_order(pid)["session_id"]
    mongo.orders.update_one({"session_id": sid}, {"$set": {"payment_status": "paid"}})
    return requests.get(f"{BASE_URL}/api/downloads/{sid}")


class TestCatalog:
    def test_total_30(self):
        r = requests.get(f"{BASE_URL}/api/products")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 30, len(items)
        assert sum(1 for p in items if p["price"] > 0) == 28
        assert sum(1 for p in items if p["price"] == 0) == 2
        data = {p["id"]: p for p in items}
        for pid, (price, cat, fname) in NEW.items():
            assert pid in data, pid
            assert data[pid]["price"] == price, pid
            assert data[pid]["category"] == cat, pid
            assert data[pid]["file_name"] == fname, pid
            assert "_id" not in data[pid]

    def test_unique_images(self):
        items = requests.get(f"{BASE_URL}/api/products").json()
        imgs = [p["image_url"] for p in items]
        dups = {i for i in imgs if imgs.count(i) > 1}
        assert not dups, dups

    @pytest.mark.parametrize("pid", list(NEW))
    def test_detail(self, pid):
        r = requests.get(f"{BASE_URL}/api/products/{pid}")
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == pid and d["price"] == NEW[pid][0] and d["name"] and d["description"]

    def test_storage_paths(self):
        for pid in NEW:
            p = mongo.products.find_one({"id": pid})
            assert p.get("storage_path"), pid
            assert p.get("file_size", 0) > 1000, pid


class TestDownloads:
    @pytest.mark.parametrize("pid", list(NEW))
    def test_paid_download(self, pid):
        r = paid_download(pid)
        assert r.status_code == 200, r.text
        fname = NEW[pid][2]
        assert fname in r.headers.get("content-disposition", "")
        if fname.endswith(".pdf"):
            assert r.headers["content-type"].startswith("application/pdf")
            assert r.content[:4] == b"%PDF"
        else:
            assert r.headers["content-type"].startswith("application/zip")
            z = zipfile.ZipFile(io.BytesIO(r.content))
            names = z.namelist()
            assert any(n.endswith(".pdf") for n in names), names
            assert any(n.endswith(".xlsx") for n in names), names
            for n in names:
                if n.endswith(".pdf"):
                    assert z.read(n)[:4] == b"%PDF"
                if n.endswith(".xlsx"):
                    assert "xl/workbook.xml" in zipfile.ZipFile(io.BytesIO(z.read(n))).namelist()

    def test_downloads_distinct_and_match_local(self):
        seed = Path(__file__).resolve().parents[1] / "seed_files"
        hashes = {}
        for pid, (_, _, fname) in NEW.items():
            r = paid_download(pid)
            assert r.status_code == 200
            local = seed / fname
            assert local.exists(), fname
            assert r.content == local.read_bytes(), f"{pid} served file differs from local seed file"
            hashes[pid] = hash(r.content)
        assert len(set(hashes.values())) == len(hashes)

    def test_unpaid_blocked(self):
        sid = make_order("course-launch")["session_id"]
        assert requests.get(f"{BASE_URL}/api/downloads/{sid}").status_code == 404


class TestRegressions:
    def test_first15_served_matches_local(self):
        seed = Path(__file__).resolve().parents[1] / "seed_files"
        for pid in ["money-map", "content-batch", "self-care"]:
            p = mongo.products.find_one({"id": pid})
            r = paid_download(pid)
            assert r.status_code == 200
            assert r.content == (seed / p["file_name"]).read_bytes(), pid

    def test_early20_new_product(self):
        v = requests.post(f"{BASE_URL}/api/discounts/validate", json={"code": "early20", "product_id": "wedding-planner"})
        assert v.status_code == 200 and v.json()["final"] == 239
        res = make_order("wedding-planner", "EARLY20")
        st = requests.get(f"{BASE_URL}/api/payments/status/{res['session_id']}").json()
        assert st["amount"] == 239 and st["discount_code"] == "EARLY20"

    def test_gpay_submit(self):
        sid = make_order("travel-planner")["session_id"]
        r = requests.post(f"{BASE_URL}/api/payments/{sid}/submit", json={"transaction_id": "TEST123456"})
        assert r.status_code == 200 and r.json()["payment_status"] == "pending_review"
        assert requests.get(f"{BASE_URL}/api/downloads/{sid}").status_code == 404

    def test_free_still_free(self):
        r = requests.post(f"{BASE_URL}/api/payments/checkout", json={"product_id": "free-moodboard", "customer_email": f"test_{uuid.uuid4().hex[:6]}@example.com", "discount_code": ""})
        assert r.status_code == 200 and r.json()["free"] is True
        CREATED_SESSIONS.append(r.json()["session_id"])
        d = requests.get(f"{BASE_URL}/api/downloads/{r.json()['session_id']}")
        assert d.status_code == 200 and d.content[:4] == b"%PDF"

    @pytest.mark.parametrize("path", ["/api/admin/products", "/api/admin/orders", "/api/admin/discounts", "/api/admin/settings"])
    def test_admin_protected(self, path):
        assert requests.get(f"{BASE_URL}{path}").status_code in (401, 403)
