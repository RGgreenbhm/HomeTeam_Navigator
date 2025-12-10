# Archived Electron Documentation

**Archived**: November 30, 2025

## Why Archived

The original Patient Explorer was designed as an Electron + React + TypeScript desktop application. During implementation, we encountered persistent Windows Defender file locking issues with Electron's `.asar` files during npm install that could not be resolved.

After evaluating alternatives, we pivoted to a **Streamlit + Python** approach for Phase 0 (Consent Outreach) and future phases. This approach:
- Avoids native module compilation issues
- Leverages existing Python infrastructure from Phase 0
- Runs locally for HIPAA compliance (localhost only)
- Integrates naturally with SQLite and the existing phase0 codebase

## Archived Contents

### Core Architecture Documents
- `architecture.md` - Electron/React/SQLCipher architecture with IPC channels
- `frontend-spec.md` - React UI component specifications and wireframes

### Story Files (30 stories across 5 epics)
- **E1**: Core Foundation (Electron project init, SQLCipher, app shell)
- **E2**: Screenshot Capture & OCR
- **E3**: Patient Data Management
- **E4**: Consent Tracking
- **E5**: Security Foundation

## What's Still Relevant

The following documents in `/docs/` remain active:
- `project-brief.md` - Core requirements (technology-agnostic)
- `prd.md` - Functional requirements (mostly technology-agnostic)
- Reference data CSV files

## New Architecture

See `/docs/architecture-streamlit.md` for the updated Streamlit + SQLite architecture.

---

*These files are preserved for reference and potential future use if Electron becomes viable.*
