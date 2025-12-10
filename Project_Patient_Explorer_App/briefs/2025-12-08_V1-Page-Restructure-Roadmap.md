# V1.0 Page Restructure Roadmap

**Date:** 2025-12-08
**Status:** Planning
**Schema Reference:** `Project_Patient_Explorer_App/schemas/patient_master_record_schema.json`

---

## Executive Summary

The current app has 16 pages with significant overlap and gaps compared to the V1.0 Patient Master Record schema. This roadmap consolidates similar functions and adds new pages to fully support the schema's clinical data model.

**Current State:** 16 pages (+ main.py dashboard)
**Target State:** 19 pages with clear separation of concerns

---

## Phase 1: Page Consolidation (Reduce Overlap)

### 1.1 Consent Management Consolidation

**Merge:** Pages 2, 11, 12 → **3_Consent_Management**

| Current Page | Functions Moving |
|--------------|------------------|
| 2_Consent_Tracking | Status updates, outreach tracking, statistics |
| 11_Consent_Response | Form submission processing, token validation |
| 12_Follow_Up_Queue | Urgency-based follow-up tracking |

**New Tab Structure:**
- Tab 1: **Status Overview** - View/update consent status
- Tab 2: **Process Responses** - Handle form submissions
- Tab 3: **Follow-Up Queue** - Urgency-sorted patient list
- Tab 4: **Statistics** - Campaign metrics

**Files to modify:**
- `app/pages/2_Consent_Tracking.py` → Rename to `3_Consent_Management.py`, merge functionality
- `app/pages/11_Consent_Response.py` → Delete after merge
- `app/pages/12_Follow_Up_Queue.py` → Delete after merge

---

### 1.2 Patient List + APCM Consolidation

**Merge:** Pages 1, 3 → **1_Patient_List** (with APCM tab)

| Current Page | Functions Moving |
|--------------|------------------|
| 1_Patient_List | Patient view, filters, import, export |
| 3_APCM_Patients | APCM enrollment, billing levels, HT elections |

**New Tab Structure:**
- Tab 1: **All Patients** - Full patient list with filters
- Tab 2: **APCM Enrolled** - APCM-specific view and management
- Tab 3: **Import/Export** - Data operations
- Tab 4: **Statistics** - Patient counts by status

**Files to modify:**
- `app/pages/1_Patient_List.py` → Add APCM tab
- `app/pages/3_APCM_Patients.py` → Delete after merge

---

### 1.3 Document Processing Consolidation

**Merge:** Pages 6, 10 → **11_Document_Processing**

| Current Page | Functions Moving |
|--------------|------------------|
| 6_Add_Documents | OCR extraction, clipboard paste, Azure DI models |
| 10_Smart_Data_Ingest | AI chat for document analysis |

**New Tab Structure:**
- Tab 1: **Quick OCR** - Simple text extraction
- Tab 2: **AI Analysis** - Chat-based intelligent parsing
- Tab 3: **History** - Previously processed documents

**Files to modify:**
- `app/pages/6_Add_Documents.py` → Rename to `11_Document_Processing.py`, merge
- `app/pages/10_Smart_Data_Ingest.py` → Delete after merge

---

### 1.4 M365 Integration Cleanup

**Modify:** Page 7 → **17_SharePoint_Sync**

- **Remove:** OneNote integration (deprecated March 2025)
- **Keep:** SharePoint sync functionality
- **Reference:** Page 14 (Patient Notes) for local note storage

**Files to modify:**
- `app/pages/7_M365_Integration.py` → Rename to `17_SharePoint_Sync.py`, remove OneNote

---

## Phase 2: New Clinical Data Pages

### 2.1 Patient Chart (NEW)

**File:** `app/pages/2_Patient_Chart.py`

**Purpose:** Interactive patient record viewer (athenaOne-inspired)

**Schema Sections Displayed:**
- `demographics` - Patient header with photo placeholder
- `identifiers` - MRN, Spruce ID, Medicare MBI
- `insurance` - Primary/secondary coverage
- `tags` - Team assignments, LOC, status tags
- Navigation to all clinical sections

**UI Pattern:** Left sidebar with section icons, main content area

**Note:** Build on existing `20_Patient_Explorer.py` prototype

---

### 2.2 Problem List (NEW)

**File:** `app/pages/5_Problem_List.py`

**Schema Source:** `clinical.problems`

