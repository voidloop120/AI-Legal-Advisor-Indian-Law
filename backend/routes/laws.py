"""
Law & Section Explorer API Routes
----------------------------------
Provides endpoints to browse, search, and inspect Indian statutory provisions:
- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)
- Consumer Protection Act, 2019 (CPA)

Rule: Always return legal information, not legal advice, and cite Act + Section.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.config import INDIAN_LAWS_PATH, LEGAL_DISCLAIMER

router = APIRouter(prefix="/api/laws", tags=["Laws & Sections"])


# ==========================================
# 1. Pydantic Models (Data Schemas)
# ==========================================

class LawItem(BaseModel):
    """Represents a single legal section in the knowledge base."""
    id: str = Field(..., examples=["bns_303"])
    act: str = Field(..., examples=["Bharatiya Nyaya Sanhita, 2023"])
    act_short: str = Field(..., examples=["BNS"])
    section: str = Field(..., examples=["Section 303"])
    title: str = Field(..., examples=["Theft"])
    description: str = Field(..., examples=["Punishes moving any movable property..."])
    punishment: str = Field(..., examples=["Imprisonment up to 3 years, or with fine..."])
    cognizable: str = Field(..., examples=["Cognizable"])
    bailable: str = Field(..., examples=["Non-Bailable"])
    keywords: List[str] = Field(default_factory=list)


class LawListResponse(BaseModel):
    """Response containing a list of laws and the mandatory legal disclaimer."""
    total_count: int
    disclaimer: str
    laws: List[LawItem]


class ActSummary(BaseModel):
    """Metadata for an Act to power filter tabs on the UI."""
    code: str
    name: str
    count: int


# ==========================================
# 2. Helper Functions
# ==========================================

def load_indian_laws() -> List[dict]:
    """
    Reads the curated legal dataset from data/legal_docs/indian_laws.json.
    Returns a Python list of dictionaries representing each legal section.
    """
    if not INDIAN_LAWS_PATH.exists():
        return []
    
    with open(INDIAN_LAWS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================================
# 3. Route Endpoints
# ==========================================

@router.get("/acts", response_model=List[ActSummary])
def get_acts_metadata():
    """
    Returns a list of all Acts available in the legal database,
    along with section count. Used to render filter tabs in the frontend.
    """
    laws = load_indian_laws()
    act_map = {
        "BNS": "Bharatiya Nyaya Sanhita, 2023",
        "BNSS": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "BSA": "Bharatiya Sakshya Adhiniyam, 2023",
        "CPA": "Consumer Protection Act, 2019",
    }
    
    # Count how many sections we have for each Act
    counts = {}
    for item in laws:
        short = item.get("act_short", "").upper()
        counts[short] = counts.get(short, 0) + 1

    result = []
    for code, full_name in act_map.items():
        result.append(
            ActSummary(
                code=code,
                name=full_name,
                count=counts.get(code, 0)
            )
        )
    return result


@router.get("", response_model=LawListResponse)
def list_or_search_laws(
    act: Optional[str] = Query(None, description="Filter by Act code: BNS, BNSS, BSA, CPA"),
    search: Optional[str] = Query(None, description="Search term for section, title, or keywords"),
):
    """
    Returns legal provisions matching optional filters:
    - act: filters by short code (e.g., 'BNS', 'BNSS', 'BSA', 'CPA')
    - search: searches case-insensitively across section numbers, titles, descriptions, and keywords.
    """
    laws = load_indian_laws()

    # Filter 1: By Act (if specified)
    if act:
        act_upper = act.strip().upper()
        laws = [item for item in laws if item.get("act_short", "").upper() == act_upper]

    # Filter 2: By Search Query (if specified)
    if search:
        query = search.strip().lower()

        def matches(item: dict) -> bool:
            # Check section number (e.g., "303")
            if query in item.get("section", "").lower():
                return True
            # Check title (e.g., "Theft")
            if query in item.get("title", "").lower():
                return True
            # Check description
            if query in item.get("description", "").lower():
                return True
            # Check keywords list
            for kw in item.get("keywords", []):
                if query in kw.lower():
                    return True
            return False

        laws = [item for item in laws if matches(item)]

    return LawListResponse(
        total_count=len(laws),
        disclaimer=LEGAL_DISCLAIMER,
        laws=[LawItem(**item) for item in laws],
    )


@router.get("/{law_id}", response_model=LawItem)
def get_law_by_id(law_id: str):
    """
    Fetches full information for a specific law by its ID (e.g. 'bns_303').
    """
    laws = load_indian_laws()
    law_id_clean = law_id.strip().lower()

    for item in laws:
        if item.get("id", "").lower() == law_id_clean:
            return LawItem(**item)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Law provision '{law_id}' was not found in the legal database.",
    )
