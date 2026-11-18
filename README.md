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
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── index.html            # Main web UI dashboard
│   ├── style.css             # Dark-themed styling
│   └── script.js             # Client-side interactions
├── data/
│   └── legal_docs/           # Legal texts (BNS, BNSS, BSA, Consumer Protection Act)
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

### 5. Open in Your Browser
- Web Interface: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API Docs (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 🎯 Current Implementation Status

- [x] **Phase 1: Foundation & Setup** — Directory structure, Git, FastAPI server, Static frontend serving, Health & Disclaimer APIs.
- [ ] **Phase 2: Database & Case Management** — SQLite database, case tracking, case journey stages.
- [ ] **Phase 3: Legal Knowledge Base & RAG** — BNS/BNSS/BSA law indexing with ChromaDB.
- [ ] **Phase 4: AI Legal Assistant** — RAG-powered chatbot with strict Act + Section citations.
- [ ] **Phase 5: FIR Analyzer** — Upload FIR, extract offenses, map relevant sections.
- [ ] **Phase 6: Auth & Final Polish** — Simple authentication, advocate preparation sheet.
