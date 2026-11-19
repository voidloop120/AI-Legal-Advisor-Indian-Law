"""
Unit tests for Case Management APIs and SQLite database integration.
"""

import pytest
from fastapi import HTTPException
from backend.routes.cases import list_cases, get_case, create_case, CaseCreateRequest


def test_list_cases():
    """Verify that list_cases returns a list of cases."""
    cases = list_cases()
    assert isinstance(cases, list)
    assert len(cases) >= 3  # Seeded initial cases
    first_case = cases[0]
    assert "case_number" in first_case
    assert "title" in first_case
    assert "current_stage" in first_case


def test_get_case_detail():
    """Verify that get_case returns details and journey timeline."""
    data = get_case(1)
    assert data["id"] == 1
    assert "timeline" in data
    assert len(data["timeline"]) > 0
    first_stage = data["timeline"][0]
    assert "stage_name" in first_stage
    assert "status" in first_stage


def test_get_case_not_found():
    """Verify that requesting a non-existent case ID raises 404."""
    with pytest.raises(HTTPException) as exc_info:
        get_case(9999)
    assert exc_info.value.status_code == 404


def test_create_case():
    """Verify that create_case creates a new case with default journey."""
    payload = CaseCreateRequest(
        title="Cheque Bounce Notice",
        case_type="Negotiable Instruments Act",
        police_station="Financial Crimes Cell",
        description="Cheque bounced due to insufficient funds."
    )
    data = create_case(payload)
    assert data["title"] == payload.title
    assert data["case_type"] == payload.case_type
    assert "case_number" in data
    assert len(data["timeline"]) == 6

