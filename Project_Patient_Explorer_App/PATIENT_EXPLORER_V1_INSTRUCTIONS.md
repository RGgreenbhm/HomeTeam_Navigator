# Patient Explorer V1.0 - Implementation Instructions for Claude Code

**Date**: December 8, 2025  
**Days to Deadline**: 23 (December 31, 2025)  
**Priority**: CRITICAL - Patient outreach campaign must launch immediately

---

## Executive Summary

This document provides instructions for updating the Patient Explorer Streamlit application to Version 1.0. The goal is to create a working patient chart explorer that:

1. Consolidates patient data from Spruce Health API and Excel files
2. Stores consolidated patient records in Azure Blob Storage (not local `data/` folder)
3. Provides an interactive chart-like interface inspired by athenaOne EMR
4. Uses custom navigation icons (provided)
5. Supports patient tagging, screenshot capture, and report generation
6. Integrates with **Plaud** for HIPAA-compliant clinical encounter transcriptions
7. Supports **Microsoft Forms** for patient consent collection with token tracking

**THIS IS A VERSION 1.0** - Focus on core functionality with the existing data sources.

### What's IN Scope for V1.0
- Patient data consolidation (Excel + Spruce API)
- Azure Blob Storage for data sync
- Interactive patient chart UI with navigation icons
- Screenshot capture and categorization
- Consent form integration (Microsoft Forms + tokens)
- Plaud webhook receiver for transcripts (design ready, awaiting API access)

### What's DEFERRED to V1.1+
- OneNote notebook ingestion
- SharePoint document publishing
- Teams meeting transcripts (using Plaud + OpenEvidence instead)
- Complex Microsoft OAuth flows

---

## Current Data Sources (V1.0 Scope)

### 1. Spruce Health API
- **Endpoint**: `https://api.sprucehealth.com/v1/contacts`
- **Authentication**: Bearer token via `SPRUCE_API_TOKEN` environment variable
- **Data Available**: Patient name, phone, email, tags, Spruce ID
- **Existing Code**: `phase0/spruce/client.py`

### 2. Excel Patient Lists (in `data/` folder)
- **Total Green Clinic Patient List**: ~1,384 patients
  - Columns: MRN, DOB, Patient Name, Address, City, State, Zip, Last Date of Service, Email, Home Phone, Cell Phone
  
- **APCM Patient Subset**: ~450 patients with APCM enrollment data
  - Additional columns: APCM Level (G0556/G0557/G0558), ICD Codes, Enrollment Date, Status

### 3. Existing SQLite Database
- **Location**: `data/patients.db`
- **Models**: See `app/database/models.py`
- **Key Tables**: patients, consents, captures, audit_logs

---

## Target Architecture

### Storage Strategy
```
Azure Blob Storage (stgreenclinicworkspace)
├── workspace-sync/
│   ├── patients.db              # SQLite database (synced)
│   ├── .env                     # Credentials (encrypted)
│   └── logs/                    # Audit logs
└── patient-data/                # NEW: Consolidated patient JSON
    ├── patients_master.json     # Master patient list
    ├── screenshots/             # Screenshot captures by patient
    │   └── {patient_id}/
    └── reports/                 # Generated reports
```