**Features:**
- Active vs resolved/inactive problem toggle
- ICD-10 code display and search
- Onset/resolved date tracking
- Problem notes and source attribution
- Add/edit/resolve problems

**Data Model Fields:**
```json
{
  "description": "string",
  "icd10": "string (pattern: ^[A-Z][0-9]{2}(\\.[0-9]{1,4})?$)",
  "status": "active | resolved | inactive",
  "onset_date": "date",
  "resolved_date": "date",
  "notes": "string",
  "source": "string"
}
```

---

### 2.3 Medications & Allergies (NEW)

**File:** `app/pages/6_Medications_Allergies.py`

**Schema Source:** `clinical.medications` + `clinical.allergies`

**Features:**
- **Medications Tab:**
  - Current vs discontinued medications
  - Dosage, frequency, route
  - Prescriber attribution
  - PRN flagging
  - Start/end dates

- **Allergies Tab:**
  - Drug allergies highlighted (cross-reference with meds)
  - Food/environmental allergies
  - Reaction descriptions
  - Severity levels (mild/moderate/severe)

**Drug-Allergy Alert:** When viewing medications, flag if patient has drug allergies

**Data Model Fields (Medications):**
```json
{
  "name": "string",
  "generic_name": "string",
  "dosage": "string",
  "frequency": "string",
  "route": "oral | topical | injection | inhalation | other",
  "prescriber": "string",
  "start_date": "date",
  "end_date": "date",
  "active": "boolean",
  "prn": "boolean",
  "indication": "string"
}
```

**Data Model Fields (Allergies):**
```json
{
  "allergen": "string",
  "type": "drug | food | environmental | other",
  "reaction": "string",
  "severity": "mild | moderate | severe | unknown",
  "onset_date": "date"
}
```

---

### 2.4 Immunizations (NEW)

**File:** `app/pages/7_Immunizations.py`

**Schema Source:** `clinical.health_maintenance` (vaccine items)

**Features:**
- Vaccine history list
- Due/overdue status highlighting
- Last administered dates
- Declined vaccines tracking
- CDC schedule reference (optional)

**Vaccines to Track:**
- Influenza (annual)
- Pneumococcal (PCV20, PPSV23)
- Shingles (Shingrix)
- Tdap/Td
- COVID-19
- Hepatitis B (if indicated)

**Data Model Fields:**
```json
{
  "item": "string (vaccine name)",
  "due_date": "date",
  "last_completed": "date",
  "status": "due | overdue | completed | declined",
  "notes": "string"
}
```

---

### 2.5 Visit History (NEW)

**File:** `app/pages/8_Visit_History.py`

**Schema Source:** `encounters`

**Features:**
- Chronological visit list
- Filter by visit type (office, telehealth, home, hospital)
- Chief complaint and diagnoses display
- Assessment/plan summary
- CPT codes for billing reference
- Source system attribution

**Data Model Fields:**
```json
{
  "id": "string",
  "date": "date",
  "type": "office_visit | telehealth | home_visit | phone_call | hospital | emergency | procedure",
  "provider": "string",
  "chief_complaint": "string",
  "diagnoses": ["string"],
  "assessment": "string",
  "plan": "string",
  "cpt_codes": ["string"],
  "source": "string"
}
```

---

### 2.6 Health Maintenance (NEW)

**File:** `app/pages/9_Health_Maintenance.py`

**Schema Source:** `clinical.health_maintenance` (non-vaccine items)

**Features:**
- Preventive care tracking
- Due/overdue status with color coding
- Last completed dates
- Patient declined tracking
- Reminder generation

**Screenings to Track:**
- Colonoscopy (every 10 years, age 45+)
- Mammogram (annual/biennial, age 40+)
- A1c (diabetics: every 3-6 months)
- Lipid panel (every 5 years or per condition)
- Annual Wellness Visit
- Depression screening (PHQ-9)
- Cognitive assessment (for geriatric patients)
- Fall risk assessment
- Advance directive review

---

### 2.7 Care Plans (NEW)

**File:** `app/pages/10_Care_Plans.py`

**Schema Source:** `care_plan`

**Features:**
- APCM care plan builder
- Goals with target dates and status
- Interventions with frequency and responsible party
- Care plan versioning
- Print/export for patient

**Data Model Fields:**
```json
{
  "created_date": "date",
  "last_updated": "date",
  "created_by": "string",
  "goals": [
    {
      "goal": "string",
      "target_date": "date",
      "status": "active | achieved | discontinued"
    }
  ],
  "interventions": [
    {
      "intervention": "string",
      "frequency": "string",
      "responsible_party": "string"
    }
  ]
}
```

