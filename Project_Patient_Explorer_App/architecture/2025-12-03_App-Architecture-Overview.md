# Patient Explorer App - Architecture Overview

**Date:** December 3, 2025
**Version:** 1.0
**Status:** Active Development
**Target:** Production by December 31, 2025

---

## Executive Summary

Patient Explorer is a HIPAA-compliant desktop application for managing patient consent during practice transition. The application uses Streamlit for rapid UI development, SQLite for local data storage, and integrates with Spruce Health (SMS), Microsoft 365 (Forms, OneNote), and Azure AI services under Business Associate Agreements.

**Key Architecture Decisions:**
- **Framework:** Streamlit (Python web framework running on localhost)
- **Database:** SQLite with SQLAlchemy ORM (BitLocker-encrypted)
- **Deployment:** Local-only (no cloud hosting for PHI security)
- **Integrations:** Spruce Health, Microsoft Graph API, Azure Claude AI
- **Security:** Multi-layered defense including device encryption, localhost binding, and BAA-covered APIs

---

## Table of Contents

1. [System Context](#1-system-context)
2. [Architectural Decisions](#2-architectural-decisions)
3. [Technology Stack](#3-technology-stack)
4. [Component Architecture](#4-component-architecture)
5. [Data Architecture](#5-data-architecture)
6. [Integration Architecture](#6-integration-architecture)
7. [Security Architecture](#7-security-architecture)
8. [Deployment Architecture](#8-deployment-architecture)
9. [Key Workflows](#9-key-workflows)
10. [Performance & Scalability](#10-performance--scalability)
11. [Future Considerations](#11-future-considerations)

---

## 1. System Context

### 1.1 Business Context

**Purpose:** Support Dr. Robert Green's practice transition from Southview Medical Group to Home Team Medical Services (effective January 1, 2026) by:
1. Tracking patient consent for medical record retention
2. Managing APCM (Advanced Primary Care Management) program transitions
3. Coordinating SMS outreach campaigns
4. Generating care plans from existing clinical notes

**Users:**
- Dr. Robert Green (Provider)
- Nurse Jenny (Clinical Staff)
- Administrative staff (2-3 people)

**Timeline:**
- December 3-31, 2025: Beta testing and consent outreach
- January 1, 2026: Practice transition effective date
- January-February 2026: Care plan generation features

### 1.2 System Landscape

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SYSTEMS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Spruce     │  │  Microsoft   │  │    Azure     │              │
│  │   Health     │  │  Graph API   │  │   Claude     │              │
│  │   (SMS/CRM)  │  │ (Forms/      │  │    (AI)      │              │
│  │     ✅ BAA   │  │  OneNote)    │  │    ✅ BAA    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│         │ REST API        │ Graph API        │ OpenAI API           │
│         │                 │                  │                       │
└─────────┼─────────────────┼──────────────────┼───────────────────────┘
          │                 │                  │
          └─────────────────┴──────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PATIENT EXPLORER APPLICATION                      │
│                  (Streamlit on http://localhost:8501)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        UI LAYER                                 │ │
│  │  • 15 Streamlit pages (Patient List, Consent Tracking, etc.)   │ │
│  │  • Authentication (local + MS OAuth planned)                    │ │
│  │  • Real-time data visualization                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                            │                                         │
│                            ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     SERVICE LAYER                               │ │
│  │  • Data loaders (Excel, APCM)                                   │ │
│  │  • API clients (Spruce, MS Graph, Azure)                        │ │
│  │  • Business logic (matching, reconciliation)                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                            │                                         │
│                            ▼                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    DATA ACCESS LAYER                            │ │
│  │  • SQLAlchemy ORM                                               │ │
│  │  • SQLite database (patients.db)                                │ │
│  │  • Audit logging                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │    Local File System     │
                    │  • SQLite DB (encrypted) │
                    │  • Import files (Excel)  │
                    │  • Log files             │
                    └──────────────────────────┘
                            │
                            ▼
                    ┌──────────────────────────┐
                    │   BitLocker Device       │
                    │  Windows 11 Pro/Ent.     │
                    └──────────────────────────┘
```

### 1.3 System Boundaries

**Inside the System:**
- Patient data management
- Consent tracking
- SMS campaign coordination
- Data import/reconciliation
- Care plan generation
- User authentication
- Audit logging

**Outside the System (Integrated):**
- SMS delivery (Spruce Health)
- Consent form hosting (Microsoft Forms)
- Clinical notes storage (OneNote)
- AI text generation (Azure Claude)
- EMR system (Allscripts - read-only via manual export)

**Explicitly Out of Scope:**
- Cloud hosting (HIPAA requires local)
- Mobile apps
- Patient-facing portal (uses Microsoft Forms instead)
- Billing integration
- Real-time EMR sync

---

## 2. Architectural Decisions

### 2.1 Framework Selection: Streamlit vs. Electron

**Original Design:** Electron + React + TypeScript

**Decision:** Pivot to Streamlit + Python

**Rationale:**

| Factor | Electron | Streamlit | Winner |
|--------|----------|-----------|--------|
| Development speed | Slower (setup, build process) | Faster (pure Python) | Streamlit |
| Windows compatibility | Issues with Defender `.asar` locking | No native modules | Streamlit |
| Python integration | Complex (IPC required) | Native | Streamlit |
| Team expertise | JavaScript/TypeScript | Python | Streamlit |
| Maintenance | Complex build tooling | Simple `pip install` | Streamlit |
| HIPAA compliance | Both support localhost-only | Both support localhost-only | Tie |

**Trade-offs Accepted:**
- ❌ Less "native" feel (web UI in browser)
- ❌ No offline installer (requires Python)
- ✅ Faster development (critical for Dec 31 deadline)
- ✅ Leverage existing Phase 0 Python codebase
- ✅ Simpler deployment and updates

### 2.2 Database Selection: SQLite vs. Cloud Database

**Decision:** SQLite with local file storage

**Rationale:**
- **HIPAA Compliance:** No cloud transmission of PHI
- **Offline Access:** Works without internet connection
- **Simplicity:** No server setup or maintenance
- **Performance:** Fast for single-user workload (<5,000 patients)
- **Backup:** Simple file-based backup to OneDrive/SharePoint

**Encryption:**
- Database file stored on BitLocker-encrypted Windows volume
- SQLite at-rest encryption (via OS-level BitLocker, not SQLCipher)

### 2.3 Authentication Strategy

**Decision:** Hybrid - Local auth + Microsoft OAuth

**Phase 1 (Current):** Local username/password
- Simple `users` table in SQLite
- Password hashing with bcrypt
- Session-based authentication in Streamlit

**Phase 2 (Planned):** Microsoft OAuth
- Azure AD login (southviewteam.com tenant)
- Delegated permissions for OneNote access
- Token-based session management
- MFA handled by Microsoft

**Rationale:**
- Start simple for beta testing
- Add OAuth when OneNote integration is needed
- Leverage existing Microsoft 365 infrastructure
- Support MFA without implementing it ourselves

### 2.4 Consent Form Delivery: Custom vs. Microsoft Forms

**Decision:** Microsoft Forms with tokenized URLs

**Rationale:**
- **Speed:** Forms can be set up in hours, not weeks
- **HIPAA:** Covered under Microsoft 365 BAA
- **Familiar:** Staff already use Microsoft ecosystem
- **Mobile-friendly:** Forms work on any device

**Implementation:**
- Form includes hidden token field (pre-filled from URL)
- Token links to patient record in database
- Responses imported via CSV or Graph API
- Consent status updated automatically

**Trade-offs:**
- ❌ Less customization than custom UI
- ❌ Manual import initially (auto-import later)
- ✅ Faster deployment
- ✅ No additional hosting required

### 2.5 Integration Architecture

**Decision:** Direct API integration (no middleware)

**Rationale:**
- **Simplicity:** Fewer moving parts
- **Security:** Direct TLS connections to BAA-covered services
- **Performance:** No additional latency from middleware
- **Maintenance:** Fewer components to update

**Integration Points:**
1. **Spruce Health:** REST API for SMS and contact management
2. **Microsoft Graph:** Forms responses, OneNote access
3. **Azure OpenAI:** Claude API for AI features
4. **SharePoint:** Future sync for multi-user scenarios (optional)

---

## 3. Technology Stack

### 3.1 Core Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **UI Framework** | Streamlit | 1.29+ | Web-based desktop UI |
| **Language** | Python | 3.10+ | Core development language |
| **Database** | SQLite | 3.45+ | Local data storage |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Data Validation** | Pydantic | 2.0+ | Type-safe models |
| **HTTP Client** | httpx | 0.25+ | Async API calls |
| **Data Processing** | pandas | 2.0+ | Excel import/export |
| **Excel** | openpyxl | 3.1+ | Excel file handling |
| **CLI** | Typer | 0.9+ | Command-line tools (Phase 0) |
| **Logging** | loguru | 0.7+ | Application logging |

### 3.2 Integration Libraries

| Service | Library | Purpose |
|---------|---------|---------|
| **Spruce Health** | httpx | REST API client |
| **Microsoft Graph** | msal + httpx | OAuth + API calls |
| **Azure OpenAI** | openai | Claude API client |
| **SharePoint** | Office365-REST-Python-Client | List sync (future) |

### 3.3 Development Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Unit and integration testing |
| **black** | Code formatting |
| **ruff** | Fast linting |
| **mypy** | Static type checking |
| **pre-commit** | Git hooks for quality checks |

### 3.4 Deployment

| Component | Technology |
|-----------|------------|
| **Runtime** | Python virtual environment (.venv) |
| **Launcher** | PowerShell script (run-app.ps1) |
| **Configuration** | .env files (gitignored) |
| **Updates** | Git pull + pip install |

---

## 4. Component Architecture

### 4.1 Directory Structure

```
Patient_Explorer/
├── app/                          # Streamlit application
│   ├── main.py                   # Entry point
│   ├── auth.py                   # Authentication module
│   ├── database/                 # Data layer
│   │   ├── __init__.py
│   │   ├── connection.py         # SQLAlchemy setup
│   │   └── models.py             # ORM models
│   ├── data_loader.py            # Excel import
│   ├── apcm_loader.py            # APCM data import
│   ├── reconciliation_agent.py   # AI-powered conflict resolution
│   ├── consent_tokens.py         # Token generation/validation
│   ├── sms_templates.py          # SMS message templates
│   ├── azure_claude.py           # Azure OpenAI integration
│   ├── azure_document.py         # Azure Document Intelligence
│   ├── microsoft_graph.py        # MS Graph API client
│   ├── sharepoint_sync.py        # SharePoint sync (future)
│   ├── test_connections.py       # API connectivity tests
│   └── pages/                    # Streamlit pages (15 total)
│       ├── 1_Patient_List.py
│       ├── 2_Consent_Tracking.py
│       ├── 3_APCM_Patients.py
│       ├── 4_Outreach_Campaign.py
│       ├── 5_AI_Assistant.py
│       ├── 6_Add_Documents.py
│       ├── 7_M365_Integration.py
│       ├── 8_Team_Tasks.py
│       ├── 9_Admin.py
│       ├── 10_Smart_Data_Ingest.py
│       ├── 11_Consent_Response.py
│       ├── 12_Follow_Up_Queue.py
│       ├── 13_Patient_Notes.py
│       ├── 14_Daily_Summary.py
│       └── 15_Test_SMS.py
├── phase0/                       # CLI tools (pre-Streamlit)
│   ├── __init__.py
│   ├── __main__.py               # CLI entry point
│   ├── main.py                   # Typer commands
│   ├── models.py                 # Pydantic models
│   ├── excel_loader.py           # Excel parsing
│   ├── spruce/                   # Spruce API client
│   │   ├── __init__.py
│   │   └── client.py
│   └── sharepoint/               # SharePoint client
│       ├── __init__.py
│       └── client.py
├── data/                         # Data files (gitignored)
│   ├── patients.db               # SQLite database
│   └── imports/                  # Excel imports
├── docs/                         # Documentation
│   ├── architecture/             # ADRs and design docs
│   ├── stories/                  # User stories (S5-S8)
│   ├── planning/                 # Project plans
│   └── research/                 # Research reports
├── .venv/                        # Python virtual environment
├── .env                          # Configuration (gitignored)
├── requirements.txt              # Python dependencies
├── run-app.ps1                   # Launcher script
└── README.md                     # Project overview
```

### 4.2 UI Layer (Streamlit Pages)

**Page Organization:**

| Page # | Name | Purpose | Key Features |
|--------|------|---------|--------------|
| 0 | Main Dashboard | Overview metrics | Consent stats, recent activity |
| 1 | Patient List | Browse/filter patients | Search, filter, bulk actions |
| 2 | Consent Tracking | Monitor consent status | Status breakdown, timeline |
| 3 | APCM Patients | APCM enrollment management | APCM-specific tracking |
| 4 | Outreach Campaign | SMS campaign management | Template selection, batch send |
| 5 | AI Assistant | AI-powered features | Chat, data analysis |
| 6 | Add Documents | Upload & OCR documents | Screenshot processing |
| 7 | M365 Integration | OneNote, Teams, SharePoint | MS ecosystem access |
| 8 | Team Tasks | Task assignment | Workflow coordination |
| 9 | Admin | User & system management | Settings, user roles |
| 10 | Smart Data Ingest | AI-powered import | Reconciliation, conflict resolution |
| 11 | Consent Response | Process form responses | Bulk import, status update |
| 12 | Follow-Up Queue | Patient follow-up | Prioritization, reminders |
| 13 | Patient Notes | Clinical notes timeline | Note management |
| 14 | Daily Summary | Metrics dashboard | Daily progress tracking |
| 15 | Test SMS | SMS testing (dev tool) | Development testing |

### 4.3 Service Layer

**Core Services:**

| Service | File | Responsibilities |
|---------|------|------------------|
| **DataLoader** | `data_loader.py` | Import patients from Excel, validate, deduplicate |
| **APCMLoader** | `apcm_loader.py` | Parse APCM enrollment data |
| **SpruceClient** | `phase0/spruce/client.py` | Contact matching, SMS sending |
| **ConsentTokens** | `consent_tokens.py` | Generate unique tokens, validate URLs |
| **SMSTemplates** | `sms_templates.py` | Render personalized messages |
| **AzureClaude** | `azure_claude.py` | AI chat and analysis |
| **MicrosoftGraph** | `microsoft_graph.py` | Forms, OneNote, Teams access |
| **ReconciliationAgent** | `reconciliation_agent.py` | AI-powered conflict resolution |
| **Auth** | `auth.py` | User authentication, sessions |

### 4.4 Data Access Layer

**Models (SQLAlchemy ORM):**

| Model | Purpose | Key Relationships |
|-------|---------|-------------------|
| `Patient` | Patient demographics | → Consent, Notes, AuditLogs |
| `Consent` | Consent tracking | ← Patient |
| `User` | Application users | → AuditLogs |
| `AuditLog` | HIPAA audit trail | ← Patient, User |
| `PatientNote` | Clinical notes | ← Patient |
| `ScheduledTask` | Follow-up tasks | ← Patient |

**Enums:**

| Enum | Values |
|------|--------|
| `ConsentStatus` | pending, invitation_sent, portal_visited, consented, declined, no_response, partial |
| `APCMStatus` | active, removed, hold, pending, not_enrolled |
| `APCMLevel` | G0556 (Level 1), G0557 (Level 2), G0558 (Level 3) |
| `UserRole` | admin, provider, staff, readonly |

---

## 5. Data Architecture

### 5.1 Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PATIENT EXPLORER DATABASE                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐                  ┌──────────────────┐         │
│  │      User        │                  │   AuditLog       │         │
│  ├──────────────────┤                  ├──────────────────┤         │
│  │ id (PK)          │───┐         ┌───│ id (PK)          │         │
│  │ username         │   │         │   │ patient_id (FK)  │         │
│  │ password_hash    │   └────────►│   │ user_id (FK)     │         │
│  │ role             │             │   │ action           │         │
│  │ created_at       │             │   │ timestamp        │         │
│  └──────────────────┘             │   │ details          │         │
│                                    │   └──────────────────┘         │
│                                    │                                 │
│  ┌──────────────────────────────┐ │   ┌──────────────────┐         │
│  │         Patient              │ │   │  PatientNote     │         │
│  ├──────────────────────────────┤ │   ├──────────────────┤         │
│  │ id (PK)                      │ │   │ id (PK)          │         │
│  │ mrn (UNIQUE)                 │ │   │ patient_id (FK)  │◄────┐   │
│  │ first_name, last_name        │─┘   │ note_type        │     │   │
│  │ date_of_birth                │     │ content          │     │   │
│  │ phone, email, address        │     │ created_at       │     │   │
│  │ spruce_matched, spruce_id    │     └──────────────────┘     │   │
│  │ preferred_name               │                              │   │
│  │ apcm_enrolled, apcm_level    │     ┌──────────────────┐     │   │
│  │ apcm_status, apcm_icd_codes  │     │ ScheduledTask    │     │   │
│  │ consent_token                │     ├──────────────────┤     │   │
│  │ consent_token_expires        │     │ id (PK)          │     │   │
│  │ consent_portal_visited       │     │ patient_id (FK)  │─────┘   │
│  │ created_at, updated_at       │     │ task_type        │         │
│  └──────┬───────────────────────┘     │ scheduled_for    │         │
│         │                             │ completed        │         │
│         │ 1:1                         └──────────────────┘         │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────┐                                  │
│  │         Consent              │                                  │
│  ├──────────────────────────────┤                                  │
│  │ id (PK)                      │                                  │
│  │ patient_id (FK, UNIQUE)      │                                  │
│  │ status (ENUM)                │                                  │
│  │ outreach_attempts            │                                  │
│  │ last_outreach_date           │                                  │
│  │ outreach_method              │                                  │
│  │ response_date                │                                  │
│  │ response_method              │                                  │
│  │ notes                        │                                  │
│  │ created_at, updated_at       │                                  │
│  └──────────────────────────────┘                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Key Data Models

**Patient Model:**
```python
class Patient(Base):
    __tablename__ = "patients"

    id: int (PK)
    mrn: str (UNIQUE, indexed)
    first_name: str
    last_name: str
    date_of_birth: str  # Stored as string from Excel
    phone: str
    email: str
    address: str
    city: str
    state: str
    zip_code: str

    # Spruce matching
    spruce_matched: bool
    spruce_id: str
    spruce_match_method: str  # 'phone', 'name', 'email'

    # Preferred name (parsed from Excel, e.g., Patricia "Pat" → Pat)
    preferred_name: str

    # APCM fields
    apcm_enrolled: bool
    apcm_signup_date: datetime
    apcm_level: APCMLevel  # G0556, G0557, G0558
    apcm_icd_codes: str  # Comma-separated
    apcm_status: APCMStatus
    apcm_status_notes: str
    apcm_insurance: str
    apcm_copay: str

    # APCM consent elections
    apcm_continue_with_hometeam: bool
    apcm_revoke_southview_billing: bool
    apcm_election_date: datetime

    # Consent portal
    consent_token: str (UNIQUE)
    consent_token_expires: datetime
    consent_portal_visited: datetime

    # Relationships
    consent: Consent (1:1)
    audit_logs: List[AuditLog]
    notes: List[PatientNote]
```

**Consent Model:**
```python
class Consent(Base):
    __tablename__ = "consents"

    id: int (PK)
    patient_id: int (FK, UNIQUE)

    status: ConsentStatus  # pending, invitation_sent, consented, etc.
    outreach_attempts: int
    last_outreach_date: datetime
    outreach_method: str  # 'spruce_message', 'phone', 'mail'
    response_date: datetime
    response_method: str
    notes: str

    # Relationship
    patient: Patient
```

### 5.3 Data Flow

**Patient Import Workflow:**
```
Excel File
  │
  ├─► DataLoader.load_patients()
  │     ├─► Parse rows
  │     ├─► Extract preferred names ("Bob" from Robert "Bob")
  │     ├─► Validate MRNs (unique)
  │     └─► Create/update Patient records
  │
  ├─► APCMLoader.load_apcm_data()
  │     ├─► Parse APCM enrollment sheet
  │     ├─► Match to patients by MRN
  │     └─► Update apcm_* fields
  │
  └─► SpruceClient.get_contacts()
        ├─► Fetch all Spruce contacts
        ├─► Match by phone (primary)
        ├─► Match by name (secondary)
        └─► Update spruce_id, spruce_matched
```

**Consent Outreach Workflow:**
```
Patient (spruce_matched=True)
  │
  ├─► Generate consent token
  │
  ├─► Render SMS template with token URL
  │
  ├─► SpruceClient.send_sms()
  │     ├─► Send to Spruce API
  │     └─► Update consent.status = invitation_sent
  │
  └─► Schedule follow-up reminders
        ├─► Day 3 reminder
        ├─► Day 7 reminder
        └─► Day 14 final reminder
```

**Consent Response Workflow:**
```
Microsoft Forms Response
  │
  ├─► CSV export or Graph API
  │
  ├─► Import to Consent Response page
  │
  └─► Match by token
        ├─► Find patient by consent_token
        ├─► Update consent.status = consented/declined
        ├─► Update consent.response_date
        └─► Log in audit_logs
```

---

## 6. Integration Architecture

### 6.1 Spruce Health Integration

**Purpose:** Patient contact matching and SMS outreach

**API Details:**
- **Base URL:** `https://api.sprucehealth.com/v1`
- **Auth:** Bearer token
- **Key Endpoints:**
  - `GET /contacts` - List contacts with pagination
  - `POST /contacts/search` - Search by name/phone
  - `POST /messages` - Send SMS
- **Rate Limits:** 100/min, 10,000/day (per organization)

**Data Synced:**
- Spruce contact ID → `Patient.spruce_id`
- Match status → `Patient.spruce_matched`
- Match method → `Patient.spruce_match_method`

**Implementation:** `phase0/spruce/client.py` (SpruceClient class)

### 6.2 Microsoft Graph API Integration

**Purpose:** Forms responses, OneNote access, Teams integration

**API Details:**
- **Base URL:** `https://graph.microsoft.com/v1.0`
- **Auth:** OAuth 2.0 with delegated permissions
- **Key Endpoints:**
  - `GET /me/onenote/notebooks` - List notebooks
  - `GET /me/onenote/pages/{id}/content` - Get page HTML
  - (Forms API for response fetching - planned)

**Permissions Required:**
- `Notes.Read` - Read user's OneNote notebooks
- `Notes.Read.All` - Read all notebooks user can access
- `offline_access` - Refresh tokens

**Implementation:** `app/microsoft_graph.py` (MicrosoftGraphClient class)

### 6.3 Azure OpenAI Integration

**Purpose:** AI-powered features (reconciliation, chat, analysis)

**API Details:**
- **Service:** Azure OpenAI (Claude Sonnet 4.5 via Azure Foundry)
- **Auth:** API key
- **Endpoint:** `https://<resource>.openai.azure.com/`
- **Model:** claude-sonnet-4-5-20250929

**HIPAA Status:** ✅ Covered under Microsoft Azure BAA

**Use Cases:**
- Smart data ingest (reconciliation agent)
- Patient note analysis
- Care plan generation
- Conflict resolution

**Implementation:** `app/azure_claude.py` (AzureClaudeClient class)

### 6.4 Integration Security

**API Credentials Storage:**
```env
# .env file (gitignored)
SPRUCE_API_TOKEN=base64_encoded_token
MS_CLIENT_ID=azure_app_client_id
MS_CLIENT_SECRET=azure_app_secret
MS_TENANT_ID=southviewteam.com
AZURE_OPENAI_ENDPOINT=https://resource.openai.azure.com/
AZURE_OPENAI_KEY=api_key
```

**TLS/HTTPS:**
- All API calls use HTTPS
- Certificate validation enabled
- No self-signed certificates accepted

**Token Management:**
- API tokens stored in environment variables
- OAuth tokens stored in Streamlit session (not persisted)
- Tokens never logged or displayed in UI

---

## 7. Security Architecture

### 7.1 Multi-Layer Security Model

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Physical Security                                   │
│   • BitLocker full-disk encryption (Windows 11)             │
│   • TPM-backed encryption keys                               │
│   • Device PIN/password protection                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ Layer 2: Network Security                                    │
│   • Localhost-only binding (127.0.0.1:8501)                 │
│   • No external network exposure                             │
│   • Firewall allows local traffic only                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ Layer 3: Application Security                                │
│   • User authentication (local + MS OAuth)                   │
│   • Role-based access control (admin/provider/staff/readonly)│
│   • Session management (Streamlit session state)             │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ Layer 4: Data Security                                       │
│   • SQLite database on encrypted volume                      │
│   • Password hashing (bcrypt)                                │
│   • API credentials in .env (gitignored)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ Layer 5: Integration Security                                │
│   • TLS for all API calls (Spruce, MS Graph, Azure)         │
│   • BAA-covered services only for PHI                        │
│   • Token-based authentication (no credentials in transit)   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ Layer 6: Audit & Monitoring                                  │
│   • All PHI access logged to audit_logs table                │
│   • User actions tracked (view, edit, export, delete)        │
│   • No PHI in application logs (aggregate stats only)        │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 HIPAA Compliance

**Technical Safeguards:**

| Requirement | Implementation |
|-------------|----------------|
| **Access Control** | User authentication with roles |
| **Audit Controls** | All PHI access logged in audit_logs |
| **Integrity** | Database constraints, validation |
| **Transmission Security** | TLS for all external API calls |

**Physical Safeguards:**

| Requirement | Implementation |
|-------------|----------------|
| **Device Security** | BitLocker encryption required |
| **Workstation Use** | Localhost-only, no network exposure |
| **Media Disposal** | Secure deletion of database files |

**Administrative Safeguards:**

| Requirement | Implementation |
|-------------|----------------|
| **BAA Management** | BAAs with Spruce, Microsoft, Azure |
| **Workforce Training** | Staff trained on PHI handling |
| **Access Authorization** | Role-based permissions |

### 7.3 Data at Rest

**Database Encryption:**
- SQLite file (`data/patients.db`) on BitLocker volume
- Windows 11 BitLocker encryption (AES-256)
- TPM-backed keys

**File Encryption:**
- Excel imports stored on encrypted volume
- Logs stored on encrypted volume
- No temporary files with PHI

### 7.4 Data in Transit

**External APIs:**
- Spruce Health: TLS 1.2+ (HTTPS)
- Microsoft Graph: TLS 1.2+ (HTTPS)
- Azure OpenAI: TLS 1.2+ (HTTPS)

**Internal:**
- Streamlit HTTP (localhost only, no TLS needed)
- SQLite (local file access, no network)

### 7.5 Authentication & Authorization

**Current (Phase 1):**
```python
# Local authentication
User(username, password_hash, role)

# Session management
st.session_state["user"] = user
st.session_state["authenticated"] = True

# Role-based access
@require_role("admin")
def admin_function():
    pass
```

**Future (Phase 2 - MS OAuth):**
```python
# Microsoft OAuth flow
1. User clicks "Sign in with Microsoft"
2. Redirect to Microsoft login
3. User authenticates (MFA handled by Microsoft)
4. App receives OAuth tokens
5. Store tokens in session
6. Use tokens for Graph API calls
```

### 7.6 Audit Logging

**What is Logged:**
- User login/logout
- Patient record view
- Patient record edit
- Data export
- SMS send
- Consent status change

**Audit Log Schema:**
```python
class AuditLog(Base):
    id: int
    timestamp: datetime
    user_id: int
    action: str  # view, edit, export, delete, sms_send
    entity_type: str  # patient, consent, user
    entity_id: int
    details: JSON  # Additional context
```

**HIPAA Requirement:** Audit logs retained for 6 years

---

## 8. Deployment Architecture

### 8.1 Local Deployment

**Target Environment:**
- Windows 11 Pro or Enterprise
- BitLocker enabled
- Python 3.10+
- 8GB RAM minimum
- 1GB free disk space

**Installation Steps:**
```bash
# 1. Clone repository
git clone https://github.com/org/patient-explorer.git
cd patient-explorer

# 2. Create virtual environment
python -m venv .venv

# 3. Activate environment
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
copy .env.example .env
# Edit .env with API credentials

# 6. Initialize database
python -m app.database.init_db

# 7. Run application
streamlit run app/main.py --server.address localhost
```

### 8.2 Launcher Script

**PowerShell Script (`run-app.ps1`):**
```powershell
# Patient Explorer Launcher
$ErrorActionPreference = "Stop"

# Check BitLocker
$bitlocker = (Get-BitLockerVolume -MountPoint C:).ProtectionStatus
if ($bitlocker -ne "On") {
    Write-Error "BitLocker must be enabled on C: drive"
    exit 1
}

# Activate virtual environment
& .venv\Scripts\Activate.ps1

# Launch Streamlit
streamlit run app/main.py --server.address localhost --server.port 8501
```

### 8.3 Configuration Management

**Environment Variables (.env):**
```env
# Spruce Health
SPRUCE_API_TOKEN=xxx

# Microsoft 365
MS_CLIENT_ID=xxx
MS_CLIENT_SECRET=xxx
MS_TENANT_ID=southviewteam.com
MS_CONSENT_FORM_URL=https://forms.office.com/r/xxx

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_KEY=xxx
AZURE_OPENAI_DEPLOYMENT=claude-sonnet-4-5

# Database
DATABASE_PATH=data/patients.db
LOG_FILE=logs/app.log

# Security
STREAMLIT_SERVER_ADDRESS=localhost
STREAMLIT_SERVER_PORT=8501
```

### 8.4 Updates & Maintenance

**Update Process:**
```bash
# 1. Pull latest code
git pull origin main

# 2. Activate environment
.venv\Scripts\activate

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Run migrations (if any)
python -m app.database.migrate

# 5. Restart application
streamlit run app/main.py --server.address localhost
```

**Backup Strategy:**
- Database: Copy `data/patients.db` to OneDrive daily
- Configuration: `.env` backed up separately (encrypted)
- Code: Git repository on GitHub

---

## 9. Key Workflows

### 9.1 Patient Import Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User uploads Excel file (Patient List page)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 2. DataLoader validates file                                     │
│    • Check required columns (MRN, name, phone)                  │
│    • Validate data types                                         │
│    • Check for duplicates                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 3. Parse and normalize data                                      │
│    • Extract preferred names ("Bob" from Robert "Bob")          │
│    • Normalize phone numbers                                     │
│    • Parse dates                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 4. Detect conflicts (MRN already exists)                        │
│    • If new: Insert                                              │
│    • If existing: Show reconciliation UI                         │
│    • User chooses: Keep, Replace, or Merge                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 5. Insert/update patients in database                           │
│    • Create Patient records                                      │
│    • Create Consent records (status=pending)                     │
│    • Generate consent tokens                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 6. Match to Spruce contacts                                      │
│    • Fetch all Spruce contacts                                   │
│    • Match by phone (primary)                                    │
│    • Match by name (secondary)                                   │
│    • Update spruce_id, spruce_matched                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 7. Display import summary                                        │
│    • Patients imported: X                                        │
│    • Patients updated: Y                                         │
│    • Spruce matched: Z                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 SMS Outreach Campaign Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User selects patients for campaign (Outreach Campaign page) │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 2. Filter criteria                                               │
│    • Spruce matched = True                                       │
│    • Consent status = pending                                    │
│    • Optional: APCM enrolled filter                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 3. Select SMS template                                           │
│    • consent_initial (non-APCM)                                  │
│    • consent_initial_apcm (APCM patients)                        │
│    • day_3_reminder, day_7_reminder, day_14_final                │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 4. Preview messages                                              │
│    • Show sample message with token URL                          │
│    • Display patient count                                       │
│    • Estimate cost (if applicable)                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 5. Send in batches                                               │
│    • Batch size: 50 messages                                     │
│    • Delay between batches: 1-2 seconds                          │
│    • Retry on failure                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 6. Update patient records                                        │
│    • consent.status = invitation_sent                            │
│    • consent.last_outreach_date = now                            │
│    • consent.outreach_attempts += 1                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 7. Schedule follow-up reminders                                  │
│    • Day 3 reminder (scheduled_for = now + 3 days)              │
│    • Day 7 reminder (scheduled_for = now + 7 days)              │
│    • Day 14 final (scheduled_for = now + 14 days)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 8. Display campaign summary                                      │
│    • Sent: X                                                     │
│    • Failed: Y                                                   │
│    • Next batch: Z patients                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 Consent Response Processing Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Patient receives SMS with tokenized consent form URL         │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 2. Patient clicks link, opens Microsoft Form                    │
│    • Token pre-filled in hidden field                           │
│    • Patient completes consent questions                         │
│    • Patient submits form                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 3. Form responses stored in Microsoft Forms                     │
│    • Export to Excel (manual)                                    │
│    • OR: Fetch via Graph API (future)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 4. Import responses to Patient Explorer                         │
│    • User uploads CSV (Consent Response page)                   │
│    • OR: Auto-import via API polling                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 5. Match responses to patients                                   │
│    • Find patient by consent_token                               │
│    • Parse consent decision (Yes/No)                             │
│    • Parse APCM elections (if applicable)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 6. Update consent status                                         │
│    • consent.status = consented or declined                      │
│    • consent.response_date = form submission time                │
│    • consent.response_method = "microsoft_forms"                 │
│    • Update APCM election fields                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 7. Cancel scheduled follow-ups                                   │
│    • Remove reminder tasks from scheduled_tasks                  │
│    • Patient no longer appears in follow-up queue                │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│ 8. Display on Consent Tracking dashboard                        │
│    • Updated counts                                              │
│    • Response timeline                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Performance & Scalability

### 10.1 Current Performance Characteristics

| Metric | Target | Current |
|--------|--------|---------|
| **Page Load Time** | <2 seconds | ~1 second |
| **Patient Import** | <30 seconds for 1,000 patients | ~15 seconds |
| **Spruce Matching** | <60 seconds for 1,384 patients | ~45 seconds |
| **SMS Batch Send** | 50 messages in <15 seconds | ~10 seconds |
| **Database Query** | <100ms for patient list | ~50ms |

### 10.2 Scalability Limits

**Current Architecture:**

| Resource | Limit | Current Usage | Headroom |
|----------|-------|---------------|----------|
| **Patients** | ~10,000 (SQLite practical limit) | 1,384 | 7x |
| **Concurrent Users** | 1 (Streamlit limitation) | 1 | N/A |
| **SMS/day** | 10,000 (Spruce limit) | <500 | 20x |
| **Database Size** | ~2GB (SQLite max practical) | ~50MB | 40x |

**Bottlenecks:**
- **Single User:** Streamlit session state is single-user by design
- **Spruce Rate Limits:** 100/min, 10,000/day
- **SQLite Writes:** Concurrent writes not supported (reads are fine)

### 10.3 Future Scalability Strategy

**Multi-User Support (Phase 2):**
- Replace Streamlit session auth with proper session management
- Add database connection pooling
- Implement optimistic locking for concurrent edits
- OR: Deploy multiple instances (one per workstation)

**Large Patient Populations:**
- SQLite can handle 10,000+ patients with proper indexing
- If >10,000 patients: Migrate to PostgreSQL or SQL Server
- Current patient count (1,384) is well within limits

**SMS Scaling:**
- Current batch approach handles rate limits
- For >10,000 patients: Implement job queue (Celery + Redis)
- Current approach sufficient for 28-day deadline

---

## 11. Future Considerations

### 11.1 Planned Enhancements (January-February 2026)

**Care Plan Generation:**
- Import clinical notes from OneNote
- AI-powered summarization (Azure Claude)
- Structured care plan templates
- Export to PDF or SharePoint

**Multi-User Sync:**
- SharePoint list sync for consent status
- Real-time updates via polling or webhooks
- Conflict resolution for simultaneous edits

**Advanced Analytics:**
- Consent response rate by cohort
- APCM enrollment trends
- Outreach effectiveness metrics
- Predictive modeling for follow-ups

### 11.2 Technical Debt

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| **Add unit tests** | High | Medium | Quality |
| **Implement MS OAuth** | High | Medium | Security |
| **Migrate to PostgreSQL** | Low | High | Scalability |
| **Add API documentation** | Medium | Low | Maintainability |
| **Implement webhooks** | Medium | Medium | Real-time updates |

### 11.3 Architecture Evolution

**Short-Term (Dec 2025):**
- Current Streamlit architecture sufficient
- Focus on feature delivery for Dec 31 deadline

**Mid-Term (Q1 2026):**
- Add Microsoft OAuth
- Implement OneNote integration
- Enhanced AI features (care plans)

**Long-Term (Q2 2026+):**
- Evaluate cloud deployment (with proper HIPAA controls)
- Consider migrating to FastAPI + React for better multi-user support
- Implement mobile companion app (if needed)

---

## 12. Conclusion

Patient Explorer's architecture is designed for rapid deployment while maintaining HIPAA compliance and security. The Streamlit-based approach enables fast iteration and leverages existing Python infrastructure from Phase 0 CLI tools.

**Strengths:**
- ✅ Fast development cycle (critical for Dec 31 deadline)
- ✅ HIPAA-compliant by design (localhost + BAA-covered APIs)
- ✅ Leverages existing Python codebase
- ✅ Simple deployment (no complex build process)
- ✅ Extensible architecture for future features

**Trade-offs:**
- ❌ Single-user limitation (acceptable for current use case)
- ❌ Less "native" feel than Electron app
- ❌ Requires Python installation (but simplified with launcher script)

**Recommendation:** Proceed with current architecture for Phase 1 (consent outreach). Re-evaluate for Phase 2 (care plans) based on multi-user requirements and staff feedback.

---

## Appendices

### A. File Count Summary

| Category | Files | Purpose |
|----------|-------|---------|
| Streamlit Pages | 15 | UI pages |
| Service Modules | 12 | Business logic |
| Database Models | 1 | ORM definitions |
| API Clients | 3 | External integrations |
| Phase 0 CLI | 9 | Original CLI tools |
| **Total** | **40** | Core application |

### B. Dependencies Summary

**Core (23 packages):**
- streamlit, sqlalchemy, pydantic, httpx, pandas, openpyxl, typer, rich, loguru, msal, openai, Office365-REST-Python-Client, bcrypt, python-dotenv, pytz, phonenumbers, beautifulsoup4, azure-ai-documentintelligence, pytest, black, ruff, mypy, pre-commit

### C. Related Documents

- **ADR-001:** Beta App Architecture Decisions
- **Architecture (Streamlit):** Detailed Streamlit architecture
- **PRD:** Product Requirements Document
- **Stories S5-S8:** Current sprint user stories
- **Spruce API Research:** Comprehensive Spruce API analysis

---

*Generated by Patient Explorer App Agent*
*December 3, 2025*
