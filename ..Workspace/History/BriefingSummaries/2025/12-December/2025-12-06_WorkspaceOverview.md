# Workspace Overview: 2025-12-06

**Days to Deadline: 25**

---

## Executive Summary

Patient_Explorer is a HIPAA-compliant patient consent tracking and outreach tool supporting Dr. Robert Green's practice transition from Southview Medical Group to Home Team Medical Services. The workspace has evolved from a CLI-focused Phase 0 tool to include a comprehensive Streamlit web application with Microsoft 365 integration capabilities.

**Current Phase:** Phase 0 - Consent Outreach Tool (Streamlit + CLI)
**Deadline:** December 31, 2025
**Status:** Active development, critical path items pending

---

## Workspace Contents

### Core Application

| Component | Location | Status |
|-----------|----------|--------|
| Streamlit App | `app/` | 15 pages, functional |
| Phase 0 CLI | `phase0/` | Complete, needs testing |
| Database | `data/patients.db` | SQLite, local |
| SharePoint Sync | `app/sharepoint_sync.py` | Implemented |

### Streamlit Pages (15 total)

1. Patient List - View and search patients
2. Consent Tracking - Track consent status
3. APCM Patients - Medicare APCM tracking
4. Outreach Campaign - SMS/email campaigns
5. AI Assistant - Azure Claude integration
6. Add Documents - Document management
7. M365 Integration - Microsoft 365 features
8. Team Tasks - Staff task management
9. Admin - Configuration and settings
10. Smart Data Ingest - Data import tools
11. Consent Response - Response tracking
12. Follow Up Queue - Follow-up management
13. Patient Notes - Clinical notes
14. Daily Summary - Activity dashboard
15. Test SMS - Spruce SMS testing

### Documentation

| Category | Count | Location |
|----------|-------|----------|
| Research Reports | 7 | `docs/research/` |
| Story Documents | 7 | `docs/stories/` |
| Architecture Docs | 1 | `docs/architecture/` |
| Planning Docs | 1 | `docs/planning/` |

### Key Research Reports (Dec 2025)

- **Microsoft Auth Strategy** - Graph API integration, MCP servers, HIPAA compliance
- **Teams Bookings Telehealth** - Virtual visits, autopilot configuration
- **Azure AD Permissions** - App registration guide
- **KP Good Shepherd Analysis** - Multi-agent framework patterns
- **OpenEvidence UI Patterns** - Medical AI interface design
- **Spruce Health API** - Capabilities and integration options
- **OneNote Integration** - OAuth requirements (app-only deprecated March 2025)

---

## Current Goals

### Primary Objective
Complete patient consent outreach campaign before December 31, 2025 deadline.

### Critical Path Items

1. **Microsoft OAuth Integration**
   - Register Azure AD application
   - Configure delegated permissions for Graph API
   - Run PowerShell Application Access Policy for Teams APIs
   - Enable user sign-in flow in Streamlit app

2. **Patient Outreach Infrastructure**
   - Create Microsoft Consent Form (BETA-001)
   - Configure Spruce SMS templates (BETA-002)
   - Deploy alpha to staff (BETA-003)

3. **Data Access**
   - Access Green Clinic Team Notebook via OneNote API
   - Retrieve Teams meeting transcripts for clinical visits
   - Configure SharePoint sync for multi-user collaboration

### Secondary Objectives

- Configure Teams Bookings for telehealth visits
- Set up autopilot@southviewteam.com as central admin account
- Evaluate MCP server integration for Claude orchestration

---

## Active Areas

### High Activity (Last 7 Days)

| Area | Changes | Notes |
|------|---------|-------|
| Workspace Settings | Multiple files | Config consolidation |
| Slash Commands | New commands | export-pdf, research-topic |
| Research Reports | 3 new | Microsoft auth, Bookings, Azure AD |
| MS OAuth | New module | `app/ms_oauth.py` created |

### Pending Work

| Area | Status | Blocker |
|------|--------|---------|
| Azure AD Registration | Not started | User action required |
| Application Access Policy | Not started | Requires admin PowerShell |
| Consent Form | Not started | User action required |
| Jenny Deployment | Not started | Requires user action |

---

## Top 3 Focus Areas

### Focus Area 1: Azure AD App Registration (CRITICAL)

**Why:** All Microsoft integrations depend on this. Blocks OneNote, Teams transcripts, and Graph API access.

**Actions:**
1. Go to Azure Portal > App registrations > New registration
2. Configure redirect URI for Streamlit (`http://localhost:8501/callback`)
3. Add Graph API permissions (User.Read, Notes.Read, OnlineMeetings.Read)
4. Generate client secret
5. Update `.env` with credentials
6. Run PowerShell Application Access Policy

**Reference:** `docs/research/2025-12-04_research_microsoft-auth-graph-api-integration-strategy.md`

### Focus Area 2: Microsoft Consent Form Creation (HIGH)

**Why:** Patient outreach cannot begin without consent collection mechanism.

**Actions:**
1. Create Microsoft Form with fields from BETA-001 story
2. Configure response collection to SharePoint list
3. Paste form URL into Streamlit Outreach Campaign page
4. Test with 5 pilot patients

**Reference:** `docs/stories/BETA-001-microsoft-forms-setup.md`

### Focus Area 3: Commit & Deploy (HIGH)

**Why:** 11 uncommitted files, 15+ untracked files. Risk of lost work. Staff testing blocked.

**Actions:**
1. Review uncommitted changes for sensitive data
2. Create meaningful commit with current progress
3. Push to remote repository
4. Run setup-beta.ps1 on Jenny's machine
5. Test Streamlit app with staff user

**Reference:** `docs/planning/alpha-deployment-guide.md`

---

## Technology Stack

| Layer | Technology | Status |
|-------|------------|--------|
| Frontend | Streamlit | Active |
| Backend | Python 3.10+ | Active |
| Database | SQLite | Active |
| Cloud Storage | SharePoint | Configured |
| Messaging | Spruce Health API | Tested |
| AI | Azure Claude (HIPAA BAA) | Ready |
| Auth | Microsoft OAuth 2.0 | Pending |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Deadline miss (25 days) | HIGH | Prioritize critical path items |
| Uncommitted changes lost | MEDIUM | Commit today |
| OAuth not working | HIGH | Follow research report step-by-step |
| Staff unfamiliar with app | MEDIUM | Schedule training with Jenny |

---

## Quick Links

| Resource | Location |
|----------|----------|
| Main App | `streamlit run app/main.py` |
| CLI Help | `python -m phase0 --help` |
| Research Reports | `docs/research/` |
| Stories | `docs/stories/` |
| Auth Strategy | `docs/research/2025-12-04_research_microsoft-auth-graph-api-integration-strategy.md` |

---

*Generated: 2025-12-06 | Reference: File system scan, git status, research reports*
