"""Patient Explorer - Interactive patient chart view with navigation icons.

Inspired by athenaOne chart interface with:
- Left navigation bar with icon buttons
- Patient header with demographics and tags
- Section views for clinical data
"""

import json
import base64
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="Patient Explorer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize database (needed for auth)
from database import init_db
init_db()

from auth import require_login, show_user_menu

# Require login
user = require_login()
show_user_menu()

# =============================================================================
# Configuration
# =============================================================================

ICONS_PATH = Path(__file__).parent.parent / "assets" / "icons"
DATA_PATH = Path(__file__).parent.parent.parent / "data" / "patients_master.json"

# Navigation sections with icons
NAV_SECTIONS = [
    ("search", "Search", "HTnav_search.png", "Find patients"),
    ("overview", "Overview", "HTnav_medical_bag.png", "Patient summary"),
    ("encounters", "Encounters", "HTnav_stethoscope.png", "Visit history"),
    ("medications", "Medications", "HTnav_Rx_bottle.png", "Current medications"),
    ("problems", "Problems", "HTnav_Problem List.png", "Problem list"),
    ("vitals", "Vitals", "HTnav_vitals.png", "Vital signs"),
    ("allergies", "Allergies", "HTnav_allergies.png", "Allergy list"),
    ("documents", "Documents", "HTnav_folder.png", "Screenshots & files"),
    ("communications", "Communications", "HTnav_phone.png", "Spruce messages"),
    ("care_plan", "Care Plan", "HTnav_clipboard.png", "APCM care plan"),
    ("billing", "Billing", "HTnav_invoice.png", "Insurance & billing"),
]

# Tag colors
TAG_COLORS = {
    "team_green": "#28a745",
    "team_lachandra": "#17a2b8",
    "team_lindsay": "#6f42c1",
    "team_jenny": "#fd7e14",
    "loc_il": "#20c997",
    "loc_al": "#e83e8c",
    "loc_mc": "#dc3545",
    "loc_office": "#6c757d",
    "loc_home": "#007bff",
    "apcm": "#ffc107",
    "consent_pending": "#fd7e14",
    "consent_obtained": "#28a745",
    "high_priority": "#dc3545",
}


# =============================================================================
# Data Loading
# =============================================================================

@st.cache_data(ttl=300)
def load_patients_json() -> Dict[str, Any]:
    """Load patient data from JSON file."""
    if not DATA_PATH.exists():
        return {"patients": [], "record_count": 0}

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_patient_by_id(patient_id: str) -> Optional[Dict[str, Any]]:
    """Find patient by UUID."""
    data = load_patients_json()
    for patient in data.get("patients", []):
        if patient.get("id") == patient_id:
            return patient
    return None


def get_patient_by_mrn(mrn: str) -> Optional[Dict[str, Any]]:
    """Find patient by MRN."""
    data = load_patients_json()
    for patient in data.get("patients", []):
        if patient.get("demographics", {}).get("mrn") == mrn:
            return patient
    return None


def search_patients(query: str) -> List[Dict[str, Any]]:
    """Search patients by name, MRN, or phone."""
    data = load_patients_json()
    query = query.lower().strip()
    results = []

    for patient in data.get("patients", []):
        demo = patient.get("demographics", {})

        # Search fields
        first = (demo.get("first_name") or "").lower()
        last = (demo.get("last_name") or "").lower()
        mrn = (demo.get("mrn") or "").lower()
        phone = (demo.get("phone_home") or "").replace("-", "").replace("(", "").replace(")", "").replace(" ", "")

        if (query in first or query in last or
            query in mrn or query in f"{first} {last}" or
            query in phone):
            results.append(patient)

    return results[:50]  # Limit to 50 results


# =============================================================================
# Icon Helpers
# =============================================================================

