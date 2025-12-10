# Story S1: Initialize Streamlit Application Structure

## Status
In Progress

## Story
**As a** developer,
**I want** a Streamlit application scaffolded with proper structure,
**so that** I have a foundation to build the Patient Explorer local UI.

## Acceptance Criteria
1. Streamlit app launches with `streamlit run app/main.py`
2. App binds to localhost only (security requirement)
3. Multi-page structure using Streamlit pages
4. Existing phase0 services are importable
5. SQLite database connection established
6. BitLocker verification runs at startup

## Tasks / Subtasks
- [ ] Create app directory structure (AC: 1, 3)
  - [ ] Create app/__init__.py
  - [ ] Create app/main.py (entry point)
  - [ ] Create app/pages/ directory
- [ ] Install Streamlit dependencies (AC: 1)
  - [ ] streamlit>=1.29.0
  - [ ] sqlalchemy>=2.0.0
  - [ ] Add to requirements.txt
- [ ] Create main entry point (AC: 1, 2, 6)
  - [ ] Security verification (BitLocker check)
  - [ ] Localhost-only binding enforcement
  - [ ] Navigation sidebar
- [ ] Create initial pages (AC: 3)
  - [ ] app/pages/1_Patients.py (placeholder)
  - [ ] app/pages/2_Consent.py (placeholder)
  - [ ] app/pages/3_Settings.py (placeholder)
- [ ] Set up database layer (AC: 5)
  - [ ] Create app/database/__init__.py
  - [ ] Create app/database/connection.py
  - [ ] Create app/database/models.py
- [ ] Verify phase0 integration (AC: 4)
  - [ ] Import phase0.models works
  - [ ] Import phase0.excel_loader works
  - [ ] Import phase0.spruce works

## Dev Notes

### Project Structure
```
app/
├── __init__.py
├── main.py                 # Entry point with security checks
├── pages/
│   ├── 1_Patients.py       # Patient list view
│   ├── 2_Consent.py        # Consent tracking
│   └── 3_Settings.py       # Configuration
├── components/             # Reusable components
│   └── __init__.py
└── database/
    ├── __init__.py
    ├── connection.py       # SQLite connection
    └── models.py           # SQLAlchemy models
```

### Security Check Implementation
```python
# app/main.py
import streamlit as st
import subprocess
import platform

def verify_bitlocker():
    """Verify BitLocker is enabled on Windows."""
    if platform.system() != "Windows":
        return True  # Skip on non-Windows

    result = subprocess.run(
        ["powershell", "-Command",
         "(Get-BitLockerVolume -MountPoint C:).ProtectionStatus"],
        capture_output=True, text=True
    )
    return "On" in result.stdout

# Main app
st.set_page_config(
    page_title="Patient Explorer",
    page_icon="🏥",
    layout="wide"
)

if not verify_bitlocker():
    st.error("⚠️ BitLocker encryption must be enabled")
    st.stop()

st.title("Patient Explorer")
st.write("Select a page from the sidebar")
```

### Localhost-Only Binding
Run with: `streamlit run app/main.py --server.address localhost`

Or set in `.streamlit/config.toml`:
```toml
[server]
address = "localhost"
port = 8501
```

## Testing
- **Location**: `tests/`
- **Framework**: pytest
- **Required Tests**:
  - App imports without errors
  - Database connection works
  - phase0 services importable

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story for Streamlit migration | Claude |

---

## Dev Agent Record
### Agent Model Used
### Debug Log References
### Completion Notes
### File List

---

## QA Results
