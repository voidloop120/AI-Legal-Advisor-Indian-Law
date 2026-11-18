"""
Configuration settings for AI Legal Advisor.
Contains project paths, app constants, and mandatory legal disclaimers.
"""
from pathlib import Path

# Base project directory (one level up from 'backend')
BASE_DIR = Path(__file__).resolve().parent.parent

# Paths to important directories
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
LEGAL_DOCS_DIR = DATA_DIR / "legal_docs"
DATABASE_PATH = DATA_DIR / "legal_advisor.db"

# Application Metadata
APP_TITLE = "AI Legal Advisor for Indian Law"
APP_VERSION = "0.1.0"

# Mandatory Legal Disclaimer
# Rule: The app gives legal information, not legal advice.
LEGAL_DISCLAIMER = (
    "AI Legal Advisor provides legal information based on Indian statutes "
    "(BNS, BNSS, BSA, Consumer Protection Act) for educational and preliminary "
    "reference only. It does not constitute formal legal advice. For actionable "
    "legal counsel or representation, please consult a licensed advocate."
)
