"""
Authentication Routes for AI Legal Advisor
------------------------------------------
Handles citizen registration, login, profile inspection,
and demo credentials for testing and viva demonstration.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.database import get_db_connection, hash_password
from backend.config import LEGAL_DISCLAIMER

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ==========================================
# 1. Pydantic Schemas
# ==========================================

class LoginRequest(BaseModel):
    """Payload for user sign in."""
    username: str = Field(..., min_length=3, description="Username of the citizen.")
    password: str = Field(..., min_length=4, description="Password.")


class RegisterRequest(BaseModel):
    """Payload for registering a new citizen account."""
    username: str = Field(..., min_length=3, max_length=30)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=4, max_length=100)


class UserProfile(BaseModel):
    """Public user profile data returned to client."""
    id: int
    username: str
    full_name: str
    email: str
    created_at: str


class AuthResponse(BaseModel):
    """Response returned upon successful authentication."""
    status: str
    message: str
    user: UserProfile
    token: str
    disclaimer: str


# ==========================================
# 2. Endpoints
# ==========================================

@router.post("/login", response_model=AuthResponse)
def login_user(payload: LoginRequest):
    """
    Authenticates a citizen with username and password.
    Returns user details and a session token.
    """
    clean_username = payload.username.strip().lower()
    hashed_pwd = hash_password(payload.password)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, email, password_hash, created_at
        FROM users
        WHERE LOWER(username) = ?
    """, (clean_username,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row or user_row["password_hash"] != hashed_pwd:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please try again."
        )

    # In a lightweight local app, generate a simple session token
    session_token = f"session_{user_row['username']}_{int(datetime.now().timestamp())}"

    return AuthResponse(
        status="success",
        message=f"Welcome back, {user_row['full_name']}!",
        user=UserProfile(
            id=user_row["id"],
            username=user_row["username"],
            full_name=user_row["full_name"],
            email=user_row["email"],
            created_at=user_row["created_at"]
        ),
        token=session_token,
        disclaimer=LEGAL_DISCLAIMER
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest):
    """
    Registers a new citizen account.
    """
    clean_username = payload.username.strip().lower()
    clean_email = payload.email.strip().lower()
    hashed_pwd = hash_password(payload.password)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if username already exists
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (clean_username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken. Please choose another."
        )

    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (clean_email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{payload.email}' is already registered."
        )

    # Insert new user
    cursor.execute("""
        INSERT INTO users (username, full_name, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (clean_username, payload.full_name.strip(), clean_email, hashed_pwd, now_str))
    new_user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session_token = f"session_{clean_username}_{int(datetime.now().timestamp())}"

    return AuthResponse(
        status="success",
        message=f"Account created successfully for {payload.full_name}!",
        user=UserProfile(
            id=new_user_id,
            username=clean_username,
            full_name=payload.full_name.strip(),
            email=clean_email,
            created_at=now_str
        ),
        token=session_token,
        disclaimer=LEGAL_DISCLAIMER
    )


@router.get("/demo-credentials")
def get_demo_credentials():
    """
    Returns the pre-seeded demo user credentials for 1-click viva testing.
    """
    return {
        "username": "ankit",
        "password": "legal123",
        "full_name": "Ankit Sharma",
        "note": "Pre-configured demo account for evaluation."
    }
