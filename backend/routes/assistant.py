"""
API Route for AI Legal Assistant
---------------------------------
Accepts legal questions from the citizen, passes them through the RAG engine,
and returns an answer with statutory citations (Act + Section) and a legal disclaimer.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.rag.assistant import get_assistant_engine
from backend.config import LEGAL_DISCLAIMER

router = APIRouter(prefix="/api/assistant", tags=["AI Legal Assistant"])


# ==========================================
# 1. Pydantic Schemas
# ==========================================

class QuestionRequest(BaseModel):
    """Payload sent by the frontend chat interface."""
    question: str = Field(
        ...,
        min_length=2,
        description="The legal question or situation described by the user."
    )
    n_provisions: Optional[int] = Field(
        3,
        ge=1,
        le=5,
        description="Number of statutory provisions to retrieve."
    )
    act_filter: Optional[str] = Field(
        None,
        description="Optional filter by Act code: 'BNS', 'BNSS', 'BSA', or 'CPA'."
    )


class CitationItem(BaseModel):
    """Details of a cited legal section."""
    act: Optional[str] = None
    act_short: Optional[str] = None
    section: Optional[str] = None
    title: Optional[str] = None
    tag: str


class AssistantResponse(BaseModel):
    """The complete response returned to the user."""
    question: str
    answer: str
    citations: List[CitationItem]
    provisions_count: int
    disclaimer: str
    llm_used: str


# ==========================================
# 2. Endpoints
# ==========================================

@router.post("/ask", response_model=AssistantResponse)
def ask_legal_question(payload: QuestionRequest):
    """
    Receives a legal question, performs RAG retrieval over Indian statutes,
    and returns a cited legal answer.
    Never hallucinates: if no statutory provision is found, it explicitly states so.
    """
    clean_question = payload.question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or blank."
        )

    engine = get_assistant_engine()
    result = engine.ask(
        question=clean_question,
        n_provisions=payload.n_provisions or 3,
        act_filter=payload.act_filter
    )

    return AssistantResponse(
        question=clean_question,
        answer=result["answer"],
        citations=result["citations"],
        provisions_count=result["provisions_count"],
        disclaimer=result.get("disclaimer", LEGAL_DISCLAIMER),
        llm_used=result.get("llm_used", "AI Assistant Engine")
    )
