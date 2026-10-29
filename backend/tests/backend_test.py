import os

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


@pytest.fixture
def client():
    with requests.Session() as session:
        session.headers.update({"Content-Type": "application/json"})
        yield session


def test_public_products_and_detail(client):
    response = client.get(f"{BASE_URL}/api/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 1
    assert all("id" in product and product["published"] for product in products)

    detail = client.get(f"{BASE_URL}/api/products/{products[0]['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == products[0]["id"]


def test_demo_checkout_status_and_paid_download(client):
    products = client.get(f"{BASE_URL}/api/products").json()
    product = products[0]
    checkout = client.post(
        f"{BASE_URL}/api/payments/checkout",
        json={
            "product_id": product["id"],
            "customer_email": "TEST_ui@example.com",
            "origin_url": "https://example.test",
        },
    )
    assert checkout.status_code == 200
    checkout_data = checkout.json()
    assert checkout_data["payment_status"] == "paid"
    assert checkout_data["demo"] is True
    session_id = checkout_data["session_id"]

    status = client.get(f"{BASE_URL}/api/payments/status/{session_id}")
    assert status.status_code == 200
    assert status.json()["product_id"] == product["id"]

    download = client.get(f"{BASE_URL}/api/downloads/{session_id}")
    assert download.status_code == 200
    assert product["name"] in download.text
    assert "attachment" in download.headers.get("content-disposition", "")


def test_download_rejects_unknown_session(client):
    response = client.get(f"{BASE_URL}/api/downloads/TEST_unknown_session")
    assert response.status_code == 404
    assert "Download unavailable" in response.json()["detail"]


@pytest.mark.parametrize("endpoint", ["/api/admin/products", "/api/admin/orders"])
def test_admin_endpoints_require_authentication(client, endpoint):
    response = client.get(f"{BASE_URL}{endpoint}")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_clerk_config_is_available(client):
    response = client.get(f"{BASE_URL}/api/clerk/config")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert isinstance(data["publishable_key"], str) and data["publishable_key"]