# Patient Explorer V1.0 Implementation Roadmap

**Date**: December 8, 2025
**Days to Deadline**: 23
**Status**: Active Development

---

## Executive Summary

Patient Explorer V1.0 is pivoting from complex Microsoft integrations to a **practical, working solution** for patient outreach. Key decisions:

1. **Defer Microsoft OAuth complexity** - OneNote app-only auth deprecated March 2025
2. **Use Plaud for recordings** - HIPAA-compliant transcription instead of Teams
3. **Keep Microsoft Forms** - Already working, no complex auth needed
4. **Focus on data consolidation** - Excel + Spruce → Azure JSON

---

## V1.0 Scope (IN)

| Feature | Status | Notes |
|---------|--------|-------|
| Patient data consolidation | 🔜 Ready to build | Excel + Spruce API → JSON |
| Azure Blob Storage sync | ✅ Complete | `patients_master.json` storage |
| Patient chart UI | 🔜 Ready to build | Navigation icons provided |
| Screenshot capture | 🔜 Ready to build | Upload + categorize |
| Microsoft Forms consent | ✅ Existing code | Token tracking ready |
| Plaud transcripts | 📋 Design complete | Awaiting API access |

## V1.0 Scope (OUT - Deferred to V1.1)

| Feature | Reason | Deferred To |
|---------|--------|-------------|
| OneNote ingestion | App-only auth deprecated | V1.1 (Jan 2025) |
| Azure AD App Registration | Not required for V1.0 | V1.1 |
| SharePoint document publishing | Not critical | V1.1 |
| Teams transcript access | Using Plaud instead | N/A |
| Complex OAuth flows | Simplified approach | V1.1 |

---

## Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| V1 Implementation Instructions | `PATIENT_EXPLORER_V1_INSTRUCTIONS.md` | Master guide for Claude Code |
| Patient Master Record Schema | `schemas/patient_master_record_schema.json` | JSON schema (622 lines) |
| Plaud Webhook Spec | `architecture/Plaud_Webhook_Integration_Spec.md` | Transcript integration |
| App File Reference | `APP_FILE_REFERENCE.md` | Existing code structure |

---

## Implementation Phases

### Phase 1: Data Consolidation Service (PRIORITY 1)

**Goal**: Create `patients_master.json` from Excel + Spruce

**New Files to Create**:
```
app/services/patient_consolidator.py  - Data merging logic
app/services/__init__.py              - Services module
```

**Tasks**:
- [ ] Load main patient Excel (~1,384 patients)
- [ ] Load APCM Excel (~450 patients)
- [ ] Fetch Spruce contacts via API
- [ ] Match patients to Spruce (phone → name+DOB → email)
- [ ] Generate consolidated JSON per schema
- [ ] Upload to Azure Blob `patient-data/patients_master.json`

**Matching Strategy**:
1. Phone number match (highest confidence)
2. Name + DOB match (secondary)
3. Email match (tertiary)
4. Unmatched patients flagged for manual review

---

### Phase 2: Patient Explorer UI (PRIORITY 2)

**Goal**: Interactive chart view inspired by athenaOne

**New Files to Create**:
```
app/pages/20_Patient_Explorer.py      - Main explorer view
app/pages/21_Screenshot_Capture.py    - Screenshot upload
app/assets/icons/                     - Navigation icons
```

**UI Components**:
- Left navigation bar with icons (provided)
- Flyout ribbon for sub-sections
- Patient header with tags
- Main workspace area

**Navigation Sections** (from icons):
| Icon | Section | Data Source |
|------|---------|-------------|
| HTnav_search.png | Patient Search | JSON master |
| HTnav_team.png | Care Team | tags.team |
| HTnav_stethoscope.png | Encounters | encounters[] |
| HTnav_Rx_bottle.png | Medications | clinical.medications[] |
| HTnav_Problem_List.png | Problems | clinical.problems[] |
| HTnav_vitals.png | Vitals | clinical.vitals_latest |
| HTnav_allergies.png | Allergies | clinical.allergies[] |
| HTnav_folder.png | Documents | screenshots[] |
| HTnav_phone.png | Communications | communications[] |
| HTnav_invoice.png | Billing/Insurance | insurance{} |

---

### Phase 3: Consent Integration (PRIORITY 3)

**Goal**: Generate consent links, track responses

**Existing Code**:
- `app/consent_tokens.py` - Token generation
- `app/pages/11_Consent_Response.py` - Response processing
- `app/pages/4_Outreach_Campaign.py` - Campaign management

**Tasks**:
- [ ] Add Form URL configuration in Settings
- [ ] Generate token-appended URLs per patient
- [ ] Test SMS send via Spruce (or manual copy)
- [ ] Import responses → update patient.consent

---

### Phase 4: Plaud Integration (PRIORITY 4 - Awaiting Access)

**Goal**: Auto-receive transcripts, match to patients

**New Files to Create**:
```
app/pages/25_Plaud_Transcripts.py     - Transcript management
azure_function/plaud_webhook/         - Webhook receiver (Optional)
```

**Environment Variables Needed**:
```env
PLAUD_CLIENT_ID=
PLAUD_CLIENT_SECRET_KEY=
PLAUD_WEBHOOK_SECRET=
PLAUD_COMPANY_DOMAIN=greenclinicteam.com
```

**Status**: Design complete, awaiting Plaud developer portal access

---

## Spruce Tag Standardization

Apply these tags in Spruce for patient categorization:

### Team Assignment
- `team_green`, `team_lachandra`, `team_lindsay`, `team_jenny`

### Level of Care
- `loc_il` (Independent), `loc_al` (Assisted), `loc_mc` (Memory Care)
- `loc_office`, `loc_home`

### Status Flags
- `apcm`, `consent_pending`, `consent_obtained`
- `high_priority`, `new_patient`, `transition_complete`

### Communication
- `prefer_sms`, `prefer_call`, `family_contact`, `no_sms`

---

## Azure Storage Structure

```
stgreenclinicworkspace (Storage Account)
├── workspace-sync/           # Existing - credentials, db, logs
│   ├── data/patients.db
│   ├── config/.env
│   └── logs/*.log
└── patient-data/             # NEW - Patient master data
    ├── patients_master.json  # Consolidated patient records
    ├── screenshots/          # Screenshot captures
    │   └── {patient_id}/
    ├── transcripts/          # Plaud transcripts
    │   └── {file_id}.json
    └── reports/              # Generated reports
```

---

## Questions for User (To Resolve)

1. **Excel Column Names**: What are the exact column headers?
2. **Spruce Matching Priority**: Phone first, then name+DOB?
3. **Default Team Assignment**: Default to `team_green` if no tag?
4. **Screenshot Storage**: Local first then sync, or direct Azure upload?

---

## Next Steps for This Session

1. **Create `patient_consolidator.py`** service
2. **Test Excel loading** with actual data files
3. **Run Spruce matching** to generate first JSON
4. **Copy navigation icons** to `app/assets/icons/`
5. **Create Patient Explorer page** with basic UI

---

## Success Criteria for V1.0

- [ ] All 1,384 patients loaded from Excel
- [ ] 90%+ Spruce match rate
- [ ] `patients_master.json` in Azure Blob
- [ ] Patient Explorer UI functional
- [ ] Screenshot capture working
- [ ] Consent tracking integrated
- [ ] Works on Dr. Green's + Jenny's machines

---

*Generated: December 8, 2025*
*Reference: PATIENT_EXPLORER_V1_INSTRUCTIONS.md*