### JSON Schema: Master Patient Record

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PatientMasterRecord",
  "type": "object",
  "required": ["id", "demographics", "metadata"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique patient identifier (UUID)"
    },
    "demographics": {
      "type": "object",
      "required": ["first_name", "last_name", "date_of_birth"],
      "properties": {
        "first_name": { "type": "string" },
        "last_name": { "type": "string" },
        "date_of_birth": { "type": "string", "format": "date" },
        "gender": { "type": "string", "enum": ["male", "female", "other", "unknown"] },
        "mrn": { "type": "string", "description": "Medical Record Number from Allscripts" },
        "phone_home": { "type": "string" },
        "phone_cell": { "type": "string" },
        "email": { "type": "string", "format": "email" },
        "address": {
          "type": "object",
          "properties": {
            "line1": { "type": "string" },
            "line2": { "type": "string" },
            "city": { "type": "string" },
            "state": { "type": "string", "maxLength": 2 },
            "zip": { "type": "string" }
          }
        }
      }
    },
    "identifiers": {
      "type": "object",
      "properties": {
        "spruce_id": { "type": "string", "description": "Spruce Health contact ID" },
        "athena_id": { "type": "string", "description": "Future: Athena One patient ID" },
        "allscripts_mrn": { "type": "string", "description": "Legacy Allscripts MRN" }
      }
    },
    "insurance": {
      "type": "object",
      "properties": {
        "primary_provider": { "type": "string" },
        "primary_member_id": { "type": "string" },
        "secondary_provider": { "type": "string" },
        "secondary_member_id": { "type": "string" },
        "medicare_part_b": { "type": "boolean" },
        "qmb_status": { "type": "boolean", "description": "Qualified Medicare Beneficiary" }
      }
    },
    "apcm": {
      "type": "object",
      "description": "Advanced Primary Care Management enrollment",
      "properties": {
        "enrolled": { "type": "boolean" },
        "enrolled_date": { "type": "string", "format": "date" },
        "level": { 
          "type": "string", 
          "enum": ["G0556", "G0557", "G0558"],
          "description": "G0556=1 condition, G0557=2+ conditions, G0558=2+ with QMB"
        },
        "icd_codes": { 
          "type": "array", 
          "items": { "type": "string" },
          "description": "Qualifying ICD-10 codes"
        },
        "status": { 
          "type": "string", 
          "enum": ["active", "pending", "removed", "hold"] 
        },
        "continue_ht": { 
          "type": "boolean", 
          "description": "Patient elected to continue APCM with Home Team" 
        },
        "revoke_sv": { 
          "type": "boolean", 
          "description": "Patient authorized Southview billing revocation" 
        }
      }
    },
    "consent": {
      "type": "object",
      "properties": {
        "status": { 
          "type": "string", 
          "enum": ["pending", "outreach_sent", "consented", "declined", "unreachable"] 
        },
        "method": { 
          "type": "string", 
          "enum": ["spruce", "phone", "mail", "in_person", "docusign", "microsoft_forms"] 
        },
        "consent_date": { "type": "string", "format": "date-time" },
        "token": { "type": "string", "description": "Unique consent form token" },
        "token_expires": { "type": "string", "format": "date-time" }
      }
    },
    "tags": {
      "type": "object",
      "description": "Standardized Spruce tags for patient categorization",
      "properties": {
        "team": {
          "type": "array",
          "items": { 
            "type": "string", 
            "enum": ["team_green", "team_lachandra", "team_lindsay"] 
          }
        },
        "loc": {
          "type": "string",
          "enum": ["loc_il", "loc_al", "loc_mc", "loc_office", "loc_home"],
          "description": "Level of Care: IL=Independent, AL=Assisted, MC=Memory Care"
        },
        "status": {
          "type": "array",
          "items": { 
            "type": "string", 
            "enum": ["apcm", "consent_pending", "high_priority", "new_patient"] 
          }
        },
        "custom": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "clinical": {
      "type": "object",
      "description": "Clinical summary data (populated from screenshots/OneNote)",
      "properties": {
        "problems": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "description": { "type": "string" },
              "icd10": { "type": "string" },
              "status": { "type": "string", "enum": ["active", "resolved", "inactive"] },
              "onset_date": { "type": "string", "format": "date" }
            }
          }
        },
        "medications": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "dosage": { "type": "string" },
              "frequency": { "type": "string" },
              "prescriber": { "type": "string" },
              "start_date": { "type": "string", "format": "date" },
              "active": { "type": "boolean" }
            }
          }
        },
        "allergies": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "allergen": { "type": "string" },
              "reaction": { "type": "string" },
              "severity": { "type": "string", "enum": ["mild", "moderate", "severe"] }
            }
          }
        },
        "vitals_latest": {
          "type": "object",
          "properties": {
            "date": { "type": "string", "format": "date" },
            "blood_pressure": { "type": "string" },
            "heart_rate": { "type": "integer" },
            "weight_lbs": { "type": "number" },
            "bmi": { "type": "number" }
          }
        }
      }
    },
    "encounters": {
      "type": "array",
      "description": "Visit history from screenshots/OneNote",
      "items": {
        "type": "object",
        "properties": {
          "date": { "type": "string", "format": "date" },
          "type": { "type": "string", "enum": ["office_visit", "telehealth", "home_visit", "phone_call"] },
          "provider": { "type": "string" },
          "chief_complaint": { "type": "string" },
          "assessment": { "type": "string" },
          "source": { "type": "string", "description": "Where this data came from" }
        }
      }
    },
    "screenshots": {
      "type": "array",
      "description": "References to captured screenshots",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "category": { 
            "type": "string", 
            "enum": [
              "demographics", "face_sheet", "encounters", "scheduling",
              "medications", "allergies", "problems", "vitals",
              "labs", "imaging", "procedures", "care_plan",
              "aledade_hcc", "aledade_gaps", "insurance", "billing"
            ]
          },
          "source": { "type": "string", "enum": ["allscripts", "athena", "aledade", "onenote", "other"] },
          "capture_date": { "type": "string", "format": "date-time" },
          "azure_blob_path": { "type": "string" },
          "ocr_text": { "type": "string" },
          "notes": { "type": "string" }
        }
      }
    },
    "communications": {
      "type": "array",
      "description": "Spruce communication log",
      "items": {
        "type": "object",
        "properties": {
          "date": { "type": "string", "format": "date-time" },
          "type": { "type": "string", "enum": ["sms", "call", "secure_message", "fax"] },
          "direction": { "type": "string", "enum": ["inbound", "outbound"] },
          "summary": { "type": "string" },
          "spruce_conversation_id": { "type": "string" }
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["created_at", "updated_at"],
      "properties": {
        "created_at": { "type": "string", "format": "date-time" },
        "updated_at": { "type": "string", "format": "date-time" },
        "created_by": { "type": "string" },
        "last_modified_by": { "type": "string" },
        "data_sources": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Where this record's data originated"
        },
        "match_confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Confidence score for Spruce matching"
        }
      }
    }
  }
}
```

---

## Navigation Interface Design

### Left Navigation Bar Icons

Map the provided icons to these navigation sections:

| Icon File | Section | Description |
|-----------|---------|-------------|
| `HTnav_search.png` | Patient Search | Search and find patients |
| `HTnav_team.png` | Care Team | View by team assignment |
| `HTnav_stethoscope.png` | Encounters | Visit history |
| `HTnav_Rx_bottle.png` | Medications | Current medications |
| `HTnav_Problem_List.png` | Problems | Problem list / diagnoses |
| `HTnav_syringe.png` | Immunizations | Immunization records |
| `HTnav_beaker_icon.png` | Labs | Lab results |
| `HTnav_xray.png` | Imaging | Radiology/imaging |
| `HTnav_vitals.png` | Vitals | Vital signs |
| `HTnav_allergies.png` | Allergies | Allergy list |
| `HTnav_clipboard.png` | Care Plans | Care plan documents |
| `HTnav_medical_bag.png` | Visit Summary | Summary view |
| `HTnav_folder.png` | Documents | Screenshots/captures |
| `HTnav_phone.png` | Communications | Spruce messages |
| `HTnav_cellphone.png` | SMS/Text | Text messaging |
| `HTnav_invoice.png` | Billing | Billing/insurance |
| `HTnav_ribbon.png` | Quality | HCC codes, quality measures |
| `HTnav_payclock.png` | Scheduling | Appointments |

### Feature Images

| Image File | Usage |
|------------|-------|
| `Image_medical_records_cartoon.png` | Charts/Records section header |
| `Image_patient_onboarding.png` | New patient intake workflow |
| `Image_population_explorer.png` | Population health analytics |
| `InfoGraphic_Home_Team_Logic.png` | AI/Auto-pilot explanation |
| `InfoGraphic_Auto_Pilot_infographic_cartoonstyle_image.png` | Workflow automation |

### Progressive Disclosure UI Pattern

Follow athenaOne's navigation pattern:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ HEADER BAR                                                                │
│ [Patient Name] [DOB] [MRN] [Tags: apcm, team_green, loc_al]  [Actions ▼]│
├─────────┬────────────────────────────────────────────────────────────────┤
│ NAV     │ FLYOUT RIBBON          │ MAIN WORKSPACE                        │
│ ─────── │ ─────────────────────  │ ─────────────────────────────────     │
│ [🔍]   │                        │                                        │
│ [👥]   │ When nav icon clicked: │  Full content view of selected item   │
│ [🩺]   │ - Show sub-items       │                                        │
│ [💊]   │ - Allow selection      │  Example: Full medication list with   │
│ [📋]   │ - Filter options       │  dosage, frequency, prescriber,       │
│ [💉]   │                        │  start date, refill status            │
│ [🧪]   │ Example (Medications): │                                        │
│ [📁]   │ > Active (12)          │                                        │
│ [📞]   │ > Discontinued (5)     │                                        │
│ [💵]   │ > PRN (3)              │                                        │
│        │                        │                                        │
└─────────┴────────────────────────┴────────────────────────────────────────┘
```

