# Module: New Patient Onboarding & Status Tracking

> Planning document for patient intake workflow and extensible status tracking patterns

## Overview

This module manages the **new patient request pipeline** - tracking prospective patients from initial inquiry through full onboarding into the practice.

---

## Phase 1: New Patient Requests Page

### Core Functionality

**Page**: `27_New_Patient_Requests.py`

Track pending patients through onboarding stages:

| Stage | Description | Required Items |
|-------|-------------|----------------|
| **Inquiry** | Initial contact received | Name, phone, reason for interest |
| **Application** | Patient info collected | Demographics, insurance info |
| **Verification** | Insurance/eligibility check | Insurance verified, copay determined |
| **Records Request** | Prior records requested | Release signed, records received |
| **Intake Prep** | Pre-visit preparation | Med list, problem list, consent forms |
| **Scheduled** | First visit scheduled | Appointment date/time |
| **Onboarded** | First visit completed | Converted to active patient |

### Data Model

```python
class NewPatientRequest(Base):
    __tablename__ = "new_patient_requests"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Contact Info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    preferred_contact = Column(String(20))  # phone, email, text

    # Request Details
    referral_source = Column(String(100))  # how they heard about us
    reason_for_visit = Column(Text)
    urgency = Column(String(20))  # routine, soon, urgent
    preferred_provider = Column(String(100))

    # Status Tracking
    current_stage = Column(String(50), default="inquiry")
    assigned_to = Column(String(100))  # staff member handling

    # Onboarding Checklist (JSON or separate table)
    checklist_items = Column(JSON)  # or relationship to OnboardingChecklistItem

    # Conversion
    converted_patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    converted_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text)

class OnboardingChecklistItem(Base):
    __tablename__ = "onboarding_checklist_items"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("new_patient_requests.id"))

    item_type = Column(String(50))  # consent, insurance, med_list, records, etc.
    item_name = Column(String(200))
    status = Column(String(20))  # pending, in_progress, received, verified, n/a
    received_date = Column(DateTime, nullable=True)
    verified_by = Column(String(100), nullable=True)
    notes = Column(Text)
```

### Default Onboarding Checklist Items

```python
DEFAULT_ONBOARDING_ITEMS = [
    # Administrative
    {"type": "admin", "name": "Patient Registration Form", "required": True},
    {"type": "admin", "name": "Photo ID Copy", "required": True},
    {"type": "admin", "name": "Emergency Contact Info", "required": True},

    # Insurance
    {"type": "insurance", "name": "Insurance Card (Front/Back)", "required": True},
    {"type": "insurance", "name": "Insurance Eligibility Verified", "required": True},
    {"type": "insurance", "name": "Copay/Deductible Confirmed", "required": False},

    # Consent & Legal
    {"type": "consent", "name": "HIPAA Notice Acknowledgment", "required": True},
    {"type": "consent", "name": "Consent to Treat", "required": True},
    {"type": "consent", "name": "Financial Policy Agreement", "required": True},
    {"type": "consent", "name": "Telehealth Consent", "required": False},
    {"type": "consent", "name": "APCM Program Consent", "required": False},

    # Medical Records
    {"type": "records", "name": "Records Release Signed", "required": False},
    {"type": "records", "name": "Prior Records Received", "required": False},
    {"type": "records", "name": "Medication List", "required": True},
    {"type": "records", "name": "Problem/Diagnosis List", "required": False},
    {"type": "records", "name": "Surgical History", "required": False},
    {"type": "records", "name": "Allergy List", "required": True},

    # Pre-Visit
    {"type": "previsit", "name": "Health History Questionnaire", "required": True},
    {"type": "previsit", "name": "First Appointment Scheduled", "required": True},
    {"type": "previsit", "name": "Welcome Packet Sent", "required": False},
]
```

### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 New Patient Requests                                     │
├─────────────────────────────────────────────────────────────┤
│ PIPELINE VIEW (Kanban-style or Table)                       │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┐        │
│ │ Inquiry │ App     │ Verify  │ Records │ Ready   │        │
│ │ (5)     │ (3)     │ (2)     │ (4)     │ (1)     │        │
│ ├─────────┼─────────┼─────────┼─────────┼─────────┤        │
│ │ [Card]  │ [Card]  │ [Card]  │ [Card]  │ [Card]  │        │
│ │ [Card]  │ [Card]  │ [Card]  │ [Card]  │         │        │
│ └─────────┴─────────┴─────────┴─────────┴─────────┘        │
├─────────────────────────────────────────────────────────────┤
│ PATIENT DETAIL (when selected)                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ John Smith - Inquiry → Application                       │ │
│ │ Phone: (555) 123-4567  |  Referred by: Dr. Jones        │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ CHECKLIST                                  PROGRESS: 40% │ │
│ │ ☑ Patient Registration Form                              │ │
│ │ ☑ Photo ID Copy                                          │ │
│ │ ☐ Insurance Card                                         │ │
│ │ ☐ HIPAA Acknowledgment                                   │ │
│ │ ☐ Consent to Treat                                       │ │
│ │ ...                                                      │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ [Mark Item Complete] [Add Note] [Move to Next Stage]    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 2: Extensible Status Tracking Pattern

The onboarding checklist pattern can be generalized for other workflows:

### Pattern: Checklist-Based Status Tracking

