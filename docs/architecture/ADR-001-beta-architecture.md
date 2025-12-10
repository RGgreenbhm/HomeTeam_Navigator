# ADR-001: Beta Version Architecture Decisions

**Status**: Accepted
**Date**: 2025-12-02
**Deciders**: Dr. Robert Green (Product Owner), BMAD Agent Team

---

## Context

Patient Explorer needs a working beta version by December 3, 2025 for Dr. Green and nurse Jenny to begin the patient consent outreach campaign. The December 31, 2025 deadline for Allscripts access termination is immutable.

### Current State Assessment

**Existing Infrastructure (Working):**
- Streamlit app with 15+ pages
- Local auth system (username/password with role-based permissions)
- SQLite database with comprehensive models (Patient, Consent, CarePlan, User)
- Consent token generation system (`consent_tokens.py`)
- SMS templates with APCM differentiation (`sms_templates.py`)
- Outreach Campaign page with Spruce CSV export
- Consent Response processing (single lookup and bulk import)
- Spruce API integration (verified working)
- Microsoft Graph client (app-only auth)

**Gaps Identified:**
1. Microsoft OAuth for OneNote access (app-only being deprecated March 2025)
2. Actual consent form for patients to complete
3. Alpha packaging for deployment to second machine

---

## Decisions

### Decision 1: Use Microsoft Forms for Consent Collection (Beta)

**Choice**: Microsoft Forms with unique patient tokens
**Rationale**:
- Already under existing HIPAA BAA with Microsoft
- No development time required
- Mobile-friendly for patients
- Power Automate integration for SharePoint sync
- Can be live within hours

**Implementation**:
1. Dr. Green creates Microsoft Form with consent questions
2. Streamlit generates unique tokens per patient (already implemented)
3. Form URL structure: `https://forms.microsoft.com/r/FORM_ID?token={patient_token}`
4. Patient completes form, response includes their token
5. Staff processes responses via Consent Response page (bulk import from Forms export)

**Deferred**: Custom Azure Static Web App consent portal (Phase 2, post-deadline)

### Decision 2: Defer Microsoft OAuth to v2.0

**Choice**: Keep local auth for beta, implement user OAuth later
**Rationale**:
- OneNote access is "nice to have" for beta, not critical path
- Messaging campaign doesn't require OneNote
- March 2025 deadline for MS change gives time after consent outreach
- Focus all effort on consent workflow

**Implementation**:
- Beta uses existing local auth (`auth.py`)
- Microsoft OAuth story deferred to post-December sprint
- User model already has `microsoft_user_id` field for future integration

### Decision 3: Simple Deployment via Git Clone + Script

**Choice**: PowerShell setup script rather than packaged installer
**Rationale**:
- Only 2 users for beta (Dr. Green + Jenny)
- Both on Windows 11 with Python available
- Avoids complexity of PyInstaller/Electron
- Easy to update via `git pull`

**Implementation**:
- Create `setup-beta.ps1` script
- Script handles: venv creation, pip install, .env template, database init
- Run with: `streamlit run app/main.py`

### Decision 4: Consent Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     BETA CONSENT WORKFLOW                        │
└─────────────────────────────────────────────────────────────────┘

1. PREPARATION (Streamlit)
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Import Excel │ ──▶ │ Match Spruce │ ──▶ │ Generate     │
   │ Patient List │     │ Contacts     │     │ Tokens       │
   └──────────────┘     └──────────────┘     └──────────────┘
                                                    │
2. OUTREACH                                         ▼
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Export CSV   │ ──▶ │ Upload to    │ ──▶ │ Bulk SMS     │
   │ for Spruce   │     │ Spruce       │     │ via Spruce   │
   └──────────────┘     └──────────────┘     └──────────────┘

3. PATIENT RESPONSE
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ SMS Received │ ──▶ │ Click Link   │ ──▶ │ Microsoft    │
   │ by Patient   │     │ with Token   │     │ Forms        │
   └──────────────┘     └──────────────┘     └──────────────┘
                                                    │
4. PROCESSING                                       ▼
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Export Forms │ ◀── │ Power Auto   │ ◀── │ Form Submit  │
   │ to Excel     │     │ (optional)   │     │ + Token      │
   └──────────────┘     └──────────────┘     └──────────────┘
          │
          ▼
   ┌──────────────┐     ┌──────────────┐
   │ Bulk Import  │ ──▶ │ Update       │
   │ in Streamlit │     │ Consent DB   │
   └──────────────┘     └──────────────┘

5. TRACKING
   ┌──────────────────────────────────────────────────────────┐
   │ Dashboard: Consent metrics, APCM elections, follow-ups   │
   └──────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive
- Beta can be deployed December 3, 2025
- No new development required for consent form (use Forms)
- Spruce integration already verified
- Existing consent response processing handles bulk import
- Staff can begin outreach immediately

### Negative/Risks
- Manual step required to export Forms responses and import to Streamlit
- No real-time sync between Forms and Streamlit (acceptable for beta)
- OneNote patient data not accessible until v2.0

### Mitigations
- Document Forms export workflow clearly
- Schedule daily import routine
- Prioritize OAuth implementation for January 2025

---

## Action Items for Beta Launch

1. [ ] Dr. Green: Create Microsoft Form with consent questions
2. [ ] Agent: Create setup-beta.ps1 deployment script
3. [ ] Agent: Create Microsoft Forms configuration guide
4. [ ] Agent: Test end-to-end workflow with sample data
5. [ ] Jenny: Test installation on her machine
6. [ ] Both: Pilot with 10 patients before full campaign

---

*Created by BMAD Agent Team during autonomous session 2025-12-02*
