"""Follow-Up Queue - Track and manage consent outreach follow-ups."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus

st.set_page_config(
    page_title="Follow-Up Queue - Patient Explorer",
    page_icon="📞",
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

st.title("📞 Follow-Up Queue")
st.markdown("Track patients who need follow-up outreach based on the consent campaign timeline.")
st.divider()


def get_follow_up_patients():
    """Get patients grouped by follow-up urgency."""
    session = get_session()
    try:
        now = datetime.utcnow()

        # Get all patients with pending/no_response status who have been contacted
        patients = session.query(Patient).join(Consent).filter(
            Consent.status.in_([ConsentStatus.PENDING, ConsentStatus.NO_RESPONSE, ConsentStatus.INVITATION_SENT]),
            Consent.last_outreach_date.isnot(None)
        ).all()

        results = {
            "overdue_day14": [],  # 14+ days - need phone call
            "due_day14": [],       # 14 days - final reminder
            "due_day7": [],        # 7 days - second reminder
            "due_day3": [],        # 3 days - first reminder
            "recently_contacted": [],  # <3 days - wait
            "never_contacted": [],     # Never contacted
        }

        for p in patients:
            if not p.consent or not p.consent.last_outreach_date:
                results["never_contacted"].append(p)
                continue

            days_since = (now - p.consent.last_outreach_date).days

            if days_since >= 21:
                results["overdue_day14"].append((p, days_since))
            elif days_since >= 14:
                results["due_day14"].append((p, days_since))
            elif days_since >= 7:
                results["due_day7"].append((p, days_since))
            elif days_since >= 3:
                results["due_day3"].append((p, days_since))
            else:
                results["recently_contacted"].append((p, days_since))

        # Get patients never contacted (no consent record or no outreach date)
        never_contacted = session.query(Patient).filter(
            Patient.spruce_matched == True
        ).outerjoin(Consent).filter(
            (Consent.id.is_(None)) |
            (Consent.last_outreach_date.is_(None))
        ).all()

        results["never_contacted"] = never_contacted

        return results

    finally:
        session.close()


def mark_as_contacted(patient_id: int, method: str = "sms") -> bool:
    """Mark a patient as contacted (update last_outreach_date)."""
    session = get_session()
    try:
        patient = session.query(Patient).get(patient_id)
        if not patient:
            return False

        if not patient.consent:
            consent = Consent(patient_id=patient_id, status=ConsentStatus.INVITATION_SENT)
            session.add(consent)
            patient.consent = consent

        patient.consent.last_outreach_date = datetime.utcnow()
        patient.consent.outreach_attempts += 1
        patient.consent.outreach_method = method

        if patient.consent.status == ConsentStatus.PENDING:
            patient.consent.status = ConsentStatus.INVITATION_SENT

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error: {e}")
        return False
    finally:
        session.close()


# Sidebar with summary
with st.sidebar:
    st.subheader("📊 Queue Summary")

    follow_ups = get_follow_up_patients()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Need Phone Call", len(follow_ups["overdue_day14"]))
        st.metric("Day 14 Reminder", len(follow_ups["due_day14"]))
        st.metric("Day 7 Reminder", len(follow_ups["due_day7"]))
    with col2:
        st.metric("Day 3 Reminder", len(follow_ups["due_day3"]))
        st.metric("Recently Contacted", len(follow_ups["recently_contacted"]))
        st.metric("Never Contacted", len(follow_ups["never_contacted"]))

    st.divider()

    st.markdown("""
    **Follow-Up Schedule:**
    - **Day 3**: Gentle reminder SMS
    - **Day 7**: Urgent reminder SMS
    - **Day 14**: Final SMS reminder
    - **Day 21+**: Phone call outreach
    """)

    st.divider()

    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()


# Main content tabs
tabs = st.tabs([
    f"🔴 Phone Call ({len(follow_ups['overdue_day14'])})",
    f"🟠 Day 14 ({len(follow_ups['due_day14'])})",
    f"🟡 Day 7 ({len(follow_ups['due_day7'])})",
    f"🟢 Day 3 ({len(follow_ups['due_day3'])})",
    f"⏳ Recent ({len(follow_ups['recently_contacted'])})",
    f"📭 Never ({len(follow_ups['never_contacted'])})",
])


def display_patient_queue(patients_with_days, queue_type: str, action_label: str):
    """Display a queue of patients with follow-up actions."""
    if not patients_with_days:
        st.info(f"No patients in {queue_type} queue.")
        return

    can_edit = has_permission("edit_consents")

    for p, days in patients_with_days:
        display_name = f"{p.last_name}, {p.first_name}"
        if p.preferred_name:
            display_name += f' "{p.preferred_name}"'

        apcm_badge = "🏥 APCM" if p.apcm_enrolled else ""

        with st.expander(f"**{display_name}** - {days} days ago {apcm_badge}"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.caption(f"**MRN:** {p.mrn}")
                st.caption(f"**Phone:** {p.phone or 'No phone on file'}")
                st.caption(f"**Attempts:** {p.consent.outreach_attempts if p.consent else 0}")

                last_method = p.consent.outreach_method if p.consent else "N/A"
                st.caption(f"**Last Method:** {last_method}")

            with col2:
                if p.consent and p.consent.notes:
                    st.caption("**Notes:**")
                    st.caption(p.consent.notes[:100])

            with col3:
                if can_edit:
                    if st.button(f"{action_label}", key=f"action_{p.id}", use_container_width=True):
                        if mark_as_contacted(p.id, "sms"):
                            st.success("Marked as contacted!")
                            st.rerun()

                    if queue_type == "phone":
                        if st.button("📞 Called", key=f"phone_{p.id}", use_container_width=True):
                            if mark_as_contacted(p.id, "phone"):
                                st.success("Marked as called!")
                                st.rerun()


def display_never_contacted(patients):
    """Display patients who have never been contacted."""
    if not patients:
        st.info("All Spruce-matched patients have been contacted at least once.")
        return

    can_edit = has_permission("edit_consents")

    st.caption(f"Found {len(patients)} patients who haven't been contacted yet.")

    # Group by APCM status
    apcm_patients = [p for p in patients if p.apcm_enrolled]
    non_apcm_patients = [p for p in patients if not p.apcm_enrolled]

    if apcm_patients:
        st.markdown("### 🏥 APCM Patients (Priority)")
        for p in apcm_patients[:20]:
            display_name = f"{p.last_name}, {p.first_name}"
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{display_name}** - {p.mrn} - {p.phone or 'No phone'}")
            with col2:
                if can_edit and st.button("📤 Sent Initial", key=f"init_{p.id}"):
                    if mark_as_contacted(p.id, "sms"):
                        st.success("Marked!")
                        st.rerun()

        if len(apcm_patients) > 20:
            st.caption(f"... and {len(apcm_patients) - 20} more APCM patients")

    if non_apcm_patients:
        st.markdown("### 👤 General Patients")
        for p in non_apcm_patients[:20]:
            display_name = f"{p.last_name}, {p.first_name}"
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"{display_name} - {p.mrn} - {p.phone or 'No phone'}")
            with col2:
                if can_edit and st.button("📤 Sent", key=f"init2_{p.id}"):
                    if mark_as_contacted(p.id, "sms"):
                        st.rerun()

        if len(non_apcm_patients) > 20:
            st.caption(f"... and {len(non_apcm_patients) - 20} more patients")


with tabs[0]:
    st.subheader("🔴 Need Phone Call (21+ Days)")
    st.markdown("These patients have not responded after multiple SMS attempts. **Phone call recommended.**")
    display_patient_queue(follow_ups["overdue_day14"], "phone", "📞 Mark Called")


with tabs[1]:
    st.subheader("🟠 Day 14 Final Reminder")
    st.markdown("Send **final SMS reminder** to these patients.")
    display_patient_queue(follow_ups["due_day14"], "day14", "📤 Send Final")


with tabs[2]:
    st.subheader("🟡 Day 7 Second Reminder")
    st.markdown("Send **second reminder** to these patients.")
    display_patient_queue(follow_ups["due_day7"], "day7", "📤 Send Day 7")


with tabs[3]:
    st.subheader("🟢 Day 3 First Reminder")
    st.markdown("Send **first follow-up reminder** to these patients.")
    display_patient_queue(follow_ups["due_day3"], "day3", "📤 Send Day 3")


with tabs[4]:
    st.subheader("⏳ Recently Contacted (<3 Days)")
    st.markdown("These patients were contacted recently. **Wait before follow-up.**")

    if follow_ups["recently_contacted"]:
        for p, days in follow_ups["recently_contacted"]:
            display_name = f"{p.last_name}, {p.first_name}"
            next_followup = 3 - days
            st.caption(f"• {display_name} ({p.mrn}) - contacted {days} day(s) ago - next follow-up in {next_followup} day(s)")
    else:
        st.info("No patients in the waiting period.")


with tabs[5]:
    st.subheader("📭 Never Contacted")
    st.markdown("These Spruce-matched patients have never received outreach.")
    display_never_contacted(follow_ups["never_contacted"])


# Batch actions section
st.divider()
st.subheader("📊 Batch Actions")

col1, col2, col3 = st.columns(3)

with col1:
    try:
        from sms_templates import get_follow_up_schedule

        st.markdown("### Export for Spruce")

        queue_to_export = st.selectbox(
            "Select Queue",
            [
                ("due_day3", "Day 3 Reminder"),
                ("due_day7", "Day 7 Reminder"),
                ("due_day14", "Day 14 Final"),
                ("overdue_day14", "Phone Call List"),
                ("never_contacted", "Never Contacted"),
            ],
            format_func=lambda x: x[1]
        )[0]

        if st.button("📥 Export Selected Queue"):
            patients_list = follow_ups[queue_to_export]

            export_data = []
            for item in patients_list:
                if isinstance(item, tuple):
                    p, days = item
                else:
                    p = item
                    days = 0

                export_data.append({
                    "MRN": p.mrn,
                    "Name": f"{p.first_name} {p.last_name}",
                    "Phone": p.phone or "",
                    "APCM": "Yes" if p.apcm_enrolled else "No",
                    "Days Since Contact": days,
                    "Attempts": p.consent.outreach_attempts if p.consent else 0,
                })

            if export_data:
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    f"📥 Download {len(export_data)} patients",
                    data=csv,
                    file_name=f"followup_{queue_to_export}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No patients in selected queue")

    except ImportError:
        st.info("SMS templates module not loaded")


with col2:
    st.markdown("### Quick Stats")

    total_pending = sum([
        len(follow_ups["overdue_day14"]),
        len(follow_ups["due_day14"]),
        len(follow_ups["due_day7"]),
        len(follow_ups["due_day3"]),
        len(follow_ups["recently_contacted"]),
    ])

    st.metric("Active Outreach", total_pending)
    st.metric("Never Contacted", len(follow_ups["never_contacted"]))

    # Calculate response rate
    session = get_session()
    try:
        total_sent = session.query(Patient).join(Consent).filter(
            Consent.last_outreach_date.isnot(None)
        ).count()

        responded = session.query(Patient).join(Consent).filter(
            Consent.status.in_([ConsentStatus.CONSENTED, ConsentStatus.DECLINED])
        ).count()

        if total_sent > 0:
            rate = (responded / total_sent) * 100
            st.metric("Response Rate", f"{rate:.1f}%")
    finally:
        session.close()


with col3:
    st.markdown("### Today's Tasks")

    # Calculate today's recommended work
    urgent_count = len(follow_ups["overdue_day14"])
    day14_count = len(follow_ups["due_day14"])
    day7_count = len(follow_ups["due_day7"])
    day3_count = len(follow_ups["due_day3"])

    if urgent_count > 0:
        st.error(f"🔴 {urgent_count} patients need phone calls")
    if day14_count > 0:
        st.warning(f"🟠 {day14_count} patients need final reminders")
    if day7_count > 0:
        st.warning(f"🟡 {day7_count} patients due for Day 7")
    if day3_count > 0:
        st.info(f"🟢 {day3_count} patients due for Day 3")

    if urgent_count + day14_count + day7_count + day3_count == 0:
        st.success("✅ No urgent follow-ups needed!")


# Footer
st.divider()
st.caption("""
**Workflow Tips:**
1. Process phone calls first (highest priority)
2. Send Day 14 reminders before they become phone calls
3. Export queues for Spruce bulk messaging
4. Mark patients as contacted after sending SMS
""")
