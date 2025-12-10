# Session Planner: 2025-12-04

**Days to Deadline: 27**

---

## 1. Session Scratch Notes

*Use this space to capture your stream-of-consciousness thoughts at the start of this session. What's on your mind? What prompted you to open this workspace today?*

```
[Enter your thoughts here before we begin...]




```

---

## 2. Proposed Focus Areas

Based on the Workspace Overview and 27-day countdown, here are the prioritized focus areas.

### Focus Area 1: Azure AD App Registration (CRITICAL)

**Priority: CRITICAL** | **Blocks: OAuth, SharePoint sync, Graph API access**

This is the single most impactful task—it unblocks multiple features.

#### Checklist

- [ ] **Step 1: Navigate to Azure Portal**
  - Go to https://portal.azure.com
  - Sign in with southviewteam.com admin account
  - Navigate to: Microsoft Entra ID → App registrations

- [ ] **Step 2: Create New Registration**
  - Click "New registration"
  - Name: `Patient Explorer`
  - Account types: "Single tenant" (southviewteam.com only)
  - Redirect URI: Web - `http://localhost:8501`
  - Click "Register"

- [ ] **Step 3: Copy Identifiers**
  - Copy **Application (client) ID** → `AZURE_CLIENT_ID` in `.env`
  - Copy **Directory (tenant) ID** → `AZURE_TENANT_ID` in `.env`

- [ ] **Step 4: Add API Permissions**
  - Go to "API permissions" → "Add a permission" → "Microsoft Graph"
  - Add Delegated permissions:
    - `User.Read`
    - `Files.ReadWrite.All`
    - `Sites.Read.All`
    - `Calendars.ReadWrite` (for Bookings)
    - `OnlineMeetings.ReadWrite` (for transcripts)
    - `OnlineMeetingTranscript.Read.All` (for transcripts)
  - Click "Grant admin consent for southviewteam.com"

- [ ] **Step 5: Create Client Secret (Optional)**
  - Go to "Certificates & secrets"
  - Click "New client secret"
  - Copy value immediately → `AZURE_CLIENT_SECRET` in `.env`

- [ ] **Step 6: Test OAuth Sign-in**
  - Run `streamlit run app/main.py`
  - Click "Sign in with Microsoft"
  - Complete authentication
  - Verify redirect back to app

---

### Focus Area 2: Application Access Policy for Teams (HIGH)

**Priority: HIGH** | **Blocks: Meeting transcript retrieval**

Required for Graph API access to Teams transcripts.

#### Checklist

- [ ] **Step 1: Install Teams PowerShell Module**
  ```powershell
  Install-Module -Name MicrosoftTeams -Force -AllowClobber
  ```

- [ ] **Step 2: Connect to Teams**
  ```powershell
  Connect-MicrosoftTeams
  # Sign in with admin account when prompted
  ```

