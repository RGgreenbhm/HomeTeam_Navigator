"""Test SMS - Send test messages before campaign launch."""

import os
import re
import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from database import get_session, init_db
from database.models import AuditLog

# Spruce organization phone (what patients see as sender)
SPRUCE_ORG_PHONE = os.getenv("SPRUCE_ORG_PHONE", "205-955-7605")

st.set_page_config(
    page_title="Test SMS - Patient Explorer",
    page_icon="📱",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, require_permission, show_user_menu

# Require login and admin permission for SMS testing
user = require_login()
require_permission("send_messages")
show_user_menu()

st.title("📱 Test SMS Messages")
st.markdown("Send test messages before launching the consent campaign.")

st.warning("""
**Test Mode Only**

This page is for testing SMS templates before sending to actual patients.
Messages sent here will appear in your Spruce inbox as outgoing messages.
""")

st.divider()


def parse_phone_number(phone: str) -> tuple[str, str, bool]:
    """Parse and validate a phone number.

    Args:
        phone: Phone number in any format

    Returns:
        Tuple of (formatted_display, normalized_digits, is_valid)
        - formatted_display: (XXX) XXX-XXXX format
        - normalized_digits: 10 digits only
        - is_valid: True if valid US number
    """
    # Extract only digits
    digits = "".join(c for c in phone if c.isdigit())

    # Handle country code
    if len(digits) == 11 and digits[0] == "1":
        digits = digits[1:]  # Remove leading 1

    # Check validity
    is_valid = len(digits) == 10

    if is_valid:
        # Format as (XXX) XXX-XXXX
        formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    else:
        formatted = phone  # Return as-is if invalid

    return formatted, digits, is_valid


def get_spruce_client():
    """Get Spruce client instance."""
    try:
        from phase0.spruce import SpruceClient
        return SpruceClient()
    except Exception as e:
        st.error(f"Failed to initialize Spruce client: {e}")
        return None


def test_spruce_connection() -> tuple[bool, str, list]:
    """Test Spruce API connection and get endpoints."""
    client = get_spruce_client()
    if not client:
        return False, "Could not create Spruce client", []

    try:
        if client.test_connection():
            # Also fetch internal endpoints to verify SMS capability
            endpoints = client.list_internal_endpoints()
            return True, f"Connected to Spruce API ({len(endpoints)} endpoints found)", endpoints
        else:
            return False, "Connection test failed", []
    except Exception as e:
        return False, str(e), []
    finally:
        client.close()


def send_test_sms(phone: str, message: str) -> dict:
    """Send a test SMS via Spruce."""
    client = get_spruce_client()
    if not client:
        return {"success": False, "error": "Spruce client not available"}

    try:
        result = client.send_sms(phone, message)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        client.close()


def log_test_sms(phone: str, message: str, success: bool, username: str):
    """Log test SMS to audit log."""
    session = get_session()
    try:
        audit = AuditLog(
            action="test_sms",
            entity_type="sms",
            details=f"Test SMS to {phone[:3]}***{phone[-4:]}: {'Sent' if success else 'Failed'}",
            user_name=username,
        )
        session.add(audit)
        session.commit()
    finally:
        session.close()


# Sidebar with SMS templates
with st.sidebar:
    st.subheader("📋 Quick Templates")

    # Import SMS templates
    try:
        from sms_templates import (
            generate_initial_sms,
            generate_followup_sms,
            get_all_templates,
            DEFAULT_OFFICE_PHONE,
        )
        templates_available = True
    except ImportError:
        templates_available = False
        st.error("SMS templates module not found")

    if templates_available:
        st.caption(f"Office Phone: {DEFAULT_OFFICE_PHONE}")

        template_type = st.selectbox(
            "Template Type",
            ["Non-APCM Initial", "APCM Initial", "Follow-up Day 3",
             "Follow-up Day 7", "Final Reminder", "Custom"]
        )


# Main content
tabs = st.tabs(["📨 Send Test SMS", "📋 Template Preview", "📜 Send History"])

with tabs[0]:
    st.subheader("Send Test SMS")

    # Connection status
    col_status1, col_status2 = st.columns([2, 1])
    with col_status1:
        st.info(f"**Sending from:** {SPRUCE_ORG_PHONE} (Spruce organization number)")
    with col_status2:
        if st.button("🔌 Test Connection"):
            with st.spinner("Testing Spruce API..."):
                connected, msg, endpoints = test_spruce_connection()
                if connected:
                    st.success(msg)
                    if endpoints:
                        with st.expander("View Internal Endpoints (for debugging)"):
                            for ep in endpoints:
                                # Spruce API nests data under "endpoint" key
                                endpoint_data = ep.get("endpoint", ep)
                                ep_type = endpoint_data.get("channel") or endpoint_data.get("type", "unknown")
                                ep_id = endpoint_data.get("id") or endpoint_data.get("endpointId", "?")
                                ep_address = endpoint_data.get("rawValue") or endpoint_data.get("address") or endpoint_data.get("phoneNumber") or "?"
                                ep_label = endpoint_data.get("label", "")

                                display_id = ep_id[:16] + "..." if ep_id and len(ep_id) > 16 else ep_id
                                if ep_label:
                                    st.caption(f"**{ep_type}**: {ep_address} - {ep_label} (ID: {display_id})")
                                else:
                                    st.caption(f"**{ep_type}**: {ep_address} (ID: {display_id})")
                else:
                    st.error(msg)

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Recipient")

        test_phone = st.text_input(
            "Phone Number",
            value="",
            placeholder="(205) 555-1234 or 2055551234",
            help="Enter phone number - any format accepted (10 digits)"
        )

        # Parse and validate phone number
        if test_phone:
            formatted, digits, is_valid = parse_phone_number(test_phone)
            if is_valid:
                st.success(f"**Will send to:** {formatted}")
            else:
                st.warning(f"**Invalid format:** Need 10 digits, got {len(digits)}")
        else:
            st.caption("Enter a 10-digit US phone number")

        test_name = st.text_input(
            "Recipient Name",
            value="Dr. Green",
            help="Name to use in personalized templates"
        )

        is_apcm = st.checkbox("Treat as APCM Patient", value=False)

    with col2:
        st.markdown("### Message")

        # Generate sample URL
        sample_url = "https://forms.office.com/r/TEST123?token=TESTTOKEN"

        if templates_available and template_type != "Custom":
            # Generate template-based message
            if template_type == "Non-APCM Initial":
                sms = generate_initial_sms(
                    test_name, None, sample_url, is_apcm=False
                )
            elif template_type == "APCM Initial":
                sms = generate_initial_sms(
                    test_name, None, sample_url, is_apcm=True
                )
            elif template_type == "Follow-up Day 3":
                sms = generate_followup_sms(
                    test_name, None, sample_url, day_offset=3, is_apcm=is_apcm
                )
            elif template_type == "Follow-up Day 7":
                sms = generate_followup_sms(
                    test_name, None, sample_url, day_offset=7, is_apcm=is_apcm
                )
            elif template_type == "Final Reminder":
                sms = generate_followup_sms(
                    test_name, None, sample_url, day_offset=14, is_apcm=is_apcm
                )
            else:
                sms = None

            if sms:
                default_message = sms.message
                st.caption(f"Template: {sms.name} | {sms.character_count} chars | {sms.sms_segments} segment(s)")
            else:
                default_message = ""
        else:
            default_message = f"""Hi {test_name}, this is a test message from Dr. Green's office.

This is a TEST - please ignore.

If you receive this message, please reply to confirm receipt.

- Dr. Green's Care Team"""

        message = st.text_area(
            "Message Content",
            value=default_message,
            height=250,
            help="Edit the message before sending"
        )

        # Character count
        char_count = len(message)
        if char_count <= 160:
            segments = 1
        elif char_count <= 306:
            segments = 2
        elif char_count <= 459:
            segments = 3
        else:
            segments = (char_count // 153) + 1

        st.caption(f"📊 {char_count} characters | {segments} SMS segment(s)")

    st.divider()

    # Send button
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        # Check phone validity before enabling send
        phone_valid = False
        if test_phone:
            _, digits, phone_valid = parse_phone_number(test_phone)

        if st.button("📤 Send Test SMS", type="primary", use_container_width=True, disabled=not phone_valid):
            if not test_phone:
                st.error("Please enter a phone number")
            elif not phone_valid:
                st.error("Please enter a valid 10-digit phone number")
            elif not message:
                st.error("Please enter a message")
            else:
                with st.spinner("Sending SMS via Spruce..."):
                    result = send_test_sms(test_phone, message)

                    # Log the attempt
                    log_test_sms(
                        test_phone,
                        message,
                        result.get("success", False),
                        user.get("username", "unknown") if user else "unknown"
                    )

                    if result.get("success"):
                        st.success(f"Message sent successfully!")
                        st.balloons()
                        st.json({
                            "message_id": result.get("message_id"),
                            "status": result.get("status"),
                        })
                    else:
                        st.error(f"Failed to send: {result.get('error')}")

    with col2:
        if st.button("🔄 Reset to Template", use_container_width=True):
            st.rerun()


with tabs[1]:
    st.subheader("Template Preview")

    if templates_available:
        all_templates = get_all_templates()

        # Group by category
        categories = {}
        for t in all_templates:
            cat = t["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(t)

        for category, templates in categories.items():
            with st.expander(f"📁 {category.replace('_', ' ').title()} Templates ({len(templates)})"):
                for t in templates:
                    apcm_badge = "🏥 APCM" if t["is_apcm"] else "👤 Non-APCM"
                    st.markdown(f"**{t['name']}** {apcm_badge}")
                    st.code(t["message"], language=None)
                    st.caption(f"📊 {t['characters']} chars | {t['segments']} segment(s) | Day {t['day_offset']}")
                    st.divider()
    else:
        st.info("Templates module not available")


with tabs[2]:
    st.subheader("Recent Test SMS History")

    session = get_session()
    try:
        # Get recent test SMS logs
        logs = session.query(AuditLog).filter(
            AuditLog.action == "test_sms"
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(20).all()

        if logs:
            for log in logs:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.caption(log.details)
                with col2:
                    st.caption(log.user_name or "System")
                with col3:
                    st.caption(log.timestamp.strftime("%Y-%m-%d %H:%M"))
        else:
            st.info("No test SMS messages sent yet")
    finally:
        session.close()


# Footer
st.divider()

st.markdown(f"""
### Testing Workflow

1. **Click "Test Connection"** to verify Spruce API is working
2. **Enter your phone number** (10 digits, any format)
3. **Select a template** from the sidebar or use custom text
4. **Review the message** and make any edits
5. **Click "Send Test SMS"** to send via Spruce
6. **Check your phone** - you'll see it from **{SPRUCE_ORG_PHONE}**
7. **Reply to the message** to test the response flow

Once all templates are approved, you can proceed to the Outreach Campaign page to send messages to patients.
""")

st.caption(f"""
**Note:** Messages are sent from {SPRUCE_ORG_PHONE} and appear in your Spruce inbox.
Mark them as resolved or delete them after testing.
""")
