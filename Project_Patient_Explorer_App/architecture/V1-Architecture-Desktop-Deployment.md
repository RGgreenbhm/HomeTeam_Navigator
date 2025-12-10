# Patient Explorer V1.0 Architecture & Desktop Deployment Guide

**Date:** 2025-12-08
**Version:** 1.0
**Status:** Planning

---

## Executive Summary

Patient Explorer V1.0 is a HIPAA-compliant patient consent tracking and clinical data management application. This document provides a comprehensive architecture reassessment incorporating recent research findings, and outlines the strategy for packaging the application as a distributable Windows desktop application.

**Key Decision:** Package existing Streamlit application with PyInstaller for immediate desktop deployment, with optional Tauri migration path for future native experience.

---

## Part 1: Architecture Reassessment

### Current State Analysis

| Component | Technology | Status |
|-----------|------------|--------|
| **Web Framework** | Streamlit 1.29+ | Production Ready |
| **Database** | SQLite + SQLAlchemy | Production Ready |
| **Authentication** | PBKDF2 + Azure AD OAuth | Production Ready |
| **API Integrations** | Spruce, Microsoft Graph, Azure Blob | Production Ready |
| **Desktop** | None (browser-based) | Gap to Address |

### Research-Driven Enhancements

Based on recent research reports, the following capabilities need integration:

#### 1. Real-Time Consent Detection (Spruce Webhooks)
```
SMS Reply → Spruce Webhook → Azure Function → Patient Explorer DB
                                    ↓
                            Consent Status Update
```
- Eliminates manual CSV export/import
- Enables real-time campaign monitoring
- Requires HTTPS endpoint for webhook receiver

#### 2. Intelligent Patient Matching (Phone + Name)
```
Excel Import → Phone Normalization (E.164) → Exact Match?
                        ↓                         ↓
                   Fuzzy Name Match          Match Found
                        ↓
                 Confidence Scoring
                        ↓
              High/Medium/Low → Auto/Review/Manual
```
- `phonenumbers` library for E.164 normalization
- `rapidfuzz` for fuzzy name matching (MIT licensed)
- Multi-stage matching with confidence tiers

#### 3. APCM Compliance Tracking (CMS Requirements)
```
Patient Record → APCM Enrollment Check → 13 Element Checklist
                        ↓                        ↓
                  Billing Code Validation    Service Documentation
                        ↓
                 Conflicting Service Warnings
```
- G0556/G0557/G0558 billing code validation
- CMS-required consent disclosures tracking
- CCM/PCM/TCM conflict detection

---

## Part 2: V1.0 Target Architecture

### System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           WINDOWS 11 DEVICE                             │
│                        (BitLocker Encrypted)                            │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    PATIENT EXPLORER V1.0                        │   │
│  │                                                                 │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │   │
│  │   │   Streamlit  │    │   SQLite     │    │   Services   │    │   │
│  │   │   Web UI     │◄──►│   Database   │◄──►│   Layer      │    │   │
│  │   │  (19 Pages)  │    │ (patients.db)│    │              │    │   │
│  │   └──────────────┘    └──────────────┘    └──────────────┘    │   │
│  │          │                                       │             │   │
│  └──────────│───────────────────────────────────────│─────────────┘   │
│             │                                       │                  │
│             ▼                                       ▼                  │
│    ┌─────────────┐                        ┌─────────────────────┐     │
│    │   Browser   │                        │   Azure Function    │     │
│    │ localhost   │                        │  (Webhook Receiver) │     │
│    │   :8501     │                        └─────────────────────┘     │
│    └─────────────┘                                  │                  │
└─────────────────────────────────────────────────────│──────────────────┘
                                                      │
              ┌───────────────────────────────────────┼───────────────────┐
              │                    EXTERNAL SERVICES (BAA COVERED)        │
              │                                                           │
              │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
              │   │   Spruce     │  │  Microsoft   │  │    Azure     │  │
              │   │   Health     │  │    Graph     │  │    Blob      │  │
              │   │   (SMS)      │  │  (SharePoint)│  │  (Backup)    │  │
              │   └──────────────┘  └──────────────┘  └──────────────┘  │
              │                                                           │
              └───────────────────────────────────────────────────────────┘