---

## Implementation Tasks

### Phase 1: Data Consolidation Service

Create `app/services/patient_consolidator.py`:

```python
"""
Patient data consolidation service.
Merges data from Spruce API and Excel files into unified JSON records.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

from phase0.spruce.client import SpruceClient

class PatientConsolidator:
    """Consolidates patient data from multiple sources."""
    
    def __init__(self, excel_path: str, apcm_excel_path: str):
        self.excel_path = excel_path
        self.apcm_excel_path = apcm_excel_path
        self.spruce_client = SpruceClient()
        self.master_records: Dict[str, Dict] = {}
    
    def load_excel_patients(self) -> pd.DataFrame:
        """Load main patient list from Excel."""
        # Implement Excel loading with column mapping
        pass
    
    def load_apcm_patients(self) -> pd.DataFrame:
        """Load APCM patient subset with enrollment data."""
        pass
    
    def fetch_spruce_contacts(self) -> List[Dict]:
        """Fetch all contacts from Spruce API."""
        return self.spruce_client.get_all_contacts()
    
    def match_patient_to_spruce(
        self, 
        patient: Dict, 
        spruce_contacts: List[Dict]
    ) -> Optional[Dict]:
        """
        Match patient to Spruce contact using:
        1. Phone number (primary)
        2. Name + DOB (secondary)
        3. Email (tertiary)
        """
        pass
    
    def create_master_record(
        self, 
        excel_data: Dict, 
        apcm_data: Optional[Dict],
        spruce_data: Optional[Dict]
    ) -> Dict:
        """Create unified patient record from all sources."""
        record = {
            "id": str(uuid.uuid4()),
            "demographics": {
                "first_name": excel_data.get("first_name"),
                "last_name": excel_data.get("last_name"),
                "date_of_birth": excel_data.get("dob"),
                # ... map all fields
            },
            "identifiers": {
                "spruce_id": spruce_data.get("id") if spruce_data else None,
                "allscripts_mrn": excel_data.get("mrn"),
            },
            "apcm": self._build_apcm_section(apcm_data) if apcm_data else None,
            "tags": self._build_tags(excel_data, apcm_data, spruce_data),
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "data_sources": ["excel", "spruce"] if spruce_data else ["excel"],
            }
        }
        return record
    
    def consolidate_all(self) -> List[Dict]:
        """Run full consolidation pipeline."""
        excel_df = self.load_excel_patients()
        apcm_df = self.load_apcm_patients()
        spruce_contacts = self.fetch_spruce_contacts()
        
        records = []
        for _, excel_row in excel_df.iterrows():
            # Find matching APCM data
            apcm_data = self._find_apcm_match(excel_row, apcm_df)
            
            # Find matching Spruce contact
            spruce_data = self.match_patient_to_spruce(
                excel_row.to_dict(), spruce_contacts
            )
            
            # Create consolidated record
            record = self.create_master_record(
                excel_row.to_dict(), apcm_data, spruce_data
            )
            records.append(record)
        
        return records
    
    def save_to_json(self, records: List[Dict], output_path: str):
        """Save consolidated records to JSON file."""
        with open(output_path, 'w') as f:
            json.dump({"patients": records, "updated_at": datetime.utcnow().isoformat()}, f, indent=2)
```

