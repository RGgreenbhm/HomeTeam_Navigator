# Architecture Decision Record: Status Tracking with JSON File Storage

> Designing checklist-based status tracking using unstructured JSON files synced to Azure Blob Storage

## Context

We need a flexible status tracking system for:
- New patient onboarding
- Visit preparation
- Health maintenance
- Diagnosis-specific protocols

**Constraint**: Use JSON file storage that syncs to Azure Blob Storage (existing pattern).

---

## Proposed Architecture

### File Structure

```
data/
├── tracking/
│   ├── _templates/                    # Checklist templates (shared)
│   │   ├── onboarding_default.json
│   │   ├── visit_prep_awv.json
│   │   ├── visit_prep_chronic.json
│   │   ├── visit_prep_new_patient.json
│   │   ├── health_maint_adult.json
│   │   ├── health_maint_pediatric.json
│   │   └── protocol_diabetes_t2.json
│   │
│   ├── new_patients/                  # New patient request queue
│   │   ├── index.json                 # Quick lookup index
│   │   ├── np_2024001.json           # Individual request files
│   │   ├── np_2024002.json
│   │   └── ...
│   │
│   ├── patient_checklists/           # Patient-specific active checklists
│   │   ├── by_patient/
│   │   │   ├── pt_12345/             # Patient ID folder
│   │   │   │   ├── onboarding.json   # Their onboarding checklist
│   │   │   │   ├── health_maint.json # Their health maintenance
│   │   │   │   └── protocols/
│   │   │   │       ├── diabetes.json
│   │   │   │       └── hypertension.json
│   │   │   └── pt_12346/
│   │   │       └── ...
│   │   │
│   │   └── by_visit/                 # Visit-specific checklists
│   │       ├── 2024-12-15/           # By date
│   │       │   ├── visit_prep_pt_12345.json
│   │       │   ├── visit_prep_pt_12346.json
│   │       │   └── day_summary.json
│   │       └── ...
│   │
│   └── completed/                    # Archive of completed checklists
│       └── 2024/
│           └── 12/
│               └── ...
```

---

## JSON Schema Designs

### 1. Checklist Template Schema

```json
// _templates/onboarding_default.json
{
  "template_id": "onboarding_default",
  "template_name": "New Patient Onboarding",
  "version": "1.0",
  "workflow_type": "onboarding",
  "created_at": "2024-12-09T00:00:00Z",
  "updated_at": "2024-12-09T00:00:00Z",

  "stages": [
    {"id": "inquiry", "name": "Inquiry", "order": 1},
    {"id": "application", "name": "Application", "order": 2},
    {"id": "verification", "name": "Verification", "order": 3},
    {"id": "records", "name": "Records Request", "order": 4},
    {"id": "intake_prep", "name": "Intake Prep", "order": 5},
    {"id": "scheduled", "name": "Scheduled", "order": 6},
    {"id": "onboarded", "name": "Onboarded", "order": 7}
  ],

  "items": [
    {
      "id": "registration_form",
      "category": "admin",
      "name": "Patient Registration Form",
      "description": "Complete demographics and contact info",
      "required": true,
      "stage": "application",
      "auto_advance": false
    },
    {
      "id": "photo_id",
      "category": "admin",
      "name": "Photo ID Copy",
      "required": true,
      "stage": "application"
    },
    {
      "id": "insurance_card",
      "category": "insurance",
      "name": "Insurance Card (Front/Back)",
      "required": true,
      "stage": "verification"
    },
    {
      "id": "eligibility_verified",
      "category": "insurance",
      "name": "Insurance Eligibility Verified",
      "required": true,
      "stage": "verification",
      "depends_on": ["insurance_card"]
    },
    {
      "id": "hipaa_ack",
      "category": "consent",
      "name": "HIPAA Notice Acknowledgment",
      "required": true,
      "stage": "intake_prep"
    },
    {
      "id": "consent_treat",
      "category": "consent",
      "name": "Consent to Treat",
      "required": true,
      "stage": "intake_prep"
    },
    {
      "id": "records_release",
      "category": "records",
      "name": "Records Release Signed",
      "required": false,
      "stage": "records"
    },
    {
      "id": "prior_records",
      "category": "records",
      "name": "Prior Records Received",
      "required": false,
      "stage": "records",
      "depends_on": ["records_release"]
    },
    {
      "id": "med_list",
      "category": "medical",
      "name": "Medication List",
      "required": true,
      "stage": "intake_prep"
    },
    {
      "id": "allergy_list",
      "category": "medical",
      "name": "Allergy List",
      "required": true,
      "stage": "intake_prep"
    },
    {
      "id": "health_questionnaire",
      "category": "previsit",
      "name": "Health History Questionnaire",
      "required": true,
      "stage": "intake_prep"
    },
    {
      "id": "first_appt",
      "category": "scheduling",
      "name": "First Appointment Scheduled",
      "required": true,
      "stage": "scheduled"
    }
  ],

  "categories": {
    "admin": {"icon": "📋", "color": "#3498db"},
    "insurance": {"icon": "💳", "color": "#2ecc71"},
    "consent": {"icon": "✍️", "color": "#9b59b6"},
    "records": {"icon": "📁", "color": "#e67e22"},
    "medical": {"icon": "🏥", "color": "#e74c3c"},
    "previsit": {"icon": "📝", "color": "#1abc9c"},
    "scheduling": {"icon": "📅", "color": "#34495e"}
  }
}
```