```python
class ChecklistTemplate(Base):
    """Reusable checklist templates for different workflows."""
    __tablename__ = "checklist_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))  # "New Patient Onboarding", "Annual Visit Prep", etc.
    workflow_type = Column(String(50))  # onboarding, visit_prep, health_maint, protocol
    items = Column(JSON)  # List of checklist item definitions
    is_active = Column(Boolean, default=True)

class PatientChecklist(Base):
    """Instance of a checklist for a specific patient/context."""
    __tablename__ = "patient_checklists"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    template_id = Column(Integer, ForeignKey("checklist_templates.id"))
    context_type = Column(String(50))  # visit, annual_wellness, protocol
    context_id = Column(Integer)  # visit_id, protocol_id, etc.
    status = Column(String(20))  # in_progress, completed, expired
    items = Column(JSON)  # Instance items with completion status
```

---

## Application Areas

### 1. Visit Preparation Tracking

**Use Case**: Ensure all pre-visit tasks are completed before patient arrives

```
Visit Prep Checklist (by visit type):

ANNUAL WELLNESS VISIT:
☐ Insurance eligibility verified
☐ AWV eligibility confirmed (no AWV in past 12 months)
☐ Health Risk Assessment sent to patient
☐ HRA completed by patient
☐ Preventive care gaps identified
☐ Lab orders placed (if needed)
☐ Labs completed
☐ Prior visit notes reviewed
☐ Medication reconciliation prepared

CHRONIC CARE VISIT:
☐ Recent labs reviewed
☐ Medication adherence checked
☐ Care gap alerts reviewed
☐ Vitals from last visit noted
☐ Patient goals from last visit

NEW PATIENT VISIT:
☐ Onboarding checklist complete
☐ Records received and reviewed
☐ Problem list prepared
☐ Medication list reconciled
```

### 2. Health Maintenance Tracking

**Use Case**: Track preventive care and screening status

```
Health Maintenance Items:

SCREENINGS (by age/sex/risk):
☐ Colonoscopy (age 45-75, q10y or q5y if polyps)
☐ Mammogram (women 40+, annually)
☐ Cervical cancer screening (women 21-65)
☐ Lung cancer screening (55-80, 20+ pack-years)
☐ AAA screening (men 65-75, ever smoked)
☐ DEXA scan (women 65+, men 70+)

IMMUNIZATIONS:
☐ Flu vaccine (annually)
☐ COVID-19 (per current guidelines)
☐ Pneumococcal (65+)
☐ Shingles (50+)
☐ Tdap (q10y)

CHRONIC DISEASE MONITORING:
☐ HbA1c (diabetics, q3-6mo)
☐ Lipid panel (ASCVD risk, annually)
☐ Kidney function (CKD, diabetics)
☐ Eye exam (diabetics, annually)
☐ Foot exam (diabetics, annually)
```

### 3. Diagnosis-Specific Protocols

**Use Case**: Ensure disease-specific care protocols are followed

```
Protocol: Type 2 Diabetes Management

INITIAL DIAGNOSIS:
☐ HbA1c obtained
☐ Lipid panel obtained
☐ Kidney function (eGFR, uACR)
☐ Eye exam referral
☐ Foot exam performed
☐ Diabetes education scheduled
☐ Nutrition counseling scheduled
☐ Medication initiated per guidelines

ONGOING MONITORING (Quarterly):
☐ HbA1c check
☐ Medication review/adjustment
☐ Hypoglycemia assessment
☐ Foot exam
☐ BP check

ANNUAL:
☐ Comprehensive metabolic panel
☐ Lipid panel
☐ Eye exam
☐ Dental referral
☐ Flu vaccine
```

---

## Future Discussion Topics

### Visit Types & Staff Workflow Guardrails

**Schedule a dedicated session to discuss:**

1. **Visit Type Definitions**
   - What visit types do we offer? (AWV, chronic care, acute, telehealth, etc.)
   - What are the time allocations for each?
   - What staff roles are involved in each?

2. **Pre-Visit Workflow**
   - Who reviews the schedule X days before?
   - What tasks must be completed before patient arrives?
   - How do we handle incomplete prep work?

3. **Day-of Workflow**
   - Check-in process and verification
   - Rooming and vitals collection
   - Provider handoff information
   - Post-visit tasks (orders, referrals, follow-up scheduling)

4. **Guardrails & Automation**
   - Required fields that block progression
   - Alerts for missing items
   - Automatic task assignment based on visit type
   - Escalation paths for blockers

5. **Quality Metrics**
   - What are we measuring?
   - How do we surface performance to staff?
   - What incentives/feedback loops exist?

---

## Implementation Priority

| Phase | Feature | Complexity | Impact |
|-------|---------|------------|--------|
| 1a | New Patient Request page (basic) | Medium | High |
| 1b | Onboarding checklist tracking | Medium | High |
| 2a | Visit prep checklists | Medium | High |
| 2b | Health maintenance dashboard | High | High |
| 3 | Protocol-based tracking | High | Medium |
| 4 | Automated guardrails/alerts | High | High |

---

## Technical Notes

### Integration Points

- **Patient Database**: Link new patient requests to patient records on conversion
- **Scheduling**: Integrate with appointment scheduling for visit prep
- **EHR**: Import/export health maintenance data
- **Notifications**: Alert staff of incomplete items, upcoming deadlines

### Audit Requirements

All checklist item changes should be logged:
- Who marked item complete
- When it was marked
- Any notes added
- Status changes

---

## Action Items

- [ ] Create `27_New_Patient_Requests.py` page
- [ ] Add database models for new patient tracking
- [ ] Design checklist template system
- [ ] **SCHEDULE**: Discussion session on visit types and workflow guardrails
- [ ] Research EHR integration options for health maintenance data

---

*Created: 2024-12-09*
*Status: Planning*
