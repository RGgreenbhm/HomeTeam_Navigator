# Session Planner: 2025-12-10

**Days to Deadline: 21**

---

## 1. Session Scratch Notes

*Use this space to capture your stream-of-consciousness thoughts at the start of this session. What's on your mind? What prompted you to open this workspace today?*

```
[Enter your thoughts here before we begin...]




```

---

## 2. Proposed Focus Areas

Based on the V1.0 readiness state and 21-day countdown, here are today's priorities.

### Focus Area 1: Deploy Consent Form to Azure (CRITICAL)

**Priority: CRITICAL** | **Estimated Time: ~35 minutes** | **Impact: Enables outreach**

The consent form is the critical path item. Everything is built and tested locally.

#### Checklist

- [ ] **Step 1: Create Azure Static Web App** (~10 min)
  - Azure Portal > Create Resource > Static Web App
  - Name: `greenclinic-consent`
  - Region: East US 2
  - Deployment: GitHub or local CLI
  - Source folder: `Project_Patient_Explorer_App/consent-form/`

- [ ] **Step 2: Create Azure Function App** (~15 min)
  - Azure Portal > Create Resource > Function App
  - Name: `greenclinic-consent-api`
  - Runtime: Python 3.10
  - Plan: Consumption (serverless)
  - Deploy from: `Project_Patient_Explorer_App/azure-function/`
  - Add App Setting: `SPRUCE_API_TOKEN=<your token>`

- [ ] **Step 3: Update Form API Endpoint** (~2 min)
  - Edit `consent-form/script.js`
  - Set `API_ENDPOINT` to your Function URL
  - Redeploy static site

- [ ] **Step 4: Test End-to-End** (~10 min)
  - Open consent form URL
  - Submit test consent
  - Verify Spruce patient gets `consent_obtained` tag
  - Check Function logs

**Reference:** [Consent Form Architecture](Project_Patient_Explorer_App/architecture/Consent_Form_Spruce_Integration.md)

---

### Focus Area 2: Test AutoScribe Module (HIGH)

**Priority: HIGH** | **Estimated Time: ~20 minutes** | **Impact: Validate new feature**

AutoScribe was added Dec 9. Needs testing on Desktop device.

#### Checklist

- [ ] **Step 1: Launch App**
  ```bash
  cd d:\Projects\Patient_Explorer
  .venv\Scripts\activate
  streamlit run app/main.py
  ```

- [ ] **Step 2: Navigate to AutoScribe**
  - Click "AutoScribe" in sidebar
  - Verify page loads without errors

- [ ] **Step 3: Test Audio Device Selection**
  - Check microphone dropdown populates
  - Check speaker dropdown populates
  - Select non-default devices (if available)

- [ ] **Step 4: Test Recording**
  - Click Record button
  - Speak test phrase
  - Click Stop
  - Verify audio file created

- [ ] **Step 5: Test Transcription** (requires Azure Speech key)
  - If configured, transcribe test audio
  - If not configured, note as future setup

- [ ] **Step 6: Test Prompt Selection**
  - Select SBAR template
  - Select Office Note template
  - Select Video Note template
  - Verify prompts load

**Reference:** [AutoScribe module](app/autoscribe/)

---

### Focus Area 3: Configure Spruce Auto-Responder (HIGH)

**Priority: HIGH** | **Estimated Time: ~15 minutes** | **Impact: Compliance**

Auto-reply for opt-out messages protects patient privacy.

#### Checklist

- [ ] **Step 1: Open Spruce Settings**
  - Log into Spruce web or app
  - Settings > Auto-responses

- [ ] **Step 2: Create Opt-Out Auto-Reply**
  - Trigger keywords: STOP, UNSUBSCRIBE, OPT OUT, CANCEL
  - Response message:
    ```
    We've received your request. You will not receive further
    messages from us. If you have questions, please call our
    office at [phone number].
    ```

- [ ] **Step 3: Create Confirmation Auto-Reply** (optional)
  - Trigger: Messages containing "YES", "CONSENT", "AGREE"
  - Response: Confirmation + next steps

- [ ] **Step 4: Test Auto-Response**
  - Send test message with "STOP"
  - Verify auto-reply sent
  - Verify patient flagged