### 2. New Patient Request Schema

```json
// new_patients/np_2024001.json
{
  "request_id": "np_2024001",
  "created_at": "2024-12-09T10:30:00Z",
  "updated_at": "2024-12-09T14:22:00Z",

  "contact": {
    "first_name": "John",
    "last_name": "Smith",
    "phone": "555-123-4567",
    "email": "john.smith@email.com",
    "preferred_contact": "phone"
  },

  "request_details": {
    "referral_source": "Dr. Jones",
    "reason_for_visit": "Diabetes management, new to area",
    "urgency": "routine",
    "preferred_provider": "Dr. Green",
    "notes": "Moving from out of state, needs records transfer"
  },

  "status": {
    "current_stage": "verification",
    "assigned_to": "jane.doe@clinic.com",
    "last_contact_date": "2024-12-09",
    "next_action": "Call to verify insurance",
    "next_action_date": "2024-12-10"
  },

  "checklist": {
    "template_id": "onboarding_default",
    "template_version": "1.0",
    "items": {
      "registration_form": {
        "status": "completed",
        "completed_at": "2024-12-09T11:00:00Z",
        "completed_by": "jane.doe@clinic.com",
        "notes": null
      },
      "photo_id": {
        "status": "completed",
        "completed_at": "2024-12-09T11:05:00Z",
        "completed_by": "jane.doe@clinic.com"
      },
      "insurance_card": {
        "status": "in_progress",
        "notes": "Patient sending via email"
      },
      "eligibility_verified": {
        "status": "pending"
      },
      "hipaa_ack": {
        "status": "pending"
      }
      // ... other items with status
    }
  },

  "conversion": {
    "converted": false,
    "patient_id": null,
    "converted_at": null
  },

  "activity_log": [
    {
      "timestamp": "2024-12-09T10:30:00Z",
      "user": "system",
      "action": "created",
      "details": "New patient request created"
    },
    {
      "timestamp": "2024-12-09T11:00:00Z",
      "user": "jane.doe@clinic.com",
      "action": "item_completed",
      "details": "Completed: Patient Registration Form"
    },
    {
      "timestamp": "2024-12-09T14:22:00Z",
      "user": "jane.doe@clinic.com",
      "action": "stage_changed",
      "details": "Moved from 'application' to 'verification'"
    }
  ]
}
```

### 3. New Patient Index Schema

```json
// new_patients/index.json
{
  "last_updated": "2024-12-09T14:22:00Z",
  "next_id": 2024003,

  "requests": [
    {
      "request_id": "np_2024001",
      "name": "Smith, John",
      "stage": "verification",
      "assigned_to": "jane.doe@clinic.com",
      "created_at": "2024-12-09T10:30:00Z",
      "urgency": "routine",
      "progress_pct": 25
    },
    {
      "request_id": "np_2024002",
      "name": "Johnson, Mary",
      "stage": "inquiry",
      "assigned_to": null,
      "created_at": "2024-12-09T12:00:00Z",
      "urgency": "soon",
      "progress_pct": 0
    }
  ],

  "stats": {
    "by_stage": {
      "inquiry": 1,
      "application": 0,
      "verification": 1,
      "records": 0,
      "intake_prep": 0,
      "scheduled": 0
    },
    "total_active": 2,
    "avg_days_to_onboard": 7.5
  }
}
```

