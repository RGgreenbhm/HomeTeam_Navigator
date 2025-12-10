# Session Planner: 2025-12-06

**Days to Deadline: 25**

---

## 1. Session Scratch Notes

*Use this space to capture your stream-of-consciousness thoughts at the start of this session. What's on your mind? What prompted you to open this workspace today?*

```
[Enter your thoughts here before we begin...]




```

---

## 2. Proposed Focus Areas

Based on the Workspace Overview and 25-day countdown, here are the prioritized focus areas.

### Focus Area 1: Azure AD App Registration (CRITICAL)

**Priority: CRITICAL** | **Deadline: ASAP**

All Microsoft integrations are blocked until this is complete. This unlocks OneNote, Teams transcripts, and Graph API.

#### Checklist

- [ ] **Step 1: Register Application**
  - Go to Azure Portal > Microsoft Entra ID > App registrations
  - Click "New registration"
  - Name: `Patient-Explorer-App`
  - Supported account types: Single tenant (southviewteam.com)
  - Redirect URI: Web, `http://localhost:8501/callback`

- [ ] **Step 2: Configure API Permissions**
  - Microsoft Graph > Delegated permissions:
    - `User.Read` (sign-in)
    - `Notes.Read` (OneNote read)
    - `OnlineMeetings.Read` (Teams meetings)
    - `Calendars.Read` (Bookings)
  - Click "Grant admin consent"

- [ ] **Step 3: Create Client Secret**
  - Certificates & secrets > New client secret
  - Description: `Patient-Explorer-Secret`
  - Copy value immediately (shown once only)

- [ ] **Step 4: Update Environment**
  - Copy Client ID from Overview page
  - Copy Tenant ID from Overview page
  - Update `.env` file:
    ```
    MS_CLIENT_ID=<client-id>
    MS_CLIENT_SECRET=<secret-value>
    MS_TENANT_ID=<tenant-id>
    ```

- [ ] **Step 5: Run Application Access Policy (PowerShell)**
  - Required for Teams transcript access
  - Run as admin:
    ```powershell
    Install-Module -Name MicrosoftTeams -Force
    Connect-MicrosoftTeams
    New-CsApplicationAccessPolicy `
        -Identity "PatientExplorer-Policy" `
        -AppIds "<client-id>" `
        -Description "Patient Explorer transcript access"
    Grant-CsApplicationAccessPolicy -PolicyName "PatientExplorer-Policy" -Global
    ```

- [ ] **Step 6: Test OAuth Flow**
  - Run `streamlit run app/main.py`
  - Click Microsoft sign-in button
  - Complete authentication
  - Verify token received

**Reference:** `docs/research/2025-12-04_research_microsoft-auth-graph-api-integration-strategy.md`

---

### Focus Area 2: Microsoft Consent Form Setup (HIGH)

**Priority: HIGH** | **Required for outreach campaign**

#### Checklist

- [ ] **Step 1: Create Form**
  - Go to forms.microsoft.com
  - Sign in as autopilot@southviewteam.com
  - Create new form: "Patient Consent for Record Transfer"

- [ ] **Step 2: Add Form Fields**
  - Full Name (required)
  - Date of Birth (required)
  - Phone Number (required)
  - Email Address (optional)
  - Consent checkbox: Record transfer to Home Team
  - Consent checkbox: APCM billing transfer (if applicable)
  - Digital signature (typed name)
  - Date

- [ ] **Step 3: Configure Response Collection**
  - Responses > Open in Excel (creates SharePoint list)
  - Or: Connect to existing SharePoint list

- [ ] **Step 4: Get Shareable Link**
  - Share > Get a link to share
  - Copy short URL for SMS messages

- [ ] **Step 5: Update Streamlit App**
  - Open Outreach Campaign page
  - Paste form URL in configuration
  - Test link opens correctly

- [ ] **Step 6: Pilot Test**
  - Send to 5 test patients
  - Verify responses collected
  - Check data flows to tracking system

**Reference:** `docs/stories/BETA-001-microsoft-forms-setup.md`

---

### Focus Area 3: Commit Changes & Staff Deployment (HIGH)

**Priority: HIGH** | **Risk mitigation + enable testing**

#### Checklist

- [ ] **Step 1: Review Uncommitted Changes**
  - Run `git status`
  - Review each modified file for sensitive data
  - Ensure no PHI in code or comments

- [ ] **Step 2: Stage and Commit**
  - `git add .` (after review)
  - Create meaningful commit message
  - Push to remote

- [ ] **Step 3: Prepare Jenny's Machine**
  - Ensure Python 3.10+ installed
  - Ensure Git installed
  - Verify BitLocker enabled

- [ ] **Step 4: Clone and Setup**
  - Clone repository
  - Create virtual environment
  - Install dependencies
  - Configure `.env` file

- [ ] **Step 5: Test Application**
  - Run `streamlit run app/main.py`
  - Verify patient list loads
  - Test basic navigation
  - Document any issues

- [ ] **Step 6: Training Session**
  - Walk through patient lookup
  - Show consent tracking workflow
  - Explain status updates

**Reference:** `docs/planning/alpha-deployment-guide.md`

---

## 3. Outstanding User To-Dos

*Items carried forward from previous sessions that still need attention.*

| Item | Source Session | Status |
|------|---------------|--------|
| Register Azure AD Application | 2025-12-04 | Not started |
| Run PowerShell Application Access Policy | 2025-12-04 | Not started |
| Create Microsoft Consent Form | 2025-12-02 | Not started |
| Paste Form URL into Streamlit | 2025-12-02 | Blocked by form creation |
| Deploy to Jenny's machine | 2025-12-02 | Not started |
| Test with 5 pilot patients | 2025-12-02 | Blocked by form creation |
| Fill in scratch notes at session start | 2025-12-01 | Recurring |

---

## 4. Current Session Intentions

### What I Want to Accomplish THIS Session

*Enter your specific goals for this session:*

```
[What do you want to achieve before closing this session?]




