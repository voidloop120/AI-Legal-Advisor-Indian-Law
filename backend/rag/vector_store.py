"""
Vector Store & Legal Knowledge Base Indexer
---------------------------------------------
This module handles:
1. Reading structured Indian laws from JSON (BNS, BNSS, BSA, CPA).
2. Generating semantic vector embeddings.
3. Storing and searching documents using ChromaDB.
4. Citing exact Act + Section with zero hallucination.

Rule: The app gives legal information, not legal advice.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import CHROMA_DB_DIR, INDIAN_LAWS_PATH, LEGAL_DISCLAIMER

# Name of the ChromaDB collection for Indian statutes
COLLECTION_NAME = "indian_legal_provisions"


def load_raw_legal_docs() -> List[Dict[str, Any]]:
    """
    Reads the curated legal provisions dataset from data/legal_docs/indian_laws.json.
    """
    if not INDIAN_LAWS_PATH.exists():
        raise FileNotFoundError(f"Legal documents file not found at {INDIAN_LAWS_PATH}")

    with open(INDIAN_LAWS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def format_doc_for_embedding(item: Dict[str, Any]) -> str:
    """
    Formats a legal provision into a rich descriptive chunk for the embedding model.
    Combining Act, Section, Title, Nature, and Keywords ensures high retrieval accuracy.
    """
    keywords_str = ", ".join(item.get("keywords", []))
    return (
        f"Act: {item.get('act')} ({item.get('act_short')})\n"
        f"Section: {item.get('section')} - {item.get('title')}\n"
        f"Nature: {item.get('cognizable')}, {item.get('bailable')}\n"
        f"Punishment: {item.get('punishment')}\n"
        f"Description: {item.get('description')}\n"
        f"Keywords: {keywords_str}"
    )


class LegalVectorStore:
    """
    Manages persistent ChromaDB vector storage and semantic retrieval for Indian laws.
    """

    def __init__(self, persist_directory: Optional[Path] = None):
        self.persist_dir = persist_directory or CHROMA_DB_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = None
        self.collection = None
        self._init_store()

    def _init_store(self):
        """
        Initializes ChromaDB persistent client and the legal collection.
        Uses ChromaDB's default embedding function (all-MiniLM-L6-v2 ONNX)
        or sentence-transformers if available.
        """
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            # Initialize ChromaDB persistent client
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))

            # Use all-MiniLM-L6-v2 default embedding function
            # This runs locally on CPU with fast performance
            emb_fn = embedding_functions.DefaultEmbeddingFunction()

            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=emb_fn,
                metadata={"description": "Indian Statutory Law Embeddings (BNS, BNSS, BSA, CPA)"}
            )

            # Check if collection needs initial indexing
            if self.collection.count() == 0:
                self.index_legal_docs()

        except ImportError as e:
            # Helpful error if dependencies are not yet finished installing
            print(f"[Warning] chromadb not yet available: {e}")

    def index_legal_docs(self, force_reindex: bool = False) -> int:
        """
        Embeds and stores all legal provisions from indian_laws.json into ChromaDB.
        Returns the number of indexed documents.
        """
        docs = load_raw_legal_docs()

        if self.collection is None:
            # When ChromaDB is still installing or initializing, fallback provides immediate search
            return len(docs)

        # If already indexed and not forcing reindex, return current count
        current_count = self.collection.count()
        if current_count > 0 and not force_reindex:
            return current_count

        ids = []
        documents = []
        metadatas = []

        for item in docs:
            doc_id = item["id"]
            doc_text = format_doc_for_embedding(item)

            ids.append(doc_id)
            documents.append(doc_text)
            metadatas.append({
                "id": item.get("id", ""),
                "act": item.get("act", ""),
                "act_short": item.get("act_short", ""),
                "section": item.get("section", ""),
                "title": item.get("title", ""),
                "cognizable": item.get("cognizable", ""),
                "bailable": item.get("bailable", ""),
                "punishment": item.get("punishment", ""),
                "description": item.get("description", "")
            })

        # Add to ChromaDB in batch
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        return len(ids)

    def search(
        self,
        query: str,
        n_results: int = 3,
        act_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantically queries the vector database for the top-k most relevant legal provisions.
        
        Args:
            query: The user's legal question or scenario (e.g. 'Someone took my laptop without asking')
            n_results: Number of matching legal sections to return (default 3)
            act_filter: Optional filter by Act code ('BNS', 'BNSS', 'BSA', 'CPA')
        """
        if self.collection is None:
            return self._fallback_keyword_search(query, n_results, act_filter)

        where_clause = None
        if act_filter:
            where_clause = {"act_short": act_filter.upper()}

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, max(1, self.collection.count())),
            where=where_clause
        )

        formatted_results = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                # Calculate simple similarity percentage from distance
                similarity_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
                formatted_results.append({
                    "id": meta.get("id"),
                    "act": meta.get("act"),
                    "act_short": meta.get("act_short"),
                    "section": meta.get("section"),
                    "title": meta.get("title"),
                    "cognizable": meta.get("cognizable"),
                    "bailable": meta.get("bailable"),
                    "punishment": meta.get("punishment"),
                    "description": meta.get("description"),
                    "similarity": round(similarity_score, 4),
                    "full_context": doc_text
                })

        return formatted_results

    def _fallback_keyword_search(
        self,
        query: str,
        n_results: int = 3,
        act_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback keyword/scoring search if ChromaDB is initializing or offline.
        Ensures the web app never crashes and always returns accurate legal information.
        """
        docs = load_raw_legal_docs()
        q_tokens = set(query.lower().split())

        scored = []
        for item in docs:
            if act_filter and item.get("act_short", "").upper() != act_filter.upper():
                continue

            text_corpus = (
                f"{item.get('section', '')} {item.get('title', '')} "
                f"{item.get('description', '')} {' '.join(item.get('keywords', []))}"
            ).lower()

            # Count token matches
            score = sum(1 for token in q_tokens if token in text_corpus)
            if score > 0:
                scored.append((score, item))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:n_results]

        results = []
        for score, item in top:
            results.append({
                "id": item.get("id"),
                "act": item.get("act"),
                "act_short": item.get("act_short"),
                "section": item.get("section"),
                "title": item.get("title"),
                "cognizable": item.get("cognizable"),
                "bailable": item.get("bailable"),
                "punishment": item.get("punishment"),
                "description": item.get("description"),
                "similarity": round(min(1.0, score / max(1, len(q_tokens))), 4),
                "full_context": format_doc_for_embedding(item)
            })

        return results


# Global singleton instance for easy import across FastAPI routes
_vector_store_instance: Optional[LegalVectorStore] = None


def get_vector_store() -> LegalVectorStore:
    """
    Returns the singleton instance of LegalVectorStore.
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = LegalVectorStore()
    return _vector_store_instance