### 4. Patient Health Maintenance Schema

```json
// patient_checklists/by_patient/pt_12345/health_maint.json
{
  "patient_id": "pt_12345",
  "template_id": "health_maint_adult",
  "last_updated": "2024-12-09T00:00:00Z",

  "patient_context": {
    "age": 58,
    "sex": "F",
    "conditions": ["diabetes_t2", "hypertension"],
    "risk_factors": ["smoker_former", "family_hx_cad"]
  },

  "items": {
    "colonoscopy": {
      "name": "Colonoscopy",
      "category": "cancer_screening",
      "applicable": true,
      "frequency": "10 years (or 5 if polyps)",
      "last_completed": "2020-03-15",
      "next_due": "2030-03-15",
      "status": "current",
      "result": "Normal, no polyps",
      "notes": null
    },
    "mammogram": {
      "name": "Mammogram",
      "category": "cancer_screening",
      "applicable": true,
      "frequency": "annually",
      "last_completed": "2024-01-20",
      "next_due": "2025-01-20",
      "status": "current",
      "result": "BIRADS 1 - Negative"
    },
    "hba1c": {
      "name": "HbA1c",
      "category": "chronic_monitoring",
      "applicable": true,
      "frequency": "every 3-6 months",
      "last_completed": "2024-09-15",
      "next_due": "2024-12-15",
      "status": "due_soon",
      "result": "7.2%",
      "target": "<7.0%"
    },
    "eye_exam": {
      "name": "Diabetic Eye Exam",
      "category": "chronic_monitoring",
      "applicable": true,
      "frequency": "annually",
      "last_completed": "2023-06-01",
      "next_due": "2024-06-01",
      "status": "overdue",
      "notes": "Needs referral to ophthalmology"
    },
    "flu_vaccine": {
      "name": "Influenza Vaccine",
      "category": "immunizations",
      "applicable": true,
      "frequency": "annually (fall)",
      "last_completed": "2024-10-15",
      "next_due": "2025-10-01",
      "status": "current"
    },
    "shingles_vaccine": {
      "name": "Shingrix (Shingles)",
      "category": "immunizations",
      "applicable": true,
      "frequency": "2-dose series",
      "doses_needed": 2,
      "doses_received": 1,
      "last_completed": "2024-08-01",
      "next_due": "2024-10-01",
      "status": "series_incomplete"
    }
  },

  "care_gaps": [
    {
      "item_id": "eye_exam",
      "severity": "high",
      "days_overdue": 192,
      "recommended_action": "Schedule ophthalmology referral"
    },
    {
      "item_id": "shingles_vaccine",
      "severity": "medium",
      "days_overdue": 70,
      "recommended_action": "Schedule Shingrix dose 2"
    }
  ],

  "alerts": [
    {
      "type": "upcoming",
      "item_id": "hba1c",
      "message": "HbA1c due in 6 days",
      "action_needed": "Order lab"
    }
  ]
}
```

### 5. Visit Prep Checklist Schema

