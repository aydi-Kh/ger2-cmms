"""Integration tests — requires a running backend at API_BASE_URL."""
import os
import pytest
import httpx

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")


@pytest.mark.integration
def test_health_endpoint_returns_200():
    response = httpx.get(f"{API_BASE}/health", timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.integration
def test_openapi_schema_accessible():
    response = httpx.get(f"{API_BASE}/api/v1/openapi.json", timeout=10)
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "GER2 CMMS API"


@pytest.mark.integration
def test_unauthenticated_assets_returns_401():
    response = httpx.get(f"{API_BASE}/api/v1/assets", timeout=10)
    assert response.status_code == 401


@pytest.mark.integration
def test_login_with_wrong_password_returns_401():
    response = httpx.post(f"{API_BASE}/api/v1/auth/login",
                          json={"email": "admin@ger2.tn", "password": "wrong"},
                          timeout=10)
    assert response.status_code == 401
