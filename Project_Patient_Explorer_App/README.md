# Project: Patient Explorer App

**Project Agent:** Patient Explorer App Agent
**Command:** `/agent-patient-explorer-app`
**Status:** Alpha Development
**Deadline:** December 31, 2025

---

## Agent Identity

This project is managed by the **Patient Explorer App Agent**, named by extracting the folder stem:

- **Folder:** `Project_Patient_Explorer_App/`
- **Agent Name:** Patient Explorer App Agent
- **Naming Rule:** `Project_` prefix removed, underscores → spaces, title case + "Agent"

---

## Project Overview

HIPAA-compliant Streamlit application for patient consent tracking, chart building, and clinical workflow support during practice transition from Southview Medical Group to Home Team Medical Services.

### Key Objectives

1. **Phase 0 (Dec 31, 2025):** Patient consent tracking and outreach
2. **Phase 1 (Jan 2025+):** Chart building with OneNote integration
3. **Phase 2 (Future):** Full clinical workflow CRM with AI support

---

## Project Agent Capabilities

The **Patient Explorer App Agent** can:

- ✅ Read entire workspace for context
- ✅ Write to `Project_Patient_Explorer_App/` folder only
- ✅ Generate status briefs in `briefs/`
- ✅ Generate research reports in `research/`
- ✅ Create architecture docs in `architecture/`
- ❌ Cannot modify files outside this folder
- ❌ Cannot modify CLAUDE.md or workspace config

### Launch the Agent

```bash
/agent-patient-explorer-app
```

---

## Folder Structure

```
Project_Patient_Explorer_App/
├── README.md              # This file
├── APP_FILE_REFERENCE.md  # Complete map of all app source files
├── briefs/                # Status briefs (YYYY-MM-DD_*.md)
├── research/              # Research reports
└── architecture/          # ADRs and technical docs
```

## App Source File Locations

The application source code lives in its original locations (not in this folder):

| Location | Contents | File Count |
|----------|----------|------------|
| `app/` | Streamlit web application | 29 files |
| `app/pages/` | UI pages (15 total) | 15 files |
| `phase0/` | Python CLI tool | 9 files |
| `docs/` | Documentation, stories, research | ~25 files |

**See [APP_FILE_REFERENCE.md](APP_FILE_REFERENCE.md) for the complete file map.**

Why files aren't moved here:
- Moving would break import paths and the running application
- This folder is for project management outputs (briefs, research), not source code
- Git history is preserved in original locations

---

## Current Status

### Implemented Features
- ✅ Patient list management
- ✅ Consent tracking (SharePoint integration)
- ✅ Spruce Health API integration
- ✅ Smart Data Ingest with AI conflict resolution (backend)
- ✅ Azure Claude integration (HIPAA-compliant)
- ✅ User authentication system

### In Development (Stories S5-S8)
- ⚠️ S5: Microsoft OAuth integration
- ⚠️ S6: OneNote integration
- ⚠️ S7: Consent form setup
- ⚠️ S8: SMS outreach campaign

---

## Key Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| Alpha Deployment | Dec 5 | In Progress |
| MS OAuth Integration (S5) | Dec 10 | Pending |
| OneNote Access (S6) | Dec 12 | Pending |
| Consent Form Live (S7) | Dec 15 | Pending |
| SMS Campaign (S8) | Dec 20 | Pending |
| Phase 0 Complete | Dec 31 | DEADLINE |

---

## Request a Status Brief

Launch the agent and ask for a brief:

```bash
/agent-patient-explorer-app
# Then: "Generate a project status brief"
```

The agent will create a dated brief in `briefs/YYYY-MM-DD_ProjectStatusBrief.md`.

---

**Project Created:** December 2, 2025
**Agent:** Patient Explorer App Agent