```json
// patient_checklists/by_visit/2024-12-15/visit_prep_pt_12345.json
{
  "visit_id": "v_2024121501",
  "patient_id": "pt_12345",
  "patient_name": "Smith, Jane",
  "visit_date": "2024-12-15",
  "visit_time": "09:30",
  "visit_type": "annual_wellness",
  "provider": "Dr. Green",

  "template_id": "visit_prep_awv",
  "created_at": "2024-12-08T08:00:00Z",
  "last_updated": "2024-12-14T16:30:00Z",

  "status": "ready",
  "completion_pct": 100,

  "items": {
    "eligibility_check": {
      "name": "Insurance Eligibility Verified",
      "status": "completed",
      "completed_at": "2024-12-08T09:00:00Z",
      "completed_by": "billing@clinic.com",
      "result": "Active, $25 copay"
    },
    "awv_eligibility": {
      "name": "AWV Eligibility Confirmed",
      "status": "completed",
      "completed_at": "2024-12-08T09:05:00Z",
      "completed_by": "billing@clinic.com",
      "result": "Last AWV: 2023-12-01, eligible"
    },
    "hra_sent": {
      "name": "Health Risk Assessment Sent",
      "status": "completed",
      "completed_at": "2024-12-08T10:00:00Z",
      "completed_by": "ma@clinic.com",
      "method": "patient_portal"
    },
    "hra_completed": {
      "name": "HRA Completed by Patient",
      "status": "completed",
      "completed_at": "2024-12-10T19:22:00Z",
      "completed_by": "patient",
      "notes": "Completed via portal"
    },
    "care_gaps_reviewed": {
      "name": "Care Gaps Identified",
      "status": "completed",
      "completed_at": "2024-12-14T15:00:00Z",
      "completed_by": "ma@clinic.com",
      "findings": ["Eye exam overdue", "Shingrix dose 2 needed"]
    },
    "labs_ordered": {
      "name": "Pre-Visit Labs Ordered",
      "status": "completed",
      "completed_at": "2024-12-08T10:30:00Z",
      "completed_by": "ma@clinic.com",
      "orders": ["CMP", "Lipid Panel", "HbA1c"]
    },
    "labs_resulted": {
      "name": "Labs Completed",
      "status": "completed",
      "completed_at": "2024-12-12T14:00:00Z",
      "notes": "All resulted, reviewed by provider"
    },
    "meds_reconciled": {
      "name": "Medication List Prepared",
      "status": "completed",
      "completed_at": "2024-12-14T16:30:00Z",
      "completed_by": "ma@clinic.com"
    }
  },

  "visit_summary": {
    "care_gaps_to_address": [
      "Diabetic eye exam - overdue 6 months",
      "Shingrix dose 2 - due"
    ],
    "pending_orders": [],
    "special_notes": "Patient requested refills during visit"
  }
}
```

### 6. Protocol Tracking Schema

```json
// patient_checklists/by_patient/pt_12345/protocols/diabetes.json
{
  "patient_id": "pt_12345",
  "protocol_id": "protocol_diabetes_t2",
  "protocol_name": "Type 2 Diabetes Management",
  "diagnosis_date": "2019-06-15",
  "last_updated": "2024-12-09T00:00:00Z",

  "current_phase": "ongoing_quarterly",

  "phases": {
    "initial_diagnosis": {
      "completed": true,
      "completed_date": "2019-07-15",
      "items": {
        "initial_hba1c": {"status": "completed", "date": "2019-06-15", "result": "8.2%"},
        "lipid_panel": {"status": "completed", "date": "2019-06-15"},
        "kidney_function": {"status": "completed", "date": "2019-06-15", "result": "eGFR 78"},
        "eye_exam_referral": {"status": "completed", "date": "2019-06-20"},
        "foot_exam": {"status": "completed", "date": "2019-06-15"},
        "diabetes_education": {"status": "completed", "date": "2019-07-01"},
        "nutrition_counseling": {"status": "completed", "date": "2019-07-10"},
        "medication_started": {"status": "completed", "date": "2019-06-15", "notes": "Metformin 500mg BID"}
      }
    },

    "ongoing_quarterly": {
      "last_completed_cycle": "2024-Q3",
      "current_cycle": "2024-Q4",
      "items": {
        "hba1c_check": {
          "status": "due",
          "last_date": "2024-09-15",
          "last_result": "7.2%",
          "target": "<7.0%",
          "next_due": "2024-12-15"
        },
        "medication_review": {
          "status": "pending",
          "last_date": "2024-09-15",
          "current_meds": ["Metformin 1000mg BID", "Jardiance 10mg daily"]
        },
        "hypoglycemia_assessment": {
          "status": "pending",
          "last_date": "2024-09-15",
          "last_result": "No episodes"
        },
        "foot_exam": {
          "status": "pending",
          "last_date": "2024-09-15"
        },
        "bp_check": {
          "status": "pending",
          "last_date": "2024-09-15",
          "last_result": "128/78"
        }
      }
    },

    "ongoing_annual": {
      "last_completed": "2024",
      "items": {
        "comprehensive_metabolic": {
          "status": "completed",
          "date": "2024-01-15"
        },
        "lipid_panel": {
          "status": "completed",
          "date": "2024-01-15",
          "result": "LDL 92"
        },
        "eye_exam": {
          "status": "overdue",
          "last_date": "2023-06-01",
          "days_overdue": 192
        },
        "dental_referral": {
          "status": "completed",
          "date": "2024-03-01"
        },
        "flu_vaccine": {
          "status": "completed",
          "date": "2024-10-15"
        }
      }
    }
  },

  "metrics_history": [
    {"date": "2024-09-15", "hba1c": 7.2, "weight": 185, "bp_sys": 128, "bp_dia": 78},
    {"date": "2024-06-15", "hba1c": 7.0, "weight": 182, "bp_sys": 124, "bp_dia": 76},
    {"date": "2024-03-15", "hba1c": 7.4, "weight": 188, "bp_sys": 132, "bp_dia": 82},
    {"date": "2023-12-15", "hba1c": 7.1, "weight": 184, "bp_sys": 126, "bp_dia": 78}
  ],

  "alerts": [
    {
      "severity": "high",
      "item": "eye_exam",
      "message": "Diabetic eye exam overdue by 6 months"
    },
    {
      "severity": "medium",
      "item": "hba1c_check",
      "message": "Quarterly HbA1c due in 6 days"
    }
  ]
}
```

