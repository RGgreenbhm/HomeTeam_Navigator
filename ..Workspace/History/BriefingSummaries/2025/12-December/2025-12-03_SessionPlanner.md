# Session Planner: 2025-12-03

**Days to Deadline: 28**

---

## 1. Session Scratch Notes

*Use this space to capture your stream-of-consciousness thoughts at the start of this session. What's on your mind? What prompted you to open this workspace today?*

```
Today, I updated the folder structure and agent configurations for this workspace and for my RG3 workspace to help me better keep track of everything and learn how to assign agents to work as teams and give them different scopes to control how they work together. 

Now, I need to workout a solution for best options to configure synchronization between users who are working in the outreach campaign for the Patient_Explorer_App.  We looked at azure yesterday, but I really think a more limited scope that just saves HIPAA sensitive reference files the app needs on sharepoint drive will be fine, as it's just me and Jenny working on the project right now, and we in communication about how it is going.  I have the Sharepoint Drives mapped to my windows explorer file system, as does Jenny, so it seems we should just be able to have the app save copies of database files to the sharepoint drive, and then let the app running on our local machine save and pull files from that sharepoint location.  Doing this will mean Jenny and I are always working from the same site, and basic Microsoft for work user licenses are all that is required to get us set up and let microsoft handle all the login details, 2FA security, etc.  

I'll task agent-BMAD to evaluate options




```

---

## 2. Proposed Focus Areas

Based on the Workspace Overview and 28-day countdown, here are the prioritized focus areas.

### Focus Area 1: Beta Deployment to Staff (CRITICAL)

**Priority: CRITICAL** | **Target: TODAY (Dec 3)**

Dr. Green and Jenny need working access to test in clinic.

#### Checklist

- [ ] **Step 1: Verify Local Environment**
  - Run `run-app.ps1` to confirm Streamlit launches
  - Test all 4 pages load without errors
  - Verify Spruce connection shows in sidebar

- [ ] **Step 2: Deploy to Jenny's Machine**
  - Copy project folder or use `setup-beta.ps1`
  - Install Python dependencies
  - Configure `.env` with credentials
  - Run `run-app.ps1` and verify launch

- [ ] **Step 3: Test Microsoft OAuth**
  - Sign in with southviewteam.com credentials
  - Complete 2FA if prompted
  - Verify session persists appropriately

- [ ] **Step 4: Document Any Issues**
  - Note errors encountered
  - Create fix list for immediate iteration

---

### Focus Area 2: Microsoft Form for Consent (CRITICAL)

**Priority: CRITICAL** | **Blocks outreach campaign**

#### Checklist

- [ ] **Step 1: Create Form in Microsoft 365**
  - Go to forms.microsoft.com
  - Create new form: "Patient Consent for Record Transfer"
  - Reference `docs/stories/BETA-001-microsoft-forms-setup.md`

- [ ] **Step 2: Add Required Fields**
  - Patient name (text)
  - Date of birth (date)
  - Consent for record transfer (yes/no)
  - Consent for APCM billing transfer (yes/no)
  - Electronic signature (text)
  - Date signed (auto-captured)

- [ ] **Step 3: Configure Form Settings**
  - Allow responses from anyone
  - Collect email addresses (optional)
  - Send confirmation to respondent

- [ ] **Step 4: Integrate with Streamlit**
  - Copy form URL
  - Paste into Outreach Campaign page sidebar
  - Test link opens correctly

---

### Focus Area 3: First Patient Outreach Test (HIGH)

**Priority: HIGH** | **Validates entire workflow**

#### Checklist

- [ ] **Step 1: Select Test Patients**
  - Choose 5 patients from Spruce-matched list
  - Prefer patients with known good contact info
  - Consider friendly/engaged patients first

- [ ] **Step 2: Send Consent Links**
  - Use Spruce SMS to send form URL
  - Include brief message explaining purpose
  - Log send time in SharePoint

- [ ] **Step 3: Monitor Responses**
  - Check Microsoft Forms for submissions
  - Note response times
  - Verify data captured correctly

- [ ] **Step 4: Process Responses**
  - Update SharePoint consent list
  - Mark patients as "consented" or "declined"
  - Document any issues with workflow

---

## 3. Outstanding User To-Dos

*Items carried forward from previous sessions that still need attention.*

