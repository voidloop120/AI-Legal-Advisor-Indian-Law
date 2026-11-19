"""
AI Legal Assistant - RAG (Retrieval-Augmented Generation) Engine
---------------------------------------------------------------
This module powers the AI Legal Advisor's Q&A capabilities.

How it works:
1. Takes a plain-language legal question from an Indian citizen.
2. Queries the LegalVectorStore (ChromaDB / curated provisions) for relevant statutes.
3. Strict Grounding:
   - If no relevant statutes match the question, it refuses to guess or invent law.
   - Always cites Act + Section (e.g. BNS Section 303, BNSS Section 35).
   - Appends the mandatory legal information disclaimer.
4. LLM Generation:
   - Supports Google Gemini API (gemini-1.5-flash / gemini-2.0-flash).
   - If no API key is provided, gracefully falls back to an intelligent template synthesizer
     so students can test offline without setup blockers.
"""

import os
import re
from typing import Any, Dict, List, Optional
from backend.config import LEGAL_DISCLAIMER
from backend.rag.vector_store import get_vector_store


# System prompt enforcing strict legal grounding and no hallucination
LEGAL_SYSTEM_PROMPT = f"""
You are "AI Legal Advisor", an intelligent legal information assistant for Indian citizens.
Your job is to explain Indian statutory law (Bharatiya Nyaya Sanhita [BNS], Bharatiya Nagarik Suraksha Sanhita [BNSS], 
Bharatiya Sakshya Adhiniyam [BSA], and Consumer Protection Act [CPA]) in clear, beginner-friendly language.

STRICT RULES YOU MUST NEVER BREAK:
1. CITATION REQUIREMENT: You MUST explicitly cite the specific Act and Section number for every legal rule or offense you mention (e.g., "Under Section 303 of the Bharatiya Nyaya Sanhita (BNS)...").
2. ZERO HALLUCINATION: You must base your answer ONLY on the provided legal provisions in the context. If the provided context does NOT contain relevant provisions to answer the question, you MUST say:
   "No matching legal provisions were found in the current statutory database for this question. Please consult a licensed legal advocate or District Legal Services Authority (DLSA) for guidance on this matter."
   Do NOT invent, assume, or extrapolate legal sections that are not in the context.
3. CLARITY: Explain legal jargon in simple terms (e.g., explain what cognizable or bailable means).
4. MANDATORY DISCLAIMER: Always remind the user that this is legal information for awareness, not formal legal advice.
"""


def format_context_for_llm(provisions: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved legal provisions into a structured context string for the LLM.
    """
    if not provisions:
        return "No statutory provisions found in database."

    context_blocks = []
    for idx, p in enumerate(provisions, 1):
        block = (
            f"--- Provision #{idx} ---\n"
            f"Act: {p.get('act')} ({p.get('act_short')})\n"
            f"Section: {p.get('section')} - {p.get('title')}\n"
            f"Nature: {p.get('cognizable', 'N/A')}, {p.get('bailable', 'N/A')}\n"
            f"Punishment / Remedy: {p.get('punishment', 'N/A')}\n"
            f"Statutory Text & Explanation: {p.get('description', '')}\n"
        )
        context_blocks.append(block)

    return "\n".join(context_blocks)


def synthesize_offline_response(query: str, provisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a clear, grounded response directly from the retrieved legal provisions
    without requiring an external API key or internet access.
    Ideal for offline lab testing, beginner demonstrations, and fallback reliability.
    """
    if not provisions:
        return {
            "answer": (
                "No matching legal provisions were found in the current statutory database "
                f"for '{query}'.\n\n"
                "Please verify the terms or consult a licensed advocate or your local "
                "District Legal Services Authority (DLSA)."
            ),
            "citations": [],
            "provisions_count": 0,
            "disclaimer": LEGAL_DISCLAIMER,
            "llm_used": "Offline Knowledge Synthesizer"
        }

    # Extract citations
    citations = []
    bullets = []
    for p in provisions:
        act = p.get("act_short", "")
        sec = p.get("section", "")
        title = p.get("title", "")
        punishment = p.get("punishment", "As prescribed by law")
        bailable = p.get("bailable", "")
        cognizable = p.get("cognizable", "")
        desc = p.get("description", "")

        citation_tag = f"{act} {sec}"
        citations.append({
            "act": p.get("act"),
            "act_short": act,
            "section": sec,
            "title": title,
            "tag": citation_tag
        })

        bullets.append(
            f"### {act} {sec}: {title}\n"
            f"- Summary: {desc}\n"
            f"- Classification: {cognizable} | {bailable}\n"
            f"- Punishment / Relief: {punishment}\n"
        )

    sections_text = "\n".join(bullets)
    answer = (
        f"Based on the Indian statutory codes currently indexed in the knowledge base, "
        f"here are the relevant legal provisions regarding your inquiry:\n\n"
        f"{sections_text}\n"
        f"**Next Steps for the Citizen:**\n"
        f"1. Keep all documentary evidence (receipts, messages, timestamps) in safe custody.\n"
        f"2. For criminal offenses that are cognizable, you may report to the nearest police station or cyber crime portal.\n"
        f"3. For consumer disputes, a formal complaint can be filed before the appropriate District Commission under the Consumer Protection Act."
    )

    return {
        "answer": answer,
        "citations": citations,
        "provisions_count": len(provisions),
        "disclaimer": LEGAL_DISCLAIMER,
        "llm_used": "Offline Knowledge Synthesizer"
    }


def call_gemini_api(prompt: str, api_key: str) -> Optional[str]:
    """
    Calls Google Gemini API using httpx for clean, non-blocking HTTP requests.
    Uses the latest Gemini Flash model for fast responses.
    """
    try:
        import httpx

        # Gemini REST API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,       # Low temperature for factual precision
                "topP": 0.8,
                "maxOutputTokens": 1000
            }
        }

        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                print(f"[Gemini API Notice] Status {response.status_code}: {response.text}")
                return None
    except Exception as e:
        print(f"[Gemini API Error] {e}")
        return None