### Phase 2: Azure Storage Integration

Update `phase0/azure_sync.py` to support patient data:

```python
def sync_patient_data(self, local_path: str, container: str = "patient-data"):
    """Sync patient JSON and screenshots to Azure."""
    # Upload patients_master.json
    # Upload screenshots folder
    # Return sync status
    pass

def download_patient_data(self, local_path: str, container: str = "patient-data"):
    """Download patient data from Azure."""
    pass
```

### Phase 3: Patient Explorer UI

Create `app/pages/20_Patient_Explorer.py`:

```python
"""
Patient Explorer - Interactive Chart View
Version 1.0
"""

import streamlit as st
import json
from pathlib import Path

# Custom CSS for athenaOne-style navigation
def load_custom_css():
    st.markdown("""
    <style>
    /* Left navigation bar */
    .nav-sidebar {
        position: fixed;
        left: 0;
        top: 60px;
        width: 60px;
        height: calc(100vh - 60px);
        background: #1a365d;
        padding: 10px 0;
    }
    
    .nav-icon {
        width: 40px;
        height: 40px;
        margin: 5px auto;
        cursor: pointer;
        opacity: 0.7;
        transition: opacity 0.2s;
    }
    
    .nav-icon:hover {
        opacity: 1;
    }
    
    .nav-icon.active {
        opacity: 1;
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
    }
    
    /* Flyout ribbon */
    .flyout-ribbon {
        position: fixed;
        left: 60px;
        top: 60px;
        width: 200px;
        height: calc(100vh - 60px);
        background: #2d3748;
        padding: 15px;
        display: none;
    }
    
    .flyout-ribbon.active {
        display: block;
    }
    
    /* Main workspace */
    .main-workspace {
        margin-left: 260px;
        padding: 20px;
    }
    
    /* Patient header */
    .patient-header {
        background: linear-gradient(135deg, #1a365d 0%, #2d3748 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    .patient-tags {
        display: flex;
        gap: 8px;
        margin-top: 10px;
    }
    
    .patient-tag {
        background: rgba(255,255,255,0.2);
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

def render_patient_header(patient: dict):
    """Render patient header bar with tags."""
    demo = patient.get("demographics", {})
    tags = patient.get("tags", {})
    
    st.markdown(f"""
    <div class="patient-header">
        <h2>{demo.get('last_name', '')}, {demo.get('first_name', '')}</h2>
        <div>DOB: {demo.get('date_of_birth', '')} | MRN: {patient.get('identifiers', {}).get('allscripts_mrn', 'N/A')}</div>
        <div class="patient-tags">
            {render_tags(tags)}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_navigation():
    """Render left navigation with icons."""
    nav_items = [
        ("search", "Patient Search", "HTnav_search.png"),
        ("team", "Care Team", "HTnav_team.png"),
        ("encounters", "Encounters", "HTnav_stethoscope.png"),
        ("medications", "Medications", "HTnav_Rx_bottle.png"),
        ("problems", "Problems", "HTnav_Problem_List.png"),
        ("labs", "Labs", "HTnav_beaker_icon.png"),
        ("vitals", "Vitals", "HTnav_vitals.png"),
        ("allergies", "Allergies", "HTnav_allergies.png"),
        ("documents", "Documents", "HTnav_folder.png"),
        ("communications", "Communications", "HTnav_phone.png"),
    ]
    
    # Use Streamlit columns or custom HTML for navigation
    pass

def main():
    st.set_page_config(
        page_title="Patient Explorer",
        page_icon="🏥",
        layout="wide"
    )
    
    load_custom_css()
    
    # Load patient data
    patients = load_patients_from_json()
    
    # Patient search/select
    selected_patient = patient_selector(patients)
    
    if selected_patient:
        render_patient_header(selected_patient)
        render_navigation()
        render_main_content(selected_patient)

if __name__ == "__main__":
    main()
```

