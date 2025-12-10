# Workspace Overview: 2025-12-04

**Days to Deadline: 27**

---

## Executive Summary

**Patient_Explorer** is a HIPAA-compliant patient consent tracking and outreach tool for managing patient data during Dr. Green's EMR transition from Southview Medical Group to Home Team Medical Services. The deadline is **December 31, 2025** (27 days remaining).

The workspace has evolved from a basic CLI tool to a comprehensive platform with:
- Streamlit web application (beta-ready)
- SharePoint sync for multi-user collaboration
- Extensive research on Microsoft authentication and Graph API integration
- BMAD agent team for autonomous development assistance

**Current Phase:** Phase 0 - Consent Outreach Campaign
**Next Milestone:** Beta deployment to Jenny for in-clinic testing

---

## Workspace Contents

### Core Application

| Component | Location | Status |
|-----------|----------|--------|
| **Streamlit App** | `app/` | Beta-ready, 15+ pages |
| **Phase 0 CLI** | `phase0/` | Functional, tested |
| **Spruce Integration** | `phase0/spruce/` | Working, API verified |
| **SharePoint Sync** | `app/sharepoint_sync.py` | New, needs Azure AD setup |

### Documentation

| Category | Location | Contents |
|----------|----------|----------|
| **Research Reports** | `docs/research/` | 6 reports (OAuth, Spruce, OpenEvidence, KP, Auth Strategy, Bookings) |
| **Architecture** | `docs/architecture/` | ADR-001 (Beta App Architecture) |
| **User Stories** | `docs/stories/` | S5-S8, BETA-001-003 |
| **Planning** | `docs/planning/` | Alpha deployment guide |
| **Dev Notes** | `docs/dev-notes/` | Technical implementation notes |

### Workspace Management

| Component | Location | Purpose |
|-----------|----------|---------|
| **Focus Documents** | `..Workspace/Focus/` | Daily briefs, session planners |
| **History Archive** | `..Workspace/History/` | Past sessions, chat logs, git status |
| **Settings** | `..Workspace/Settings/` | Config files, reconciliation rules |
| **Reference** | `..Workspace/Reference/` | Research notes, templates |

### Configuration

| File | Purpose |
|------|---------|
| `CLAUDE.md` | AI assistant guide, HIPAA rules, workspace system |
| `.env` | API credentials (gitignored) |
| `.env.example` | Credential template with documentation |
| `requirements.txt` | Python dependencies |

---

## Current Goals

### Immediate (This Week)

1. **Register Azure AD Application** - Required for OAuth sign-in
2. **Configure Application Access Policy** - Required for Teams transcript access
3. **Create Microsoft Form** - For patient consent collection
4. **Deploy to Jenny's Machine** - Beta testing in clinic

### Short-term (Before Dec 31)

1. **Complete consent outreach campaign** - All 550+ patients contacted
2. **Achieve 60%+ consent rate** - Target for successful transition
3. **Document all responses** - For legal compliance
4. **Finalize patient transition list** - For Home Team onboarding

### Medium-term (January 2025)

1. **Phase 1: Chart Builder** - Screenshot capture, OCR, care plans
2. **Telehealth integration** - Teams Bookings for virtual visits
3. **Claude MCP orchestration** - AI-assisted workflow automation

---

## Active Development Areas

### 1. Microsoft Authentication (HOT)

**Recent Activity:** Comprehensive research completed today

- Graph API permissions matrix documented
- MCP server integration guides created (APIM and Local options)
- Application Access Policy steps clarified
- OneNote deprecation (March 2025) addressed

**Next Steps:**
- User to register Azure AD app
- User to run PowerShell policy commands
- Test OAuth sign-in flow

### 2. Telehealth/Bookings (HOT)

**Recent Activity:** Separate research report created today

- Bookings vs Regular Meetings comparison
- autopilot@southviewteam.com admin setup guide
- Virtual Appointments (Teams Premium) features documented
- HIPAA compliance checklist for telehealth

**Next Steps:**
- Enable Bookings in M365 Admin Center
- Create booking page for Green Clinic
- Configure providers as staff

### 3. SharePoint Sync (WARM)

**Recent Activity:** Feature implemented Dec 3

- Module created: `app/sharepoint_sync.py`
- Admin page updated with Sync tab
- Sidebar sync indicator added

**Blocking Issue:** Requires Azure AD OAuth to test

### 4. Consent Campaign (WARM)

**Status:** Ready to launch, blocked by form creation

- SMS templates drafted
- Workflow documented
- SharePoint tracking list design ready

**Blocking Issue:** Microsoft Form not created

---

## Top 3 Focus Areas for Development

### 1. Azure AD / OAuth Configuration (CRITICAL)

**Why:** Blocks SharePoint sync, authentication, and Graph API access

**Actions:**
- [ ] Register app in Azure Portal
- [ ] Configure redirect URI: `http://localhost:8501`
- [ ] Add Graph API permissions (User.Read, Files.ReadWrite.All, Sites.Read.All)
- [ ] Copy Client ID and Tenant ID to `.env`
- [ ] Run Application Access Policy PowerShell commands

**Reference:** `docs/research/2025-12-04_research_microsoft-auth-graph-api-integration-strategy.md`

### 2. Consent Form Creation (CRITICAL)

**Why:** Blocks patient outreach campaign

**Actions:**
- [ ] Create form at forms.microsoft.com
- [ ] Add fields: Name, DOB, consent checkboxes, signature
- [ ] Configure response settings
- [ ] Copy URL to Streamlit app sidebar

**Reference:** `docs/stories/BETA-001-microsoft-forms-setup.md`

### 3. Beta Deployment (HIGH)

**Why:** Enables in-clinic testing with Dr. Green and Jenny

**Actions:**
- [ ] Run `run-app.ps1` to verify local setup
- [ ] Copy project to Jenny's machine
- [ ] Install Python dependencies
- [ ] Configure `.env` with credentials
- [ ] Test all pages load correctly

**Reference:** `docs/planning/alpha-deployment-guide.md`

---

## Technology Stack

| Layer | Technology | Status |
|-------|------------|--------|
| **Frontend** | Streamlit | Working |
| **Backend** | Python 3.10+ | Working |
| **Database** | SQLite (local) | Working |
| **Sync** | SharePoint + Azure OAuth | Pending setup |
| **Messaging** | Spruce Health API | Working |
| **Consent Tracking** | Microsoft Forms + SharePoint | Pending setup |
| **AI** | Azure Claude (Foundry) | Available, HIPAA-covered |

---

## Team & Resources

| Role | Person/System | Status |
|------|---------------|--------|
| **Project Lead** | Dr. Robert Green | Active |
| **Clinical Staff** | Jenny | Pending beta access |
| **AI Development** | Claude Code + BMAD Agents | Active |
| **Admin Account** | autopilot@southviewteam.com | Available for automation |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Azure AD setup delays | Medium | High | Clear documentation provided |
| Low consent response rate | Medium | High | Multiple outreach channels |
| Technical issues at deployment | Low | Medium | Documented troubleshooting |
| HIPAA compliance gaps | Low | Critical | BAA in place, PHI controls documented |

---

## Session Recommendations

Based on current state, today's session should focus on:

1. **Complete Azure AD registration** - Unblocks multiple features
2. **Run PowerShell policy commands** - Unblocks transcript access
3. **Create Microsoft Form** - Unblocks consent campaign

All three are user-driven tasks that the agent team has fully documented and prepared for.

---

*Generated: 2025-12-04*
*Reference: CLAUDE.md, docs/, recent commits, session planners*
