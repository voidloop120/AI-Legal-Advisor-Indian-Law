"""
Database module for AI Legal Advisor.
Uses Python's standard library `sqlite3` for simple, lightweight data storage.
"""

import sqlite3
from datetime import datetime
from backend.config import DATABASE_PATH, DATA_DIR


def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Row factory is set to sqlite3.Row so columns can be accessed by name (e.g. row['title']).
    """
    # Ensure the data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign key support in SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Initializes database tables if they do not exist,
    and seeds sample initial cases if the database is brand new.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Table for Cases
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        case_type TEXT NOT NULL,
        police_station TEXT,
        current_stage TEXT NOT NULL,
        status TEXT NOT NULL,
        progress_percent INTEGER DEFAULT 0,
        description TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Table for Case Journey / Timeline Stages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS case_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        stage_name TEXT NOT NULL,
        stage_order INTEGER NOT NULL,
        status TEXT NOT NULL,       -- 'completed', 'current', or 'pending'
        stage_date TEXT,
        description TEXT,
        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # 3. Seed sample data if table is currently empty
    cursor.execute("SELECT COUNT(*) AS count FROM cases")
    count = cursor.fetchone()["count"]

    if count == 0:
        _seed_sample_cases(conn)

    conn.close()


def _seed_sample_cases(conn: sqlite3.Connection):
    """
    Seeds initial sample cases matching the UI mockup.
    This gives the student immediate data to see on the frontend.
    """
    cursor = conn.cursor()

    # Standard stages for a typical criminal case in India
    stages_template = [
        ("FIR Registered", "completed", "10 Jan 2026", "FIR filed at local police station."),
        ("Investigation", "current", "In Progress", "Police collecting evidence, examining witnesses under BNSS."),
        ("Charge Sheet", "pending", "Upcoming", "Filing of final investigation report in court."),
        ("Court Proceedings", "pending", "Upcoming", "Cognizance and framing of charges."),
        ("Hearing", "pending", "Upcoming", "Examination of witnesses and legal arguments."),
        ("Final Order", "pending", "Upcoming", "Judgment delivered by Magistrate/Judge.")
    ]

    sample_cases = [
        {
            "case_number": "2026-001",
            "title": "FIR No. 123/2026",
            "case_type": "Criminal - FIR",
            "police_station": "XYZ Police Station",
            "current_stage": "Investigation",
            "status": "Active",
            "progress_percent": 46,
            "description": "Allegation of financial fraud and misrepresentation.",
            "created_at": datetime.now().isoformat()
        },
        {
            "case_number": "2025-088",
            "title": "Property Dispute",
            "case_type": "Civil Suit",
            "police_station": "N/A (Civil Court)",
            "current_stage": "Hearing",
            "status": "In Progress",
            "progress_percent": 70,
            "description": "Boundary dispute regarding ancestral land property.",
            "created_at": datetime.now().isoformat()
        },
        {
            "case_number": "2024-056",
            "title": "Consumer Complaint",
            "case_type": "Consumer Protection Act",
            "police_station": "District Consumer Forum",
            "current_stage": "Order Pending",
            "status": "Closed",
            "progress_percent": 90,
            "description": "Defective electronics product and deficiency in service.",
            "created_at": datetime.now().isoformat()
        }
    ]

    for case_data in sample_cases:
        cursor.execute("""
            INSERT INTO cases (case_number, title, case_type, police_station, current_stage, status, progress_percent, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_data["case_number"],
            case_data["title"],
            case_data["case_type"],
            case_data["police_station"],
            case_data["current_stage"],
            case_data["status"],
            case_data["progress_percent"],
            case_data["description"],
            case_data["created_at"]
        ))
        case_id = cursor.lastrowid

        # Insert default timeline stages for each case
        for order, (stage_name, status, stage_date, desc) in enumerate(stages_template, start=1):
            cursor.execute("""
                INSERT INTO case_timeline (case_id, stage_name, stage_order, status, stage_date, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (case_id, stage_name, order, status, stage_date, desc))

    conn.commit()
