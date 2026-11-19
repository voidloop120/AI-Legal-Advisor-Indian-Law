"""
Unit tests for Authentication module (Login, Register, Demo credentials).
"""

import pytest
from fastapi import HTTPException
from backend.routes.auth import login_user, register_user, get_demo_credentials, LoginRequest, RegisterRequest


def test_login_demo_user_success():
    """Verify that the pre-seeded demo user 'ankit' logs in successfully."""
    payload = LoginRequest(username="ankit", password="legal123")
    res = login_user(payload)

    assert res.status == "success"
    assert res.user.username == "ankit"
    assert res.user.full_name == "Ankit Sharma"
    assert len(res.token) > 0
    assert "not constitute formal legal advice" in res.disclaimer or "not formal legal advice" in res.disclaimer


def test_login_invalid_password():
    """Verify that an incorrect password raises HTTPException 401."""
    payload = LoginRequest(username="ankit", password="wrongpassword")
    with pytest.raises(HTTPException) as exc_info:
        login_user(payload)
    assert exc_info.value.status_code == 401


def test_register_new_user():
    """Verify that a new citizen can register successfully."""
    import time
    unique_suffix = int(time.time() * 1000)
    payload = RegisterRequest(
        username=f"citizen_{unique_suffix}",
        full_name="Priya Patel",
        email=f"priya_{unique_suffix}@example.com",
        password="secretpassword"
    )
    res = register_user(payload)

    assert res.status == "success"
    assert res.user.full_name == "Priya Patel"
    assert res.user.id > 0
    assert res.user.username == f"citizen_{unique_suffix}"


def test_register_duplicate_username():
    """Verify that registering an existing username raises HTTPException 409."""
    payload = RegisterRequest(
        username="ankit",
        full_name="Another Ankit",
        email="another_ankit@example.com",
        password="somepassword"
    )
    with pytest.raises(HTTPException) as exc_info:
        register_user(payload)
    assert exc_info.value.status_code == 409


def test_get_demo_credentials():
    """Verify that demo credentials endpoint returns ankit and legal123."""
    creds = get_demo_credentials()
    assert creds["username"] == "ankit"
    assert creds["password"] == "legal123"
