"""
Unit tests for FIR Analyzer module and API routes.
"""

import pytest
from fastapi import HTTPException
from backend.routes.fir import analyze_fir, get_sample_firs, FIRAnalyzeRequest
from backend.rag.fir_analyzer import SAMPLE_FIRS


def test_analyze_cyber_fraud_fir():
    """Verify analysis of cyber fraud FIR: BNS 318, Cognizable, Non-Bailable."""
    payload = FIRAnalyzeRequest(text=SAMPLE_FIRS["cyber_fraud"]["text"])
    res = analyze_fir(payload)

    assert res["status"] == "success"
    assert res["overall_classification"]["is_cognizable"] is True
    assert res["overall_classification"]["is_non_bailable"] is True
    assert "Rs. 45,000" in res["entities_detected"].get("financial_loss", "")

    # Verify that BNS Section 318 is in the matched sections
    sections = [s["section"] for s in res["matched_sections"]]
    assert "Section 318" in sections
    assert "not constitute formal legal advice" in res["disclaimer"] or "not formal legal advice" in res["disclaimer"]


def test_analyze_vehicle_theft_fir():
    """Verify analysis of motorcycle theft FIR: BNS 303 and vehicle registration extraction."""
    payload = FIRAnalyzeRequest(text=SAMPLE_FIRS["theft"]["text"])
    res = analyze_fir(payload)

    assert res["status"] == "success"
    assert res["overall_classification"]["is_cognizable"] is True
    assert "KA-03-HF-9821" in res["entities_detected"].get("vehicle_number", "")

    sections = [s["section"] for s in res["matched_sections"]]
    assert "Section 303" in sections


def test_get_sample_firs():
    """Verify that sample FIRs endpoint returns all 3 demonstration scenarios."""
    data = get_sample_firs()
    samples = data["samples"]
    assert "cyber_fraud" in samples
    assert "theft" in samples
    assert "assault_hurt" in samples
    assert "disclaimer" in data


def test_analyze_fir_insufficient_length():
    """Verify that submitting an FIR text less than 10 characters is rejected by Pydantic validation."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        FIRAnalyzeRequest(text="too short")