| Item | Source Session | Status |
|------|---------------|--------|
| Create Microsoft Form | 2025-12-02 | **Not started** |
| Paste Form URL into Streamlit | 2025-12-02 | Blocked (needs form) |
| Deploy to Jenny's machine | 2025-12-02 | **Not started** |
| Test with 5 patients | 2025-12-02 | Blocked (needs form) |
| Initialize SharePoint consent list | 2025-12-01 | Needs verification |
| End-to-end workflow test | 2025-12-01 | Not started |

---

## 4. Current Session Intentions

### What I Want to Accomplish THIS Session

*Enter your specific goals for this session:*

```
[COMPLETED] Implement SharePoint file sync for Patient_Explorer app
- Created app/sharepoint_sync.py module
- Added SharePoint Sync tab to Admin page
- Added sync status indicator to sidebar on all pages
- Updated .env.example with sync documentation
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
| **Azure AD Setup** | HIGH | See instructions below |
| Register app in Azure AD portal | HIGH | Required for OAuth login |
| Configure redirect URI: `http://localhost:8501` | HIGH | Must match exactly |
| Add delegated API permissions | HIGH | See list in .env.example |
| Copy Client ID and Tenant ID to .env | HIGH | From Azure portal |
| Test "Sign in with Microsoft" in app | HIGH | Should redirect and return |
| Browse SharePoint and select sync folder | HIGH | In Admin > SharePoint Sync |
| Have Jenny do the same OAuth flow | HIGH | Each user signs in themselves |

**Azure AD App Registration Steps:**
1. Go to https://portal.azure.com
2. Navigate to: Azure Active Directory > App registrations
3. Click "New registration"
4. Name: `Patient Explorer`
5. Account types: "Single tenant"
6. Redirect URI: Web - `http://localhost:8501`
7. After creation, copy:
   - Application (client) ID -> `AZURE_CLIENT_ID`
   - Directory (tenant) ID -> `AZURE_TENANT_ID`
8. Go to "API permissions" > Add:
   - Microsoft Graph > Delegated > User.Read
   - Microsoft Graph > Delegated > Files.ReadWrite.All
   - Microsoft Graph > Delegated > Sites.Read.All
   - Microsoft Graph > Delegated > Notes.Read.All (optional, for future)
9. Click "Grant admin consent" if you're admin

### For Agent (Next Session Prep)

| Task | Priority | Notes |
|------|----------|-------|
| Verify sync feature works on both machines | HIGH | May need path adjustments |
| Add audit logging for sync operations | MEDIUM | For HIPAA compliance |
| Consider adding "last edited by" indicator | LOW | Future enhancement |

### Cloud Agent Delegation Opportunities

*Tasks that could be delegated to run autonomously post-session:*

| Task | Suggested Agent | Complexity | Notes |
|------|-----------------|------------|-------|
| Write user documentation for sync | BMAD-Docs | Low | Step-by-step guide |
| Create ADR for sync architecture | BMAD-Architect | Medium | Document decision |

---

## Previous Session Summary (2025-12-02)

**What was accomplished:**
- BMAD Agent Team completed all 6 phases overnight
- Research reports generated (OAuth, Spruce, OpenEvidence, KP)
- Architecture Decision Record (ADR-001) finalized
- 8 user stories created (S5-S8, BETA-001-003)
- Alpha deployment guide drafted
- Single Invite feature added to Streamlit app
- Workspace briefing system launched

**Key decisions made:**
1. Use MS OAuth as authentication gate
2. Use Microsoft Forms for consent collection (hybrid approach)
3. Batch script launcher for alpha deployment
4. SQLite only for alpha (add sync later)
5. Azure Claude for AI (HIPAA-compliant)

**Deferred to January 2025:**
- KP folder / Good Shepherd agent review
- OpenEvidence UI patterns implementation
- Microsoft user OAuth for OneNote
- IBM Granite model evaluation
- OpenEMR integration research

---

## Session Metadata

- **Generated**: 2025-12-03
- **Reference**: 2025-12-03_WorkspaceOverview.md
- **Days to Deadline**: 28
- **Session Start Time**: _______________
- **Session End Time**: _______________

---

*Tip: Fill in Section 1 (Scratch Notes) and Section 4 (Session Intentions) at the START of your session. Update Section 5 (Follow-Up Log) DURING and at the END of your session.*
