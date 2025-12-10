# User Input Checklist - Patient Explorer

**Generated:** December 1, 2025 (Autonomous Session)
**Status:** Awaiting User Review

---

## Overview

During the autonomous development session, I completed the following work:
1. Created **Consent Response Processing** page (`pages/11_Consent_Response.py`)
2. Created **Follow-Up Queue** page (`pages/12_Follow_Up_Queue.py`)
3. Created **Patient Notes** page (`pages/13_Patient_Notes.py`) - local OneNote alternative
4. Created **Daily Summary** dashboard (`pages/14_Daily_Summary.py`)
5. Created comprehensive **SMS Templates** module (`sms_templates.py`)
6. Enhanced the **Outreach Campaign** page with template preview
7. Updated **M365 Integration** page with OneNote deprecation notices
8. Added **PatientNote** model to database for local note storage
9. Reviewed all project documentation

Below are items that require your input before proceeding.

---

## Priority Items Requiring Input

### 1. Office Phone Number Configuration ✅ COMPLETE
**Location:** `app/sms_templates.py` line 27
**Configured:** `DEFAULT_OFFICE_PHONE = "(205) 955-7605"`

```python
DEFAULT_OFFICE_PHONE = "(205) 955-7605"  # Spruce office number
```

---

### 2. Microsoft Forms URL
**Location:** Used in multiple places for consent portal
**Action Required:** Create Microsoft Forms consent form and provide the URL

**Form Requirements:**
- Welcome message explaining the practice transition
- Records retention consent checkbox
- APCM continuation questions (for APCM patients):
  - "Do you want to continue APCM with Home Team?"
  - "Do you authorize notification to Southview?"
- Token field (pre-populated from URL parameter)
- Confirmation page

**Integration Steps:**
1. Create form in Microsoft Forms
2. Copy the share URL (e.g., `https://forms.microsoft.com/r/abc123`)
3. Enter URL in Outreach Campaign sidebar

---

### 3. Consent Form Legal Language
**Documents:** `docs/phase0b-consent-outreach-plan.md` section 8
**Action Required:** Legal review of consent language

**Needs Review:**
- Records retention consent wording
- APCM continuation authorization
- Southview billing revocation authorization
- HIPAA disclosure language

---

### 4. SMS Message Content Approval
**Location:** `app/sms_templates.py`
**Action Required:** Review and approve SMS templates before campaign

**Templates to Review:**
1. Non-APCM Initial Outreach (lines 61-75)
2. APCM Initial Outreach (lines 78-94)
3. Follow-up Day 3 (lines 101-109)
4. Follow-up Day 7 (lines 112-121)
5. Final Reminder Day 14 (lines 124-134)

**Key Questions:**
- Is "Dr. Robert Green" the correct name to use?
- Is "Home Team Medical Services" the correct destination name?
- Is "January 2026" the correct transition date?
- Should there be a character limit concern? (Most templates are 2 SMS segments)

---

### 5. Spruce Health Integration
**Status:** Ready for manual export/import
**Question:** Do you want to pursue Spruce API integration?

Based on my research (`docs/2025-11-30_Spruce Health API Report.md`):
- Spruce does have an API but requires partnership agreement
- Current workflow uses CSV export from Streamlit → manual import to Spruce
- API would enable automatic sync but adds complexity

**Options:**
- [ ] Continue with manual CSV workflow (simpler, works now)
- [ ] Request Spruce API access (more automation, longer setup)

---

### 6. OneNote Alternative Strategy
**Context:** Microsoft is deprecating app-only auth for OneNote (March 2025)

**Options to choose from:**
- [ ] **SharePoint Lists** - Use SharePoint for patient tracking (works now)
- [ ] **Local-only** - Keep all data in Patient Explorer's SQLite database
- [ ] **Implement OAuth** - Add user sign-in for OneNote (significant work)
- [ ] **Different service** - Explore other HIPAA-compliant note solutions

