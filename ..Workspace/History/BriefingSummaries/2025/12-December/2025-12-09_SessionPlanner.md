# Session Planner: 2025-12-09

**Days to Deadline: 22**

---

## 1. Session Scratch Notes

*Use this space to capture your stream-of-consciousness thoughts at the start of this session. What's on your mind? What prompted you to open this workspace today?*

```
Plan a new module for this project "Module_AutoScribe" that will enable users to capture text and or audio for use in creating medical notes.  We will need a library for the system to store prompt messages the user can select as buttons for "SBAR", "office note", and "video note" that will link to a stored set of prompts for one of our AI agents (preferably Claude Sonnet API) to process according to the prompt instructions.  This means we will also need a link to the prompt library that lets users create new prompts (available as a dropdown list under a "custom" button to let user choose a different prompt).  Ask me after this step for the prompts to go along with these standard SBAR and Office Note and Video Note buttons.   For user interface, make include a rich text free text box at the top where user may provide additional context (including ability to paste a screenshot for the agent to interpret), then a section for "Record Audio" that can record and store audio information in our Azure storage location.  Include controls to allow user to toggle on and off the system audio, and controls to select which microphone and speaker to use for recording and replaying the audio (starting with the system default, but searching system for all available to include in the dropdown).  Save the audio recordings and list them below the recording (allow a pause button than in effect stops the recording and then starts a new one), so if the user starts and stops, the subsequent recordings should append to the prior ones for a single composite audio file with a total maximum record time of 60 minutes total per encounter.    




```

---

## 2. Proposed Focus Areas

Based on the completed Patient Consolidation (86.9% match rate) and ready-to-deploy Consent Form, here are today's priorities.

### Focus Area 1: Deploy Consent Form to Azure (CRITICAL)

**Priority: CRITICAL** | **Estimated Time: ~35 minutes**

The consent form is built and tested locally. Deployment enables patient outreach immediately.

#### Checklist

- [ ] **Step 1: Create Azure Static Web App** (~10 min)
  - Go to Azure Portal > Create Resource > Static Web App
  - Name: `greenclinic-consent`
  - Region: East US 2
  - Source: Local deployment or GitHub
  - Deploy from `Project_Patient_Explorer_App/consent-form/`

- [ ] **Step 2: Create Azure Function App** (~15 min)
  - Create Resource > Function App
  - Name: `greenclinic-consent-api`
  - Runtime: Python 3.10
  - Plan: Consumption (serverless)
  - Deploy from `Project_Patient_Explorer_App/azure-function/`
  - Add environment variable: `SPRUCE_API_TOKEN=<your token>`

- [ ] **Step 3: Update Form JavaScript** (~2 min)
  - Edit `consent-form/script.js`
  - Set `API_ENDPOINT` to your Function URL
  - Redeploy static site

- [ ] **Step 4: Test End-to-End** (~10 min)
  - Open consent form URL in browser
  - Submit test consent
  - Verify patient tagged in Spruce with `consent_obtained`
  - Check Function logs for any errors

**Reference:** `Project_Patient_Explorer_App/architecture/Consent_Form_Spruce_Integration.md`

---

### Focus Area 2: Configure Spruce Auto-Responder (HIGH)

**Priority: HIGH** | **Estimated Time: ~15 minutes**

Set up automatic privacy replies for patients who reply "STOP" or similar opt-out keywords.

#### Checklist

- [ ] **Step 1: Open Spruce Settings**
  - Log into Spruce app or web
  - Navigate to Settings > Auto-responses

- [ ] **Step 2: Create Privacy Auto-Reply**
  - Trigger: Messages containing "STOP", "UNSUBSCRIBE", "OPT OUT"
  - Response: See template in `docs/guides/spruce-auto-responder-setup.md`

- [ ] **Step 3: Test Auto-Response**
  - Send test message with "STOP"
  - Verify auto-reply is sent
  - Verify patient is flagged for manual review

**Reference:** `docs/guides/spruce-auto-responder-setup.md`

---

### Focus Area 3: Apply Spruce Tags to Patients (HIGH)

**Priority: HIGH** | **After Deployment**

Apply standardized tags in Spruce for patient categorization and workflow management.

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
- `apcm` - APCM enrolled (486 patients from APCM Excel)
- `consent_pending` - Awaiting consent response
- `consent_obtained` - Consent received (auto-applied by form)
- `high_priority` - Needs immediate attention

**Reference:** `Project_Patient_Explorer_App/PATIENT_EXPLORER_V1_INSTRUCTIONS.md`

---

## 3. Outstanding User To-Dos

*Items carried forward from previous sessions that still need attention.*