### Phase 4: Screenshot Capture Module

Create `app/services/screenshot_capture.py`:

```python
"""
Screenshot capture and categorization service.
Allows manual screenshot upload with category tagging.
"""

import streamlit as st
from datetime import datetime
import base64
from pathlib import Path

SCREENSHOT_CATEGORIES = [
    "demographics",
    "face_sheet", 
    "encounters",
    "scheduling",
    "medications",
    "allergies",
    "problems",
    "vitals",
    "labs",
    "imaging",
    "procedures",
    "care_plan",
    "aledade_hcc",
    "aledade_gaps",
    "insurance",
    "billing"
]

SCREENSHOT_SOURCES = ["allscripts", "athena", "aledade", "onenote", "other"]

def capture_screenshot_ui(patient_id: str):
    """UI component for screenshot upload and categorization."""
    
    st.subheader("📸 Capture Screenshot")
    
    uploaded_file = st.file_uploader(
        "Upload screenshot",
        type=["png", "jpg", "jpeg"],
        key=f"screenshot_{patient_id}"
    )
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Category",
                options=SCREENSHOT_CATEGORIES,
                key=f"cat_{patient_id}"
            )
            
            source = st.selectbox(
                "Source",
                options=SCREENSHOT_SOURCES,
                key=f"src_{patient_id}"
            )
        
        with col2:
            notes = st.text_area(
                "Notes",
                placeholder="Optional notes about this screenshot...",
                key=f"notes_{patient_id}"
            )
        
        if st.button("Save Screenshot", key=f"save_{patient_id}"):
            # Save to Azure Blob Storage
            # Update patient record
            # Return success
            pass
```