---

## Sync Strategy

### Azure Blob Storage Structure

```
patient-explorer-data/
├── tracking/
│   ├── _templates/
│   ├── new_patients/
│   ├── patient_checklists/
│   └── completed/
```

### Conflict Resolution

For JSON files, use **last-write-wins** with these safeguards:

1. **Index files** (`index.json`): Regenerate from individual files on sync conflict
2. **Individual records**: Keep both versions, flag for manual review
3. **Templates**: Version-controlled, newer version wins

### Sync Triggers

```python
# In phase0/sync.py - extend existing sync patterns

TRACKING_SYNC_PATHS = [
    "data/tracking/_templates/",
    "data/tracking/new_patients/",
    "data/tracking/patient_checklists/",
]

# Add to .gitignore-sync.json
{
  "sync_paths": [
    "data/",
    "data/tracking/",  # Add tracking folder
    ".env",
    "logs/"
  ]
}
```

---

## UI Loading Pattern

```python
# Helper to load tracking data

import json
from pathlib import Path

TRACKING_DIR = Path("data/tracking")

def load_template(template_id: str) -> dict:
    """Load a checklist template."""
    path = TRACKING_DIR / "_templates" / f"{template_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None

def load_new_patient_index() -> dict:
    """Load the new patient request index."""
    path = TRACKING_DIR / "new_patients" / "index.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"requests": [], "stats": {}}

def load_new_patient_request(request_id: str) -> dict:
    """Load a specific new patient request."""
    path = TRACKING_DIR / "new_patients" / f"{request_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None

def save_new_patient_request(request_id: str, data: dict):
    """Save a new patient request and update index."""
    path = TRACKING_DIR / "new_patients" / f"{request_id}.json"
    path.write_text(json.dumps(data, indent=2, default=str))
    _rebuild_new_patient_index()

def load_patient_health_maint(patient_id: str) -> dict:
    """Load patient's health maintenance tracking."""
    path = TRACKING_DIR / "patient_checklists" / "by_patient" / patient_id / "health_maint.json"
    if path.exists():
        return json.loads(path.read_text())
    return None

def load_visit_prep(visit_date: str, patient_id: str) -> dict:
    """Load visit prep checklist."""
    path = TRACKING_DIR / "patient_checklists" / "by_visit" / visit_date / f"visit_prep_{patient_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None
```

---

## Benefits of This Approach

| Benefit | Description |
|---------|-------------|
| **Offline-first** | All data stored locally, works without connectivity |
| **Human-readable** | JSON files can be inspected/edited manually if needed |
| **Flexible schema** | Easy to add new fields without migrations |
| **Easy backup** | Just sync the folder to Azure |
| **Git-friendly** | Could version-control templates in git |
| **Multi-device** | Syncs via existing Azure Blob pattern |
| **Audit trail** | Activity logs embedded in each record |

## Trade-offs

| Trade-off | Mitigation |
|-----------|------------|
| **No queries** | Use index files for quick lookups |
| **Concurrent edits** | Last-write-wins with conflict flagging |
| **Large scale** | Archive completed records monthly |
| **Relationships** | Use ID references, load related files as needed |

---

## Next Steps

1. [ ] Create `data/tracking/` directory structure
2. [ ] Build template JSON files
3. [ ] Add tracking folder to sync manifest
4. [ ] Create `tracking_loader.py` helper module
5. [ ] Build `27_New_Patient_Requests.py` page
6. [ ] Test sync with Azure Blob

---

*Created: 2024-12-09*
*Status: Architecture Draft*
