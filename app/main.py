"""Patient Explorer - Streamlit Application

HIPAA-compliant patient consent tracking and outreach tool.
Runs locally only (localhost:8501) for PHI protection.
"""

import streamlit as st
import base64
from pathlib import Path
from database import init_db, get_session
from database.models import Patient, Consent, ConsentStatus


def get_image_base64(image_path: Path) -> str:
    """Load an image and return as base64 string for HTML embedding."""
    if image_path.exists():
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


# Asset paths
ASSETS_DIR = Path(__file__).parent / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"

# Page configuration
st.set_page_config(
    page_title="Patient Explorer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database on first run
@st.cache_resource
def initialize_database():
    """Initialize database tables (runs once)."""
    init_db()
    # Ensure admin user exists
    from auth import ensure_admin_exists
    ensure_admin_exists()
    return True

initialize_database()

# Authentication
from auth import require_login, show_user_menu

# Require login for main app
user = require_login()

# Show user menu in sidebar
show_user_menu()


def get_consent_stats():
    """Get consent tracking statistics."""
    session = get_session()
    try:
        total = session.query(Patient).count()
        matched = session.query(Patient).filter(Patient.spruce_matched == True).count()

        # Consent stats
        consented = session.query(Consent).filter(
            Consent.status == ConsentStatus.CONSENTED
        ).count()
        declined = session.query(Consent).filter(
            Consent.status == ConsentStatus.DECLINED
        ).count()
        pending = session.query(Consent).filter(
            Consent.status == ConsentStatus.PENDING
        ).count()
        no_response = session.query(Consent).filter(
            Consent.status == ConsentStatus.NO_RESPONSE
        ).count()

        return {
            "total": total,
            "matched": matched,
            "consented": consented,
            "declined": declined,
            "pending": pending,
            "no_response": no_response,
        }
    finally:
        session.close()


# Main page content
st.title("Patient Explorer")

# Load brand icons for values grid
icon_stethoscope = get_image_base64(ICONS_DIR / "HTnav_stethoscope.png")
icon_clipboard = get_image_base64(ICONS_DIR / "HTnav_clipboard.png")
icon_team = get_image_base64(ICONS_DIR / "HTnav_team.png")
icon_ribbon = get_image_base64(ICONS_DIR / "HTnav_ribbon.png")
icon_medical_bag = get_image_base64(ICONS_DIR / "HTnav_medical_bag_large.png")

# Welcome section with mission and values
welcome_col1, welcome_col2 = st.columns([3, 1])

with welcome_col1:
    st.markdown(f"""
    <style>
    .mission-box {{
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 24px;
        color: white;
    }}
    .mission-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;
    }}
    .mission-header img {{
        width: 48px;
        height: 48px;
    }}
    .mission-box h2 {{
        color: #ffffff;
        margin: 0;
        font-size: 1.5rem;
    }}
    .mission-box p {{
        color: #e8f4f8;
        font-size: 1.05rem;
        line-height: 1.6;
    }}
    .mission-box .tagline {{
        font-style: italic;
        color: #a8d4e6;
        border-left: 3px solid #4a9ece;
        padding-left: 16px;
        margin: 16px 0;
    }}
    .values-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-top: 16px;
    }}
    .value-item {{
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }}
    .value-item img {{
        width: 32px;
        height: 32px;
        margin-bottom: 8px;
    }}
    .value-item strong {{
        color: #ffffff;
        display: block;
        margin-bottom: 4px;
    }}
    .value-item span {{
        color: #c8e4f0;
        font-size: 0.9rem;
    }}
    </style>

    <div class="mission-box">
        <div class="mission-header">
            <img src="data:image/png;base64,{icon_medical_bag}" alt="Home Team">
            <h2>Welcome to Home Team</h2>
        </div>
        <p class="tagline">
            "We build and defend Home Team as the healthcare platform where medical
            professionals have personal relationships with their patients and
            respectful arrangements with their employers."
        </p>
        <p>
            Every patient in this system represents a relationship built on trust.
            As we navigate this transition together, we're not just managing records —
            we're preserving the connections that make healthcare personal.
        </p>
        <div class="values-grid">
            <div class="value-item">
                <img src="data:image/png;base64,{icon_stethoscope}" alt="Personal Care">
                <strong>Personal Care</strong>
                <span>Patients are people, not numbers</span>
            </div>
            <div class="value-item">
                <img src="data:image/png;base64,{icon_clipboard}" alt="Trust">
                <strong>Trust & Respect</strong>
                <span>Earned through every interaction</span>
            </div>
            <div class="value-item">
                <img src="data:image/png;base64,{icon_team}" alt="Team">
                <strong>Team Excellence</strong>
                <span>Supporting each other's success</span>
            </div>
            <div class="value-item">
                <img src="data:image/png;base64,{icon_ribbon}" alt="Growth">
                <strong>Continuous Growth</strong>
                <span>Learning and improving together</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with welcome_col2:
    # Display patient onboarding illustration
    onboarding_image = IMAGES_DIR / "Image_patient onboarding.png"
    if onboarding_image.exists():
        st.image(str(onboarding_image), use_container_width=True)

st.subheader("Consent Outreach & Tracking Dashboard")
st.divider()

# Check if patients are loaded
stats = get_consent_stats()

if stats["total"] == 0:
    st.info("📋 No patient data loaded yet.")

    st.markdown("""
    ### Getting Started

    Patient data is stored securely in **Azure storage** and will load automatically
    when available. To add new patient data:

    1. **Go to Add Data** → Use the sidebar to navigate to the **Add Data** page
    2. **Upload documents** → Screenshots, PDFs, or images from your EMR
    3. **Use AI extraction** → Let the AI help extract patient information
    4. **Import from OneNote** → Connect your clinic's OneNote notebooks

    The system will automatically sync patient data from Azure storage when configured.
    """)
else:
    # Dashboard metrics
    st.subheader("📊 Consent Tracking Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Patients",
            value=stats["total"],
            help="Total patients in the system"
        )

    with col2:
        st.metric(
            label="Spruce Matched",
            value=stats["matched"],
            delta=f"{(stats['matched']/stats['total']*100):.0f}%" if stats["total"] > 0 else "0%",
            help="Patients found in Spruce Health"
        )

    with col3:
        st.metric(
            label="Consented",
            value=stats["consented"],
            delta=f"{(stats['consented']/stats['total']*100):.0f}%" if stats["total"] > 0 else "0%",
            delta_color="normal",
            help="Patients who consented to records retention"
        )

    with col4:
        st.metric(
            label="Pending",
            value=stats["pending"] + stats["no_response"],
            help="Patients awaiting consent decision"
        )

    st.divider()

    # Consent status breakdown
    st.subheader("📋 Consent Status Breakdown")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        | Status | Count |
        |--------|-------|
        | ✅ Consented | {stats['consented']} |
        | ❌ Declined | {stats['declined']} |
        | ⏳ Pending | {stats['pending']} |
        | 📭 No Response | {stats['no_response']} |
        """)

    with col2:
        # Simple progress toward goal
        if stats["total"] > 0:
            progress = (stats["consented"] + stats["declined"]) / stats["total"]
            st.progress(progress, text=f"Outreach Progress: {progress*100:.1f}% complete")

            remaining = stats["total"] - stats["consented"] - stats["declined"]
            st.caption(f"{remaining} patients still need to be contacted")

# Footer
st.divider()
col1, col2 = st.columns([2, 1])
with col1:
    st.caption("Patient Explorer v1.0 | Home Team Medical Services")
    st.caption("Building personal healthcare, one patient at a time.")
with col2:
    st.caption("HIPAA Compliant | localhost:8501")