---

## Spruce Tag Standardization

### Tag Categories for Spruce Contacts

Implement these standardized tags in Spruce for patient categorization:

#### Team Assignment
- `team_green` - Dr. Green's patients
- `team_lachandra` - NP LaChandra's patients  
- `team_lindsay` - NP Lindsay's patients
- `team_jenny` - RN Jenny's assigned patients

#### Level of Care (Living Arrangement)
- `loc_il` - Independent Living
- `loc_al` - Assisted Living
- `loc_mc` - Memory Care
- `loc_office` - Clinic visits only
- `loc_home` - Home visits

#### Status Flags
- `apcm` - APCM enrolled
- `consent_pending` - Awaiting consent response
- `consent_obtained` - Consent received
- `high_priority` - Needs immediate attention
- `new_patient` - New to practice
- `transition_complete` - Fully transitioned to Home Team

#### Communication Preferences
- `prefer_sms` - Prefers text messages
- `prefer_call` - Prefers phone calls
- `family_contact` - Contact family member instead

---

## Testing Checklist

Before deploying V1.0:

- [ ] Excel import loads all 1,384 patients correctly
- [ ] APCM data merges with ~450 patients
- [ ] Spruce matching achieves >90% match rate
- [ ] JSON export generates valid schema
- [ ] Azure sync uploads/downloads correctly
- [ ] Navigation icons display properly
- [ ] Patient search returns correct results
- [ ] Screenshot upload saves to Azure
- [ ] Tags display and filter correctly
- [ ] Works on both Dr. Green's and Jenny's machines

---

## Environment Variables Required

```env
# Spruce Health API
SPRUCE_API_TOKEN=your_base64_token
SPRUCE_ACCESS_ID=your_access_id

# Azure Storage
AZURE_STORAGE_ACCOUNT=stgreenclinicworkspace
AZURE_STORAGE_CONTAINER=workspace-sync
AZURE_TENANT_ID=your_tenant_id

# Microsoft OAuth (for future OneNote integration)
MS_CLIENT_ID=your_client_id
MS_CLIENT_SECRET=your_client_secret
MS_TENANT_ID=southviewteam.com
MS_REDIRECT_URI=http://localhost:8501/callback

# Database
DATABASE_PATH=data/patients.db
```

