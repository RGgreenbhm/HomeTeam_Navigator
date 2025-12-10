"""Consent Response Processing - Handle patient consent form submissions."""

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
    page_title="Consent Response - Patient Explorer",
    page_icon="📬",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and consent edit permission
user = require_login()
require_permission("edit_consents")
show_user_menu()

st.title("📬 Consent Response Processing")
st.markdown("Process patient consent responses from Microsoft Forms or manual entry.")
st.divider()


def validate_token(token: str) -> dict | None:
    """Validate a consent token and return patient info if valid."""
    if not token or len(token) < 8:
        return None

    session = get_session()
    try:
        patient = session.query(Patient).filter(
            Patient.consent_token == token.strip()
        ).first()

        if not patient:
            return None

        # Check expiration
        is_expired = False
        if patient.consent_token_expires:
            is_expired = patient.consent_token_expires < datetime.utcnow()

        # Get current consent status
        consent_status = "pending"
        if patient.consent:
            consent_status = patient.consent.status.value

        return {
            "patient_id": patient.id,
            "mrn": patient.mrn,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "preferred_name": patient.preferred_name,
            "phone": patient.phone,
            "token": patient.consent_token,
            "token_expires": patient.consent_token_expires,
            "is_expired": is_expired,
            "current_status": consent_status,
            "apcm_enrolled": patient.apcm_enrolled,
            "apcm_continue_with_hometeam": patient.apcm_continue_with_hometeam,
            "apcm_revoke_southview_billing": patient.apcm_revoke_southview_billing,
        }
    finally:
        session.close()


def process_consent_response(
    patient_id: int,
    consent_decision: str,
    apcm_continue: bool | None = None,
    apcm_revoke_sv: bool | None = None,
    method: str = "form",
    notes: str = None,
    user_name: str = None
) -> tuple[bool, str]:
    """Process a consent response and update patient record.

    Args:
        patient_id: Database ID of the patient
        consent_decision: 'consented' or 'declined'
        apcm_continue: For APCM patients - continue with Home Team?
        apcm_revoke_sv: For APCM patients - revoke Southview billing?
        method: Response method (form, phone, in_person)
        notes: Optional notes
        user_name: Name of user processing the response

    Returns:
        Tuple of (success: bool, message: str)
    """
    session = get_session()
    try:
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return False, "Patient not found"

        # Update or create consent record
        if not patient.consent:
            consent = Consent(patient_id=patient_id)
            session.add(consent)
            patient.consent = consent

        old_status = patient.consent.status.value

        # Update consent status
        if consent_decision == "consented":
            patient.consent.status = ConsentStatus.CONSENTED
        elif consent_decision == "declined":
            patient.consent.status = ConsentStatus.DECLINED
        else:
            return False, f"Invalid consent decision: {consent_decision}"

        # Update consent metadata
        patient.consent.response_date = datetime.utcnow()
        patient.consent.response_method = method
        patient.consent.outreach_attempts += 1
        patient.consent.last_outreach_date = datetime.utcnow()

        if notes:
            existing_notes = patient.consent.notes or ""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            patient.consent.notes = f"{existing_notes}\n[{timestamp}] {notes}".strip()

        # Update APCM elections if applicable
        if patient.apcm_enrolled and apcm_continue is not None:
            patient.apcm_continue_with_hometeam = apcm_continue

        if patient.apcm_enrolled and apcm_revoke_sv is not None:
            patient.apcm_revoke_southview_billing = apcm_revoke_sv

        # Create audit log entry
        audit_details = f"Consent {consent_decision} via {method}. Previous: {old_status}"
        if patient.apcm_enrolled:
            audit_details += f" | APCM: continue={apcm_continue}, revoke_sv={apcm_revoke_sv}"

        audit = AuditLog(
            patient_id=patient_id,
            action="consent_response",
            entity_type="consent",
            entity_id=patient.consent.id,
            details=audit_details,
            user_name=user_name,
        )
        session.add(audit)

        session.commit()

        return True, f"Successfully recorded {consent_decision} for {patient.first_name} {patient.last_name}"

    except Exception as e:
        session.rollback()
        return False, f"Error processing response: {str(e)}"
    finally:
        session.close()


