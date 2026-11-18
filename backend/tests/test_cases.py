"""
Unit tests for Case Management APIs and SQLite database integration.
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_cases():
    """Verify that GET /api/cases returns a list of cases."""
    response = client.get("/api/cases")
    assert response.status_code == 200
    cases = response.json()
    assert isinstance(cases, list)
    assert len(cases) >= 3  # Seeded initial cases
    first_case = cases[0]
    assert "case_number" in first_case
    assert "title" in first_case
    assert "current_stage" in first_case


def test_get_case_detail():
    """Verify that GET /api/cases/{id} returns details and journey timeline."""
    response = client.get("/api/cases/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "timeline" in data
    assert len(data["timeline"]) > 0
    first_stage = data["timeline"][0]
    assert "stage_name" in first_stage
    assert "status" in first_stage


def test_get_case_not_found():
    """Verify that requesting a non-existent case ID returns 404."""
    response = client.get("/api/cases/9999")
    assert response.status_code == 404


def test_create_case():
    """Verify that POST /api/cases creates a new case with default journey."""
    payload = {
        "title": "Cheque Bounce Notice",
        "case_type": "Negotiable Instruments Act",
        "police_station": "Financial Crimes Cell",
        "description": "Cheque bounced due to insufficient funds."
    }
    response = client.post("/api/cases", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["case_type"] == payload["case_type"]
    assert "case_number" in data
    assert len(data["timeline"]) == 6
