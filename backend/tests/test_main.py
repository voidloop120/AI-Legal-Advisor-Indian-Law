"""
Basic unit tests for FastAPI main application and endpoints.
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    """Verify that the /api/health endpoint returns 200 and proper legal disclaimer."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "disclaimer" in data
    assert "not formal legal advice" in data["disclaimer"]

def test_disclaimer_endpoint():
    """Verify that the /api/disclaimer endpoint returns the legal disclaimer."""
    response = client.get("/api/disclaimer")
    assert response.status_code == 200
    data = response.json()
    assert "disclaimer" in data

def test_frontend_index_served():
    """Verify that visiting / serves the index.html frontend page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Legal Advisor" in response.text
