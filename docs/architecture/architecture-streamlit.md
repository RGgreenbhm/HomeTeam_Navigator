# Patient Explorer - Streamlit Architecture Document

**Version**: 2.0
**Date**: November 30, 2025
**Status**: Active

---

## Table of Contents

1. [Introduction & Scope](#1-introduction--scope)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Data Models](#4-data-models)
5. [Security & HIPAA Compliance](#5-security--hipaa-compliance)
6. [Integration Points](#6-integration-points)
7. [Deployment](#7-deployment)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Introduction & Scope

### 1.1 Purpose

This document defines the technical architecture for **Patient Explorer**, a HIPAA-compliant local application for patient consent tracking, Spruce Health integration, and care plan generation during practice transition.

### 1.2 Architecture Decision

After evaluating Electron + React + TypeScript (original design), we pivoted to **Streamlit + Python** due to:
- Windows Defender file locking issues with Electron `.asar` files
- Existing Python infrastructure from Phase 0 CLI tools
- Faster development cycle for internal clinical tools
- Simplified deployment (no native module compilation)

### 1.3 Scope

**Phase 0 (Current - Consent Outreach):**
- Patient list import from Excel
- Spruce Health contact matching
- Consent status tracking
- Local SQLite storage

**Phase 1 (Jan-Feb 2025):**
- Streamlit UI for patient management
- Care plan generation
- Microsoft account integration (SharePoint/Teams)

**Out of Scope:**
- Cloud deployment (HIPAA requires local-only)
- Public internet access
- Mobile applications

### 1.4 Key Architectural Drivers

| Driver | Constraint | Implementation |
|--------|------------|----------------|
| **HIPAA Compliance** | Must use BAA-covered services only | Azure, Microsoft 365, Spruce (all under BAA) |
| **Offline-First** | Clinical workflows require offline access | SQLite local database, no cloud dependency |
| **Multi-User** | 4 team members need shared access | SharePoint/Teams integration for data sync |
| **Rapid Development** | 30-day emergency timeline | Python + Streamlit (proven, fast iteration) |
| **AI Capabilities** | HIPAA-compliant AI assistance | Azure Foundry Claude (under Microsoft BAA) |

### 1.5 AI Services (HIPAA-Compliant)

**Azure Foundry Claude** is available under the Microsoft HIPAA BAA for:
- AI-assisted consent form processing
- Patient communication parsing
- Care plan generation
- Conflict resolution suggestions

See: `docs/Research_Reports/2025-11-30_Azure-Claude-HIPAA-BAA-Compatible.md`

---

## 2. High-Level Architecture

### 2.1 System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │  Excel      │   │  Spruce     │   │ SharePoint  │   │   Azure     │     │
│  │  Patient    │   │  Health     │   │ (Consent    │   │   OCR       │     │
│  │  Lists      │   │  (BAA)      │   │  Tracking)  │   │  (BAA)      │     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘     │
│         │ Import          │ API             │ API             │ API         │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                                      │                                       │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        PATIENT EXPLORER                                │  │
│  │                   (Streamlit Local Web App)                            │  │
│  │                      http://localhost:8501                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│                          ┌─────────────────────┐                            │
│                          │   SQLite Database   │                            │
│                          │   (Local + Encrypted)│                            │
│                          └─────────────────────┘                            │
│                               BitLocker Device                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Application Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STREAMLIT APPLICATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         STREAMLIT UI LAYER                           │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │    │
│  │  │  Patient List │  │  Consent      │  │  Care Plan    │           │    │
│  │  │  Page         │  │  Dashboard    │  │  Generator    │           │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘           │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │    │
│  │  │  Import       │  │  Match        │  │  Settings     │           │    │
│  │  │  Wizard       │  │  Results      │  │  Page         │           │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         SERVICE LAYER (phase0)                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ Excel Loader │  │ Spruce       │  │ SharePoint   │              │    │
│  │  │ Service      │  │ Client       │  │ Client       │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │ Patient      │  │ Consent      │  │ Care Plan    │              │    │
│  │  │ Service      │  │ Service      │  │ Service      │              │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         DATA ACCESS LAYER                            │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │                    SQLite + SQLAlchemy                        │   │    │
│  │  │              (patients.db - encrypted at rest)                │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Directory Structure

```
Patient_Explorer/
├── phase0/                     # Python services (existing)
│   ├── __init__.py
│   ├── main.py                 # CLI commands
│   ├── models.py               # Pydantic data models
│   ├── excel_loader.py         # Excel import service
│   ├── spruce/                 # Spruce Health API client
│   │   ├── __init__.py
│   │   └── client.py
│   └── sharepoint/             # SharePoint integration
│       ├── __init__.py
│       └── client.py
├── app/                        # Streamlit application (new)
│   ├── __init__.py
│   ├── main.py                 # Streamlit entry point
│   ├── pages/                  # Multi-page app structure
│   │   ├── 1_Patients.py       # Patient list view
│   │   ├── 2_Consent.py        # Consent tracking dashboard
│   │   ├── 3_Care_Plans.py     # Care plan generator
│   │   ├── 4_Import.py         # Excel import wizard
│   │   └── 5_Settings.py       # Configuration
│   ├── components/             # Reusable UI components
│   │   ├── patient_table.py
│   │   ├── consent_form.py
│   │   └── stats_cards.py
│   └── database/               # SQLite database layer
│       ├── __init__.py
│       ├── models.py           # SQLAlchemy models
│       └── connection.py       # Database connection
├── data/                       # Patient data (gitignored)
├── docs/                       # Documentation
├── .venv/                      # Python virtual environment
├── .env                        # API credentials (gitignored)
└── requirements.txt            # Python dependencies
```

---

## 3. Technology Stack

### 3.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **UI Framework** | Streamlit | 1.29+ | Local web application |
| **Language** | Python | 3.10+ | Core development |
| **Database** | SQLite | 3.45+ | Local encrypted storage |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Data Models** | Pydantic | 2.0+ | Type-safe validation |
| **HTTP Client** | httpx | 0.25+ | Async API calls |
| **Excel** | pandas + openpyxl | 2.0+ / 3.1+ | Excel import/export |
| **CLI** | Typer + Rich | 0.9+ | Command-line tools |

### 3.2 Integration Technologies

| Integration | Library | Purpose |
|-------------|---------|---------|
| **Spruce Health** | httpx | REST API for contacts |
| **SharePoint** | Office365-REST-Python-Client | Consent list sync |
| **Azure OCR** | azure-cognitiveservices-vision | Screenshot text extraction |
| **Microsoft Auth** | msal | Azure AD authentication (future) |

### 3.3 Development Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Unit and integration testing |
| **black** | Code formatting |
| **ruff** | Linting |
| **mypy** | Static type checking |

---

## 4. Data Models

### 4.1 Core Entities

```python
# SQLAlchemy Models (app/database/models.py)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    mrn = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)

    # Spruce integration
    spruce_id = Column(String)
    spruce_matched = Column(Boolean, default=False)
    spruce_match_method = Column(String)  # phone, name, email

    # APCM tracking
    apcm_eligible = Column(Boolean, default=False)
    apcm_enrolled = Column(Boolean, default=False)

    # Timestamps
    last_visit_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    consent = relationship("Consent", back_populates="patient", uselist=False)
    captures = relationship("Capture", back_populates="patient")


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Consent status
    status = Column(String, default="pending")  # pending, obtained, declined, unreachable
    method = Column(String)  # spruce, phone, mail, in_person, docusign

    # Dates
    outreach_date = Column(DateTime)
    response_date = Column(DateTime)
    consent_date = Column(DateTime)

    # Documentation
    spruce_message_id = Column(String)
    docusign_envelope_id = Column(String)
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="consent")


class Capture(Base):
    __tablename__ = "captures"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Capture data
    capture_type = Column(String)  # screenshot, text, document
    source = Column(String)  # allscripts, onenote, spruce
    raw_content = Column(Text)
    ocr_text = Column(Text)

    # Timestamps
    capture_date = Column(DateTime, default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="captures")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    user_id = Column(String)
    action = Column(String)  # view, edit, export, delete
    entity_type = Column(String)  # patient, consent, capture
    entity_id = Column(Integer)
    details = Column(JSON)
```

### 4.2 Consent Status Values

| Status | Description |
|--------|-------------|
| `pending` | No outreach attempted |
| `outreach_sent` | Invitation/message sent, awaiting response |
| `consented` | Patient has consented |
| `declined` | Patient declined consent |
| `unreachable` | Unable to contact patient |

### 4.3 Consent Methods

| Method | Description |
|--------|-------------|
| `spruce` | Text message via Spruce Health |
| `phone` | Phone call consent |
| `mail` | Mailed paper form |
| `in_person` | In-office paper signature |
| `docusign` | Electronic signature via DocuSign |

---

## 5. Security & HIPAA Compliance

### 5.1 Defense in Depth

| Layer | Protection | Implementation |
|-------|------------|----------------|
| **1. Device** | Full-disk encryption | Windows BitLocker required |
| **2. Application** | Local-only access | Streamlit binds to localhost only |
| **3. Database** | At-rest encryption | SQLite on BitLocker volume |
| **4. Transport** | TLS for external APIs | HTTPS to Spruce/SharePoint/Azure |
| **5. Access** | Microsoft authentication | Azure AD login (Phase 1) |
| **6. Audit** | Activity logging | All PHI access logged |

### 5.2 HIPAA Safeguards

**Administrative:**
- BAA in place with Microsoft (SharePoint, Azure OCR)
- BAA in place with Spruce Health
- No BAA with Anthropic (Claude cannot access PHI)

**Technical:**
- Streamlit runs on `localhost:8501` only (no network exposure)
- All API credentials stored in `.env` (gitignored)
- Database file on encrypted volume only
- Audit logging for all PHI access

**Physical:**
- Windows 11 with BitLocker required
- Device policy enforced at startup

### 5.3 Startup Security Checks

```python
# app/main.py - Security checks before starting

def verify_security():
    """Verify security requirements before starting app."""

    # Check BitLocker status
    if platform.system() == "Windows":
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-BitLockerVolume -MountPoint C:).ProtectionStatus"],
            capture_output=True, text=True
        )
        if "On" not in result.stdout:
            st.error("BitLocker encryption must be enabled")
            st.stop()

    # Verify localhost binding
    if os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost") != "localhost":
        st.error("Application must run on localhost only")
        st.stop()
```

---

## 6. Integration Points

### 6.1 Spruce Health API

**Purpose:** Match patients to Spruce contacts for messaging consent

**Endpoints Used:**
- `GET /v1/contacts` - List all contacts with pagination
- `GET /v1/contacts/{id}` - Get contact details

**Authentication:** Bearer token (Base64 encoded)

**Data Synced:**
- Patient name, phone, email
- Spruce patient ID for message tracking

### 6.2 SharePoint Integration

**Purpose:** Centralized consent tracking for team collaboration

**Features:**
- SharePoint List for consent records
- Syncs with local SQLite database
- Allows team to update consent status from any device

**Authentication:** Azure AD OAuth with client credentials

### 6.3 Azure Cognitive Services (Phase 1)

**Purpose:** OCR for Allscripts/OneNote screenshot extraction

**Service:** Computer Vision API (Read operation)

**BAA Status:** Microsoft BAA covers Azure Cognitive Services

---

## 7. Deployment

### 7.1 Local Deployment Only

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app (localhost only)
streamlit run app/main.py --server.address localhost
```

### 7.2 Startup Script

```batch
@echo off
:: patient_explorer.bat - Launch script

:: Activate virtual environment
call .venv\Scripts\activate

:: Set localhost only
set STREAMLIT_SERVER_ADDRESS=localhost
set STREAMLIT_SERVER_PORT=8501

:: Run Streamlit
streamlit run app/main.py --server.address localhost --server.port 8501
```

### 7.3 Environment Variables

```env
# .env file (gitignored)

# Spruce Health API
SPRUCE_API_TOKEN=your_base64_token

# SharePoint (optional)
SHAREPOINT_SITE_URL=https://tenant.sharepoint.com/sites/PatientConsent
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret

# Azure OCR (Phase 1)
AZURE_OCR_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OCR_KEY=your_key

# Database
DATABASE_PATH=data/patients.db
LOG_FILE=logs/phase0.log
```

---

## 8. Testing Strategy

### 8.1 Test Levels

| Level | Framework | Coverage |
|-------|-----------|----------|
| **Unit** | pytest | Service layer functions |
| **Integration** | pytest + SQLite in-memory | Database operations |
| **UI** | Streamlit testing | Page rendering (manual) |
| **Security** | Custom checks | BitLocker verification |

### 8.2 Test Structure

```
tests/
├── unit/
│   ├── test_excel_loader.py
│   ├── test_spruce_client.py
│   └── test_consent_service.py
├── integration/
│   ├── test_database.py
│   └── test_sharepoint_sync.py
└── conftest.py              # Fixtures
```

### 8.3 HIPAA Compliance Tests

```python
def test_localhost_binding():
    """Verify app only binds to localhost."""
    # Check Streamlit config
    assert os.getenv("STREAMLIT_SERVER_ADDRESS") == "localhost"

def test_no_phi_in_logs():
    """Verify no PHI appears in log files."""
    # Check log output for sensitive patterns
    pass

def test_bitlocker_check():
    """Verify BitLocker check runs at startup."""
    pass
```

---

## Appendices

### A. Migration from Electron Design

The original Electron architecture (archived in `/archive/electron-docs/`) included:
- Main/Renderer process separation
- IPC channel communication
- React + TypeScript UI
- SQLCipher encryption

The Streamlit architecture simplifies this to:
- Single Python process
- Direct database access
- Streamlit components
- BitLocker for encryption (OS-level)

### B. Phase Roadmap

| Phase | Features | Target |
|-------|----------|--------|
| **Phase 0** | CLI tools, Spruce matching | Complete |
| **Phase 1A** | Streamlit UI, patient list, consent tracking | Dec 2025 |
| **Phase 1B** | SharePoint sync, multi-user | Jan 2025 |
| **Phase 1C** | Care plan generation, OCR | Feb 2025 |

---

*Last Updated: November 30, 2025 (v2.0 - Streamlit architecture)*