---

### 2.8 Screenshot Gallery (NEW)

**File:** `app/pages/12_Screenshot_Gallery.py`

**Schema Source:** `screenshots`

**Features:**
- Patient-specific screenshot browser
- Category filtering (demographics, medications, labs, etc.)
- Source system filtering (Allscripts, Athena, Aledade)
- OCR text preview
- Azure Blob Storage integration
- Capture date sorting

**Data Model Fields:**
```json
{
  "id": "uuid",
  "category": "demographics | face_sheet | encounters | medications | allergies | problems | vitals | labs | imaging | procedures | care_plan | aledade_hcc | aledade_gaps | insurance | billing | other",
  "source": "allscripts | athena | aledade | onenote | spruce | other",
  "capture_date": "datetime",
  "captured_by": "string",
  "azure_blob_path": "string",
  "file_name": "string",
  "ocr_text": "string",
  "ocr_processed": "boolean"
}
```

---

### 2.9 Spruce Messages (NEW)

**File:** `app/pages/15_Spruce_Messages.py`

**Schema Source:** `communications`

**Features:**
- Patient communication log from Spruce
- Filter by type (SMS, call, secure message, fax)
- Inbound/outbound direction
- Staff member attribution
- Link to Spruce conversation

**Data Model Fields:**
```json
{
  "id": "string",
  "date": "datetime",
  "type": "sms | call | secure_message | fax | email",
  "direction": "inbound | outbound",
  "summary": "string",
  "staff_member": "string",
  "spruce_conversation_id": "string",
  "spruce_message_id": "string"
}
```

---

## Phase 3: Final Page Numbering

After consolidation and new page creation:

| # | Page Name | Status | Notes |
|---|-----------|--------|-------|
| 1 | Patient_List | Modify | Add APCM tab, absorb Page 3 |
| 2 | Patient_Chart | NEW | Clinical viewer, build on Page 20 |
| 3 | Consent_Management | Modify | Absorb Pages 2, 11, 12 |
| 4 | Outreach_Campaign | Keep | Simplify token UI |
| 5 | Problem_List | NEW | From clinical.problems |
| 6 | Medications_Allergies | NEW | Meds + allergies together |
| 7 | Immunizations | NEW | Vaccine tracking |
| 8 | Visit_History | NEW | From encounters |
| 9 | Health_Maintenance | NEW | Screenings/preventive care |
| 10 | Care_Plans | NEW | APCM care plan builder |
| 11 | Document_Processing | Modify | Absorb Pages 6, 10 |
| 12 | Screenshot_Gallery | NEW | Patient screenshot browser |
| 13 | AI_Assistant | Keep | Azure Claude integration |
| 14 | Patient_Notes | Keep | Local notes |
| 15 | Spruce_Messages | NEW | Communication log |
| 16 | Team_Tasks | Keep | MS Planner integration |
| 17 | SharePoint_Sync | Modify | From Page 7, remove OneNote |
| 18 | Admin | Keep | User management |
| 19 | Daily_Summary | Keep | Campaign dashboard |

---

## Database Model Updates Required

The current `app/database/models.py` needs expansion to match V1.0 schema:

### New Tables Needed

1. **PatientProblem** - `clinical.problems` array
2. **PatientMedication** - `clinical.medications` array
3. **PatientAllergy** - `clinical.allergies` array
4. **PatientImmunization** - Health maintenance (vaccines)
5. **PatientScreening** - Health maintenance (non-vaccines)
6. **PatientEncounter** - `encounters` array
7. **PatientScreenshot** - `screenshots` array
8. **PatientCommunication** - `communications` array
9. **PatientCarePlan** - `care_plan` object
10. **PatientCarePlanGoal** - Goals within care plan
11. **PatientCarePlanIntervention** - Interventions within care plan

### Existing Tables to Modify

- **Patient** - Add `identifiers`, `insurance`, `tags`, `scheduling` fields
- **Consent** - Align with schema's consent object

---

## Implementation Order

### Sprint 1: Consolidation (Reduce Complexity)
1. Merge consent pages (2+11+12 → 3)
2. Merge patient/APCM pages (1+3 → 1)
3. Merge document pages (6+10 → 11)
4. Clean up M365 page (remove OneNote)

### Sprint 2: Patient Chart Foundation
1. Create Patient_Chart page (build on Page 20)
2. Create navigation structure
3. Implement demographics/identifiers/insurance display

