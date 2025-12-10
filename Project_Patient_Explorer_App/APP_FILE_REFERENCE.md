# Patient Explorer App - File Reference

**Generated:** December 3, 2025
**Purpose:** Map of all files needed to run the Patient Explorer App

---

## Why Files Are Not Nested Here

The application source files remain in their original locations (`app/`, `phase0/`, etc.) rather than being moved into this `Project_` folder because:

1. **Application integrity** - Moving files would break import paths and the running application
2. **Git history** - Preserving file locations maintains version control history
3. **Separation of concerns** - This folder is for project management (briefs, research, docs), not source code
4. **BMAD convention** - Project_ folders contain agent outputs, not primary source code

This reference document provides a complete map to all relevant files.

---

## Quick Start Commands

```bash
# Run Streamlit App
.venv\Scripts\activate
streamlit run app/main.py

# Or use the PowerShell script
.\run-app.ps1

# Run Phase 0 CLI
python -m phase0 --help
python -m phase0 test-spruce
python -m phase0 load-patients data/patients.xlsx
```

---

## 1. STREAMLIT APPLICATION (`app/`)

### Core Framework (Required to Run)

| File | Purpose |
|------|---------|
| `app/main.py` | **Entry point** - Initializes DB, auth, displays dashboard |
| `app/database/__init__.py` | Database module exports |
| `app/database/connection.py` | SQLAlchemy engine, session factory |
| `app/database/models.py` | ORM models: Patient, Consent, User, enums |
| `app/auth.py` | Authentication, password hashing, role permissions |

### Data Import & Processing

| File | Purpose |
|------|---------|
| `app/data_loader.py` | Import patients from Excel |
| `app/apcm_loader.py` | APCM enrollment data parsing |
| `app/reconciliation_agent.py` | AI-powered conflict resolution for imports |

### API Integrations

| File | Purpose |
|------|---------|
| `app/azure_claude.py` | Azure OpenAI Claude (HIPAA-compliant AI) |
| `app/azure_document.py` | Azure Document Intelligence (OCR) |
| `app/microsoft_graph.py` | Microsoft Graph API (Teams, OneNote) |
| `app/sharepoint_sync.py` | SharePoint list sync for consent tracking |

### Feature Modules

| File | Purpose |
|------|---------|
| `app/consent_tokens.py` | Generate/validate consent portal tokens |
| `app/sms_templates.py` | Spruce SMS message templates |
| `app/test_connections.py` | API connection test suite |

### UI Pages (15 Total)

| File | Page Name | Purpose |
|------|-----------|---------|
| `app/pages/1_Patient_List.py` | Patient List | View/filter/import patients |
| `app/pages/2_Consent_Tracking.py` | Consent Tracking | Track consent status |
| `app/pages/3_APCM_Patients.py` | APCM Patients | APCM enrollment management |
| `app/pages/4_Outreach_Campaign.py` | Outreach Campaign | SMS/email outreach |
| `app/pages/5_AI_Assistant.py` | AI Assistant | AI-powered features |
| `app/pages/6_Add_Documents.py` | Add Documents | Upload and OCR documents |
| `app/pages/7_M365_Integration.py` | M365 Integration | OneNote, Teams, SharePoint |
| `app/pages/8_Team_Tasks.py` | Team Tasks | Task assignment |
| `app/pages/9_Admin.py` | Admin | User/role/system management |
| `app/pages/10_Smart_Data_Ingest.py` | Smart Data Ingest | AI-powered data import |
| `app/pages/11_Consent_Response.py` | Consent Response | Process consent responses |
| `app/pages/12_Follow_Up_Queue.py` | Follow-Up Queue | Patient follow-up prioritization |
| `app/pages/13_Patient_Notes.py` | Patient Notes | Clinical notes timeline |
| `app/pages/14_Daily_Summary.py` | Daily Summary | Dashboard metrics |
| `app/pages/15_Test_SMS.py` | Test SMS | SMS testing (dev tool) |

**Total: 29 Python files in `app/`**

---

## 2. PHASE 0 CLI (`phase0/`)

### Core CLI Framework

| File | Purpose |
|------|---------|
| `phase0/__init__.py` | Package init, version |
| `phase0/__main__.py` | Entry point for `python -m phase0` |
| `phase0/main.py` | Typer CLI commands |
| `phase0/models.py` | Pydantic data models |
| `phase0/excel_loader.py` | Excel patient file loading |

### API Clients

| File | Purpose |
|------|---------|
| `phase0/spruce/__init__.py` | Spruce module init |
| `phase0/spruce/client.py` | Spruce API: contacts, SMS, conversations |
| `phase0/sharepoint/__init__.py` | SharePoint module init |
| `phase0/sharepoint/client.py` | SharePoint REST client |

**Total: 9 Python files in `phase0/`**

---

## 3. CONFIGURATION FILES

### Environment & Dependencies

| File | Purpose | Required |
|------|---------|----------|
| `requirements.txt` | Python dependencies | ✅ Yes |
| `.env` | API credentials (gitignored) | ✅ Yes |
| `.env.example` | Template for .env | Reference |

### Startup Scripts

