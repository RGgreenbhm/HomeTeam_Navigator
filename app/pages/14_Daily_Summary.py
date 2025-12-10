"""Daily Summary - Campaign progress and activity summary."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import Patient, Consent, ConsentStatus, AuditLog, PatientNote

st.set_page_config(
    page_title="Daily Summary - Patient Explorer",
    page_icon="📊",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, show_user_menu

# Require login
user = require_login()
show_user_menu()

st.title("📊 Daily Summary")
st.markdown("Campaign progress, activity metrics, and daily recap.")
st.divider()


def get_daily_stats(date: datetime.date):
    """Get statistics for a specific date."""
    session = get_session()
    try:
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())

        # Responses today
        responses_today = session.query(Consent).filter(
            Consent.response_date >= start,
            Consent.response_date <= end
        ).all()

        consented_today = sum(1 for c in responses_today if c.status == ConsentStatus.CONSENTED)
        declined_today = sum(1 for c in responses_today if c.status == ConsentStatus.DECLINED)

        # Outreach today
        outreach_today = session.query(Consent).filter(
            Consent.last_outreach_date >= start,
            Consent.last_outreach_date <= end
        ).count()

        # Notes created today
        notes_today = session.query(PatientNote).filter(
            PatientNote.created_at >= start,
            PatientNote.created_at <= end
        ).count()

        # Activity log entries today
        activity_today = session.query(AuditLog).filter(
            AuditLog.timestamp >= start,
            AuditLog.timestamp <= end
        ).count()

        return {
            "responses_total": len(responses_today),
            "consented": consented_today,
            "declined": declined_today,
            "outreach": outreach_today,
            "notes": notes_today,
            "activity": activity_today,
        }

    finally:
        session.close()


def get_campaign_totals():
    """Get overall campaign totals."""
    session = get_session()
    try:
        total_patients = session.query(Patient).count()
        spruce_matched = session.query(Patient).filter(Patient.spruce_matched == True).count()
        apcm_total = session.query(Patient).filter(Patient.apcm_enrolled == True).count()

        # Consent breakdown
        consented = session.query(Consent).filter(Consent.status == ConsentStatus.CONSENTED).count()
        declined = session.query(Consent).filter(Consent.status == ConsentStatus.DECLINED).count()
        pending = session.query(Consent).filter(
            Consent.status.in_([ConsentStatus.PENDING, ConsentStatus.INVITATION_SENT, ConsentStatus.NO_RESPONSE])
        ).count()

        # With tokens
        with_tokens = session.query(Patient).filter(Patient.consent_token.isnot(None)).count()

        # APCM elections
        apcm_continue = session.query(Patient).filter(
            Patient.apcm_enrolled == True,
            Patient.apcm_continue_with_hometeam == True
        ).count()

        apcm_decline = session.query(Patient).filter(
            Patient.apcm_enrolled == True,
            Patient.apcm_continue_with_hometeam == False
        ).count()

        return {
            "total_patients": total_patients,
            "spruce_matched": spruce_matched,
            "apcm_total": apcm_total,
            "consented": consented,
            "declined": declined,
            "pending": pending,
            "with_tokens": with_tokens,
            "apcm_continue": apcm_continue,
            "apcm_decline": apcm_decline,
        }

    finally:
        session.close()


def get_recent_activity(limit: int = 20):
    """Get recent audit log entries."""
    session = get_session()
    try:
        logs = session.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

        return [{
            "time": log.timestamp.strftime("%Y-%m-%d %H:%M"),
            "action": log.action.replace("_", " ").title(),
            "type": log.entity_type,
            "user": log.user_name or "System",
            "details": (log.details or "")[:50],
        } for log in logs]

    finally:
        session.close()


def get_response_trend(days: int = 7):
    """Get response trend for the last N days."""
    session = get_session()
    try:
        trend = []
        today = datetime.utcnow().date()

        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            start = datetime.combine(date, datetime.min.time())
            end = datetime.combine(date, datetime.max.time())

            day_responses = session.query(Consent).filter(
                Consent.response_date >= start,
                Consent.response_date <= end
            ).all()

            consented = sum(1 for c in day_responses if c.status == ConsentStatus.CONSENTED)
            declined = sum(1 for c in day_responses if c.status == ConsentStatus.DECLINED)

            trend.append({
                "date": date.strftime("%m/%d"),
                "consented": consented,
                "declined": declined,
                "total": consented + declined,
            })

        return trend

    finally:
        session.close()


# Date selection
col1, col2 = st.columns([2, 1])

with col1:
    selected_date = st.date_input(
        "Select Date",
        value=datetime.utcnow().date(),
        max_value=datetime.utcnow().date()
    )

with col2:
    st.markdown("")
    st.markdown("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.divider()

# Daily stats
daily = get_daily_stats(selected_date)
totals = get_campaign_totals()

# Main metrics row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Responses",
        daily["responses_total"],
        help="Total consent responses received"
    )

with col2:
    st.metric(
        "Consented",
        daily["consented"],
        delta=f"+{daily['consented']}" if daily["consented"] > 0 else None
    )

with col3:
    st.metric(
        "Declined",
        daily["declined"],
        delta=f"{daily['declined']}" if daily["declined"] > 0 else None,
        delta_color="inverse"
    )

with col4:
    st.metric(
        "Outreach Sent",
        daily["outreach"],
        help="SMS/phone outreach attempts"
    )

with col5:
    st.metric(
        "Notes Added",
        daily["notes"],
        help="Patient notes created"
    )

st.divider()

# Tabs for different views
tabs = st.tabs(["📈 Campaign Progress", "📊 Response Trend", "📋 Activity Log", "📑 Export"])

with tabs[0]:
    st.subheader("Campaign Progress")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Overall Consent Status")

        # Calculate percentages
        total_trackable = totals["spruce_matched"]
        if total_trackable > 0:
            consent_pct = (totals["consented"] / total_trackable) * 100
            decline_pct = (totals["declined"] / total_trackable) * 100
            pending_pct = 100 - consent_pct - decline_pct
        else:
            consent_pct = decline_pct = pending_pct = 0

        # Progress bars
        st.markdown(f"**Consented:** {totals['consented']} ({consent_pct:.1f}%)")
        st.progress(consent_pct / 100)

        st.markdown(f"**Declined:** {totals['declined']} ({decline_pct:.1f}%)")
        st.progress(decline_pct / 100)

        st.markdown(f"**Pending:** {totals['pending']} ({pending_pct:.1f}%)")
        st.progress(pending_pct / 100)

        st.divider()

        # Key metrics
        st.markdown("### Key Metrics")
        metrics_data = [
            ("Total Patients", totals["total_patients"]),
            ("Spruce Matched", totals["spruce_matched"]),
            ("With Consent Tokens", totals["with_tokens"]),
            ("Response Rate", f"{((totals['consented'] + totals['declined']) / max(totals['spruce_matched'], 1)) * 100:.1f}%"),
        ]

        for label, value in metrics_data:
            st.caption(f"**{label}:** {value}")

    with col2:
        st.markdown("### APCM Campaign Status")

        if totals["apcm_total"] > 0:
            apcm_continue_pct = (totals["apcm_continue"] / totals["apcm_total"]) * 100
            apcm_decline_pct = (totals["apcm_decline"] / totals["apcm_total"]) * 100
            apcm_pending_pct = 100 - apcm_continue_pct - apcm_decline_pct

            st.markdown(f"**Continue with Home Team:** {totals['apcm_continue']} ({apcm_continue_pct:.1f}%)")
            st.progress(apcm_continue_pct / 100)

            st.markdown(f"**Declined:** {totals['apcm_decline']} ({apcm_decline_pct:.1f}%)")
            st.progress(apcm_decline_pct / 100)

            st.markdown(f"**Pending Decision:** {totals['apcm_total'] - totals['apcm_continue'] - totals['apcm_decline']}")

            st.divider()

            st.markdown("### APCM Summary")
            st.caption(f"**Total APCM Patients:** {totals['apcm_total']}")
            st.caption(f"**Decided:** {totals['apcm_continue'] + totals['apcm_decline']}")
            st.caption(f"**Pending:** {totals['apcm_total'] - totals['apcm_continue'] - totals['apcm_decline']}")
        else:
            st.info("No APCM patients in database")


with tabs[1]:
    st.subheader("Response Trend (Last 7 Days)")

    trend_data = get_response_trend(7)

    if any(d["total"] > 0 for d in trend_data):
        df = pd.DataFrame(trend_data)

        try:
            import plotly.express as px

            fig = px.bar(
                df,
                x="date",
                y=["consented", "declined"],
                title="Daily Consent Responses",
                labels={"value": "Count", "date": "Date", "variable": "Status"},
                color_discrete_map={"consented": "#28a745", "declined": "#dc3545"},
                barmode="group"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
            st.dataframe(df, hide_index=True)

        # Daily breakdown table
        st.markdown("### Daily Breakdown")
        st.dataframe(
            df.rename(columns={
                "date": "Date",
                "consented": "Consented",
                "declined": "Declined",
                "total": "Total"
            }),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No response data available for the selected period.")


with tabs[2]:
    st.subheader("Recent Activity")

    activity = get_recent_activity(30)

    if activity:
        st.dataframe(
            pd.DataFrame(activity),
            hide_index=True,
            use_container_width=True,
            column_config={
                "time": st.column_config.TextColumn("Time", width="medium"),
                "action": st.column_config.TextColumn("Action", width="small"),
                "type": st.column_config.TextColumn("Type", width="small"),
                "user": st.column_config.TextColumn("User", width="small"),
                "details": st.column_config.TextColumn("Details", width="large"),
            }
        )
    else:
        st.info("No recent activity logged.")


with tabs[3]:
    st.subheader("Export Reports")

    st.markdown("Download campaign data for external reporting.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Campaign Summary")

        if st.button("📥 Download Summary CSV"):
            session = get_session()
            try:
                # Build summary data
                patients = session.query(Patient).filter(Patient.spruce_matched == True).all()

                summary_data = []
                for p in patients:
                    consent_status = "No Record"
                    response_date = ""
                    outreach_attempts = 0

                    if p.consent:
                        consent_status = p.consent.status.value.replace("_", " ").title()
                        response_date = p.consent.response_date.strftime("%Y-%m-%d") if p.consent.response_date else ""
                        outreach_attempts = p.consent.outreach_attempts

                    summary_data.append({
                        "MRN": p.mrn,
                        "Name": f"{p.last_name}, {p.first_name}",
                        "Phone": p.phone or "",
                        "APCM": "Yes" if p.apcm_enrolled else "No",
                        "Consent Status": consent_status,
                        "Response Date": response_date,
                        "Outreach Attempts": outreach_attempts,
                        "Has Token": "Yes" if p.consent_token else "No",
                        "Continue HT": "Yes" if p.apcm_continue_with_hometeam else ("No" if p.apcm_continue_with_hometeam is False else "Pending"),
                    })

                df = pd.DataFrame(summary_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    "📥 Download",
                    data=csv,
                    file_name=f"campaign_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_summary"
                )

            finally:
                session.close()

    with col2:
        st.markdown("### Activity Log Export")

        days_to_export = st.number_input("Days of activity", min_value=1, max_value=90, value=7)

        if st.button("📥 Download Activity Log"):
            session = get_session()
            try:
                cutoff = datetime.utcnow() - timedelta(days=days_to_export)

                logs = session.query(AuditLog).filter(
                    AuditLog.timestamp >= cutoff
                ).order_by(AuditLog.timestamp.desc()).all()

                log_data = [{
                    "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Action": log.action,
                    "Entity Type": log.entity_type,
                    "Entity ID": log.entity_id,
                    "User": log.user_name or "System",
                    "Patient ID": log.patient_id,
                    "Details": log.details,
                } for log in logs]

                df = pd.DataFrame(log_data)
                csv = df.to_csv(index=False)

                st.download_button(
                    "📥 Download",
                    data=csv,
                    file_name=f"activity_log_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_activity"
                )

            finally:
                session.close()


# Footer with tips
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Today's Focus")

    # Calculate priorities
    session = get_session()
    try:
        # Overdue follow-ups
        now = datetime.utcnow()
        cutoff_14 = now - timedelta(days=14)

        overdue = session.query(Patient).join(Consent).filter(
            Consent.status.in_([ConsentStatus.PENDING, ConsentStatus.NO_RESPONSE, ConsentStatus.INVITATION_SENT]),
            Consent.last_outreach_date <= cutoff_14
        ).count()

        if overdue > 0:
            st.warning(f"🔴 {overdue} patients need phone follow-up (14+ days)")

        # Day 7 reminders
        cutoff_7 = now - timedelta(days=7)
        day7 = session.query(Patient).join(Consent).filter(
            Consent.status.in_([ConsentStatus.PENDING, ConsentStatus.NO_RESPONSE, ConsentStatus.INVITATION_SENT]),
            Consent.last_outreach_date <= cutoff_7,
            Consent.last_outreach_date > cutoff_14
        ).count()

        if day7 > 0:
            st.info(f"🟡 {day7} patients due for Day 7 reminder")

        # Never contacted
        never = session.query(Patient).filter(
            Patient.spruce_matched == True
        ).outerjoin(Consent).filter(
            (Consent.id.is_(None)) | (Consent.last_outreach_date.is_(None))
        ).count()

        if never > 0:
            st.caption(f"📭 {never} patients never contacted")

        if overdue == 0 and day7 == 0:
            st.success("✅ No urgent follow-ups needed!")

    finally:
        session.close()

with col2:
    st.markdown("### Quick Links")
    st.markdown("""
    - **[Follow-Up Queue](/Follow_Up_Queue)** - Process overdue patients
    - **[Outreach Campaign](/Outreach_Campaign)** - Generate tokens & exports
    - **[Consent Tracking](/Consent_Tracking)** - Update statuses
    - **[Consent Response](/Consent_Response)** - Process form responses
    """)
