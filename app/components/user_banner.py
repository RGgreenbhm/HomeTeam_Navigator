"""User Session Banner Component for Streamlit.

Displays current logged-in user with logout option.
Tracks session for HIPAA audit compliance.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def init_session_tracking() -> str:
    """Initialize session tracking and return session ID.

    Returns:
        Session ID for audit logging
    """
    if "autoscribe_session_id" not in st.session_state:
        st.session_state.autoscribe_session_id = generate_session_id()
        st.session_state.autoscribe_session_start = datetime.now()

    return st.session_state.autoscribe_session_id


def get_session_duration() -> Optional[int]:
    """Get current session duration in seconds.

    Returns:
        Duration in seconds, or None if session not started
    """
    if "autoscribe_session_start" in st.session_state:
        duration = datetime.now() - st.session_state.autoscribe_session_start
        return int(duration.total_seconds())
    return None


def show_user_banner(
    user: Any,
    show_logout: bool = True,
    on_logout_callback: Optional[callable] = None,
) -> None:
    """Display user session banner at top of page.

    Args:
        user: User object with email/name attributes
        show_logout: Whether to show logout button
        on_logout_callback: Optional callback function on logout
    """
    # Initialize session tracking
    session_id = init_session_tracking()

    # Get user display info
    if hasattr(user, 'email'):
        user_display = user.email
    elif hasattr(user, 'name'):
        user_display = user.name
    elif isinstance(user, dict):
        user_display = user.get('email') or user.get('name') or str(user.get('id', 'Unknown'))
    else:
        user_display = str(user)

    # Create banner container
    banner_col1, banner_col2 = st.columns([4, 1])

    with banner_col1:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #1e3a5f 0%, #2c5282 100%);
                padding: 8px 16px;
                border-radius: 8px;
                color: white;
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                <span style="font-size: 1.1em;">👤</span>
                <span><strong>Logged in:</strong> {user_display}</span>
                <span style="opacity: 0.7; font-size: 0.85em; margin-left: auto;">
                    Session: {session_id[-12:]}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with banner_col2:
        if show_logout:
            if st.button("🚪 Logout", key="autoscribe_logout_btn", use_container_width=True):
                # Log session end before logout
                _handle_logout(user, session_id, on_logout_callback)


def _handle_logout(user: Any, session_id: str, callback: Optional[callable] = None) -> None:
    """Handle logout action with audit logging.

    Args:
        user: User object
        session_id: Current session ID
        callback: Optional callback function
    """
    try:
        # Log session end to audit
        from autoscribe.audit import get_audit_logger, AuditEvent

        audit = get_audit_logger()
        duration = get_session_duration()

        user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else str(user))

        audit.log_session_end(
            user_id=str(user_id),
            session_id=session_id,
            duration_seconds=duration,
        )
    except Exception as e:
        # Don't block logout on audit failure
        st.warning(f"Could not log session end: {e}")

    # Clear session state
    if "autoscribe_session_id" in st.session_state:
        del st.session_state.autoscribe_session_id
    if "autoscribe_session_start" in st.session_state:
        del st.session_state.autoscribe_session_start

    # Call custom callback if provided
    if callback:
        callback()

    # Clear main auth session state
    if "authenticated" in st.session_state:
        st.session_state.authenticated = False
    if "current_user" in st.session_state:
        del st.session_state.current_user

    # Force rerun to show login page
    st.rerun()


def show_compact_user_info(user: Any) -> str:
    """Get compact user info string for display.

    Args:
        user: User object

    Returns:
        Formatted user string
    """
    if hasattr(user, 'email'):
        return user.email
    elif hasattr(user, 'name'):
        return user.name
    elif isinstance(user, dict):
        return user.get('email') or user.get('name') or 'Unknown User'
    return str(user)


def get_user_id(user: Any) -> str:
    """Extract user ID from user object.

    Args:
        user: User object

    Returns:
        User ID string
    """
    if hasattr(user, 'id'):
        return str(user.id)
    elif isinstance(user, dict):
        return str(user.get('id', user.get('email', 'unknown')))
    return str(user)
