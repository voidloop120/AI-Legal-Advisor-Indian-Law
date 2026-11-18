"""
Unit tests for Law & Section Explorer API and dataset.
"""

from backend.routes.laws import list_or_search_laws, get_law_by_id, get_acts_metadata
from fastapi import HTTPException


def test_get_acts_metadata():
    """Verify that all 4 Indian legal acts are present with valid section counts."""
    acts = get_acts_metadata()
    codes = [a.code for a in acts]
    assert "BNS" in codes
    assert "BNSS" in codes
    assert "BSA" in codes
    assert "CPA" in codes
    for act in acts:
        assert act.count > 0


def test_list_all_laws():
    """Verify that listing laws without filters returns all 18 curated sections."""
    res = list_or_search_laws(act=None, search=None)
    assert res.total_count == 18
    assert len(res.laws) == 18
    assert "not constitute formal legal advice" in res.disclaimer


def test_filter_by_act():
    """Verify filtering by Act code works properly (case-insensitive)."""
    res_bns = list_or_search_laws(act="bns", search=None)
    assert res_bns.total_count == 6
    for law in res_bns.laws:
        assert law.act_short == "BNS"

    res_cpa = list_or_search_laws(act="CPA", search=None)
    assert res_cpa.total_count == 4
    for law in res_cpa.laws:
        assert law.act_short == "CPA"


def test_search_by_keyword():
    """Verify case-insensitive search by keyword (e.g. 'theft', 'bail', 'defamation')."""
    res_theft = list_or_search_laws(act=None, search="theft")
    assert res_theft.total_count >= 1
    sections = [l.section for l in res_theft.laws]
    assert "Section 303" in sections

    res_bail = list_or_search_laws(act="BNSS", search="anticipatory bail")
    assert res_bail.total_count >= 1
    assert any("482" in l.section for l in res_bail.laws)


def test_get_law_by_id_success():
    """Verify fetching a specific law by valid ID."""
    law = get_law_by_id("bns_303")
    assert law.id == "bns_303"
    assert law.section == "Section 303"
    assert law.title == "Theft"
    assert law.bailable == "Non-Bailable"
    assert law.cognizable == "Cognizable"


def test_get_law_by_id_not_found():
    """Verify that requesting a non-existent law ID raises 404."""
    try:
        get_law_by_id("unknown_section_999")
        assert False, "Should have raised HTTPException 404"
    except HTTPException as exc:
        assert exc.status_code == 404
