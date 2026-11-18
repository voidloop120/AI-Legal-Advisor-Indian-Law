# ⚖️ AI Legal Advisor for Indian Law

An intelligent legal information system designed for Indian citizens to understand their legal cases, explore legal provisions under the new criminal codes (**Bharatiya Nyaya Sanhita [BNS]**, **Bharatiya Nagarik Suraksha Sanhita [BNSS]**, and **Bharatiya Sakshya Adhiniyam [BSA]**) as well as the **Consumer Protection Act**, and analyze First Information Reports (FIRs).

> **⚠️ MANDATORY LEGAL DISCLAIMER:**  
> **AI Legal Advisor provides legal information for educational and preliminary awareness only, NOT formal legal advice.**  
> It does not create an advocate-client relationship. If you are facing criminal charges, court summons, or urgent civil matters, please consult a licensed advocate or contact your nearest District Legal Services Authority (DLSA).

---

## 🛠️ Tech Stack

- **Frontend:** Vanilla HTML5, CSS3, JavaScript (no complex framework dependencies)
- **Backend:** Python 3.13+, FastAPI, Uvicorn
- **Database:** SQLite
- **RAG Pipeline:** ChromaDB + Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLM:** Google Gemini API / Ollama
- **Version Control:** Git

---

## 📁 Project Structure

```text
AI_Legal_Advisor/
├── backend/
│   ├── __init__.py           # Package marker
│   ├── main.py               # FastAPI application entry point & static server
│   ├── config.py             # App settings, paths, and legal disclaimer
│   ├── database.py           # SQLite database connection & schema
│   ├── requirements.txt      # Python dependencies
│   ├── rag/                  # RAG (Retrieval-Augmented Generation) package
│   │   ├── __init__.py
│   │   ├── vector_store.py   # ChromaDB vector store & semantic search
│   │   └── indexer.py        # CLI script to index laws & test queries
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── cases.py          # Case management & journey APIs
│   │   └── laws.py           # Law & Section Explorer APIs (BNS, BNSS, BSA, CPA)
│   └── tests/
│       ├── __init__.py
│       ├── test_cases.py     # Tests for case management
│       ├── test_laws.py      # Tests for laws explorer
│       ├── test_main.py      # Tests for core server
│       └── test_rag.py       # Tests for RAG vector retrieval
├── frontend/
│   ├── index.html            # Main web UI dashboard & modals
│   ├── style.css             # Dark-themed responsive styling
│   └── script.js             # Client-side interactions & API bindings
├── data/
│   ├── legal_advisor.db      # SQLite database
│   ├── chroma_db/            # ChromaDB persistent vector database
│   └── legal_docs/           # Statutory provisions (BNS, BNSS, BSA, CPA)
│       └── indian_laws.json
├── .gitignore                # Files excluded from git
└── README.md                 # Project documentation and guide
```

---

## 🚀 Getting Started (How to Run)

### 1. Prerequisites
- Python 3.11+ installed (Recommended: Python 3.13)
- Git installed

### 2. Activate the Virtual Environment
Open PowerShell or Terminal in this folder:

```powershell
# On Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# If script execution is restricted on your machine, run:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### 4. Run the Backend Server
```powershell
uvicorn backend.main:app --reload
```

### 5. Test the Legal RAG Indexer (CLI)
```powershell
python -m backend.rag.indexer
```

### 6. Run Automated Unit Tests
```powershell
pytest backend/tests/test_laws.py backend/tests/test_rag.py -v
```

### 7. Open in Your Browser
- Web Interface: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Law Explorer API: [http://127.0.0.1:8000/api/laws](http://127.0.0.1:8000/api/laws)

---

## 🎯 Current Implementation Status

- [x] **Phase 1: Foundation & Setup** — Directory structure, Git, FastAPI server, Static frontend serving, Health & Disclaimer APIs.
- [x] **Phase 2: Database & Case Management** — SQLite database, case tracking, case journey stages, dynamic UI integration.
- [x] **Phase 3: Legal Knowledge Base & RAG** — BNS/BNSS/BSA/CPA statutory explorer, ChromaDB vector store, semantic search indexer, and unit test suite.
- [ ] **Phase 4: AI Legal Assistant** — RAG-powered chatbot with strict Act + Section citations.
- [ ] **Phase 5: FIR Analyzer** — Upload FIR, extract offenses, map relevant sections.
- [ ] **Phase 6: Auth & Final Polish** — Simple authentication, advocate preparation sheet.