### Sprint 3: Clinical Data - Core
1. Problem_List page + database model
2. Medications_Allergies page + database models
3. Drug-allergy cross-reference alerting

### Sprint 4: Clinical Data - History
1. Immunizations page + database model
2. Visit_History page + database model
3. Health_Maintenance page + database model

### Sprint 5: Care Plans & Documents
1. Care_Plans page + database models
2. Screenshot_Gallery page + database model
3. Azure Blob integration for screenshots

### Sprint 6: Communication & Polish
1. Spruce_Messages page + database model
2. Final page renumbering
3. Navigation menu updates
4. Testing and documentation

---

## Files to Delete After Consolidation

- `app/pages/3_APCM_Patients.py` (merged into Patient_List)
- `app/pages/6_Add_Documents.py` (merged into Document_Processing)
- `app/pages/10_Smart_Data_Ingest.py` (merged into Document_Processing)
- `app/pages/11_Consent_Response.py` (merged into Consent_Management)
- `app/pages/12_Follow_Up_Queue.py` (merged into Consent_Management)
- `app/pages/20_Patient_Explorer.py` (evolved into Patient_Chart)

---

## Success Criteria

- [ ] All V1.0 schema sections have corresponding UI pages
- [ ] No duplicate functionality across pages
- [ ] Clear page naming that reflects function
- [ ] Database models match JSON schema structure
- [ ] All clinical data is patient-scoped (requires patient selection)
- [ ] Audit logging on all clinical data changes
- [ ] OneNote dependency removed before March 2025 deadline

---

## Research Integration

The following research reports inform this roadmap implementation:

### Spruce Webhooks for Inbound SMS
**Reference:** `docs/Research_Reports/2025-12-08_research_spruce-webhooks-inbound-sms.md`

**Key Findings:**
- `conversationItem.created` webhook event captures real-time SMS replies
- Enables automatic consent detection without manual CSV export
- Requires HTTPS endpoint (Azure Function recommended)
- Signature verification via `X-Spruce-Signature` header (HMAC-SHA256)

**Impact on Pages:**

| Page | Enhancement |
|------|-------------|
| **3_Consent_Management** | Add "Webhook Status" tab showing real-time consent responses |
| **15_Spruce_Messages** | Display webhook-received messages with auto-detected consent status |
| **4_Outreach_Campaign** | Show real-time response rates from webhook data |

**New Backend Components Needed:**
1. `app/services/spruce_webhook.py` - Webhook receiver and signature verification
2. `app/services/consent_detector.py` - Pattern matching for consent/decline keywords
3. Azure Function deployment for webhook endpoint
4. Environment variables: `SPRUCE_WEBHOOK_SECRET`

**Consent Detection Patterns:**
```python
CONSENT_PATTERNS = ['yes', 'i consent', 'i agree', 'accept', 'approve', 'ok', 'sure']
DECLINE_PATTERNS = ['no', 'decline', 'refuse', 'stop', 'cancel']
```

---

### Phone Number Matching & Patient Data Consolidation
**Reference:** `docs/Research_Reports/2025-12-08_research_phone-number-patient-matching.md`

**Key Findings:**
- Use `phonenumbers` library for E.164 normalization (+12055551234)
- Use `rapidfuzz` for fuzzy name matching (MIT license, faster than fuzzywuzzy)
- Multi-stage matching: exact phone → fuzzy name → combined → last-10-digits
- Handle edge cases: shared family phones, typos, missing data

**Impact on Pages:**

| Page | Enhancement |
|------|-------------|
| **1_Patient_List** | Add "Match Status" column, "Re-match" action button |
| **1_Patient_List** | Add "Matching Review" tab for low-confidence matches |
| **15_Spruce_Messages** | Auto-link messages to patients via phone matching |

**New Backend Components Needed:**
1. `app/services/phone_normalizer.py` - PhoneNormalizer class (E.164 conversion)
2. `app/services/name_matcher.py` - NameMatcher class (rapidfuzz integration)
3. `app/services/patient_matcher.py` - PatientMatcher class (multi-stage algorithm)

**New Dependencies:**
```
phonenumbers>=8.13.0
rapidfuzz>=3.0.0
```

**Matching Confidence Tiers:**
| Tier | Score | Action |
|------|-------|--------|
| High | ≥90% | Auto-accept |
| Medium | 75-89% | Flag for review |
| Low | <75% | Manual match required |