class LegalAssistantEngine:
    """
    Orchestrates RAG retrieval, context validation, LLM prompting, and citations.
    """

    def __init__(self):
        self.vector_store = get_vector_store()

    def ask(self, question: str, n_provisions: int = 3, act_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Answers a user's legal question using RAG over Indian statutes.

        Args:
            question: Plain text question from user (e.g. 'What is the punishment for theft under BNS?')
            n_provisions: Max number of statutory provisions to retrieve (default 3)
            act_filter: Optional filter ('BNS', 'BNSS', 'BSA', 'CPA')
        """
        clean_question = question.strip()
        if not clean_question:
            return {
                "answer": "Please ask a specific legal question or describe your scenario.",
                "citations": [],
                "provisions_count": 0,
                "disclaimer": LEGAL_DISCLAIMER,
                "llm_used": "Validator"
            }

        # 1. Retrieve most relevant statutory provisions from ChromaDB / Knowledge Base
        provisions = self.vector_store.search(
            query=clean_question,
            n_results=n_provisions,
            act_filter=act_filter
        )

        # 2. Extract citations
        citations = []
        for p in provisions:
            citations.append({
                "act": p.get("act"),
                "act_short": p.get("act_short"),
                "section": p.get("section"),
                "title": p.get("title"),
                "tag": f"{p.get('act_short')} {p.get('section')}"
            })

        # 3. Check for Gemini API key
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        # If API key is present, prompt the LLM with strict grounding
        if api_key:
            context_text = format_context_for_llm(provisions)
            prompt = (
                f"{LEGAL_SYSTEM_PROMPT}\n\n"
                f"### RETRIEVED STATUTORY CONTEXT (INDIAN LAW):\n"
                f"{context_text}\n\n"
                f"### CITIZEN'S QUESTION:\n"
                f"{clean_question}\n\n"
                f"### YOUR RESPONSE (Remember to cite Act + Section, be beginner-friendly, and never invent law):\n"
            )

            llm_text = call_gemini_api(prompt, api_key)
            if llm_text:
                return {
                    "answer": llm_text.strip(),
                    "citations": citations,
                    "provisions_count": len(provisions),
                    "disclaimer": LEGAL_DISCLAIMER,
                    "llm_used": "Gemini 1.5 Flash"
                }

        # 4. Fallback to smart offline synthesizer if no API key or API call failed
        return synthesize_offline_response(clean_question, provisions)


# Global singleton instance
_assistant_engine: Optional[LegalAssistantEngine] = None


def get_assistant_engine() -> LegalAssistantEngine:
    """Returns the singleton instance of LegalAssistantEngine."""
    global _assistant_engine
    if _assistant_engine is None:
        _assistant_engine = LegalAssistantEngine()
    return _assistant_engine
