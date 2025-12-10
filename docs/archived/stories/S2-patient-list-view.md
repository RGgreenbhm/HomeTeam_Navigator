# Story S2: Patient List View with Filtering

## Status
Draft

## Story
**As a** clinical user,
**I want** to see all patients in a filterable, searchable table,
**so that** I can quickly find and manage patient records.

## Acceptance Criteria
1. Table displays columns: MRN, Name, DOB, Phone, Email, Consent Status, Spruce Match
2. Search box filters by name or MRN
3. Filter dropdowns for: Consent Status, Spruce Match status
4. Pagination or infinite scroll for 1,383 patients
5. Click row to view patient details in sidebar/modal
6. Export filtered results to CSV
7. Shows aggregate statistics at top (total, matched, consented)

## Tasks / Subtasks
- [ ] Create Patient List page (AC: 1, 7)
  - [ ] Create app/pages/1_Patients.py
  - [ ] Add stats cards at top (total, matched, etc.)
  - [ ] Display patient data in st.dataframe or st.table
- [ ] Implement search and filters (AC: 2, 3)
  - [ ] Search input for name/MRN
  - [ ] Consent status multiselect
  - [ ] Spruce match checkbox
- [ ] Add pagination (AC: 4)
  - [ ] st.pagination or page numbers
  - [ ] 50 patients per page
- [ ] Create patient detail view (AC: 5)
  - [ ] Sidebar or expander for details
  - [ ] Show all patient fields
  - [ ] Link to consent editing
- [ ] Export functionality (AC: 6)
  - [ ] st.download_button for CSV
  - [ ] Include filtered data only

## Dev Notes

### Streamlit Data Display
```python
import streamlit as st
import pandas as pd
from database.connection import get_session
from database.models import Patient

st.title("🧑‍⚕️ Patients")

# Stats cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Patients", 1383)
with col2:
    st.metric("Spruce Matched", 1195, "86.4%")
with col3:
    st.metric("Consented", 0, "0%")
with col4:
    st.metric("Pending", 1383)

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    search = st.text_input("Search by name or MRN")
with col2:
    consent_filter = st.multiselect(
        "Consent Status",
        ["pending", "consented", "declined", "unreachable"]
    )
with col3:
    spruce_only = st.checkbox("Spruce matched only")

# Data table
df = load_patients(search, consent_filter, spruce_only)
st.dataframe(df, use_container_width=True)

# Export
st.download_button(
    "📥 Export to CSV",
    df.to_csv(index=False),
    "patients.csv",
    "text/csv"
)
```

### Patient Detail Sidebar
```python
# When row selected
with st.sidebar:
    st.subheader(f"{patient.last_name}, {patient.first_name}")
    st.write(f"**MRN:** {patient.mrn}")
    st.write(f"**DOB:** {patient.date_of_birth}")
    st.write(f"**Phone:** {patient.phone}")
    st.write(f"**Email:** {patient.email}")
    st.write(f"**Spruce ID:** {patient.spruce_id or 'Not matched'}")

    st.divider()
    if st.button("Edit Consent"):
        st.session_state.edit_patient = patient.id
```

## Testing
- **Location**: `tests/ui/`
- **Framework**: pytest + Streamlit testing
- **Required Tests**:
  - Table renders with patient data
  - Search filters correctly
  - Export produces valid CSV

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story | Claude |

---

## Dev Agent Record
### Agent Model Used
### Debug Log References
### Completion Notes
### File List

---

## QA Results