```

### Database Schema (V1.0 Enhanced)

#### Core Tables (Existing)
- `patients` - Master patient record
- `consents` - Consent tracking
- `users` - Authentication
- `audit_logs` - HIPAA compliance
- `patient_notes` - Local notes

#### New Clinical Tables
- `patient_problems` - Problem list (ICD-10)
- `patient_medications` - Medication list
- `patient_allergies` - Allergy list
- `patient_immunizations` - Vaccine tracking
- `patient_screenings` - Health maintenance
- `patient_encounters` - Visit history
- `patient_screenshots` - EMR screenshot references
- `patient_communications` - Spruce message log
- `patient_care_plans` - APCM care plans

#### New APCM Fields on Patient Table
```python
# APCM Compliance Tracking
apcm_consent_disclosures = Column(JSON)  # {single_provider, cost_sharing, right_to_stop}
apcm_service_elements = Column(JSON)      # 13 element checklist
apcm_qmb_status = Column(Boolean)         # Qualified Medicare Beneficiary
apcm_last_billing_date = Column(Date)
apcm_conflicting_services = Column(JSON)  # CCM/PCM/TCM tracking
```

### Service Layer Architecture

```
app/services/
├── __init__.py
├── patient_consolidator.py    # Existing - data consolidation
├── phone_normalizer.py        # NEW - E.164 conversion
├── name_matcher.py            # NEW - Fuzzy name matching
├── patient_matcher.py         # NEW - Multi-stage matching
├── spruce_webhook.py          # NEW - Webhook receiver
├── consent_detector.py        # NEW - SMS pattern matching
├── apcm_compliance.py         # NEW - Billing validation
└── azure_function_client.py   # NEW - Webhook endpoint management
```

---

## Part 3: Desktop Deployment Strategy

### Option Comparison

| Approach | Effort | Size | Native Feel | Offline | Recommendation |
|----------|--------|------|-------------|---------|----------------|
| **PyInstaller + Streamlit** | Low | ~200MB | Medium | Yes | **Phase 1 (Now)** |
| **Tauri** | High | ~50MB | High | Yes | Phase 2 (Future) |
| **Electron** | High | ~150MB | Medium | Yes | Not Recommended |
| **PyQt6** | Medium | ~100MB | High | Yes | Alternative |

### Recommended: PyInstaller Desktop Launcher

Package the existing Streamlit app as a Windows executable with a native launcher.

#### Architecture

```
PatientExplorer.exe (PyInstaller)
        │
        ├── Starts Streamlit server (background)
        ├── Opens default browser to localhost:8501
        ├── System tray icon for status/control
        └── Clean shutdown on exit
```

#### Benefits
- Minimal code changes to existing app
- Single-click startup for users
- No Python installation required
- Portable (can run from USB with BitLocker)
- Maintains HIPAA localhost-only constraint

### Implementation Files

#### 1. Desktop Launcher (`scripts/launcher.py`)
```python
"""
Patient Explorer Desktop Launcher
Starts Streamlit server and opens browser
"""
import subprocess
import webbrowser
import time
import sys
import os
from pathlib import Path

