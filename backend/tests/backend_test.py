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


# Obsolete demo-checkout test removed (flow replaced by manual GPay, see test_gpay_flow.py)


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