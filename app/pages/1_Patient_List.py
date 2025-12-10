"""Patient List Page - View and manage patient records."""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus, APCMStatus
from data_loader import import_all_data, get_import_summary

st.set_page_config(
    page_title="Patient List - Patient Explorer",
    page_icon="📋",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and permission to view patients
user = require_login()
require_permission("view_patients")
show_user_menu()

st.title("📋 Patient List")
st.markdown("View and manage patient records for consent outreach.")
st.divider()


def load_patients_from_db():
    """Load all patients with their consent status."""
    session = get_session()
    try:
        patients = session.query(Patient).all()

        data = []
        for p in patients:
            consent_status = "No record"
            if p.consent:
                consent_status = p.consent.status.value.replace("_", " ").title()

            # Format display name with preferred name
            display_name = p.first_name
            if p.preferred_name:
                display_name += f' "{p.preferred_name}"'

            data.append({
                "MRN": p.mrn,
                "Last Name": p.last_name,
                "First Name": display_name,
                "DOB": p.date_of_birth,
                "Phone": p.phone or "",
                "Spruce Match": "✅" if p.spruce_matched else "❌",
                "Match Method": p.spruce_match_method or "",
                "APCM": "✅" if p.apcm_enrolled else "",
                "Consent Status": consent_status,
            })

        return pd.DataFrame(data)
    finally:
        session.close()


# Sidebar
with st.sidebar:
    # Import section at top
    st.subheader("📥 Data Import")

    # Show current database summary
    summary = get_import_summary()

    if summary["total_patients"] > 0:
        st.caption(f"**Database:** {summary['total_patients']} patients")
        st.caption(f"Spruce matched: {summary['spruce_matched']}")
        st.caption(f"APCM active: {summary['apcm_active']}")
    else:
        st.caption("Database is empty")

    st.divider()

    # Single unified import button (requires edit permission)
    can_import = has_permission("edit_patients")
    if st.button("🔄 Import All Data", use_container_width=True, type="primary", disabled=not can_import):
        if not can_import:
            st.warning("You don't have permission to import data")
            st.stop()
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(step: str, current: int, total: int):
            progress_bar.progress(current / total)
            status_text.text(step)

        try:
            results = import_all_data(progress_callback=update_progress)

            # Show results
            st.success(f"""
            **Import Complete!**
            - Patients: {results['patients_imported']} new, {results['patients_updated']} updated
            - Spruce matched: {results['spruce_matched']} of {results['spruce_total']} contacts
            - APCM enrolled: {results['apcm_imported']}
            """)

            if results["errors"] > 0:
                st.warning(f"Errors: {results['errors']}")

            st.rerun()

        except FileNotFoundError as e:
            st.error(f"File not found: {e}")
        except ConnectionError as e:
            st.error(f"Spruce API error: {e}")
        except Exception as e:
            st.error(f"Import error: {e}")

    st.caption("Imports patients, matches with Spruce API, and loads APCM data in one step.")

    st.divider()

    # Filters
    st.subheader("🔍 Filters")

    filter_matched = st.selectbox(
        "Spruce Match Status",
        ["All", "Matched Only", "Unmatched Only"]
    )

    filter_apcm = st.selectbox(
        "APCM Status",
        ["All", "APCM Enrolled", "Not APCM"]
    )

    filter_consent = st.selectbox(
        "Consent Status",
        ["All", "Pending", "Consented", "Declined", "No Response"]
    )

    search_term = st.text_input("Search (MRN or Name)", "")


# Load and display patients
df = load_patients_from_db()

if df.empty:
    st.info("""
    **No patients in database yet.**

    **To add patient data:**

    1. **Add Data page** - Upload documents, paste screenshots from your EMR, or import from OneNote
    2. **Import from Azure** - Patient data syncs automatically from Azure storage when configured

    Go to **Add Data** in the sidebar to get started.

    *Legacy import: If you have Excel files in the `data/` folder, click "Import All Data" in the sidebar.*
    """)
else:
    # Apply filters
    if filter_matched == "Matched Only":
        df = df[df["Spruce Match"] == "✅"]
    elif filter_matched == "Unmatched Only":
        df = df[df["Spruce Match"] == "❌"]

    if filter_apcm == "APCM Enrolled":
        df = df[df["APCM"] == "✅"]
    elif filter_apcm == "Not APCM":
        df = df[df["APCM"] != "✅"]

    if filter_consent != "All":
        df = df[df["Consent Status"] == filter_consent]

    if search_term:
        mask = (
            df["MRN"].str.contains(search_term, case=False, na=False) |
            df["Last Name"].str.contains(search_term, case=False, na=False) |
            df["First Name"].str.contains(search_term, case=False, na=False)
        )
        df = df[mask]

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Showing", f"{len(df)} patients")
    with col2:
        matched_count = len(df[df["Spruce Match"] == "✅"])
        st.metric("Spruce Matched", matched_count)
    with col3:
        apcm_count = len(df[df["APCM"] == "✅"])
        st.metric("APCM Enrolled", apcm_count)
    with col4:
        pending_count = len(df[df["Consent Status"] == "Pending"])
        st.metric("Pending Consent", pending_count)

    st.divider()

    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MRN": st.column_config.TextColumn("MRN", width="small"),
            "Last Name": st.column_config.TextColumn("Last Name", width="medium"),
            "First Name": st.column_config.TextColumn("First Name", width="medium"),
            "DOB": st.column_config.TextColumn("DOB", width="small"),
            "Phone": st.column_config.TextColumn("Phone", width="small"),
            "Spruce Match": st.column_config.TextColumn("Spruce", width="small"),
            "Match Method": st.column_config.TextColumn("Match By", width="small"),
            "APCM": st.column_config.TextColumn("APCM", width="small"),
            "Consent Status": st.column_config.TextColumn("Consent", width="medium"),
        }
    )

    # Export option (requires export_data permission for PHI)
    st.divider()

    col1, col2 = st.columns([3, 1])
    with col2:
        can_export = has_permission("export_data")
        if can_export:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📤 Export to CSV",
                data=csv,
                file_name="patient_list.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button(
                "📤 Export to CSV",
                disabled=True,
                use_container_width=True,
                help="You don't have permission to export PHI data"
            )