```

### Items to Discuss Now, But Reserve for Future Sessions

*Topics you want to mention or brainstorm, but not necessarily act on today:*

```
[What should we talk about but save for later?]




```

---

## 5. Session Follow-Up Log

*Append notes throughout the session about tasks for next time.*

### For User (Before Next Session)

| Task | Priority | Notes |
|------|----------|-------|
| Complete Azure AD registration | CRITICAL | Blocks all MS integrations |
| Run PowerShell Access Policy | CRITICAL | Required for transcripts |
| Create Microsoft Consent Form | HIGH | Required for outreach |
| Commit uncommitted changes | HIGH | 11 files at risk |

### For Agent (Next Session Prep)

| Task | Priority | Notes |
|------|----------|-------|
| Test OAuth flow once registered | HIGH | Verify integration |
| Review consent form responses | MEDIUM | After form created |
| Support deployment troubleshooting | MEDIUM | If Jenny has issues |

### Cloud Agent Delegation Opportunities

| Task | Suggested Agent | Complexity | Notes |
|------|-----------------|------------|-------|
| Code review phase0/ module | Claude Code | Low | HIPAA compliance check |
| Generate SMS templates | Claude | Low | For Spruce outreach |
| Review research reports | Claude | Low | Summarize key findings |

### Deferred to January 2025

| Task | Notes |
|------|-------|
| KP Good Shepherd agent framework | Clinical AI integration |
| OpenEvidence UI patterns | Ambient recording interface |
| IBM Granite model evaluation | Custom lightweight models |
| OpenEMR integration | Long-term EMR strategy |
| Athena API / Data Factory | Team currently setting up |

---

## Session Metadata

- **Generated**: 2025-12-06
- **Reference**: 2025-12-06_WorkspaceOverview.md
- **Days to Deadline**: 25
- **Session Start Time**: _______________
- **Session End Time**: _______________

---

*Tip: Fill in Section 1 (Scratch Notes) and Section 4 (Session Intentions) at the START of your session. Update Section 5 (Follow-Up Log) DURING and at the END of your session.*