def get_icon_base64(icon_name: str) -> Optional[str]:
    """Load icon as base64 for embedding in HTML."""
    icon_path = ICONS_PATH / icon_name
    if icon_path.exists():
        with open(icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def icon_button(key: str, label: str, icon_name: str, tooltip: str, selected: bool = False) -> bool:
    """Render an icon button and return True if clicked."""
    icon_b64 = get_icon_base64(icon_name)

    bg_color = "#e3f2fd" if selected else "transparent"
    border = "2px solid #1976d2" if selected else "1px solid #ddd"

    if icon_b64:
        st.markdown(f"""
        <style>
        .icon-btn-{key} {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px;
            margin: 4px 0;
            border: {border};
            border-radius: 8px;
            background: {bg_color};
            cursor: pointer;
            transition: all 0.2s;
        }}
        .icon-btn-{key}:hover {{
            background: #e3f2fd;
            border-color: #1976d2;
        }}
        .icon-btn-{key} img {{
            width: 32px;
            height: 32px;
        }}
        .icon-btn-{key} span {{
            font-size: 10px;
            margin-top: 4px;
            color: #333;
        }}
        </style>
        """, unsafe_allow_html=True)

    return st.button(f"{'🔹 ' if selected else ''}{label}", key=f"nav_{key}",
                    use_container_width=True, type="primary" if selected else "secondary")


# =============================================================================
# UI Components
# =============================================================================

def render_patient_header(patient: Dict[str, Any]):
    """Render patient header with demographics and tags."""
    demo = patient.get("demographics", {})
    tags = patient.get("tags", {})
    identifiers = patient.get("identifiers", {})
    apcm = patient.get("apcm", {})

    # Calculate age
    dob = demo.get("date_of_birth")
    age = ""
    if dob:
        try:
            birth = datetime.fromisoformat(dob)
            age = f" ({(datetime.now() - birth).days // 365}y)"
        except:
            pass

    # Build tag pills
    all_tags = []
    for team in tags.get("team", []):
        all_tags.append((team, TAG_COLORS.get(team, "#6c757d")))
    if tags.get("loc"):
        all_tags.append((tags["loc"], TAG_COLORS.get(tags["loc"], "#6c757d")))
    for status in tags.get("status", []):
        all_tags.append((status, TAG_COLORS.get(status, "#6c757d")))

    tag_html = " ".join([
        f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:12px;margin-right:4px;">{tag.replace("_", " ").title()}</span>'
        for tag, color in all_tags
    ])

    # Header layout
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);padding:20px;border-radius:10px;color:white;margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <h1 style="margin:0;color:white;">{demo.get('last_name', '')}, {demo.get('first_name', '')}{age}</h1>
                <p style="margin:5px 0;opacity:0.9;">
                    DOB: {dob or 'Unknown'} | MRN: {demo.get('mrn', 'N/A')} |
                    Phone: {demo.get('phone_home') or 'N/A'}
                </p>
                <div style="margin-top:10px;">{tag_html}</div>
            </div>
            <div style="text-align:right;">
                {f'<span style="background:#ffc107;color:#000;padding:4px 12px;border-radius:4px;font-weight:bold;">APCM {apcm.get("level", "")}</span>' if apcm.get('enrolled') else ''}
                <br/>
                {f'<small>Spruce ID: {identifiers.get("spruce_id", "")[:8]}...</small>' if identifiers.get('spruce_id') else '<small>Not matched to Spruce</small>'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_search_section():
    """Render patient search interface."""
    st.subheader("🔍 Patient Search")

    data = load_patients_json()
    stats = data.get("statistics", {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Patients", data.get("record_count", 0))
    col2.metric("Spruce Matched", stats.get("matched_by_phone", 0) + stats.get("matched_by_name_dob", 0))
    col3.metric("APCM Records", stats.get("apcm_loaded", 0))
    col4.metric("Unmatched", stats.get("unmatched", 0))

    st.divider()

    query = st.text_input("Search by name, MRN, or phone:", key="patient_search",
                         placeholder="Enter patient name, MRN, or phone number...")

    if query and len(query) >= 2:
        results = search_patients(query)

        if results:
            st.success(f"Found {len(results)} patient(s)")

            for patient in results:
                demo = patient.get("demographics", {})
                apcm = patient.get("apcm", {})
                identifiers = patient.get("identifiers", {})

                with st.container():
                    cols = st.columns([3, 2, 2, 1])

                    cols[0].write(f"**{demo.get('last_name', '')}, {demo.get('first_name', '')}**")
                    cols[1].write(f"MRN: {demo.get('mrn', 'N/A')}")
                    cols[2].write(f"DOB: {demo.get('date_of_birth', 'N/A')}")

                    if cols[3].button("View", key=f"view_{patient.get('id')}"):
                        st.session_state.selected_patient_id = patient.get("id")
                        st.session_state.nav_section = "overview"
                        st.rerun()
        else:
            st.warning("No patients found matching your search.")
    else:
        # Show recent/all patients
        st.caption("Enter at least 2 characters to search, or browse all patients below:")

        patients = data.get("patients", [])[:100]  # Show first 100

        if patients:
            # Create simple table
            rows = []
            for p in patients:
                demo = p.get("demographics", {})
                rows.append({
                    "Name": f"{demo.get('last_name', '')}, {demo.get('first_name', '')}",
                    "MRN": demo.get("mrn", ""),
                    "DOB": demo.get("date_of_birth", ""),
                    "Phone": demo.get("phone_home", ""),
                    "APCM": "Yes" if p.get("apcm", {}).get("enrolled") else "",
                    "Spruce": "Yes" if p.get("identifiers", {}).get("spruce_id") else "",
                })

            import pandas as pd
            df = pd.DataFrame(rows)

            # Show as interactive table
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            if event.selection and event.selection.rows:
                selected_idx = event.selection.rows[0]
                selected_patient = patients[selected_idx]
                st.session_state.selected_patient_id = selected_patient.get("id")
                st.session_state.nav_section = "overview"
                st.rerun()


def render_overview_section(patient: Dict[str, Any]):
    """Render patient overview/summary."""
    st.subheader("📋 Patient Overview")

    demo = patient.get("demographics", {})
    apcm = patient.get("apcm", {})
    consent = patient.get("consent", {})
    scheduling = patient.get("scheduling", {})
    clinical = patient.get("clinical", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Demographics")
        st.write(f"**Name:** {demo.get('first_name', '')} {demo.get('last_name', '')}")
        st.write(f"**DOB:** {demo.get('date_of_birth', 'N/A')}")
        st.write(f"**MRN:** {demo.get('mrn', 'N/A')}")
        st.write(f"**Phone:** {demo.get('phone_home', 'N/A')}")
        st.write(f"**Email:** {demo.get('email', 'N/A')}")

        addr = demo.get("address", {})
        if addr:
            st.write(f"**Address:** {addr.get('line1', '')}, {addr.get('city', '')} {addr.get('state', '')} {addr.get('zip', '')}")

    with col2:
        st.markdown("#### Status")

        # APCM Status
        if apcm.get("enrolled"):
            st.success(f"APCM Enrolled - Level {apcm.get('level', 'N/A')}")
            if apcm.get("icd_codes"):
                st.caption(f"ICD Codes: {', '.join(apcm.get('icd_codes', []))}")
        else:
            st.info("Not enrolled in APCM")

        # Consent Status
        consent_status = consent.get("status", "pending")
        if consent_status == "consented":
            st.success(f"Consent: Obtained")
        elif consent_status == "declined":
            st.error("Consent: Declined")
        else:
            st.warning(f"Consent: {consent_status.replace('_', ' ').title()}")

        # Last Visit
        if scheduling.get("last_visit_date"):
            st.write(f"**Last Visit:** {scheduling.get('last_visit_date')}")

    st.divider()

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Problems", len(clinical.get("problems", [])))
    col2.metric("Medications", len(clinical.get("medications", [])))
    col3.metric("Allergies", len(clinical.get("allergies", [])))
    col4.metric("Screenshots", len(patient.get("screenshots", [])))


def render_medications_section(patient: Dict[str, Any]):
    """Render medications list."""
    st.subheader("💊 Medications")

    medications = patient.get("clinical", {}).get("medications", [])

    if not medications:
        st.info("No medications recorded. Capture screenshots from EMR to populate.")
        return

    for med in medications:
        with st.expander(f"**{med.get('name', 'Unknown')}** - {med.get('dosage', '')}"):
            st.write(f"**Frequency:** {med.get('frequency', 'N/A')}")
            st.write(f"**Route:** {med.get('route', 'N/A')}")
            st.write(f"**Prescriber:** {med.get('prescriber', 'N/A')}")
            if med.get("indication"):
                st.write(f"**Indication:** {med.get('indication')}")


def render_problems_section(patient: Dict[str, Any]):
    """Render problem list."""
    st.subheader("📝 Problem List")

    problems = patient.get("clinical", {}).get("problems", [])

    if not problems:
        st.info("No problems recorded. Capture screenshots from EMR to populate.")
        return

    for prob in problems:
        status_icon = "🟢" if prob.get("status") == "active" else "⚪"
        with st.expander(f"{status_icon} **{prob.get('description', 'Unknown')}** ({prob.get('icd10', '')})"):
            st.write(f"**Status:** {prob.get('status', 'N/A')}")
            if prob.get("onset_date"):
                st.write(f"**Onset:** {prob.get('onset_date')}")
            if prob.get("notes"):
                st.write(f"**Notes:** {prob.get('notes')}")


def render_allergies_section(patient: Dict[str, Any]):
    """Render allergy list."""
    st.subheader("⚠️ Allergies")

    allergies = patient.get("clinical", {}).get("allergies", [])

    if not allergies:
        st.info("No allergies recorded. Capture screenshots from EMR to populate.")
        return

    for allergy in allergies:
        severity_color = {"severe": "🔴", "moderate": "🟡", "mild": "🟢"}.get(
            allergy.get("severity", ""), "⚪"
        )
        st.write(f"{severity_color} **{allergy.get('allergen', 'Unknown')}** - {allergy.get('reaction', 'N/A')}")


def render_vitals_section(patient: Dict[str, Any]):
    """Render vital signs."""
    st.subheader("❤️ Vital Signs")

    vitals = patient.get("clinical", {}).get("vitals_latest", {})

    if not vitals:
        st.info("No vitals recorded. Capture screenshots from EMR to populate.")
        return

    col1, col2, col3, col4 = st.columns(4)

    bp_sys = vitals.get("blood_pressure_systolic")
    bp_dia = vitals.get("blood_pressure_diastolic")
    if bp_sys and bp_dia:
        col1.metric("Blood Pressure", f"{bp_sys}/{bp_dia}")

    if vitals.get("heart_rate"):
        col2.metric("Heart Rate", f"{vitals.get('heart_rate')} bpm")

    if vitals.get("weight_lbs"):
        col3.metric("Weight", f"{vitals.get('weight_lbs')} lbs")

    if vitals.get("oxygen_saturation"):
        col4.metric("O2 Sat", f"{vitals.get('oxygen_saturation')}%")


def render_documents_section(patient: Dict[str, Any]):
    """Render screenshots and documents."""
    st.subheader("📁 Documents & Screenshots")

    screenshots = patient.get("screenshots", [])

    if not screenshots:
        st.info("No screenshots captured yet.")

        st.markdown("### Capture Screenshots")
        st.write("Use the screenshot capture tool to add EMR screenshots to this patient's record.")

        if st.button("📷 Go to Screenshot Capture", type="primary"):
            st.switch_page("pages/21_Screenshot_Capture.py")
        return

    # Group by category
    by_category = {}
    for ss in screenshots:
        cat = ss.get("category", "other")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(ss)

    for category, items in by_category.items():
        with st.expander(f"**{category.replace('_', ' ').title()}** ({len(items)} files)"):
            for item in items:
                st.write(f"📄 {item.get('file_name', 'Unknown')} - {item.get('capture_date', 'N/A')}")


def render_communications_section(patient: Dict[str, Any]):
    """Render Spruce communications log."""
    st.subheader("📱 Communications")

    communications = patient.get("communications", [])
    identifiers = patient.get("identifiers", {})

    if not identifiers.get("spruce_id"):
        st.warning("Patient not matched to Spruce. Cannot display communications.")
        return

    if not communications:
        st.info("No communications recorded in patient file.")
        st.caption(f"Spruce ID: {identifiers.get('spruce_id')}")
        return

    for comm in communications[:20]:  # Show last 20
        direction_icon = "📤" if comm.get("direction") == "outbound" else "📥"
        st.write(f"{direction_icon} **{comm.get('date', '')}** - {comm.get('type', 'message')}")
        if comm.get("summary"):
            st.caption(comm.get("summary"))


def render_care_plan_section(patient: Dict[str, Any]):
    """Render APCM care plan."""
    st.subheader("📋 Care Plan")

    care_plan = patient.get("care_plan", {})
    apcm = patient.get("apcm", {})

    if not apcm.get("enrolled"):
        st.info("Patient not enrolled in APCM. Care plan not applicable.")
        return

    if not care_plan:
        st.warning("No care plan documented yet.")
        st.write("Create a care plan for this APCM patient.")
        return

    st.write(f"**Created:** {care_plan.get('created_date', 'N/A')}")
    st.write(f"**Last Updated:** {care_plan.get('last_updated', 'N/A')}")

    # Goals
    goals = care_plan.get("goals", [])
    if goals:
        st.markdown("#### Goals")
        for goal in goals:
            status_icon = "✅" if goal.get("status") == "achieved" else "🎯"
            st.write(f"{status_icon} {goal.get('goal', '')}")


def render_billing_section(patient: Dict[str, Any]):
    """Render insurance and billing info."""
    st.subheader("💰 Insurance & Billing")

    insurance = patient.get("insurance", {})
    apcm = patient.get("apcm", {})

    primary = insurance.get("primary", {})
    if primary:
        st.markdown("#### Primary Insurance")
        st.write(f"**Provider:** {primary.get('provider', 'N/A')}")
        st.write(f"**Plan:** {primary.get('plan_name', 'N/A')}")
        st.write(f"**Member ID:** {primary.get('member_id', 'N/A')}")
    else:
        st.info("No primary insurance on file.")

    if apcm.get("enrolled"):
        st.markdown("#### APCM Billing")
        st.write(f"**Level:** {apcm.get('level', 'N/A')}")
        st.write(f"**Last Billed:** {apcm.get('last_billing_date', 'N/A')}")


def render_encounters_section(patient: Dict[str, Any]):
    """Render encounter/visit history."""
    st.subheader("🩺 Encounters")

    encounters = patient.get("encounters", [])

    if not encounters:
        st.info("No encounters recorded. Capture screenshots from EMR to populate.")
        return

    for enc in encounters[:10]:  # Show last 10
        type_icon = {"office_visit": "🏥", "telehealth": "💻", "home_visit": "🏠",
                    "phone_call": "📞"}.get(enc.get("type", ""), "📋")

        with st.expander(f"{type_icon} **{enc.get('date', 'N/A')}** - {enc.get('type', 'visit').replace('_', ' ').title()}"):
            st.write(f"**Provider:** {enc.get('provider', 'N/A')}")
            if enc.get("chief_complaint"):
                st.write(f"**Chief Complaint:** {enc.get('chief_complaint')}")
            if enc.get("assessment"):
                st.write(f"**Assessment:** {enc.get('assessment')}")


# =============================================================================
# Main App
# =============================================================================

def main():
    # Initialize session state
    if "selected_patient_id" not in st.session_state:
        st.session_state.selected_patient_id = None
    if "nav_section" not in st.session_state:
        st.session_state.nav_section = "search"

    # Check if data file exists
    if not DATA_PATH.exists():
        st.error("Patient data file not found!")
        st.write(f"Expected: `{DATA_PATH}`")
        st.info("Run the patient consolidator to generate the data file:")
        st.code("python -m app.services.patient_consolidator")
        return

    # Layout: Navigation sidebar + Main content
    nav_col, main_col = st.columns([1, 5])

    # Navigation sidebar
    with nav_col:
        st.markdown("### Navigate")

        for key, label, icon, tooltip in NAV_SECTIONS:
            is_selected = st.session_state.nav_section == key

            # Only show patient-specific sections if patient selected
            if key != "search" and not st.session_state.selected_patient_id:
                continue

            if st.button(
                f"{'▶ ' if is_selected else ''}{label}",
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
                help=tooltip,
            ):
                st.session_state.nav_section = key
                st.rerun()

        # Clear selection button
        if st.session_state.selected_patient_id:
            st.divider()
            if st.button("← Back to Search", use_container_width=True):
                st.session_state.selected_patient_id = None
                st.session_state.nav_section = "search"
                st.rerun()

    # Main content area
    with main_col:
        current_section = st.session_state.nav_section
        patient_id = st.session_state.selected_patient_id

        if current_section == "search" or not patient_id:
            render_search_section()
        else:
            # Load selected patient
            patient = get_patient_by_id(patient_id)

            if not patient:
                st.error("Patient not found!")
                st.session_state.selected_patient_id = None
                st.rerun()
                return

            # Render patient header
            render_patient_header(patient)

            # Render appropriate section
            section_renderers = {
                "overview": render_overview_section,
                "encounters": render_encounters_section,
                "medications": render_medications_section,
                "problems": render_problems_section,
                "vitals": render_vitals_section,
                "allergies": render_allergies_section,
                "documents": render_documents_section,
                "communications": render_communications_section,
                "care_plan": render_care_plan_section,
                "billing": render_billing_section,
            }

            renderer = section_renderers.get(current_section, render_overview_section)
            renderer(patient)


if __name__ == "__main__":
    main()