| Item | Source Session | Status |
|------|---------------|--------|
| **Deploy Consent Form to Azure** | 2025-12-08 | **Ready** (steps above) |
| Configure Spruce Auto-Responder | 2025-12-08 | **Ready** (guide available) |
| Apply Spruce tags to patients | 2025-12-08 | **Ready** (tag list defined) |
| Share security PDF with Pat & Brian | 2025-12-06 | **Ready** (PDF in Export_Ready/) |
| Deploy to Jenny's machine | 2025-12-02 | **Ready** (Azure sync works) |
| Create Microsoft Consent Form | 2025-12-02 | **Superseded** (Azure form ready) |

### Completed Items (Remove from List)

| Item | Completion Date | Notes |
|------|-----------------|-------|
| Patient data consolidation | 2025-12-08 | 86.9% match rate achieved |
| Patient Explorer UI page | 2025-12-08 | 682 lines, 11 sections |
| Consent form architecture | 2025-12-08 | Option B selected, built |
| Navigation icons imported | 2025-12-08 | 39 icons ready |
| Azure Blob Storage sync | 2025-12-06 | PHI sync working |

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
| Deploy consent form to Azure | CRITICAL | ~35 min total, steps in Focus Area 1 |
| Configure Spruce auto-responder | HIGH | ~15 min, guide in docs/guides/ |
| Apply Spruce tags to patients | HIGH | Start with team assignment |
| Share security PDF with Pat & Brian | MEDIUM | Ready at Export_Ready/ |
| Deploy to Jenny's machine | MEDIUM | Clone + sync-pull |

### For Agent (Next Session Prep)

| Task | Priority | Notes |
|------|----------|-------|
| Test consent form after deployment | HIGH | Verify Spruce tagging works |
| Review unmatched patients (181) | MEDIUM | May need manual matching |
| Support deployment troubleshooting | MEDIUM | If Azure issues arise |
| Help with bulk SMS campaign | LOW | After form deployed |

### Cloud Agent Delegation Opportunities

| Task | Suggested Agent | Complexity | Notes |
|------|-----------------|------------|-------|
| Generate personalized SMS variants | Claude | Low | Using patient names from JSON |
| Validate JSON schema completeness | Claude | Low | Check patients_master.json |
| Create training doc for Jenny | Claude | Low | Patient Explorer UI walkthrough |
| Code review consent form | Claude Code | Low | Security check before deploy |

### Deferred to January 2025

| Task | Notes |
|------|-------|
| Azure AD App Registration | Not needed for V1.0 (using form-based consent) |
| OneNote notebook browser | Requires OAuth + Graph API |
| Teams transcript access | Using Plaud instead |
| KP Good Shepherd agent framework | Clinical AI integration |
| OpenEvidence UI patterns | Ambient recording interface |
| IBM Granite model evaluation | Custom lightweight models |
| OpenEMR integration | Long-term EMR strategy |
| Azure Key Vault migration | Production credential management |

---

## What's New Since Last Session (Dec 8)

### Completed

1. **Patient Consolidator Service** - 86.9% match rate achieved
2. **Patient Explorer UI** - Full 11-section chart view
3. **Consent Form System** - HTML/CSS/JS + Azure Function
4. **SMS Templates** - Multiple outreach variants
5. **Spruce Integration Guides** - Comprehensive documentation

### Ready for Deployment

| Component | Location | Status |
|-----------|----------|--------|
| Consent Form | `Project_Patient_Explorer_App/consent-form/` | Ready |
| Azure Function | `Project_Patient_Explorer_App/azure-function/` | Ready |
| patients_master.json | Azure Blob Storage | Uploaded |
| Security Overview PDF | `Export_Ready/` | Ready |

### Key V1.0 Decisions Confirmed

- **Form-to-Spruce** architecture selected (Option B)
- No Azure AD registration required for V1.0
- Spruce API handles patient tagging directly
- All PHI stays in HIPAA-compliant services

---

## Quick Reference

### Common Commands

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run Streamlit app
streamlit run app/main.py

# Run patient consolidation
python -m phase0 consolidate-patients

# Sync to Azure (after changes)
python -m phase0 sync-push --interactive

# Pull from Azure (on new device)
python -m phase0 sync-pull --interactive
```

### Key Files

| File | Purpose |
|------|---------|
| `data/patients_master.json` | Consolidated patient records |
| `app/pages/20_Patient_Explorer.py` | Patient chart UI |
| `Project_Patient_Explorer_App/consent-form/` | Consent form to deploy |
| `docs/guides/spruce-auto-responder-setup.md` | Auto-reply configuration |

---

## Session Metadata

- **Generated**: 2025-12-09
- **Reference**: 2025-12-09_WorkspaceOverview.md
- **Days to Deadline**: 22
- **Session Start Time**: _______________
- **Session End Time**: _______________

---

*Tip: Fill in Section 1 (Scratch Notes) and Section 4 (Session Intentions) at the START of your session. Update Section 5 (Follow-Up Log) DURING and at the END of your session.*
