"""
API Routes for FIR (First Information Report) Analysis
------------------------------------------------------
Provides endpoints to:
1. Analyze raw or pasted FIR text against BNS and BNSS statutes.
2. Upload .txt FIR files.
3. Fetch pre-loaded sample FIR scenarios for demonstration.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.config import LEGAL_DISCLAIMER
from backend.rag.fir_analyzer import SAMPLE_FIRS, analyze_fir_text

router = APIRouter(prefix="/api/fir", tags=["FIR Analyzer"])


# ==========================================
# 1. Pydantic Schemas
# ==========================================

class FIRAnalyzeRequest(BaseModel):
    """Payload when sending FIR text or uploaded file text for analysis."""
    text: str = Field(
        ...,
        min_length=10,
        description="The full narrative or complaint text of the FIR."
    )
    file_name: Optional[str] = Field(
        None,
        description="Optional name of the uploaded document (e.g. fir_complaint.txt)."
    )


class MatchedSectionInfo(BaseModel):
    """Statutory details for an alleged offense."""
    act: str
    section: str
    title: str
    punishment: Optional[str] = None
    cognizable: Optional[str] = None
    bailable: Optional[str] = None
    description: Optional[str] = None


class ClassificationSummary(BaseModel):
    """Overall classification of the FIR."""
    nature: str
    bail_status: str
    is_cognizable: bool
    is_non_bailable: bool


class FIRAnalyzeResponse(BaseModel):
    """Complete structured analysis returned to the client."""
    status: str
    fir_length_chars: int
    entities_detected: Dict[str, Any]
    overall_classification: ClassificationSummary
    matched_sections: List[MatchedSectionInfo]
    arrest_power_guidance: str
    bail_guidance: str
    citizen_rights_and_steps: List[str]
    disclaimer: str


# ==========================================
# 2. Endpoints
# ==========================================

@router.post("/analyze", response_model=FIRAnalyzeResponse)
def analyze_fir(payload: FIRAnalyzeRequest):
    """
    Analyzes an FIR narrative or uploaded document text.
    Extracts entities, matches offenses to BNS sections,
    and returns bail and arrest classifications under BNSS.
    """
    clean_text = payload.text.strip()
    if len(clean_text) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FIR narrative must be at least 10 characters long to perform legal analysis."
        )

    result = analyze_fir_text(clean_text)
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return result


@router.get("/samples")
def get_sample_firs():
    """
    Returns curated sample FIR scenarios (Cyber fraud, Theft, Assault)
    so users and evaluators can test with 1-click.
    """
    return {
        "samples": SAMPLE_FIRS,
        "disclaimer": LEGAL_DISCLAIMER
    }