# Sidebar with stats
with st.sidebar:
    st.subheader("📊 Today's Activity")

    session = get_session()
    try:
        today = datetime.utcnow().date()

        # Count today's responses
        todays_responses = session.query(Consent).filter(
            Consent.response_date >= datetime.combine(today, datetime.min.time())
        ).count()

        # Count by status
        todays_consented = session.query(Consent).filter(
            Consent.response_date >= datetime.combine(today, datetime.min.time()),
            Consent.status == ConsentStatus.CONSENTED
        ).count()

        todays_declined = session.query(Consent).filter(
            Consent.response_date >= datetime.combine(today, datetime.min.time()),
            Consent.status == ConsentStatus.DECLINED
        ).count()

        st.metric("Responses Today", todays_responses)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Consented", todays_consented)
        with col2:
            st.metric("Declined", todays_declined)

    finally:
        session.close()

    st.divider()

    st.markdown("""
    **Response Methods:**
    - 📱 **Form**: Microsoft Forms submission
    - 📞 **Phone**: Verbal consent via call
    - 🏥 **In-Person**: Consent during visit
    """)


# Main content tabs
tabs = st.tabs(["🔑 Token Lookup", "📥 Bulk Import", "🔍 Recent Responses"])

with tabs[0]:
    st.subheader("Process Single Consent Response")

    st.markdown("""
    Enter the consent token from the patient's response form to look up their record
    and process their consent decision.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        token_input = st.text_input(
            "Consent Token",
            placeholder="Enter 16-character token (e.g., ABC123XYZ789DEFG)",
            max_chars=20,
            key="single_token"
        )

    with col2:
        lookup_btn = st.button("🔍 Look Up", type="primary", use_container_width=True)

    if lookup_btn and token_input:
        patient_info = validate_token(token_input)

        if patient_info is None:
            st.error("❌ Token not found. Please check the token and try again.")
        else:
            st.success("✅ Token validated!")

            if patient_info["is_expired"]:
                st.warning(f"⚠️ This token expired on {patient_info['token_expires'].strftime('%Y-%m-%d')}")

            st.divider()

            # Patient info display
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Patient Information")
                display_name = f"{patient_info['first_name']} {patient_info['last_name']}"
                if patient_info["preferred_name"]:
                    display_name += f' ("{patient_info["preferred_name"]}")'

                st.markdown(f"**Name:** {display_name}")
                st.markdown(f"**MRN:** {patient_info['mrn']}")
                st.markdown(f"**Phone:** {patient_info['phone'] or 'Not on file'}")
                st.markdown(f"**Current Status:** {patient_info['current_status'].replace('_', ' ').title()}")

                if patient_info["apcm_enrolled"]:
                    st.markdown("**APCM:** ✅ Enrolled")
                    if patient_info["apcm_continue_with_hometeam"] is not None:
                        ht_status = "✅ Yes" if patient_info["apcm_continue_with_hometeam"] else "❌ No"
                        st.markdown(f"**Continue with Home Team:** {ht_status}")

            with col2:
                st.markdown("### Record Response")

                # Skip if already decided
                if patient_info["current_status"] in ["consented", "declined"]:
                    st.info(f"This patient has already {patient_info['current_status']}.")
                    if st.checkbox("Override existing decision"):
                        show_form = True
                    else:
                        show_form = False
                else:
                    show_form = True

                if show_form:
                    with st.form("consent_response_form"):
                        consent_decision = st.radio(
                            "Consent Decision",
                            ["consented", "declined"],
                            format_func=lambda x: "✅ Consented" if x == "consented" else "❌ Declined",
                            horizontal=True
                        )

                        response_method = st.selectbox(
                            "Response Method",
                            ["form", "phone", "in_person"],
                            format_func=lambda x: {"form": "📱 Form", "phone": "📞 Phone", "in_person": "🏥 In-Person"}[x]
                        )

                        # APCM-specific questions
                        apcm_continue = None
                        apcm_revoke = None

                        if patient_info["apcm_enrolled"]:
                            st.markdown("---")
                            st.markdown("**APCM Elections:**")

                            apcm_continue = st.radio(
                                "Continue with Home Team Medical Services?",
                                [True, False, None],
                                format_func=lambda x: {True: "✅ Yes", False: "❌ No", None: "Not Answered"}[x],
                                horizontal=True
                            )

                            apcm_revoke = st.radio(
                                "Revoke Southview billing authorization?",
                                [True, False, None],
                                format_func=lambda x: {True: "✅ Yes", False: "❌ No", None: "Not Answered"}[x],
                                horizontal=True
                            )

                        notes = st.text_area("Notes (optional)", height=80)

                        submitted = st.form_submit_button("💾 Save Response", type="primary")

                        if submitted:
                            success, message = process_consent_response(
                                patient_id=patient_info["patient_id"],
                                consent_decision=consent_decision,
                                apcm_continue=apcm_continue,
                                apcm_revoke_sv=apcm_revoke,
                                method=response_method,
                                notes=notes,
                                user_name=user.username if user else None
                            )

                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)


with tabs[1]:
    st.subheader("Bulk Import from Microsoft Forms")

    st.markdown("""
    Export responses from Microsoft Forms as Excel/CSV and upload here to process
    multiple consent responses at once.

    **Required columns:**
    - `Token` or `Consent Token` - The patient's unique consent token
    - `Consent` or `Decision` - "Yes"/"Consented" or "No"/"Declined"

    **Optional columns:**
    - `Continue with Home Team` - For APCM patients (Yes/No)
    - `Revoke Southview` - For APCM patients (Yes/No)
    - `Notes` or `Comments` - Additional notes
    """)

    uploaded_file = st.file_uploader(
        "Upload Forms Export",
        type=["xlsx", "xls", "csv"],
        key="bulk_import"
    )

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success(f"✅ Loaded {len(df)} rows")

            # Preview data
            with st.expander("Preview Data", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            # Map columns
            st.markdown("### Column Mapping")

            col1, col2, col3 = st.columns(3)

            columns = ["(not mapped)"] + list(df.columns)

            with col1:
                token_col = st.selectbox(
                    "Token Column",
                    columns,
                    index=next((i+1 for i, c in enumerate(df.columns) if "token" in c.lower()), 0)
                )

            with col2:
                consent_col = st.selectbox(
                    "Consent Decision Column",
                    columns,
                    index=next((i+1 for i, c in enumerate(df.columns) if any(x in c.lower() for x in ["consent", "decision"])), 0)
                )

            with col3:
                notes_col = st.selectbox(
                    "Notes Column (optional)",
                    columns,
                    index=next((i+1 for i, c in enumerate(df.columns) if any(x in c.lower() for x in ["note", "comment"])), 0)
                )

            # APCM columns
            col1, col2 = st.columns(2)

            with col1:
                ht_col = st.selectbox(
                    "Continue with Home Team Column (optional)",
                    columns,
                    index=next((i+1 for i, c in enumerate(df.columns) if "home team" in c.lower()), 0)
                )

            with col2:
                sv_col = st.selectbox(
                    "Revoke Southview Column (optional)",
                    columns,
                    index=next((i+1 for i, c in enumerate(df.columns) if "southview" in c.lower()), 0)
                )

            st.divider()

            # Process button
            if token_col != "(not mapped)" and consent_col != "(not mapped)":
                if st.button("🚀 Process All Responses", type="primary"):
                    results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}

                    progress = st.progress(0)
                    status_text = st.empty()

                    for idx, row in df.iterrows():
                        progress.progress((idx + 1) / len(df))
                        status_text.text(f"Processing row {idx + 1} of {len(df)}...")

                        token = str(row[token_col]).strip() if pd.notna(row[token_col]) else None

                        if not token:
                            results["skipped"] += 1
                            continue

                        # Validate token
                        patient_info = validate_token(token)
                        if not patient_info:
                            results["failed"] += 1
                            results["errors"].append(f"Row {idx + 1}: Invalid token '{token}'")
                            continue

                        # Parse consent decision
                        consent_raw = str(row[consent_col]).strip().lower() if pd.notna(row[consent_col]) else ""

                        if consent_raw in ["yes", "consented", "consent", "agree", "agreed", "1", "true"]:
                            consent_decision = "consented"
                        elif consent_raw in ["no", "declined", "decline", "disagree", "0", "false"]:
                            consent_decision = "declined"
                        else:
                            results["skipped"] += 1
                            continue

                        # Parse APCM fields
                        apcm_continue = None
                        apcm_revoke = None

                        if ht_col != "(not mapped)" and pd.notna(row.get(ht_col)):
                            ht_raw = str(row[ht_col]).strip().lower()
                            if ht_raw in ["yes", "1", "true"]:
                                apcm_continue = True
                            elif ht_raw in ["no", "0", "false"]:
                                apcm_continue = False

                        if sv_col != "(not mapped)" and pd.notna(row.get(sv_col)):
                            sv_raw = str(row[sv_col]).strip().lower()
                            if sv_raw in ["yes", "1", "true"]:
                                apcm_revoke = True
                            elif sv_raw in ["no", "0", "false"]:
                                apcm_revoke = False

                        # Get notes
                        notes = None
                        if notes_col != "(not mapped)" and pd.notna(row.get(notes_col)):
                            notes = str(row[notes_col]).strip()

                        # Process the response
                        success, message = process_consent_response(
                            patient_id=patient_info["patient_id"],
                            consent_decision=consent_decision,
                            apcm_continue=apcm_continue,
                            apcm_revoke_sv=apcm_revoke,
                            method="form",
                            notes=notes,
                            user_name=user.username if user else None
                        )

                        if success:
                            results["success"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Row {idx + 1}: {message}")

                    progress.progress(100)
                    status_text.text("Processing complete!")

                    # Show results
                    st.divider()
                    st.markdown("### Import Results")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("✅ Processed", results["success"])
                    with col2:
                        st.metric("❌ Failed", results["failed"])
                    with col3:
                        st.metric("⏭️ Skipped", results["skipped"])

                    if results["errors"]:
                        with st.expander(f"View {len(results['errors'])} Errors"):
                            for err in results["errors"]:
                                st.caption(err)

                    if results["success"] > 0:
                        st.balloons()
            else:
                st.warning("Please map the Token and Consent Decision columns to proceed.")

        except Exception as e:
            st.error(f"Error reading file: {e}")


with tabs[2]:
    st.subheader("Recent Consent Responses")

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        days_back = st.selectbox(
            "Time Period",
            [7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days"
        )

    with col2:
        status_filter = st.selectbox(
            "Status Filter",
            ["All", "Consented", "Declined"]
        )

    session = get_session()
    try:
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days_back)

        query = session.query(Patient).join(Consent).filter(
            Consent.response_date >= cutoff
        )

        if status_filter == "Consented":
            query = query.filter(Consent.status == ConsentStatus.CONSENTED)
        elif status_filter == "Declined":
            query = query.filter(Consent.status == ConsentStatus.DECLINED)

        patients = query.order_by(Consent.response_date.desc()).all()

        if not patients:
            st.info(f"No consent responses in the last {days_back} days.")
        else:
            response_data = []
            for p in patients:
                response_data.append({
                    "Date": p.consent.response_date.strftime("%Y-%m-%d %H:%M") if p.consent.response_date else "",
                    "MRN": p.mrn,
                    "Name": f"{p.last_name}, {p.first_name}",
                    "Status": "✅ Consented" if p.consent.status == ConsentStatus.CONSENTED else "❌ Declined",
                    "Method": (p.consent.response_method or "unknown").replace("_", " ").title(),
                    "APCM": "✅" if p.apcm_enrolled else "",
                    "Notes": (p.consent.notes or "")[:50] + "..." if p.consent.notes and len(p.consent.notes) > 50 else (p.consent.notes or ""),
                })

            df = pd.DataFrame(response_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Export option
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Export to CSV",
                data=csv,
                file_name=f"consent_responses_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    finally:
        session.close()


# Footer
st.divider()
st.caption("""
**Tips:**
- Tokens are case-sensitive - enter exactly as shown on the form
- Expired tokens can still be processed (with warning)
- All responses are logged for HIPAA compliance
""")
