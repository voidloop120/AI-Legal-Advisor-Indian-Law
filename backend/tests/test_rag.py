"""
Unit tests for RAG Knowledge Base and Vector Retrieval.
Tests document preparation, indexing, and legal semantic search.
"""

from backend.rag.vector_store import (
    load_raw_legal_docs,
    format_doc_for_embedding,
    LegalVectorStore,
    get_vector_store
)


def test_load_raw_legal_docs():
    """Verify that all legal documents are loaded with valid structure."""
    docs = load_raw_legal_docs()
    assert len(docs) >= 18
    for doc in docs:
        assert "id" in doc
        assert "act" in doc
        assert "act_short" in doc
        assert "section" in doc
        assert "title" in doc
        assert "description" in doc
        assert "punishment" in doc
        assert "cognizable" in doc
        assert "bailable" in doc


def test_format_doc_for_embedding():
    """Verify that documents are formatted with Act, Section, and Nature tags."""
    sample = {
        "id": "bns_303",
        "act": "Bharatiya Nyaya Sanhita, 2023",
        "act_short": "BNS",
        "section": "Section 303",
        "title": "Theft",
        "cognizable": "Cognizable",
        "bailable": "Non-Bailable",
        "punishment": "Up to 3 years",
        "description": "Moving property dishonestly.",
        "keywords": ["theft", "stolen"]
    }
    chunk = format_doc_for_embedding(sample)
    assert "Bharatiya Nyaya Sanhita" in chunk
    assert "Section 303" in chunk
    assert "Cognizable" in chunk
    assert "Non-Bailable" in chunk
    assert "Moving property dishonestly" in chunk


def test_vector_store_search_theft():
    """Verify that a query for theft retrieves BNS Section 303."""
    store = get_vector_store()
    results = store.search("punishment for stealing mobile phone or theft", n_results=3)
    assert len(results) > 0
    top = results[0]
    assert top["act_short"] == "BNS"
    assert "303" in top["section"]


def test_vector_store_search_evidence():
    """Verify that a query for digital evidence retrieves BSA Section 61 or 63."""
    store = get_vector_store()
    results = store.search("digital evidence electronic records whatsapp message", n_results=3)
    assert len(results) > 0
    acts = [r["act_short"] for r in results]
    assert "BSA" in acts


def test_vector_store_act_filter():
    """Verify that filtering by act_short only returns provisions from that Act."""
    store = get_vector_store()
    results = store.search("defect and compensation", n_results=3, act_filter="CPA")
    assert len(results) > 0
    for r in results:
        assert r["act_short"] == "CPA"