---

### CMS APCM Billing Requirements
**Reference:** `docs/Research_Reports/2025-12-08_research_cms-apcm-billing-requirements.md`

**Key Findings:**
- APCM consent required once per provider relationship (new consent needed for Home Team)
- Only one provider can bill per patient per month (clean cutoff: Southview Dec, Home Team Jan)
- 13 service elements required for APCM billing (not all monthly)
- Billing codes: G0556 (~$15/mo), G0557 (~$50/mo), G0558 (~$110/mo for QMB)
- Cannot bill CCM, PCM, TCM in same month as APCM

**Impact on Pages:**

| Page | Enhancement |
|------|-------------|
| **3_Consent_Management** | Add CMS-required APCM disclosures checklist (single-provider, cost-sharing, right-to-stop) |
| **10_Care_Plans** | Add 13 APCM service element tracking checklist |
| **1_Patient_List (APCM tab)** | Add billing code validation, QMB status tracking, conflicting services warnings |
| **9_Health_Maintenance** | Link to APCM Element #7 (Preventive services tracking) |
| **6_Medications_Allergies** | Link to APCM Element #8 (Medication reconciliation) |

**New Backend Components Needed:**
1. `app/services/apcm_compliance.py` - APCM billing validation and conflict checking
2. Database field: `apcm_consent_disclosures_provided` (JSON: single_provider, cost_sharing, right_to_stop)
3. Database field: `apcm_service_elements` (JSON tracking 13 elements per patient)

**APCM Service Elements to Track:**
```python
APCM_SERVICE_ELEMENTS = [
    "consent_documented",
    "initiating_visit",
    "24_7_access",
    "continuity_of_care",
    "alternative_delivery",
    "needs_assessment",
    "preventive_tracking",
    "medication_reconciliation",
    "care_plan",
    "care_plan_shared",
    "transition_management",
    "specialist_coordination",
    "patient_engagement"
]
```

---

## Updated Sprint Plan (with Research Integration)

### Sprint 1: Consolidation + Matching Foundation
1. Merge consent pages (2+11+12 → 3)
2. Merge patient/APCM pages (1+3 → 1)
3. Merge document pages (6+10 → 11)
4. Clean up M365 page (remove OneNote)
5. **NEW:** Add `phonenumbers` and `rapidfuzz` to requirements.txt
6. **NEW:** Create `PhoneNormalizer` and `NameMatcher` services

### Sprint 2: Patient Chart + Webhook Infrastructure
1. Create Patient_Chart page (build on Page 20)
2. Create navigation structure
3. Implement demographics/identifiers/insurance display
4. **NEW:** Deploy Azure Function for Spruce webhook endpoint
5. **NEW:** Create `SpruceWebhookReceiver` service with signature verification

### Sprint 3: Clinical Data - Core + Matching UI
1. Problem_List page + database model
2. Medications_Allergies page + database models
3. Drug-allergy cross-reference alerting
4. **NEW:** Add "Matching Review" tab to Patient_List
5. **NEW:** Create `PatientMatcher` service with multi-stage algorithm

### Sprint 4: Clinical Data - History + Consent Automation
1. Immunizations page + database model
2. Visit_History page + database model
3. Health_Maintenance page + database model
4. **NEW:** Integrate webhook consent detection into Consent_Management
5. **NEW:** Add real-time consent response indicators

### Sprint 5: Care Plans & Documents
1. Care_Plans page + database models
2. Screenshot_Gallery page + database model
3. Azure Blob integration for screenshots

### Sprint 6: Communication & Polish
1. Spruce_Messages page + database model
2. **NEW:** Link Spruce messages to patients via phone matching
3. Final page renumbering
4. Navigation menu updates
5. Testing and documentation

---

## Environment Variables (Updated)

Add to `.env`:
```env
# Existing
SPRUCE_API_TOKEN=your_bearer_token

# NEW - Webhook support
SPRUCE_WEBHOOK_SECRET=whsec_your_webhook_secret

# NEW - Azure Function (if deploying webhook receiver)
AZURE_FUNCTION_URL=https://your-function.azurewebsites.net/api/spruce-webhook
```

---

## Dependencies Update

Add to `requirements.txt`:
```
# Phone normalization
phonenumbers>=8.13.0

# Fuzzy name matching
rapidfuzz>=3.0.0
```

---

*Generated by Patient Explorer App Agent | 2025-12-08*
*Updated with research integration | 2025-12-08*
