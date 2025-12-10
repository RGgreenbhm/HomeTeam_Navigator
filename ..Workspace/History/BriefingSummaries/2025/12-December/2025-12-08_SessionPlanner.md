# Session Planner: 2025-12-08

**Days to Deadline: 23**

---

## 1. Session Scratch Notes

*Use this space to capture your stream-of-consciousness thoughts at the start of this session. What's on your mind? What prompted you to open this workspace today?*

```
I want to finish mapping out the JSON architecture and update a version 1.0 of the patient explorer app so we can start using it for patient outreach right now.  This will mean incorporating all of the settings about patient tags in spruce and other workflows we have considered, and beginning to ingest data from microsoft one-note notebook.  So we'll need to finish integrating the OneNote connection within the patient explorer app (should be able to do that now that we can log in with our microsoft user credentials).  I'd like to be able to send SMS text messages through spruce, but that is not strictly necessary if we can just get a full list of our patients reconciled across the spruce API database, and the files in our "data" folder.  The goal moving forward will be to no longer reference the "data" folder files, but to store a consolidated record of all patients that are already matched within our Azure storeage location, and then update the Patient explorer app to reference that location for all synchronization of patient data moving forward. 




```

---

## 2. Proposed Focus Areas (V1.0 PIVOT)

**IMPORTANT**: Based on V1 Instructions, we are **deferring Microsoft OAuth complexity** and focusing on a **working solution NOW**.

### Focus Area 1: Patient Data Consolidation (CRITICAL)

**Priority: CRITICAL** | **This Session**

Create consolidated patient JSON from Excel + Spruce API, store in Azure.

#### Checklist

- [x] **Step 1: Create Patient Consolidator Service** ✅
  - Created `app/services/patient_consolidator.py`
  - Implemented Excel loading (main patient list + APCM)
  - Implemented Spruce API contact fetching
  - Implemented patient matching (phone → name+DOB → email)

- [x] **Step 2: Test with Actual Data Files** ✅
  - Loaded 1,383 patients from `data/dr green patient list 3 years with phone numbers.xls`
  - Loaded 486 APCM records from `data/2025-11-30_Green_APCM.xlsx`
  - Column mapping verified and working

- [x] **Step 3: Run Spruce Matching** ✅
  - Fetched 1,433 Spruce contacts via API
  - Matched 1,147 by phone (highest confidence)
  - Matched 50 by name+DOB (secondary)
  - Matched 5 by email (tertiary)
  - 181 unmatched (13.1%) flagged for manual review
  - **86.9% overall match rate**

- [x] **Step 4: Generate patients_master.json** ✅
  - Applied JSON schema (1.72 MB file generated)
  - Includes all fields: demographics, identifiers, apcm, consent, tags

- [x] **Step 5: Upload to Azure Blob** ✅
  - Uploaded `patients_master.json` to Azure Blob Storage
  - Verified sync works via `sync-push` command

**Reference:** `Project_Patient_Explorer_App/PATIENT_EXPLORER_V1_INSTRUCTIONS.md`

---

### Focus Area 2: Patient Explorer UI (HIGH)

**Priority: HIGH** | **After Data Ready**

Create interactive chart view with navigation icons (athenaOne-inspired).

#### Checklist

- [x] **Step 1: Copy Navigation Icons** ✅
  - Created `app/assets/icons/` folder
  - Copied 39 `HTnav_*.png` icons from workspace reference
  - Icons ready for use

- [x] **Step 2: Create Patient Explorer Page** ✅
  - Created `app/pages/20_Patient_Explorer.py` (580+ lines)
  - Loads patients from `patients_master.json`
  - Patient search by name, MRN, phone implemented

- [x] **Step 3: Build Navigation Component** ✅
  - Left sidebar with icon buttons for 11 sections
  - Section switching via session state
  - Back to search button

- [x] **Step 4: Implement Patient Header** ✅
  - Shows: Name, DOB, MRN, Phone, Age
  - Gradient header with custom CSS
  - Tag pills with colors for team/loc/status

- [x] **Step 5: Create Section Views** ✅
  - Overview, Medications, Problems, Allergies, Vitals
  - Documents, Communications, Care Plan, Billing
  - Encounters section with visit history

**Reference:** Navigation icons from V1 Instructions

---

### Focus Area 3: Spruce Tag Standardization (HIGH)

**Priority: HIGH** | **Apply in Spruce App**

Apply standardized tags in Spruce for patient categorization.

#### Tag Categories to Apply

**Team Assignment:**
- `team_green` - Dr. Green's patients
- `team_lachandra` - NP LaChandra's patients
- `team_lindsay` - NP Lindsay's patients
- `team_jenny` - RN Jenny's assigned patients

**Level of Care:**
- `loc_il` - Independent Living
- `loc_al` - Assisted Living
- `loc_mc` - Memory Care
- `loc_office` - Clinic visits only
- `loc_home` - Home visits

**Status Flags:**
- `apcm` - APCM enrolled
- `consent_pending` - Awaiting consent response
- `consent_obtained` - Consent received
- `high_priority` - Needs immediate attention

**Reference:** V1 Instructions - Spruce Tag Standardization section

---

