"""
Legal RAG Indexer CLI
---------------------
Beginner-friendly script to build and verify the ChromaDB vector store
over Indian statutory provisions (BNS, BNSS, BSA, CPA).

How to run from terminal:
    python -m backend.rag.indexer

Rule: The app gives legal information, not legal advice.
"""

import sys
from backend.rag.vector_store import get_vector_store, load_raw_legal_docs
from backend.config import LEGAL_DISCLAIMER


def main():
    print("=" * 65)
    print("[AI Legal Advisor] - Knowledge Base Indexer")
    print("=" * 65)
    print(f"\n[LEGAL DISCLAIMER]\n{LEGAL_DISCLAIMER}\n")

    # 1. Load raw laws
    raw_docs = load_raw_legal_docs()
    print(f"[File] Loaded {len(raw_docs)} Indian legal sections from JSON.")

    # 2. Initialize Vector Store & Index
    print("[Store] Connecting to ChromaDB vector store...")
    vector_store = get_vector_store()
    
    count = vector_store.index_legal_docs(force_reindex=True)
    print(f"[Success] Indexed {count} legal documents in knowledge base.\n")

    # 3. Test sample queries to demonstrate semantic search
    sample_queries = [
        "What is the punishment for mobile theft or stealing goods?",
        "How can someone apply for anticipatory bail under BNSS?",
        "Can WhatsApp chat or email be submitted as electronic evidence?",
        "Company refused refund for defective goods and sent misleading ad."
    ]

    print("-" * 65)
    print("[Search] Running Sample Semantic Queries:")
    print("-" * 65)

    for query in sample_queries:
        print(f"\n[Query] '{query}'")
        matches = vector_store.search(query, n_results=1)

        if matches:
            top = matches[0]
            print(f"   Act:            {top['act']} ({top['act_short']})")
            print(f"   Section:        {top['section']} - {top['title']}")
            print(f"   Classification: {top['cognizable']} | {top['bailable']}")
            print(f"   Punishment:     {top['punishment']}")
            print(f"   Match Score:    {int(top['similarity'] * 100)}%")
        else:
            print("   [Notice] No matching legal section found in database.")

    print("\n" + "=" * 65)
    print("[Done] Knowledge Base index verified and ready for AI RAG chatbot!")
    print("=" * 65)


if __name__ == "__main__":
    main()
