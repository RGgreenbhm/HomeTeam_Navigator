"""APCM Patients Page - Manage Advanced Primary Care Management patients."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus, APCMStatus, APCMLevel
from apcm_loader import load_apcm_patients, get_apcm_summary

st.set_page_config(
    page_title="APCM Patients - Patient Explorer",
    page_icon="💰",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and patient view permission
user = require_login()
require_permission("view_patients")
show_user_menu()

st.title("💰 APCM Patients")
st.markdown("Advanced Primary Care Management enrollment and consent tracking.")
st.divider()


def get_apcm_file_path():
    """Find the APCM Excel file in the data directory."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    apcm_files = list(data_dir.glob("*APCM*.xlsx")) + list(data_dir.glob("*APCM*.xls"))
    if apcm_files:
        return str(apcm_files[0])
    return None


def import_apcm_to_database():
    """Import APCM patients from Excel, matching/updating existing patient records."""
    apcm_path = get_apcm_file_path()
    if not apcm_path:
        st.error("No APCM Excel file found in data/ directory")
        return 0, 0, 0

    data = load_apcm_patients(apcm_path)
    session = get_session()

    updated = 0
    created = 0
    errors = 0

    try:
        for patient_data in data['active'] + data['removed']:
            mrn = patient_data['mrn']
            if not mrn:
                continue

            # Find existing patient by MRN
            existing = session.query(Patient).filter(Patient.mrn == mrn).first()

            # Determine APCM level enum
            level_enum = None
            if patient_data['level_code'] == 'G0556':
                level_enum = APCMLevel.LEVEL_1
            elif patient_data['level_code'] == 'G0557':
                level_enum = APCMLevel.LEVEL_2
            elif patient_data['level_code'] == 'G0558':
                level_enum = APCMLevel.LEVEL_3

            # Determine APCM status enum
            status_enum = APCMStatus.ACTIVE if patient_data['status'] == 'active' else APCMStatus.REMOVED

            if existing:
                # Update existing patient with APCM info
                existing.apcm_enrolled = (patient_data['status'] == 'active')
                existing.apcm_signup_date = patient_data['signup_date']
                existing.apcm_level = level_enum
                existing.apcm_icd_codes = patient_data['icd_codes']
                existing.apcm_status = status_enum
                existing.apcm_status_notes = patient_data['status_notes']
                existing.apcm_insurance = patient_data['insurance']
                existing.apcm_copay = patient_data['copay']

                # Update preferred name if not already set
                if patient_data['preferred_name'] and not existing.preferred_name:
                    existing.preferred_name = patient_data['preferred_name']

                updated += 1
            else:
                # Create new patient record
                new_patient = Patient(
                    mrn=mrn,
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    preferred_name=patient_data['preferred_name'],
                    apcm_enrolled=(patient_data['status'] == 'active'),
                    apcm_signup_date=patient_data['signup_date'],
                    apcm_level=level_enum,
                    apcm_icd_codes=patient_data['icd_codes'],
                    apcm_status=status_enum,
                    apcm_status_notes=patient_data['status_notes'],
                    apcm_insurance=patient_data['insurance'],
                    apcm_copay=patient_data['copay'],
                )
                session.add(new_patient)

                # Create pending consent record
                consent = Consent(patient=new_patient, status=ConsentStatus.PENDING)
                session.add(consent)

                created += 1

        session.commit()
    except Exception as e:
        session.rollback()
        st.error(f"Import error: {e}")
        errors += 1
    finally:
        session.close()

    return updated, created, errors