## 3. Outstanding User To-Dos

*Items carried forward from previous sessions that still need attention.*

| Item | Source Session | Status |
|------|---------------|--------|
| Apply Spruce tags to patients | 2025-12-08 | **New** (V1.0 requirement) |
| Review Excel column headers | 2025-12-08 | **New** (for patient consolidator) |
| Create Microsoft Consent Form | 2025-12-02 | **Not started** (6 days) |
| Deploy to Jenny's machine | 2025-12-02 | **Ready** (Azure sync done) |
| Share security doc with Pat & Brian | 2025-12-08 | **Ready** (PDF created) |
| ~~Register Azure AD Application~~ | 2025-12-03 | **Deferred** (V1.1) |
| ~~Run PowerShell Application Access Policy~~ | 2025-12-04 | **Deferred** (V1.1) |

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
| **Deploy Consent Form to Azure** | HIGH | See deployment steps below |
| Configure Spruce Auto-Responder | HIGH | Follow `docs/guides/spruce-auto-responder-setup.md` |
| Apply Spruce tags to patients | HIGH | team_*, loc_*, status flags |
| Share security PDF with Pat & Brian | MEDIUM | Ready at Export_Ready/ |
| Deploy to Jenny's machine | MEDIUM | Azure sync ready, just needs setup |

#### Consent Form Azure Deployment Steps

1. **Create Azure Static Web App** (~10 min)
   - Go to Azure Portal → Create Resource → Static Web App
   - Name: `greenclinic-consent`
   - Region: East US 2
   - Source: Deploy from `Project_Patient_Explorer_App/consent-form/`

2. **Create Azure Function App** (~15 min)
   - Create Resource → Function App
   - Name: `greenclinic-consent-api`
   - Runtime: Python 3.10
   - Plan: Consumption (serverless)
   - Deploy from `Project_Patient_Explorer_App/azure-function/`
   - Add env var: `SPRUCE_API_TOKEN=<your token>`

3. **Update Form JavaScript** (~2 min)
   - Edit `consent-form/script.js`
   - Set `API_ENDPOINT` to your Function URL

4. **Test End-to-End** (~10 min)
   - Send test SMS → Click link → Fill form → Verify in Spruce

### For Agent (Next Session Prep)

| Task | Priority | Notes |
|------|----------|-------|
| Build patient_consolidator.py | CRITICAL | Excel + Spruce → JSON |
| Create Patient Explorer UI page | HIGH | Navigation icons provided |
| Test Azure patient-data container | HIGH | New container for master JSON |
| Implement screenshot capture | MEDIUM | Upload + categorize |

### Cloud Agent Delegation Opportunities

| Task | Suggested Agent | Complexity | Notes |
|------|-----------------|------------|-------|
| Generate SMS outreach templates | Claude | Low | Multiple message variants |
| Validate JSON schema completeness | Claude | Low | Check patient_master_record_schema.json |
| Create deployment documentation | Claude | Low | Step-by-step for Jenny |
| Code review phase0/ module | Claude Code | Low | HIPAA compliance check |

### Deferred to January 2025

| Task | Notes |
|------|-------|
| Azure AD App Registration | Not needed for V1.0 |
| OneNote notebook browser | Requires OAuth + Graph API |
| Teams transcript access | Using Plaud instead |
| KP Good Shepherd agent framework | Clinical AI integration |
| OpenEvidence UI patterns | Ambient recording interface |
| IBM Granite model evaluation | Custom lightweight models |
| OpenEMR integration | Long-term EMR strategy |
| Azure Key Vault migration | Production credential management |

---

## What's Different Since Last Session (Dec 6)

### Completed

1. **Azure Blob Storage Sync** - Full implementation with CLI commands
2. **Security Overview Document** - PDF ready for Pat & Brian
3. **Workspace Sync Command** - `/workspace-sync` for Git+Azure sync
4. **New Device Setup Guide** - Instructions for Jenny
5. **V1.0 Pivot Decision** - Defer Microsoft OAuth, focus on data consolidation

### V1.0 Specification Documents Added

1. **PATIENT_EXPLORER_V1_INSTRUCTIONS.md** → `Project_Patient_Explorer_App/`
2. **Plaud_Webhook_Integration_Spec.md** → `Project_Patient_Explorer_App/architecture/`
3. **patient_master_record_schema.json** → `Project_Patient_Explorer_App/schemas/`
4. **V1-Implementation-Roadmap.md** → `Project_Patient_Explorer_App/briefs/`

### Key V1.0 Decisions

- **Defer**: Azure AD registration, OneNote, Teams transcripts
- **Keep**: Microsoft Forms (already working)
- **Add**: Plaud for HIPAA-compliant transcription
- **Focus**: Excel + Spruce → Azure JSON consolidation

---

## Session Metadata

- **Generated**: 2025-12-08
- **Reference**: 2025-12-08_WorkspaceOverview.md
- **Days to Deadline**: 23
- **Session Start Time**: _______________
- **Session End Time**: _______________

---

*Tip: Fill in Section 1 (Scratch Notes) and Section 4 (Session Intentions) at the START of your session. Update Section 5 (Follow-Up Log) DURING and at the END of your session.*