**Reference:** [Spruce Auto-Responder Guide](docs/guides/spruce-auto-responder-setup.md)

---

## 3. Outstanding User To-Dos

*Items carried forward from previous sessions.*

| Item | Source Session | Status | Days Pending |
|------|---------------|--------|--------------|
| **Deploy Consent Form to Azure** | 2025-12-08 | Ready | 2 |
| Configure Spruce Auto-Responder | 2025-12-08 | Ready | 2 |
| Apply Spruce tags to patients | 2025-12-08 | Ready | 2 |
| Fix Azure Storage permissions | 2025-12-08 | Open | 2 |
| Share security PDF with Pat & Brian | 2025-12-06 | Ready | 4 |
| Deploy to Jenny's machine | 2025-12-02 | Ready | 8 |

### Recently Completed

| Item | Completion Date |
|------|-----------------|
| Desktop device setup | 2025-12-10 |
| AutoScribe module | 2025-12-09 |
| Patient consolidation (86.9%) | 2025-12-08 |
| Patient Explorer UI | 2025-12-08 |
| Consent form architecture | 2025-12-08 |
| Azure Blob Storage sync | 2025-12-06 |

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
| Deploy consent form to Azure | CRITICAL | 35 min, detailed steps above |
| Test AutoScribe audio recording | HIGH | Verify devices work |
| Configure Spruce auto-responder | HIGH | 15 min setup |
| Apply Spruce tags to patients | MEDIUM | Start with team assignment |
| Fix Azure Storage permissions | MEDIUM | Add Storage Blob Data Contributor |

### For Agent (Next Session Prep)

| Task | Priority | Notes |
|------|----------|-------|
| Verify consent form deployment | HIGH | Test Spruce tagging |
| Support AutoScribe troubleshooting | HIGH | If audio issues |
| Help with bulk SMS campaign | MEDIUM | After form deployed |
| Generate training doc for Jenny | LOW | Patient Explorer walkthrough |

### Cloud Agent Delegation Opportunities

| Task | Suggested Agent | Complexity | Notes |
|------|-----------------|------------|-------|
| Generate personalized SMS variants | Claude | Low | Use patient names from JSON |
| Create Jenny training guide | Claude | Low | Patient Explorer UI walkthrough |
| Review 181 unmatched patients | Claude | Medium | Manual matching suggestions |
| Code review AutoScribe module | Claude Code | Low | Security + HIPAA check |

### Deferred to January 2025

| Task | Notes |
|------|-------|
| Azure AD App Registration | Not needed for V1.0 |
| OneNote notebook browser | Requires OAuth |
| Teams transcript access | Using Plaud instead |
| KP Good Shepherd framework | Clinical AI integration |
| OpenEvidence UI patterns | Ambient recording |
| IBM Granite model evaluation | Custom models |
| Azure Key Vault migration | Production credentials |

---

## Session Progress Log

*Track what you accomplish during this session:*

| Time | Action | Result |
|------|--------|--------|
| | Desktop device setup | ✅ Completed |
| | Workspace sync | ✅ 120 files pulled |
| | Dec 10 briefings generated | ✅ 3 documents |

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `Project_Patient_Explorer_App/consent-form/` | Consent form to deploy |
| `Project_Patient_Explorer_App/azure-function/` | API backend to deploy |
| `app/pages/25_AutoScribe.py` | AutoScribe UI page |
| `docs/guides/spruce-auto-responder-setup.md` | Auto-reply guide |
| `data/patients_master.json` | Consolidated patient records |

### Common Commands

```bash
# Activate environment
.venv\Scripts\activate

# Run Streamlit app
streamlit run app/main.py

# Test Spruce connection
python -m phase0 test-spruce

# Sync to Azure
python -m phase0 sync-push --interactive
```

---

## Session Metadata

- **Generated**: 2025-12-10
- **Reference**: 2025-12-10_WorkspaceOverview.md
- **Days to Deadline**: 21
- **Device**: Desktop
- **Session Start Time**: _______________
- **Session End Time**: _______________

---

*Tip: Fill in Section 1 (Scratch Notes) and Section 4 (Session Intentions) at the START of your session. Update Section 5 (Follow-Up Log) DURING and at the END of your session.*