| File | Purpose |
|------|---------|
| `run-app.ps1` | PowerShell: activate venv, run Streamlit |
| `setup-beta.ps1` | Environment setup script |

### IDE Configuration

| File | Purpose |
|------|---------|
| `.vscode/settings.json` | VS Code workspace settings |
| `.claude/settings.local.json` | Claude Code IDE settings |
| `.gitignore` | Git exclusions |

---

## 4. DOCUMENTATION (`docs/`)

### Architecture

| File | Purpose |
|------|---------|
| `docs/architecture/2025-12-02_ADR-001-Beta-App-Architecture.md` | Architecture decisions |
| `docs/architecture/architecture-streamlit.md` | App architecture overview |
| `docs/architecture/prd.md` | Product Requirements Document |

### Planning

| File | Purpose |
|------|---------|
| `docs/planning/project-brief.md` | Project overview |
| `docs/planning/phase0b-consent-outreach-plan.md` | Phase 0 workflow |
| `docs/planning/alpha-deployment-guide.md` | Deployment instructions |
| `docs/planning/USER-INPUT-CHECKLIST.md` | Setup checklist |
| `docs/planning/consent-form-draft.md` | Consent form template |

### User Stories (Current Sprint: S5-S8)

| File | Story |
|------|-------|
| `docs/stories/S5-microsoft-oauth-integration.md` | MS OAuth |
| `docs/stories/S6-onenote-integration.md` | OneNote access |
| `docs/stories/S7-consent-form-setup.md` | Consent forms |
| `docs/stories/S8-sms-outreach-campaign.md` | SMS outreach |

### Research Reports

| File | Topic |
|------|-------|
| `docs/research/2025-12-02_Spruce-Health-API-Capabilities.md` | Spruce API |
| `docs/research/2025-12-02_Microsoft-OAuth-OneNote-Integration.md` | MS OAuth |
| `docs/research/2025-12-02_OpenEvidence-UI-Patterns.md` | UI patterns |

---

## 5. DATA & DATABASE

### Database

| File | Purpose |
|------|---------|
| `data/patients.db` | SQLite database (auto-created) |

### Reference Data (`..Workspace/Reference/Reference_Files/`)

| File | Records | Purpose |
|------|---------|---------|
| `Ref_CPT Procedure Codes.csv` | ~500+ | Procedure codes |
| `Ref_ICD Codes.csv` | ~10,000+ | Diagnosis codes |
| `Ref_Medication_Info.csv` | ~10,000+ | Drug information |
| `Ref_CVX_Immunizations.csv` | ~55 | Vaccine codes |
| `Ref_Lab_Panels.csv` | ~80 | Lab panel groups |
| `Ref_Lab_ReferenceRanges.csv` | ~65 | Normal lab values |
| `Ref_Vitals_ReferenceRanges.csv` | ~45 | Vital sign ranges |

---

## 6. PROJECT METADATA

### Root Documentation

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `CLAUDE.md` | AI assistant guidance |
| `LESSONS-LEARNED.md` | Development history |
| `SMART-DATA-INGEST-IMPLEMENTATION.md` | Latest feature status |

### Workspace Management (`..Workspace/`)

| Folder | Purpose |
|--------|---------|
| `..Workspace/Focus/` | Daily session documents |
| `..Workspace/History/` | Archives (briefs, chats, git) |
| `..Workspace/Reference/` | Manual reference artifacts |
| `..Workspace/Settings/` | Master configuration |

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Web App** | Streamlit | 1.29+ |
| **Database** | SQLite + SQLAlchemy | 2.0+ |
| **Data** | pandas, openpyxl | 2.0+, 3.1+ |
| **HTTP** | httpx, requests | 0.25+, 2.31+ |
| **CLI** | Typer, Rich | 0.9+, 13+ |
| **AI** | Azure OpenAI (Claude) | Sonnet 4.5 |
| **OCR** | Azure Document Intelligence | - |
| **Logging** | loguru | 0.7+ |

---

## Minimum Files to Run App

### Streamlit App (Essential)
```
app/main.py
app/database/models.py
app/database/connection.py
app/database/__init__.py
app/auth.py
app/data_loader.py
app/pages/*.py (all 15)
requirements.txt
.env
```

### Phase 0 CLI (Essential)
```
phase0/__main__.py
phase0/main.py
phase0/models.py
phase0/excel_loader.py
phase0/spruce/client.py
phase0/sharepoint/client.py
requirements.txt
.env
```

---

## File Counts Summary

| Category | File Count |
|----------|------------|
| Streamlit App (`app/`) | 29 |
| Phase 0 CLI (`phase0/`) | 9 |
| Configuration | 6 |
| Documentation (`docs/`) | ~25 |
| **Total Core Files** | ~70 |

---

## Related Project Folder Documents

This `Project_Patient_Explorer_App/` folder contains:

| Folder | Purpose |
|--------|---------|
| `briefs/` | Project status briefs (YYYY-MM-DD_*.md) |
| `research/` | Project-specific research reports |
| `architecture/` | Project-specific ADRs |

These are **agent outputs** separate from the source code.

---

*Reference generated by Patient Explorer App Agent*
*Last updated: December 3, 2025*