def get_app_path():
    """Get path to app directory (handles PyInstaller bundling)"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent

def main():
    app_path = get_app_path()
    main_py = app_path / "app" / "main.py"

    # Start Streamlit server
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(main_py),
         "--server.port", "8501",
         "--server.address", "127.0.0.1",
         "--server.headless", "true"],
        cwd=str(app_path)
    )

    # Wait for server to start
    time.sleep(3)

    # Open browser
    webbrowser.open("http://localhost:8501")

    # Wait for process (keeps running until closed)
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()

if __name__ == "__main__":
    main()
```

#### 2. PyInstaller Spec (`PatientExplorer.spec`)
```python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Collect Streamlit and dependencies
datas = []
binaries = []
hiddenimports = []

for pkg in ['streamlit', 'altair', 'pandas', 'plotly']:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['scripts/launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + [
        ('app', 'app'),
        ('data', 'data'),
        ('.env', '.'),
    ],
    hiddenimports=hiddenimports + [
        'streamlit.runtime.scriptrunner.magic_funcs',
        'sqlalchemy.dialects.sqlite',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PatientExplorer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/assets/icons/HTnav_medical_bag.png',
)
```

#### 3. Build Script (`scripts/build-desktop.ps1`)
```powershell
# Patient Explorer Desktop Build Script
# Requires: Python 3.10+, PyInstaller

Write-Host "Building Patient Explorer Desktop..." -ForegroundColor Cyan

# Activate virtual environment
& ".\.venv\Scripts\Activate.ps1"

# Install PyInstaller if needed
pip install pyinstaller

# Clean previous builds
Remove-Item -Recurse -Force .\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\dist -ErrorAction SilentlyContinue

# Build executable
pyinstaller PatientExplorer.spec --clean

# Copy additional files
Copy-Item ".env.example" ".\dist\PatientExplorer\.env.example"
New-Item -ItemType Directory -Force ".\dist\PatientExplorer\data"
New-Item -ItemType Directory -Force ".\dist\PatientExplorer\logs"

Write-Host "Build complete! Output: .\dist\PatientExplorer\" -ForegroundColor Green
Write-Host "To distribute: Zip the dist\PatientExplorer folder" -ForegroundColor Yellow
```

### Distribution Package Structure

```
PatientExplorer/
├── PatientExplorer.exe        # Main executable (double-click to run)
├── .env                       # Configuration (user edits)
├── .env.example               # Configuration template
├── data/                      # Patient data (user populates)
│   └── patients.db            # SQLite database (created on first run)
├── logs/                      # Application logs
├── README.txt                 # Quick start instructions
└── _internal/                 # PyInstaller runtime (hidden)
```

### Installation Instructions for End Users

```
PATIENT EXPLORER - INSTALLATION GUIDE

Requirements:
- Windows 11 Pro or Enterprise
- BitLocker encryption enabled (required for HIPAA)
- Internet access for first-time API setup

Installation:
1. Extract PatientExplorer.zip to your desired location
   (Recommended: C:\PatientExplorer or Desktop)

2. Copy your .env file to the PatientExplorer folder
   (Contains your API keys - obtain from IT administrator)

3. Double-click PatientExplorer.exe to start

4. Your default browser will open to the application
   (Always runs on localhost:8501 for security)

First Run:
- The application will create a new database on first run
- Import your patient Excel file via the Patient List page
- Configure Microsoft 365 integration in Admin settings

Support:
- Contact IT administrator for API key setup
- Application logs are in the logs/ folder
```

---

## Part 4: Security Considerations

### HIPAA Compliance Checklist

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Encryption at Rest** | BitLocker (device), SQLCipher optional (DB) | ✅ |
| **Encryption in Transit** | TLS 1.2+ for all API calls | ✅ |
| **Access Control** | Role-based (Admin/Provider/Staff/Readonly) | ✅ |
| **Audit Logging** | All data access logged with timestamp/user | ✅ |
| **Authentication** | PBKDF2 local + Azure AD OAuth | ✅ |
| **Session Management** | Streamlit session state | ✅ |
| **Localhost Only** | Server binds to 127.0.0.1 only | ✅ |
| **BAA Coverage** | Spruce, Microsoft, Azure all under BAA | ✅ |

### Desktop-Specific Security

1. **No Network Exposure**
   - Streamlit server only binds to localhost
   - No external connections except to BAA-covered APIs

2. **Portable Security**
   - Can run from encrypted USB drive
   - All data stays on local encrypted storage

3. **Credential Protection**
   - `.env` file contains API keys
   - Should be protected by Windows file permissions
   - Never committed to git

---

## Part 5: Implementation Roadmap

### Phase 1: Desktop Packaging (Week 1)

1. Create launcher script
2. Create PyInstaller spec
3. Test build process
4. Create distribution package
5. Write installation guide
6. Test on clean Windows 11 machine

### Phase 2: Research Integration (Weeks 2-3)

1. Add `phonenumbers` and `rapidfuzz` dependencies
2. Implement phone/name matching services
3. Deploy Azure Function for Spruce webhooks
4. Integrate APCM compliance tracking

### Phase 3: Page Consolidation (Weeks 4-5)

1. Merge consent pages (2+11+12 → 3)
2. Merge patient/APCM pages (1+3 → 1)
3. Merge document pages (6+10 → 11)
4. Remove OneNote from M365 page

### Phase 4: Clinical Data Pages (Weeks 6-8)

1. Patient Chart page
2. Problem List page
3. Medications & Allergies page
4. Immunizations page
5. Visit History page
6. Health Maintenance page
7. Care Plans page

### Phase 5: Polish & Release (Week 9)

1. Final page renumbering
2. Navigation updates
3. Testing and QA
4. Documentation
5. V1.0 release

---

## Part 6: Dependencies Update

### requirements.txt Additions

```
# Desktop packaging
pyinstaller>=6.0.0

# Phone number handling
phonenumbers>=8.13.0

# Fuzzy name matching
rapidfuzz>=3.0.0

# Webhook signature verification (already have httpx)
# No additional dependencies needed
```

### Environment Variables Update

```env
# Existing (keep as-is)
SPRUCE_API_TOKEN=...
SPRUCE_ACCESS_ID=...
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...

# NEW - Webhook support
SPRUCE_WEBHOOK_SECRET=whsec_your_webhook_secret

# NEW - Azure Function
AZURE_FUNCTION_URL=https://your-function.azurewebsites.net/api/spruce-webhook

# NEW - Matching configuration
PHONE_MATCH_CONFIDENCE_HIGH=0.90
PHONE_MATCH_CONFIDENCE_MEDIUM=0.75
NAME_MATCH_THRESHOLD=80
```

---

## Part 7: Future Considerations

### Tauri Migration (Post-V1.0)

If native desktop experience becomes priority:

1. **Keep Python backend** via Tauri sidecar process
2. **Port UI to Svelte/React** for Tauri frontend
3. **Benefits:**
   - Smaller package (~50MB vs ~200MB)
   - Native window management
   - Better OS integration
   - No browser dependency

### Multi-Device Sync (Post-V1.0)

For practices with multiple workstations:

1. **CouchDB** for offline-first sync
2. **Per-patient versioning** for conflict resolution
3. **Azure Blob** for central backup
4. Maintains HIPAA compliance via encryption

---

## Appendix A: File Changes Summary

### New Files to Create

| File | Purpose |
|------|---------|
| `scripts/launcher.py` | Desktop launcher |
| `PatientExplorer.spec` | PyInstaller configuration |
| `scripts/build-desktop.ps1` | Build script |
| `app/services/phone_normalizer.py` | Phone E.164 conversion |
| `app/services/name_matcher.py` | Fuzzy name matching |
| `app/services/patient_matcher.py` | Multi-stage matching |
| `app/services/spruce_webhook.py` | Webhook handler |
| `app/services/consent_detector.py` | SMS pattern matching |
| `app/services/apcm_compliance.py` | APCM billing validation |

### Files to Modify

| File | Changes |
|------|---------|
| `requirements.txt` | Add pyinstaller, phonenumbers, rapidfuzz |
| `.env.example` | Add webhook and matching config |
| `app/database/models.py` | Add clinical tables, APCM fields |
| `app/pages/1_Patient_List.py` | Add APCM tab, matching review |
| `app/pages/2_Consent_Tracking.py` | Merge with pages 11, 12 |

---

*Document generated: 2025-12-08*
*Patient Explorer V1.0 Architecture & Desktop Deployment Guide*