---

## File Structure After Implementation

```
Patient_Explorer/
├── app/
│   ├── pages/
│   │   ├── 20_Patient_Explorer.py      # NEW: Main explorer view
│   │   ├── 21_Screenshot_Capture.py    # NEW: Screenshot upload
│   │   └── 22_Population_View.py       # NEW: Population analytics
│   ├── services/
│   │   ├── patient_consolidator.py     # NEW: Data consolidation
│   │   └── screenshot_capture.py       # NEW: Screenshot handling
│   └── assets/
│       └── icons/                      # Copy navigation icons here
│           ├── HTnav_search.png
│           ├── HTnav_team.png
│           └── ... (all icons)
├── phase0/
│   └── azure_sync.py                   # UPDATED: Add patient-data sync
└── data/
    └── patients_master.json            # Generated consolidated data
```

---

## Immediate Next Steps for Claude Code Agent

1. **Create `app/services/patient_consolidator.py`** with full implementation
2. **Update `phase0/azure_sync.py`** to support patient-data container
3. **Create `app/pages/20_Patient_Explorer.py`** with navigation framework
4. **Copy icons** to `app/assets/icons/` directory
5. **Create Streamlit component** for navigation bar with icons
6. **Implement patient search** functionality
7. **Add screenshot capture** UI and Azure upload
8. **Test data consolidation** with sample Excel files
9. **Run sync** to verify Azure integration

---

## Questions for User (Robert)

1. **Excel Column Names**: What are the exact column headers in your Excel files?
2. **Spruce Matching Priority**: Should phone matching take priority over name matching?
3. **Default Team Assignment**: If a patient has no team tag, default to `team_green`?
4. **Screenshot Storage**: Local first then sync, or direct Azure upload?

---

*Document Version: 1.0*  
*Created: December 8, 2025*  
*For: Home Team Medical Services - Patient Explorer App*  
*Target: Claude Code Agent in Patient_Explorer Repository*

---

## Recording/Transcription Integration

### Primary Solution: Plaud + OpenEvidence

**Replacing Microsoft Teams for telehealth and recordings:**

| Use Case | Solution | Status |
|----------|----------|--------|
| **In-Person Recording** | Plaud AI device | ✅ In use |
| **Transcription** | Plaud cloud (HIPAA) | ✅ In use |
| **Video Visits** | OpenEvidence (HIPAA) | ✅ Available |
| **Transcript Ingestion** | Plaud webhooks → Patient Explorer | 🔜 Design ready |

### Plaud Webhook Integration

See companion document: `PLAUD_WEBHOOK_INTEGRATION_SPEC.md`

**Key Components:**

1. **Webhook Receiver** (Azure Function or Streamlit endpoint)
   - Receives `audio_transcribe.completed` events
   - Verifies signature with `PLAUD_WEBHOOK_SECRET`
   - Filters by `@greenclinicteam.com` domain

2. **Transcript Storage**
   - Save to Azure Blob: `patient-data/transcripts/{file_id}.json`
   - Include: transcript text, segments with speakers, AI summary, action items

3. **Patient Matching**
   - Strategy 1: Parse patient name from recording title
   - Strategy 2: Match by scheduled appointment time
   - Strategy 3: Manual matching in UI

4. **Environment Variables**
```env
PLAUD_CLIENT_ID=your_client_id
PLAUD_CLIENT_SECRET_KEY=your_secret_key
PLAUD_WEBHOOK_SECRET=your_webhook_signing_secret
PLAUD_COMPANY_DOMAIN=greenclinicteam.com
```

### Transcript Data Structure

When matched to a patient, add to their record:

```json
{
  "transcripts": [
    {
      "id": "file_abc123",
      "source": "plaud",
      "recorded_at": "2025-12-08T14:00:00Z",
      "recorded_by": "drgreen@greenclinicteam.com",
      "duration_seconds": 1847,
      "azure_blob_path": "transcripts/file_abc123.json",
      "summary": "45-year-old male presents with...",
      "key_points": ["Chest pain x 3 days", "EKG ordered"],
      "action_items": ["Schedule stress test", "Follow up 1 week"],
      "matched_at": "2025-12-08T15:00:00Z"
    }
  ]
}
```

---

## Consent Form Integration

### Microsoft Forms with Token Tracking

**Workflow:**
1. Form URL stored in app configuration
2. Generate unique token per patient (`consent_tokens.py`)
3. Append token to form URL: `https://forms.microsoft.com/r/abc123?token=PATIENT_TOKEN`
4. Send via Spruce SMS
5. Patient completes form
6. Export responses from Forms
7. Bulk import to Patient Explorer, matching by token

**Existing Code:**
- `app/consent_tokens.py` - Token generation
- `app/pages/11_Consent_Response.py` - Response processing
- `app/pages/4_Outreach_Campaign.py` - Campaign management

**Configuration Storage:**
```python
# Store in settings or .env
CONSENT_FORM_URL=https://forms.microsoft.com/r/YOUR_FORM_ID
CONSENT_TOKEN_EXPIRY_DAYS=30
```

**New Feature: Form Configuration Page**

Add to `app/pages/30_Settings.py`:
```python
st.subheader("Consent Form Configuration")

form_url = st.text_input(
    "Microsoft Forms URL",
    value=st.session_state.get('consent_form_url', ''),
    help="The shareable URL from Microsoft Forms"
)

if st.button("Save Form URL"):
    save_setting('consent_form_url', form_url)
    st.success("Form URL saved!")

# Preview generated link
st.write("**Example Patient Link:**")
sample_token = "ABC123XYZ"
st.code(f"{form_url}?token={sample_token}")
```

---

## Revised Implementation Phases

### Phase 1: Data Consolidation (Priority 1)
- [ ] Create `patient_consolidator.py` service
- [ ] Load Excel patient lists
- [ ] Fetch Spruce contacts via API
- [ ] Match patients to Spruce contacts
- [ ] Generate consolidated `patients_master.json`
- [ ] Upload to Azure Blob Storage

### Phase 2: Patient Explorer UI (Priority 2)
- [ ] Create navigation component with icons
- [ ] Build patient search page
- [ ] Implement patient header with tags
- [ ] Create section views (medications, problems, etc.)
- [ ] Add screenshot capture UI

### Phase 3: Consent Integration (Priority 3)
- [ ] Add Form URL configuration page
- [ ] Ensure token generation works with form
- [ ] Test response import workflow
- [ ] Create consent status dashboard

### Phase 4: Plaud Integration (Priority 4 - Awaiting Access)
- [ ] Deploy Azure Function for webhook receiver
- [ ] Create Plaud Transcripts page in Streamlit
- [ ] Implement patient matching UI
- [ ] Add transcripts to patient records

---

## Removed from V1.0 (Microsoft Complexity)

The following Microsoft integrations have been **removed** from V1.0 scope due to complexity and deprecation issues:

| Feature | Reason | Alternative |
|---------|--------|-------------|
| Azure AD App Registration | OneNote app-only auth deprecated March 2025 | Using existing user auth |
| Teams Transcript Access | Requires complex Application Access Policy | Plaud for recordings |
| PowerShell policies | Additional IT complexity | Plaud webhooks |
| OneNote ingestion | Requires delegated OAuth | Deferred to V1.1 |
| SharePoint publishing | Not critical for V1.0 | Deferred to V1.1 |

**What STAYS:**
- Microsoft Forms (already working, no complex auth)
- Azure Blob Storage (already configured)
- Basic Microsoft user login (already working)

---

*Document Updated: December 8, 2025*
*Version: 1.0.1 - Added Plaud integration, removed MS complexity*
