"""
Unit tests for AI Legal Assistant API and RAG pipeline.
"""

import pytest
from fastapi import HTTPException
from backend.routes.assistant import ask_legal_question, QuestionRequest


def test_ask_legal_question_theft():
    """Verify that asking about theft returns BNS Section 303 citation and legal disclaimer."""
    payload = QuestionRequest(question="What is the punishment for theft under BNS?")
    res = ask_legal_question(payload)
    assert res.provisions_count >= 1
    assert len(res.citations) >= 1
    citation_tags = [c.tag for c in res.citations]
    assert "BNS Section 303" in citation_tags
    assert "not constitute formal legal advice" in res.disclaimer or "not formal legal advice" in res.disclaimer


def test_ask_legal_question_unrelated():
    """
    Verify zero hallucination rule:
    When an unrelated question is asked, provisions_count is 0 and no citations are invented.
    """
    payload = QuestionRequest(question="How to bake a chocolate cake in space?")
    res = ask_legal_question(payload)
    assert res.provisions_count == 0
    assert len(res.citations) == 0
    assert "No matching legal provisions" in res.answer


def test_ask_legal_question_consumer_filter():
    """Verify that asking with CPA filter only retrieves Consumer Protection Act provisions."""
    payload = QuestionRequest(
        question="How do I file a consumer complaint for defective goods?",
        act_filter="CPA"
    )
    res = ask_legal_question(payload)
    assert res.provisions_count >= 1
    for citation in res.citations:
        assert citation.act_short == "CPA"


def test_ask_empty_question():
    """Verify that blank questions raise HTTPException 400."""
    with pytest.raises(HTTPException) as exc_info:
        ask_legal_question(QuestionRequest(question="   "))
    assert exc_info.value.status_code == 400
