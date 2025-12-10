"""Outreach Campaign Page - Generate consent links and manage SMS campaigns."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus, APCMStatus
from consent_tokens import (
    batch_create_tokens,
    get_outreach_summary,
    get_patients_needing_tokens,
    build_form_url,
    TOKEN_EXPIRATION_DAYS,
)

st.set_page_config(
    page_title="Outreach Campaign - Patient Explorer",
    page_icon="📨",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and message sending permission for outreach
user = require_login()
require_permission("send_messages")
show_user_menu()

st.title("📨 Outreach Campaign")
st.markdown("Generate consent links and manage SMS outreach via Spruce.")
st.divider()

# Session state for form URL
if "ms_forms_url" not in st.session_state:
    st.session_state.ms_forms_url = ""


# Sidebar configuration
with st.sidebar:
    st.subheader("📊 Campaign Summary")

    summary = get_outreach_summary()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Patients", summary["total_patients"])
        st.metric("Tokens Generated", summary["with_token"])
    with col2:
        st.metric("Tokens Valid", summary["token_valid"])
        st.metric("Need Tokens", summary["pending_token"])

    st.divider()

    st.markdown("**Consent Status:**")
    for status, count in summary.get("consent_by_status", {}).items():
        st.caption(f"- {status.replace('_', ' ').title()}: {count}")

    st.divider()

    st.markdown("**APCM Elections:**")
    st.caption(f"- Pending decision: {summary['apcm_pending_decision']}")
    st.caption(f"- Decided: {summary['apcm_decided']}")

    st.divider()

    # Microsoft Forms URL configuration
    st.subheader("🔗 Form Configuration")
    ms_forms_url = st.text_input(
        "Microsoft Forms Base URL",
        value=st.session_state.ms_forms_url,
        placeholder="https://forms.microsoft.com/r/...",
        help="Your Microsoft Forms URL (create form first, then paste URL here)"
    )
    if ms_forms_url:
        st.session_state.ms_forms_url = ms_forms_url


# Main content tabs
tabs = st.tabs(["🎯 Generate Tokens", "👤 Single Invite", "📱 SMS Export", "📝 SMS Templates", "📈 Campaign Status", "📋 Token List"])

with tabs[0]:
    st.subheader("Generate Consent Tokens")

    st.markdown("""
    Generate unique consent tokens for patients. Each token creates a personalized
    link that tracks their consent response.

    **Workflow:**
    1. Select which patients need tokens
    2. Generate tokens in batch
    3. Export for Spruce SMS campaign
    """)

    st.divider()

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        filter_type = st.selectbox(
            "Select Patients",
            [
                ("all", "All patients without tokens"),
                ("apcm_only", "APCM patients only (priority)"),
                ("spruce_matched", "Spruce-matched patients only"),
            ],
            format_func=lambda x: x[1]
        )[0]

    with col2:
        expiration_days = st.number_input(
            "Token Expiration (days)",
            min_value=7,
            max_value=90,
            value=TOKEN_EXPIRATION_DAYS,
            help="How long the consent links remain valid"
        )

    # Get patients needing tokens
    patients_needing = get_patients_needing_tokens("no_token")

    # Apply additional filter
    if filter_type == "apcm_only":
        patients_needing = [p for p in patients_needing if p.apcm_enrolled]
    elif filter_type == "spruce_matched":
        patients_needing = [p for p in patients_needing if p.spruce_matched]

    st.info(f"**{len(patients_needing)}** patients need consent tokens")

    if patients_needing:
        # Preview table
        with st.expander("Preview Patients", expanded=False):
            preview_data = [{
                "MRN": p.mrn,
                "Name": f"{p.last_name}, {p.first_name}",
                "Phone": p.phone or "No phone",
                "Spruce": "✅" if p.spruce_matched else "❌",
                "APCM": "✅" if p.apcm_enrolled else "",
            } for p in patients_needing[:50]]

            st.dataframe(pd.DataFrame(preview_data), hide_index=True)

            if len(patients_needing) > 50:
                st.caption(f"Showing first 50 of {len(patients_needing)} patients")

        # Generate button
        st.divider()

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            generate_all = st.button(
                f"🔑 Generate {len(patients_needing)} Tokens",
                type="primary",
                use_container_width=True
            )

        if generate_all:
            with st.spinner(f"Generating tokens for {len(patients_needing)} patients..."):
                patient_ids = [p.id for p in patients_needing]
                results = batch_create_tokens(patient_ids, expiration_days)

                # Count results
                success = sum(1 for r in results.values() if r["error"] is None)
                errors = sum(1 for r in results.values() if r["error"] is not None)

                if success > 0:
                    st.success(f"✅ Generated {success} tokens successfully!")
                if errors > 0:
                    st.warning(f"⚠️ {errors} errors occurred")

                st.rerun()
    else:
        st.success("All patients have consent tokens!")


with tabs[1]:
    st.subheader("Single Patient Invite")

    st.markdown("""
    Generate a consent token for a single patient. Useful for:
    - One-off invitations
    - Test invites
    - Patients not in the main list
    """)

    st.divider()

    # Import token creation function
    from consent_tokens import create_single_token

    # Two options: lookup existing patient or enter details manually
    invite_mode = st.radio(
        "Select patient",
        ["🔍 Search existing patient", "✏️ Enter details manually"],
        horizontal=True
    )

    if invite_mode == "🔍 Search existing patient":
        # Patient search
        search_query = st.text_input(
            "Search by name, MRN, or phone",
            placeholder="e.g., Green, TEST001, or 757-784"
        )

        if search_query and len(search_query) >= 2:
            session = get_session()
            try:
                search_term = f"%{search_query}%"
                patients = session.query(Patient).filter(
                    (Patient.first_name.ilike(search_term)) |
                    (Patient.last_name.ilike(search_term)) |
                    (Patient.mrn.ilike(search_term)) |
                    (Patient.phone.ilike(search_term))
                ).limit(10).all()

                if patients:
                    # Create selection options
                    patient_options = {
                        f"{p.mrn} - {p.first_name} {p.last_name} ({p.phone or 'No phone'})": p.id
                        for p in patients
                    }

                    selected = st.selectbox(
                        "Select patient",
                        options=list(patient_options.keys())
                    )

                    if selected:
                        selected_patient_id = patient_options[selected]
                        selected_patient = session.query(Patient).filter(Patient.id == selected_patient_id).first()

                        st.divider()

                        # Show patient details
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Patient Details:**")
                            st.write(f"**Name:** {selected_patient.first_name} {selected_patient.last_name}")
                            st.write(f"**MRN:** {selected_patient.mrn}")
                            st.write(f"**Phone:** {selected_patient.phone or 'Not on file'}")
                            st.write(f"**APCM:** {'Yes' if selected_patient.apcm_enrolled else 'No'}")

                        with col2:
                            st.markdown("**Current Token Status:**")
                            if selected_patient.consent_token:
                                st.warning(f"Token exists: `{selected_patient.consent_token}`")
                                regenerate = st.checkbox("Regenerate token (invalidates old one)")
                            else:
                                st.info("No token yet")
                                regenerate = True

                            # Proxy contact option
                            st.markdown("**Proxy Contact (Optional):**")
                            use_proxy = st.checkbox("Send to family member/caregiver instead")
                            proxy_name = ""
                            proxy_phone = ""
                            if use_proxy:
                                proxy_name = st.text_input("Proxy Name", placeholder="e.g., Jane Doe (daughter)")
                                proxy_phone = st.text_input("Proxy Phone", placeholder="e.g., 555-123-4567")

                        # Generate button
                        if st.button("🔑 Generate Token & Link", type="primary"):
                            if regenerate or not selected_patient.consent_token:
                                result = create_single_token(selected_patient.id, TOKEN_EXPIRATION_DAYS)

                                if result["error"]:
                                    st.error(f"Error: {result['error']}")
                                else:
                                    st.success("✅ Token generated!")

                                    # Build the URL
                                    if st.session_state.ms_forms_url:
                                        consent_url = build_form_url(
                                            st.session_state.ms_forms_url,
                                            result["token"],
                                            selected_patient
                                        )

                                        st.markdown("**Consent Link:**")
                                        st.code(consent_url)

                                        # SMS ready to send
                                        sms_phone = proxy_phone if use_proxy and proxy_phone else selected_patient.phone
                                        sms_name = proxy_name if use_proxy and proxy_name else selected_patient.first_name

                                        st.markdown("**Ready to Send:**")
                                        st.write(f"📱 **To:** {sms_phone or 'No phone'}")

                                        sms_message = f"Hi {sms_name}, this is Dr. Green's office. Please complete this consent form: {consent_url}"
                                        st.code(sms_message)

                                        if proxy_name:
                                            st.caption(f"Proxy for: {selected_patient.first_name} {selected_patient.last_name}")
                                    else:
                                        st.warning("Configure Form URL in sidebar to generate links")
                                        st.code(f"Token: {result['token']}")
                else:
                    st.info("No patients found matching your search")
            finally:
                session.close()

    else:  # Manual entry mode
        st.info("For patients not in the database, you can create a manual invite link.")

        col1, col2 = st.columns(2)
        with col1:
            manual_name = st.text_input("Patient/Proxy Name", placeholder="e.g., Robert Green")
            manual_phone = st.text_input("Phone Number", placeholder="e.g., 757-784-2320")
        with col2:
            manual_mrn = st.text_input("MRN (optional)", placeholder="e.g., 12345")
            is_apcm = st.checkbox("APCM Patient")

        if st.button("🔑 Generate Manual Token", type="primary"):
            if manual_name and manual_phone:
                # Generate a random token
                import secrets
                manual_token = secrets.token_urlsafe(12)[:16].upper()

                if st.session_state.ms_forms_url:
                    consent_url = f"{st.session_state.ms_forms_url}?token={manual_token}"

                    st.success("✅ Manual token generated!")
                    st.markdown("**Consent Link:**")
                    st.code(consent_url)

                    sms_message = f"Hi {manual_name.split()[0]}, this is Dr. Green's office. Please complete this consent form: {consent_url}"
                    st.markdown("**SMS Message:**")
                    st.code(sms_message)

                    st.warning("⚠️ Note: Manual tokens are not tracked in the database. Record this token manually.")
                    st.caption(f"Token: {manual_token} | Phone: {manual_phone} | MRN: {manual_mrn or 'N/A'}")
                else:
                    st.warning("Configure Form URL in sidebar first")
            else:
                st.error("Please enter name and phone number")


with tabs[2]:
    st.subheader("Export for Spruce SMS")

    # Import SMS templates module
    try:
        from sms_templates import generate_initial_sms, get_follow_up_schedule
        sms_templates_available = True
    except ImportError:
        sms_templates_available = False

    st.markdown("""
    Export patient list with personalized consent links for Spruce bulk SMS.

    **Steps:**
    1. Ensure Microsoft Forms URL is configured in sidebar
    2. Select patient filter
    3. Download CSV for Spruce import
    """)

    st.divider()

    if not st.session_state.ms_forms_url:
        st.warning("⚠️ Configure Microsoft Forms URL in the sidebar first")
    else:
        # Filter options for export
        export_filter = st.selectbox(
            "Export Filter",
            [
                ("ready", "Ready for outreach (has token + Spruce match)"),
                ("apcm_priority", "APCM patients ready for outreach"),
                ("all_tokens", "All patients with tokens"),
            ],
            format_func=lambda x: x[1]
        )[0]

        # Get patients for export
        session = get_session()
        try:
            query = session.query(Patient).filter(
                Patient.consent_token.isnot(None)
            )

            if export_filter == "ready":
                query = query.filter(Patient.spruce_matched == True)
            elif export_filter == "apcm_priority":
                query = query.filter(
                    Patient.spruce_matched == True,
                    Patient.apcm_enrolled == True
                )

            patients = query.all()

            st.info(f"**{len(patients)}** patients ready for export")

            if patients:
                # Build export data
                export_data = []
                for p in patients:
                    display_name = p.first_name
                    if p.preferred_name:
                        display_name = p.preferred_name

                    consent_url = build_form_url(
                        st.session_state.ms_forms_url,
                        p.consent_token,
                        p
                    )

                    # Generate SMS message using templates
                    if sms_templates_available:
                        sms_template = generate_initial_sms(
                            patient_first_name=p.first_name,
                            patient_preferred_name=p.preferred_name,
                            consent_url=consent_url,
                            is_apcm=p.apcm_enrolled,
                            office_phone="(XXX) XXX-XXXX"  # Configure in settings
                        )
                        sms_message = sms_template.message
                    else:
                        # Fallback to simple template
                        sms_message = f"""Hi {display_name}, this is Home Team Medical Services. Dr. Green's practice is transitioning, and we need your consent for records. Please complete this short form: {consent_url}"""

                    export_data.append({
                        "MRN": p.mrn,
                        "Name": f"{p.first_name} {p.last_name}",
                        "Preferred": p.preferred_name or "",
                        "Phone": p.phone or "",
                        "Consent_URL": consent_url,
                        "Token": p.consent_token,
                        "APCM": "Yes" if p.apcm_enrolled else "No",
                        "SMS_Message": sms_message,
                    })

                df_export = pd.DataFrame(export_data)

                # Preview
                st.markdown("**Preview:**")
                st.dataframe(
                    df_export[["Name", "Phone", "APCM", "Token"]].head(10),
                    hide_index=True
                )

                st.divider()

                # Export buttons
                col1, col2 = st.columns(2)

                with col1:
                    # Full export
                    csv_full = df_export.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download Full Export ({len(patients)} patients)",
                        data=csv_full,
                        file_name=f"consent_outreach_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

                with col2:
                    # Spruce-ready export (just phone, name, message)
                    spruce_data = df_export[["Phone", "Name", "SMS_Message"]].copy()
                    spruce_data = spruce_data[spruce_data["Phone"] != ""]
                    csv_spruce = spruce_data.to_csv(index=False)

                    st.download_button(
                        label=f"📱 Download Spruce SMS Export ({len(spruce_data)} with phones)",
                        data=csv_spruce,
                        file_name=f"spruce_sms_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

                # Sample SMS message
                st.divider()
                st.markdown("**Sample SMS Message:**")
                if export_data:
                    st.code(export_data[0]["SMS_Message"], language=None)

        finally:
            session.close()


with tabs[3]:
    st.subheader("SMS Message Templates")

    st.markdown("""
    Preview and customize SMS templates for different patient populations and outreach stages.
    Templates are automatically selected based on APCM status.
    """)

    st.divider()

    try:
        from sms_templates import get_all_templates, get_follow_up_schedule

        # Template preview
        all_templates = get_all_templates()

        # Group by category
        categories = {"initial": "Initial Outreach", "follow_up": "Follow-up Reminders", "confirmation": "Confirmations"}

        for cat_key, cat_name in categories.items():
            cat_templates = [t for t in all_templates if t["category"] == cat_key]
            if cat_templates:
                st.markdown(f"### {cat_name}")

                for tmpl in cat_templates:
                    apcm_badge = "🏥 APCM" if tmpl["is_apcm"] else "👤 General"
                    day_badge = f"Day {tmpl['day_offset']}" if tmpl["day_offset"] > 0 else ""

                    with st.expander(f"**{tmpl['name']}** {apcm_badge} {day_badge}"):
                        st.code(tmpl["message"], language=None)

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Characters", tmpl["characters"])
                        with col2:
                            st.metric("SMS Segments", tmpl["segments"])
                        with col3:
                            if tmpl["segments"] == 1:
                                st.success("Single SMS")
                            elif tmpl["segments"] == 2:
                                st.warning("2 SMS segments")
                            else:
                                st.error(f"{tmpl['segments']} SMS segments")

        st.divider()

        # Follow-up schedule
        st.markdown("### Recommended Follow-up Schedule")

        schedule = get_follow_up_schedule()
        schedule_df = pd.DataFrame(schedule)

        st.dataframe(
            schedule_df,
            hide_index=True,
            column_config={
                "day": st.column_config.NumberColumn("Day", width="small"),
                "action": st.column_config.TextColumn("Action", width="medium"),
                "description": st.column_config.TextColumn("Description", width="large"),
                "template": st.column_config.TextColumn("Template", width="medium"),
                "priority": st.column_config.TextColumn("Priority", width="small"),
            }
        )

        st.info("""
        **Best Practices:**
        - Send initial messages Tuesday-Thursday, 10am-2pm
        - Limit to 100 patients per day (Spruce rate limits)
        - Skip patients who have already responded
        - Day 21+ requires manual phone outreach
        """)

    except ImportError:
        st.warning("SMS templates module not available. Please check installation.")
        st.code("from sms_templates import get_all_templates", language="python")


with tabs[4]:
    st.subheader("Campaign Status")

    st.markdown("Track consent outreach progress and response rates.")
    st.divider()

    # Get detailed stats
    session = get_session()
    try:
        import plotly.express as px

        # Consent status distribution
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Consent Status")

            consent_data = session.query(
                Consent.status
            ).join(Patient).all()

            if consent_data:
                status_counts = {}
                for (status,) in consent_data:
                    label = status.value.replace("_", " ").title()
                    status_counts[label] = status_counts.get(label, 0) + 1

                status_df = pd.DataFrame([
                    {"Status": k, "Count": v}
                    for k, v in status_counts.items()
                ])

                fig = px.pie(status_df, values="Count", names="Status", hole=0.4)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No consent data yet")

        with col2:
            st.markdown("### Token Status")

            total = session.query(Patient).count()
            with_token = session.query(Patient).filter(
                Patient.consent_token.isnot(None)
            ).count()
            without_token = total - with_token

            token_df = pd.DataFrame([
                {"Status": "With Token", "Count": with_token},
                {"Status": "No Token", "Count": without_token},
            ])

            fig = px.pie(token_df, values="Count", names="Status", hole=0.4,
                        color_discrete_sequence=["#28a745", "#dc3545"])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # APCM-specific tracking
        st.markdown("### APCM Elections Progress")

        col1, col2, col3, col4 = st.columns(4)

        apcm_total = session.query(Patient).filter(
            Patient.apcm_enrolled == True
        ).count()

        apcm_continue = session.query(Patient).filter(
            Patient.apcm_continue_with_hometeam == True
        ).count()

        apcm_decline = session.query(Patient).filter(
            Patient.apcm_continue_with_hometeam == False
        ).count()

        apcm_pending = apcm_total - apcm_continue - apcm_decline

        with col1:
            st.metric("APCM Total", apcm_total)
        with col2:
            st.metric("Continue with HT", apcm_continue)
        with col3:
            st.metric("Declined", apcm_decline)
        with col4:
            st.metric("Pending Decision", apcm_pending)

        # Progress bar
        if apcm_total > 0:
            progress = (apcm_continue + apcm_decline) / apcm_total
            st.progress(progress, text=f"{int(progress * 100)}% of APCM patients have decided")

    finally:
        session.close()


with tabs[5]:
    st.subheader("Token List")

    st.markdown("View all generated consent tokens and their status.")
    st.divider()

    # Filter
    token_filter = st.selectbox(
        "Filter",
        ["All with tokens", "Valid tokens only", "Expired tokens", "No token yet"]
    )

    session = get_session()
    try:
        query = session.query(Patient)

        if token_filter == "All with tokens":
            query = query.filter(Patient.consent_token.isnot(None))
        elif token_filter == "Valid tokens only":
            query = query.filter(
                Patient.consent_token.isnot(None),
                Patient.consent_token_expires > datetime.utcnow()
            )
        elif token_filter == "Expired tokens":
            query = query.filter(
                Patient.consent_token.isnot(None),
                Patient.consent_token_expires <= datetime.utcnow()
            )
        elif token_filter == "No token yet":
            query = query.filter(Patient.consent_token.is_(None))

        patients = query.all()

        if patients:
            token_data = []
            for p in patients:
                # Determine token status
                if not p.consent_token:
                    token_status = "None"
                elif p.consent_token_expires and p.consent_token_expires < datetime.utcnow():
                    token_status = "Expired"
                else:
                    token_status = "Valid"

                # Consent status
                consent_status = "N/A"
                if p.consent:
                    consent_status = p.consent.status.value.replace("_", " ").title()

                token_data.append({
                    "MRN": p.mrn,
                    "Name": f"{p.last_name}, {p.first_name}",
                    "Token": p.consent_token or "—",
                    "Expires": p.consent_token_expires.strftime("%Y-%m-%d") if p.consent_token_expires else "—",
                    "Token Status": token_status,
                    "Consent Status": consent_status,
                    "APCM": "✅" if p.apcm_enrolled else "",
                    "Spruce": "✅" if p.spruce_matched else "❌",
                })

            df = pd.DataFrame(token_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.caption(f"Showing {len(patients)} patients")
        else:
            st.info("No patients match the selected filter")

    finally:
        session.close()
