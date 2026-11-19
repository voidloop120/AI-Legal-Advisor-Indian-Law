"""
Basic unit tests for FastAPI main application and endpoints.
"""
from backend.main import health_check, get_disclaimer
from backend.config import FRONTEND_DIR


def test_health_check():
    """Verify that health_check returns 200 and proper legal disclaimer."""
    data = health_check()
    assert data["status"] == "healthy"
    assert "disclaimer" in data
    assert "not constitute formal legal advice" in data["disclaimer"]


def test_disclaimer_endpoint():
    """Verify that get_disclaimer returns the legal disclaimer."""
    data = get_disclaimer()
    assert "disclaimer" in data
    assert "not constitute formal legal advice" in data["disclaimer"] or "not formal legal advice" in data["disclaimer"]


def test_frontend_index_exists():
    """Verify that index.html exists in the frontend directory."""
    index_file = FRONTEND_DIR / "index.html"
    assert index_file.exists()
    content = index_file.read_text(encoding="utf-8")
    assert "AI Legal Advisor" in content

