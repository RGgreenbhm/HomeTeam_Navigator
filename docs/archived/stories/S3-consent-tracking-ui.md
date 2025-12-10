# Story S3: Consent Tracking Dashboard and Forms

## Status
Draft

## Story
**As a** clinical staff member,
**I want** to update patient consent status with tracking details,
**so that** we have documented consent for record retention.

## Acceptance Criteria
1. Dashboard shows consent status breakdown (pie chart or metrics)
2. Quick-update form for changing consent status
3. Track consent method (Spruce, phone, mail, in-person, DocuSign)
4. Record outreach date, response date, consent date
5. Add notes field for each consent record
6. Bulk update consent status for multiple patients
7. Filter patient list by consent status

## Tasks / Subtasks
- [ ] Create Consent Dashboard page (AC: 1)
  - [ ] Create app/pages/2_Consent.py
  - [ ] Add metrics: pending, consented, declined, unreachable
  - [ ] Add pie chart or progress bar
- [ ] Create consent form component (AC: 2, 3, 4, 5)
  - [ ] Status dropdown (pending, consented, declined, unreachable)
  - [ ] Method dropdown (spruce, phone, mail, in_person, docusign)
  - [ ] Date pickers for outreach/response/consent dates
  - [ ] Notes text area
  - [ ] Save button with database update
- [ ] Patient selection for consent update (AC: 7)
  - [ ] Search/select patient
  - [ ] Show current consent status
  - [ ] Display patient details in context
- [ ] Bulk update functionality (AC: 6)
  - [ ] Checkbox selection in patient table
  - [ ] "Update Selected" button
  - [ ] Bulk status change form

## Dev Notes

### Consent Dashboard Layout
```python
import streamlit as st
import plotly.express as px

st.title("📋 Consent Tracking")

# Metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Pending", 1200, delta="-50 this week")
with col2:
    st.metric("Consented", 150, delta="+30 this week")
with col3:
    st.metric("Declined", 20)
with col4:
    st.metric("Unreachable", 13)

# Progress bar
progress = consented / total
st.progress(progress, text=f"{progress*100:.1f}% Complete")

# Status breakdown chart
fig = px.pie(
    names=["Pending", "Consented", "Declined", "Unreachable"],
    values=[1200, 150, 20, 13],
    title="Consent Status Distribution"
)
st.plotly_chart(fig)
```

### Consent Update Form
```python
st.subheader("Update Consent")

# Patient selection
patient_id = st.selectbox(
    "Select Patient",
    options=get_patients(),
    format_func=lambda p: f"{p.last_name}, {p.first_name} (MRN: {p.mrn})"
)

# Current status display
current = get_consent(patient_id)
st.info(f"Current Status: {current.status or 'Not set'}")

# Update form
with st.form("consent_form"):
    status = st.selectbox(
        "New Status",
        ["pending", "outreach_sent", "consented", "declined", "unreachable"]
    )
    method = st.selectbox(
        "Consent Method",
        ["spruce", "phone", "mail", "in_person", "docusign", "n/a"]
    )
    outreach_date = st.date_input("Outreach Date")
    consent_date = st.date_input("Consent Date", value=None)
    notes = st.text_area("Notes")

    if st.form_submit_button("Save"):
        update_consent(patient_id, status, method, outreach_date, consent_date, notes)
        st.success("Consent updated!")
```

## Testing
- **Required Tests**:
  - Consent update saves to database
  - Metrics calculate correctly
  - Bulk update works for multiple patients

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story | Claude |
