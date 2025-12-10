"""Consent Tracking Page - Update and track patient consent status."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus, AuditLog

st.set_page_config(
    page_title="Consent Tracking - Patient Explorer",
    page_icon="✅",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and consent view permission
user = require_login()
require_permission("view_consents")
show_user_menu()

# Check edit permission for later use
can_edit_consents = has_permission("edit_consents")

st.title("✅ Consent Tracking")
st.markdown("Track and update patient consent for records retention.")
st.divider()


def get_patients_for_consent():
    """Get patients with consent info for tracking."""
    session = get_session()
    try:
        patients = session.query(Patient).filter(Patient.spruce_matched == True).all()

        data = []
        for p in patients:
            status = ConsentStatus.PENDING
            outreach_attempts = 0
            last_outreach = None
            notes = ""

            if p.consent:
                status = p.consent.status
                outreach_attempts = p.consent.outreach_attempts
                last_outreach = p.consent.last_outreach_date
                notes = p.consent.notes or ""

            data.append({
                "id": p.id,
                "MRN": p.mrn,
                "Name": f"{p.last_name}, {p.first_name}",
                "Phone": p.phone or "",
                "Status": status.value,
                "Attempts": outreach_attempts,
                "Last Outreach": last_outreach.strftime("%Y-%m-%d") if last_outreach else "",
                "Notes": notes,
            })

        return data
    finally:
        session.close()


def update_consent(patient_id: int, new_status: str, notes: str = None):
    """Update consent status for a patient."""
    session = get_session()
    try:
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return False

        if not patient.consent:
            consent = Consent(patient_id=patient_id)
            session.add(consent)
            patient.consent = consent

        # Update status
        old_status = patient.consent.status.value
        patient.consent.status = ConsentStatus(new_status)
        patient.consent.outreach_attempts += 1
        patient.consent.last_outreach_date = datetime.utcnow()

        if notes:
            patient.consent.notes = notes

        if new_status in ["consented", "declined"]:
            patient.consent.response_date = datetime.utcnow()

        # Audit log
        audit = AuditLog(
            patient_id=patient_id,
            action="update",
            entity_type="consent",
            entity_id=patient.consent.id,
            details=f"Status changed from {old_status} to {new_status}",
        )
        session.add(audit)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error updating consent: {e}")
        return False
    finally:
        session.close()


# Tabs for different workflows
tab1, tab2, tab3 = st.tabs(["📋 Pending Outreach", "✅ Responses", "📊 Statistics"])

with tab1:
    st.subheader("Patients Awaiting Consent")

    patients = get_patients_for_consent()
    pending = [p for p in patients if p["Status"] in ["pending", "no_response"]]

    if not pending:
        st.info("No patients pending consent outreach.")
    else:
        st.caption(f"Showing {len(pending)} patients needing outreach")

        for p in pending:
            with st.expander(f"**{p['Name']}** - MRN: {p['MRN']} | Attempts: {p['Attempts']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.text(f"Phone: {p['Phone']}")
                    st.text(f"Last Outreach: {p['Last Outreach'] or 'Never'}")

                    notes = st.text_area(
                        "Notes",
                        value=p["Notes"],
                        key=f"notes_{p['id']}",
                        height=80
                    )

                with col2:
                    st.markdown("**Update Status:**")

                    if st.button("✅ Consented", key=f"consent_{p['id']}", use_container_width=True):
                        if update_consent(p["id"], "consented", notes):
                            st.success("Marked as consented!")
                            st.rerun()

                    if st.button("❌ Declined", key=f"decline_{p['id']}", use_container_width=True):
                        if update_consent(p["id"], "declined", notes):
                            st.warning("Marked as declined")
                            st.rerun()

                    if st.button("📭 No Response", key=f"noresp_{p['id']}", use_container_width=True):
                        if update_consent(p["id"], "no_response", notes):
                            st.info("Marked as no response")
                            st.rerun()

with tab2:
    st.subheader("Completed Responses")

    patients = get_patients_for_consent()
    completed = [p for p in patients if p["Status"] in ["consented", "declined"]]

    if not completed:
        st.info("No completed consent responses yet.")
    else:
        # Split by status
        consented = [p for p in completed if p["Status"] == "consented"]
        declined = [p for p in completed if p["Status"] == "declined"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### ✅ Consented ({len(consented)})")
            for p in consented:
                st.text(f"{p['Name']} - {p['MRN']}")

        with col2:
            st.markdown(f"### ❌ Declined ({len(declined)})")
            for p in declined:
                st.text(f"{p['Name']} - {p['MRN']}")

with tab3:
    st.subheader("Consent Statistics")

    patients = get_patients_for_consent()

    if not patients:
        st.info("No Spruce-matched patients to track.")
    else:
        total = len(patients)
        consented = len([p for p in patients if p["Status"] == "consented"])
        declined = len([p for p in patients if p["Status"] == "declined"])
        pending = len([p for p in patients if p["Status"] == "pending"])
        no_response = len([p for p in patients if p["Status"] == "no_response"])

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Matched", total)
        with col2:
            st.metric("Consented", consented, delta=f"{consented/total*100:.0f}%")
        with col3:
            st.metric("Declined", declined)
        with col4:
            st.metric("Awaiting", pending + no_response)

        st.divider()

        # Progress bar
        completion = (consented + declined) / total if total > 0 else 0
        st.progress(completion, text=f"Consent Campaign: {completion*100:.1f}% complete")

        # Breakdown chart
        import plotly.express as px

        status_data = pd.DataFrame({
            "Status": ["Consented", "Declined", "Pending", "No Response"],
            "Count": [consented, declined, pending, no_response]
        })

        fig = px.pie(
            status_data,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map={
                "Consented": "#28a745",
                "Declined": "#dc3545",
                "Pending": "#ffc107",
                "No Response": "#6c757d"
            }
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