- [ ] **Step 3: Create Application Access Policy**
  ```powershell
  New-CsApplicationAccessPolicy `
      -Identity "Patient-Explorer-Policy" `
      -AppIds "<your-client-id-from-step-3-above>" `
      -Description "Allow Patient Explorer to access Teams meetings"
  ```

- [ ] **Step 4: Grant Policy Tenant-Wide**
  ```powershell
  Grant-CsApplicationAccessPolicy `
      -PolicyName "Patient-Explorer-Policy" `
      -Global
  ```

- [ ] **Step 5: Verify Policy (wait 30 minutes)**
  ```powershell
  Get-CsApplicationAccessPolicy
  ```

---

### Focus Area 3: Create Microsoft Consent Form (HIGH)

**Priority: HIGH** | **Blocks: Patient outreach campaign**

#### Checklist

- [ ] **Step 1: Create Form**
  - Go to https://forms.microsoft.com
  - Sign in with southviewteam.com account
  - Click "New Form"
  - Title: "Patient Consent for Record Transfer"

- [ ] **Step 2: Add Required Fields**
  - Patient Full Name (text, required)
  - Date of Birth (date, required)
  - "I consent to transfer my medical records to Home Team Medical" (choice: Yes/No)
  - "I consent to transfer my APCM billing authorization" (choice: Yes/No)
  - Electronic Signature (text, required)
  - Date Signed (auto-captured)

- [ ] **Step 3: Configure Settings**
  - Allow responses from anyone (patients don't have M365 accounts)
  - Send confirmation email to respondent
  - Set custom thank you message

- [ ] **Step 4: Copy Form URL**
  - Click "Collect responses"
  - Copy the shareable link

- [ ] **Step 5: Add URL to Streamlit App**
  - Open `app/pages/3_Outreach_Campaign.py`
  - Paste URL in sidebar configuration
  - Test link opens correctly

---

## 3. Outstanding User To-Dos

*Items carried forward from previous sessions that still need attention.*

| Item | Source Session | Status |
|------|---------------|--------|
| Register Azure AD app | 2025-12-03 | **Not started** |
| Configure redirect URI | 2025-12-03 | Blocked (needs app registration) |
| Add API permissions | 2025-12-03 | Blocked (needs app registration) |
| Copy Client ID to .env | 2025-12-03 | Blocked (needs app registration) |
| Create Microsoft Form | 2025-12-02 | **Not started** |
| Paste Form URL into Streamlit | 2025-12-02 | Blocked (needs form) |
| Deploy to Jenny's machine | 2025-12-02 | **Not started** |
| Test with 5 patients | 2025-12-02 | Blocked (needs form) |
| Run Application Access Policy PowerShell | 2025-12-03 | **Not started** |

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
| Complete Azure AD registration | CRITICAL | Steps documented in Focus Area 1 |
| Run PowerShell policy commands | HIGH | Steps documented in Focus Area 2 |
| Create Microsoft Form | HIGH | Steps documented in Focus Area 3 |
| Test OAuth flow in app | HIGH | After Azure AD setup |
| Deploy to Jenny | MEDIUM | After OAuth works |

### For Agent (Next Session Prep)

| Task | Priority | Notes |
|------|----------|-------|
| Verify OAuth integration works | HIGH | Test after user completes setup |
| Help troubleshoot any 400/401 errors | HIGH | Common issues documented in research |
| Support transcript retrieval testing | MEDIUM | After policy propagates |
| Generate PDFs for research reports | LOW | Two reports pending export |

### Cloud Agent Delegation Opportunities

*Tasks that could be delegated to run autonomously post-session:*

| Task | Suggested Agent | Complexity | Notes |
|------|-----------------|------------|-------|
| Review consent form for HIPAA compliance | Claude | Low | Legal language check |
| Generate SMS outreach templates | Claude | Low | Multiple message variants |
| Create deployment documentation | BMAD-Docs | Medium | Step-by-step for Jenny |

---

## Previous Session Summary (2025-12-03)

**What was accomplished:**
- SharePoint sync feature implemented (`app/sharepoint_sync.py`)
- Sync status indicator added to all pages
- Admin page updated with SharePoint Sync tab
- Azure AD setup instructions documented

**What was deferred:**
- Actual Azure AD registration (user task)
- Microsoft Form creation (user task)
- Jenny deployment (blocked by auth)

---

## Today's Research Completed

**Microsoft Auth & Graph API Integration:**
- Comprehensive 900+ line research report
- MCP server integration guides (APIM and Local)
- Permission matrix for all workflows
- Troubleshooting section

**Teams Bookings & Virtual Visits:**
- Separate 400+ line research report
- Bookings setup with autopilot as admin
- Virtual Appointments (Premium) features
- HIPAA compliance checklist

**Location:** `docs/research/2025-12-04_*.md`

---

## Session Metadata

- **Generated**: 2025-12-04
- **Reference**: 2025-12-04_WorkspaceOverview.md
- **Days to Deadline**: 27
- **Session Start Time**: _______________
- **Session End Time**: _______________

---

*Tip: Fill in Section 1 (Scratch Notes) and Section 4 (Session Intentions) at the START of your session. Update Section 5 (Follow-Up Log) DURING and at the END of your session.*