def get_apcm_patients_from_db():
    """Get all APCM patients from database."""
    session = get_session()
    try:
        patients = session.query(Patient).filter(
            Patient.apcm_status.in_([APCMStatus.ACTIVE, APCMStatus.REMOVED, APCMStatus.HOLD, APCMStatus.PENDING])
        ).all()

        data = []
        for p in patients:
            consent_status = "No record"
            if p.consent:
                consent_status = p.consent.status.value.replace("_", " ").title()

            # Format display name
            display_name = f"{p.last_name}, {p.first_name}"
            if p.preferred_name:
                display_name += f' "{p.preferred_name}"'

            data.append({
                "id": p.id,
                "MRN": p.mrn,
                "Name": display_name,
                "Preferred": p.preferred_name or "",
                "Signup Date": p.apcm_signup_date.strftime("%Y-%m-%d") if p.apcm_signup_date else "",
                "Level": p.apcm_level.value if p.apcm_level else "",
                "ICD Codes": p.apcm_icd_codes or "",
                "APCM Status": p.apcm_status.value.title() if p.apcm_status else "",
                "Spruce Match": "✅" if p.spruce_matched else "❌",
                "Consent": consent_status,
                "Continue HT": "✅" if p.apcm_continue_with_hometeam else ("❌" if p.apcm_continue_with_hometeam is False else "⏳"),
                "Revoke SV": "✅" if p.apcm_revoke_southview_billing else ("❌" if p.apcm_revoke_southview_billing is False else "⏳"),
                "Notes": p.apcm_status_notes or "",
            })

        return pd.DataFrame(data)
    finally:
        session.close()


