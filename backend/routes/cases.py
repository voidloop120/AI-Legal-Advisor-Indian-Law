"""
API routes for Case Management and Case Journey.
Allows creating new cases, fetching all cases, and inspecting timeline stages.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.database import get_db_connection

router = APIRouter(prefix="/api/cases", tags=["Cases"])


# ==========================================
# 1. Pydantic Schemas (Data Validation)
# ==========================================

class CaseCreateRequest(BaseModel):
    """Input payload when a user creates a new case."""
    title: str = Field(..., example="Motor Vehicle Accident")
    case_type: str = Field(..., example="Criminal - FIR")
    police_station: Optional[str] = Field("Local Police Station", example="Indiranagar PS")
    description: Optional[str] = Field("", example="Accident on 14th Main road involving two vehicles.")


class TimelineStageResponse(BaseModel):
    """A single stage in the case journey."""
    id: int
    stage_name: str
    stage_order: int
    status: str       # 'completed', 'current', or 'pending'
    stage_date: Optional[str] = None
    description: Optional[str] = None


class CaseSummaryResponse(BaseModel):
    """Summary of a case for the My Cases list."""
    id: int
    case_number: str
    title: str
    case_type: str
    police_station: Optional[str]
    current_stage: str
    status: str
    progress_percent: int
    created_at: str


class CaseDetailResponse(CaseSummaryResponse):
    """Detailed case information including timeline journey."""
    description: Optional[str]
    timeline: List[TimelineStageResponse] = []


# ==========================================
# 2. Route Endpoints
# ==========================================

@router.get("", response_model=List[CaseSummaryResponse])
def list_cases():
    """
    Returns all cases stored in the database, ordered by latest first.
    Used to populate the 'My Cases' section on the dashboard.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, case_number, title, case_type, police_station,
               current_stage, status, progress_percent, created_at
        FROM cases
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    # Convert sqlite3.Row objects to standard dictionaries
    return [dict(row) for row in rows]


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: int):
    """
    Fetches details of a specific case, including all journey/timeline stages.
    Used to update the 'Case Journey' panel.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch case header
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    case_row = cursor.fetchone()

    if not case_row:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found."
        )

    # Fetch timeline stages for this case
    cursor.execute("""
        SELECT id, stage_name, stage_order, status, stage_date, description
        FROM case_timeline
        WHERE case_id = ?
        ORDER BY stage_order ASC
    """, (case_id,))
    timeline_rows = cursor.fetchall()
    conn.close()

    case_dict = dict(case_row)
    case_dict["timeline"] = [dict(t) for t in timeline_rows]
    return case_dict


@router.post("", response_model=CaseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreateRequest):
    """
    Creates a new legal case with standard Indian legal process timeline stages.
    Called when a user submits the 'Start New Case' form.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate a sequential case number, e.g. "2026-004"
    cursor.execute("SELECT COUNT(*) AS total FROM cases")
    total = cursor.fetchone()["total"]
    year = datetime.now().year
    case_number = f"{year}-{(total + 1):03d}"

    now_iso = datetime.now().isoformat()
    initial_stage = "FIR Registered"
    initial_status = "Active"
    initial_progress = 15

    cursor.execute("""
        INSERT INTO cases (case_number, title, case_type, police_station, current_stage, status, progress_percent, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_number,
        payload.title,
        payload.case_type,
        payload.police_station or "N/A",
        initial_stage,
        initial_status,
        initial_progress,
        payload.description or "",
        now_iso
    ))
    case_id = cursor.lastrowid

    # Create the standard roadmap of stages for this new case
    default_stages = [
        ("FIR Registered", "completed", datetime.now().strftime("%d %b %Y"), "FIR registered and initial details recorded."),
        ("Investigation", "current", "In Progress", "Police inquiry, evidence gathering, and statement recording."),
        ("Charge Sheet", "pending", "Upcoming", "Preparation and filing of police report in Magistrate Court."),
        ("Court Proceedings", "pending", "Upcoming", "Court takes cognizance; summons/bailable warrant issued."),
        ("Hearing", "pending", "Upcoming", "Evidence framing, examination of witnesses, arguments."),
        ("Final Order", "pending", "Upcoming", "Judgment or final compound order passed by the Court.")
    ]

    for order, (stage_name, stage_status, stage_date, desc) in enumerate(default_stages, start=1):
        cursor.execute("""
            INSERT INTO case_timeline (case_id, stage_name, stage_order, status, stage_date, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (case_id, stage_name, order, stage_status, stage_date, desc))

    conn.commit()

    # Re-fetch the complete case to return
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    new_case = dict(cursor.fetchone())

    cursor.execute("""
        SELECT id, stage_name, stage_order, status, stage_date, description
        FROM case_timeline
        WHERE case_id = ?
        ORDER BY stage_order ASC
    """, (case_id,))
    timeline = [dict(r) for r in cursor.fetchall()]
    conn.close()

    new_case["timeline"] = timeline
    return new_case
