"""
AI Legal Advisor - FastAPI Main Application
--------------------------------------------
This is the entry point for the backend server.
It sets up API routes and serves the frontend web interface.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import APP_TITLE, APP_VERSION, FRONTEND_DIR, LEGAL_DISCLAIMER
from backend.database import init_db
from backend.routes.cases import router as cases_router
from backend.routes.laws import router as laws_router

# 1. Initialize Database on startup
init_db()

# 2. Initialize FastAPI application
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="FastAPI backend for AI Legal Advisor (Indian Law)",
)

# 3. Add CORS middleware (allows frontend to communicate with backend smoothly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Register API routers
app.include_router(cases_router)
app.include_router(laws_router)


# 5. Basic API endpoints
@app.get("/api/health")
def health_check():
    """
    Health check endpoint to verify backend server is running.
    Also returns the mandatory legal disclaimer.
    """
    return {
        "status": "healthy",
        "app": APP_TITLE,
        "version": APP_VERSION,
        "disclaimer": LEGAL_DISCLAIMER,
    }


@app.get("/api/disclaimer")
def get_disclaimer():
    """
    Returns the legal information disclaimer.
    Rule: AI Legal Advisor provides legal information, not legal advice.
    """
    return {
        "disclaimer": LEGAL_DISCLAIMER
    }


# 4. Serve the Frontend
# Mount the frontend directory so that index.html, style.css, and script.js
# are automatically accessible at http://127.0.0.1:8000/
app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend",
)