# Sidebar
with st.sidebar:
    st.subheader("📊 APCM Summary")

    apcm_path = get_apcm_file_path()
    if apcm_path:
        try:
            summary = get_apcm_summary(apcm_path)
            st.metric("Active Enrolled", summary['active_count'])
            st.metric("Removed", summary['removed_count'])

            st.markdown("**By Level:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("L1", summary['level_1_count'], help="G0556 - One DX")
            with col2:
                st.metric("L2", summary['level_2_count'], help="G0557 - 2+ DX")
            with col3:
                st.metric("L3", summary['level_3_count'], help="G0558 - QMB")
        except Exception as e:
            st.error(f"Error reading APCM file: {e}")
    else:
        st.warning("No APCM file found")

    st.divider()

    # Import button
    if st.button("📥 Import/Update APCM Data", use_container_width=True):
        with st.spinner("Importing APCM patients..."):
            updated, created, errors = import_apcm_to_database()
            if errors == 0:
                st.success(f"Updated: {updated}, Created: {created}")
                st.rerun()
            else:
                st.error(f"Errors occurred during import")

    st.divider()

    # Filters
    st.subheader("🔍 Filters")

    filter_status = st.selectbox(
        "APCM Status",
        ["All", "Active", "Removed", "Hold", "Pending"]
    )

    filter_level = st.selectbox(
        "Billing Level",
        ["All", "G0556 (Level 1)", "G0557 (Level 2)", "G0558 (Level 3/QMB)"]
    )

    filter_consent = st.selectbox(
        "Consent Status",
        ["All", "Pending", "Consented", "Declined"]
    )

    filter_elections = st.selectbox(
        "HT Elections",
        ["All", "Continue HT ✅", "Not Yet Decided ⏳", "Declined ❌"]
    )


# Main content
tabs = st.tabs(["📋 Patient List", "📈 Statistics", "📤 Export"])

with tabs[0]:
    df = get_apcm_patients_from_db()

    if df.empty:
        st.info("No APCM patients in database. Use 'Import/Update APCM Data' in the sidebar.")
    else:
        # Apply filters
        if filter_status != "All":
            df = df[df["APCM Status"] == filter_status]

        if filter_level != "All":
            level_code = filter_level.split(" ")[0]
            df = df[df["Level"] == level_code]

        if filter_consent != "All":
            df = df[df["Consent"] == filter_consent]

        if filter_elections == "Continue HT ✅":
            df = df[df["Continue HT"] == "✅"]
        elif filter_elections == "Not Yet Decided ⏳":
            df = df[df["Continue HT"] == "⏳"]
        elif filter_elections == "Declined ❌":
            df = df[df["Continue HT"] == "❌"]

        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Showing", f"{len(df)} patients")
        with col2:
            active_count = len(df[df["APCM Status"] == "Active"])
            st.metric("Active", active_count)
        with col3:
            spruce_count = len(df[df["Spruce Match"] == "✅"])
            st.metric("Spruce Matched", spruce_count)
        with col4:
            continue_count = len(df[df["Continue HT"] == "✅"])
            st.metric("Continuing w/ HT", continue_count)

        st.divider()

        # Display table
        st.dataframe(
            df.drop(columns=["id"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "MRN": st.column_config.TextColumn("MRN", width="small"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Preferred": st.column_config.TextColumn("Preferred", width="small"),
                "Signup Date": st.column_config.TextColumn("Signup", width="small"),
                "Level": st.column_config.TextColumn("Level", width="small"),
                "ICD Codes": st.column_config.TextColumn("ICD Codes", width="large"),
                "APCM Status": st.column_config.TextColumn("Status", width="small"),
                "Spruce Match": st.column_config.TextColumn("Spruce", width="small"),
                "Consent": st.column_config.TextColumn("Consent", width="small"),
                "Continue HT": st.column_config.TextColumn("Continue HT", width="small"),
                "Revoke SV": st.column_config.TextColumn("Revoke SV", width="small"),
                "Notes": st.column_config.TextColumn("Notes", width="medium"),
            }
        )


with tabs[1]:
    st.subheader("APCM Statistics")

    df = get_apcm_patients_from_db()

    if df.empty:
        st.info("No data to display")
    else:
        import plotly.express as px

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Enrollment Status")
            status_counts = df["APCM Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig = px.bar(status_counts, x="Status", y="Count", color="Status")
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### Billing Levels")
            level_df = df[df["Level"] != ""]
            if not level_df.empty:
                level_counts = level_df["Level"].value_counts().reset_index()
                level_counts.columns = ["Level", "Count"]
                fig = px.bar(level_counts, x="Level", y="Count", color="Level")
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No billing level data")

        st.divider()

        st.markdown("### Consent Progress")
        col1, col2 = st.columns(2)

        with col1:
            consent_counts = df["Consent"].value_counts().reset_index()
            consent_counts.columns = ["Status", "Count"]
            fig = px.bar(consent_counts, x="Status", y="Count", color="Status")
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Home Team elections
            st.markdown("**Home Team Elections:**")
            ht_counts = df["Continue HT"].value_counts()
            for status, count in ht_counts.items():
                st.write(f"- {status}: {count}")


with tabs[2]:
    st.subheader("Export APCM Data")

    df = get_apcm_patients_from_db()

    if df.empty:
        st.info("No data to export")
    else:
        st.markdown("### Export Options")

        col1, col2 = st.columns(2)

        with col1:
            # Export all APCM patients
            csv_all = df.drop(columns=["id"]).to_csv(index=False)
            st.download_button(
                label="📥 Export All APCM Patients",
                data=csv_all,
                file_name=f"apcm_patients_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:
            # Export for Spruce (phone list)
            st.markdown("**For Spruce Bulk SMS:**")

            # Get patients with Spruce match and pending consent
            session = get_session()
            try:
                pending_patients = session.query(Patient).filter(
                    Patient.apcm_enrolled == True,
                    Patient.spruce_matched == True,
                    Patient.apcm_continue_with_hometeam == None,
                ).all()

                if pending_patients:
                    spruce_data = [{
                        "MRN": p.mrn,
                        "Name": f"{p.last_name}, {p.first_name}",
                        "Phone": p.phone or "",
                    } for p in pending_patients]

                    spruce_df = pd.DataFrame(spruce_data)
                    csv_spruce = spruce_df.to_csv(index=False)

                    st.download_button(
                        label=f"📱 Export for Spruce ({len(pending_patients)} patients)",
                        data=csv_spruce,
                        file_name=f"apcm_spruce_outreach_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.info("No patients pending HT election with Spruce match")
            finally:
                session.close()

        st.divider()

        st.markdown("### Quick Stats for Export")

        active_df = df[df["APCM Status"] == "Active"]
        st.write(f"- **Active APCM patients:** {len(active_df)}")
        st.write(f"- **With Spruce match:** {len(active_df[active_df['Spruce Match'] == '✅'])}")
        st.write(f"- **Elected to continue w/ HT:** {len(active_df[active_df['Continue HT'] == '✅'])}")
        st.write(f"- **Still pending decision:** {len(active_df[active_df['Continue HT'] == '⏳'])}")