**Recommendation:** Use SharePoint Lists for shared tracking, local database for PHI.

---

## Configuration Items

### Environment Variables Needed
```env
# Already configured (verify these are correct):
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-secret

# For Azure Claude (if using AI features):
AZURE_CLAUDE_ENDPOINT=https://your-endpoint
AZURE_CLAUDE_API_KEY=your-key
```

### Azure AD Permissions Required
```
Microsoft Graph API (Application):
- Organization.Read.All ✅
- Sites.Read.All ✅
- Sites.ReadWrite.All (optional)
- Group.Read.All ✅
- Notes.Read.All ⚠️ (deprecated for app-only)
- Notes.ReadWrite.All ⚠️ (deprecated for app-only)
```

---

## Questions for Clarification

### Campaign Timing
1. When do you want to start the first outreach wave?
2. How many patients per day should be contacted? (Plan suggests 100/day max)
3. What days/times work best for the team? (Plan suggests Tue-Thu, 10am-2pm)

### Patient Data
1. Is the APCM patient list up to date in the database?
2. Do all patients have correct phone numbers?
3. Are there any patients who should be excluded from SMS outreach?

### Team Workflow
1. Who will be processing consent responses?
2. Should we track which staff member processed each response?
3. What's the escalation path for declined consents?

---

## Files Created/Modified This Session

### New Files
1. `app/pages/11_Consent_Response.py` - Consent response processing page
   - Token validation and lookup
   - Single response processing with APCM elections
   - Bulk import from Microsoft Forms Excel export
   - Recent responses view with export

2. `app/pages/12_Follow_Up_Queue.py` - Follow-up outreach tracking
   - Patients grouped by urgency (Day 3, 7, 14, 21+)
   - Quick actions to mark as contacted
   - Export queues for Spruce bulk messaging
   - Response rate tracking

3. `app/pages/13_Patient_Notes.py` - Local patient notes (OneNote alternative)
   - Create, edit, delete notes per patient
   - Note types: General, Outreach, Clinical, Admin
   - Pin important notes
   - Quick templates for common notes
   - Full audit logging

4. `app/pages/14_Daily_Summary.py` - Campaign dashboard and reporting
   - Daily metrics and trends
   - Campaign progress visualization
   - APCM election tracking
   - Activity log export
   - Campaign summary export

5. `app/sms_templates.py` - SMS template generation module
   - APCM vs non-APCM templates
   - Follow-up sequence (Day 0, 3, 7, 14)
   - Confirmation templates
   - Character count and SMS segment tracking

6. `docs/USER-INPUT-CHECKLIST.md` - This file

### Modified Files
1. `app/pages/4_Outreach_Campaign.py` - Added SMS Templates tab with preview
2. `app/pages/7_M365_Integration.py` - Added OneNote deprecation notices
3. `app/database/models.py` - Added PatientNote model for local notes

---

## Next Steps (After User Review)

1. [ ] Configure office phone number in sms_templates.py
2. [ ] Create Microsoft Forms consent form
3. [ ] Get legal approval on consent language
4. [ ] Review and approve SMS templates
5. [ ] Decide on OneNote alternative
6. [ ] Import APCM patient data if not already done
7. [ ] Generate consent tokens for patients
8. [ ] Test with small batch (10 patients)
9. [ ] Launch Wave 1 outreach

---

## Technical Notes

### Consent Response Page Features
- Token validation with expiration checking
- Single response processing with form
- Bulk import from Microsoft Forms Excel export
- APCM election tracking (continue with HT, revoke Southview)
- Audit logging for HIPAA compliance

### SMS Templates Features
- Automatic APCM vs non-APCM template selection
- Character count and SMS segment tracking
- Follow-up schedule (Day 0, 3, 7, 14)
- Confirmation templates for responses

---

*This checklist was generated during an autonomous development session.
Please review and provide input on the items above.*
