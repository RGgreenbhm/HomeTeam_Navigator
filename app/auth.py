"""Authentication module for Patient Explorer.

Provides user authentication with password hashing and session management.
Integrates with Streamlit session state for login persistence.

Usage:
    from auth import require_login, get_current_user, has_permission

    # In your page:
    user = require_login()  # Redirects to login if not authenticated

    if has_permission("edit_patients"):
        # Show edit controls
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets

import streamlit as st
from sqlalchemy.orm import Session

from database import get_session, init_db
from database.models import User, UserRole

logger = logging.getLogger(__name__)


# =============================================================================
# Admin Email Configuration
# =============================================================================
# These Microsoft accounts will be granted admin role on login
ADMIN_MS_EMAILS = [
    "rgreen@southviewteam.com",
    "rgreen@greenclinicteam.com",
    "autopilot@southviewteam.com",
]


def is_admin_email(email: str) -> bool:
    """Check if an email should be granted admin role.

    Args:
        email: Email address to check

    Returns:
        True if email is in the admin list
    """
    if not email:
        return False
    email_lower = email.lower().strip()
    return email_lower in [e.lower() for e in ADMIN_MS_EMAILS]


# =============================================================================
# Password Hashing (using hashlib for simplicity, bcrypt recommended for prod)
# =============================================================================

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash a password with salt.

    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)

    Returns:
        Tuple of (hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # Use PBKDF2 with SHA256
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    password_hash = hash_bytes.hex()

    return f"{salt}${password_hash}", salt


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash.

    Args:
        password: Plain text password to verify
        stored_hash: Stored hash in format "salt$hash"

    Returns:
        True if password matches
    """
    try:
        salt, expected_hash = stored_hash.split('$')
        computed_hash, _ = hash_password(password, salt)
        return computed_hash == stored_hash
    except Exception:
        return False


# =============================================================================
# User Management
# =============================================================================

def create_user(
    username: str,
    email: str,
    password: str,
    display_name: str,
    role: UserRole = UserRole.READONLY,
    session: Optional[Session] = None,
) -> User:
    """Create a new user.

    Args:
        username: Unique username
        email: User email
        password: Plain text password (will be hashed)
        display_name: Display name
        role: User role
        session: Optional database session

    Returns:
        Created User object
    """
    _session = session or get_session()

    password_hash, _ = hash_password(password)

    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        display_name=display_name,
        role=role,
    )

    # Set default permissions based on role
    if role == UserRole.ADMIN:
        user.can_view_patients = True
        user.can_edit_patients = True
        user.can_view_consents = True
        user.can_edit_consents = True
        user.can_send_messages = True
        user.can_export_data = True
        user.can_view_tasks = True
        user.can_manage_tasks = True
        user.can_use_ai = True
        user.can_use_scanner = True
    elif role == UserRole.PROVIDER:
        user.can_view_patients = True
        user.can_edit_patients = True
        user.can_view_consents = True
        user.can_edit_consents = True
        user.can_send_messages = True
        user.can_export_data = True
        user.can_view_tasks = True
        user.can_manage_tasks = True
        user.can_use_ai = True
        user.can_use_scanner = True
    elif role == UserRole.STAFF:
        user.can_view_patients = True
        user.can_edit_patients = True
        user.can_view_consents = True
        user.can_edit_consents = True
        user.can_send_messages = True
        user.can_export_data = False
        user.can_view_tasks = True
        user.can_manage_tasks = False
        user.can_use_ai = True
        user.can_use_scanner = True
    else:  # READONLY
        user.can_view_patients = True
        user.can_edit_patients = False
        user.can_view_consents = True
        user.can_edit_consents = False
        user.can_send_messages = False
        user.can_export_data = False
        user.can_view_tasks = True
        user.can_manage_tasks = False
        user.can_use_ai = False
        user.can_use_scanner = False

    _session.add(user)
    _session.commit()
    _session.refresh(user)

    if not session:
        _session.close()

    logger.info(f"Created user: {username} ({role.value})")
    return user


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password.

    Args:
        username: Username or email
        password: Plain text password

    Returns:
        User object if authenticated, None otherwise
    """
    session = get_session()

    try:
        # Try username first, then email
        user = session.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.is_active and verify_password(password, user.password_hash):
            # Update last login
            user.last_login = datetime.utcnow()
            user.last_activity = datetime.utcnow()
            session.commit()

            # Refresh user to reload attributes after commit (they get marked expired)
            session.refresh(user)

            # Expunge user from session so it can be used after session closes
            session.expunge(user)

            logger.info(f"User authenticated: {username}")
            return user

        logger.warning(f"Authentication failed for: {username}")
        return None

    finally:
        session.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID."""
    session = get_session()
    try:
        return session.query(User).filter(User.id == user_id).first()
    finally:
        session.close()


def get_all_users() -> list[User]:
    """Get all users."""
    session = get_session()
    try:
        return session.query(User).all()
    finally:
        session.close()


def update_user_password(user_id: int, new_password: str) -> bool:
    """Update a user's password."""
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.password_hash, _ = hash_password(new_password)
            session.commit()
            return True
        return False
    finally:
        session.close()


# =============================================================================
# Streamlit Session Management
# =============================================================================

def init_auth_state():
    """Initialize authentication state in Streamlit session."""
    if "auth_user_id" not in st.session_state:
        st.session_state.auth_user_id = None
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "auth_logged_in" not in st.session_state:
        st.session_state.auth_logged_in = False


def login_user(user: User):
    """Store user in session after successful login."""
    st.session_state.auth_user_id = user.id
    st.session_state.auth_user = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role.value,
        "permissions": {
            "view_patients": user.can_view_patients,
            "edit_patients": user.can_edit_patients,
            "view_consents": user.can_view_consents,
            "edit_consents": user.can_edit_consents,
            "send_messages": user.can_send_messages,
            "export_data": user.can_export_data,
            "view_tasks": user.can_view_tasks,
            "manage_tasks": user.can_manage_tasks,
            "use_ai": user.can_use_ai,
            "use_scanner": user.can_use_scanner,
        }
    }
    st.session_state.auth_logged_in = True


def logout_user():
    """Clear user from session and Microsoft OAuth state.

    This performs a complete logout by clearing:
    - App authentication state (auth_user_id, auth_user, auth_logged_in)
    - Microsoft OAuth tokens and user info
    """
    # Clear app auth state
    st.session_state.auth_user_id = None
    st.session_state.auth_user = None
    st.session_state.auth_logged_in = False

    # Clear Microsoft OAuth state
    try:
        from ms_oauth import clear_ms_auth
        clear_ms_auth()
    except ImportError:
        pass  # ms_oauth module not available


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the currently logged in user from session.

    Returns:
        User dict or None if not logged in
    """
    init_auth_state()
    return st.session_state.auth_user


def is_logged_in() -> bool:
    """Check if a user is logged in."""
    init_auth_state()
    return st.session_state.auth_logged_in


def has_permission(permission: str) -> bool:
    """Check if current user has a specific permission.

    Args:
        permission: Permission name (e.g., "edit_patients", "export_data")

    Returns:
        True if user has permission
    """
    user = get_current_user()
    if not user:
        return False

    # Admins have all permissions
    if user.get("role") == "admin":
        return True

    return user.get("permissions", {}).get(permission, False)


def require_login() -> Dict[str, Any]:
    """Require user to be logged in, show login form if not.

    Call this at the top of protected pages. This function also validates
    session consistency - if the browser was closed and reopened, it will
    detect stale state and force re-authentication.

    Returns:
        Current user dict (only returns if logged in)
    """
    init_auth_state()

    # Check for session inconsistency (browser close/reopen scenario)
    # If logged_in flag is True but user data is missing, force logout
    if st.session_state.auth_logged_in and not st.session_state.auth_user:
        logger.warning("Session inconsistency detected - forcing logout")
        logout_user()

    # Also validate Microsoft OAuth state consistency
    try:
        from ms_oauth import is_user_authenticated
        # If we think we're logged in but MS OAuth says we're not, force logout
        if st.session_state.auth_logged_in and not is_user_authenticated():
            logger.warning("MS OAuth state inconsistency - forcing logout")
            logout_user()
    except ImportError:
        pass  # ms_oauth module not available

    if not is_logged_in():
        show_login_form()
        st.stop()

    return get_current_user()


def require_permission(permission: str):
    """Require user to have a specific permission.

    Args:
        permission: Required permission name
    """
    user = require_login()

    if not has_permission(permission):
        st.error(f"You don't have permission to access this feature.")
        st.info(f"Required permission: {permission}")
        st.stop()


def show_login_form():
    """Display the login form."""
    # Handle OAuth callback first
    try:
        from ms_oauth import handle_oauth_callback, is_user_authenticated, get_ms_user

        # Check for OAuth callback
        if handle_oauth_callback():
            # OAuth was successful - create/link user account
            ms_user = get_ms_user()
            if ms_user:
                _handle_ms_login(ms_user)
                return
    except ImportError:
        pass  # ms_oauth module not available

    st.title("Login Required")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Patient Explorer")
        st.markdown("Please log in to continue.")

        # Microsoft Sign-In Button
        st.markdown("#### Sign in with Microsoft")
        try:
            from ms_oauth import show_ms_login_button, is_user_authenticated, get_ms_user

            # Check if already authenticated with MS
            if is_user_authenticated():
                ms_user = get_ms_user()
                if ms_user:
                    _handle_ms_login(ms_user)
                    return

            show_ms_login_button()
            st.caption("Use your organization Microsoft account")
        except ImportError:
            st.error("Microsoft sign-in not configured. Please contact administrator.")
        except Exception as e:
            st.warning(f"Microsoft sign-in unavailable: {e}")

        st.divider()
        st.caption("Contact your administrator if you need access.")


def _handle_ms_login(ms_user: Dict[str, Any]):
    """Handle Microsoft OAuth login - create or link user account.

    Args:
        ms_user: Microsoft user info from OAuth
    """
    session = get_session()

    try:
        email = ms_user.get("email", "").lower()
        display_name = ms_user.get("display_name", "Unknown User")
        ms_id = ms_user.get("id")

        if not email:
            st.error("Could not get email from Microsoft account")
            return

        # Check if user exists by Microsoft ID or email
        user = session.query(User).filter(
            (User.microsoft_user_id == ms_id) | (User.email == email)
        ).first()

        if user:
            # Update Microsoft association if needed
            if not user.microsoft_user_id:
                user.microsoft_user_id = ms_id
                user.microsoft_email = email
                session.commit()

            # Check if user should be admin based on email
            if is_admin_email(email) and user.role != UserRole.ADMIN:
                # Upgrade to admin role
                user.role = UserRole.ADMIN
                user.can_view_patients = True
                user.can_edit_patients = True
                user.can_view_consents = True
                user.can_edit_consents = True
                user.can_send_messages = True
                user.can_export_data = True
                user.can_view_tasks = True
                user.can_manage_tasks = True
                user.can_use_ai = True
                user.can_use_scanner = True
                logger.info(f"Upgraded user {email} to admin role")

            # Update last login
            user.last_login = datetime.utcnow()
            user.last_activity = datetime.utcnow()
            session.commit()

            # Refresh and detach user
            session.refresh(user)
            session.expunge(user)

            login_user(user)
            st.success(f"Welcome back, {display_name}!")
            st.rerun()
        else:
            # Create new user from Microsoft account
            # Determine role based on admin email list
            user_role = UserRole.ADMIN if is_admin_email(email) else UserRole.STAFF
            username = email.split("@")[0]

            # Make username unique if needed
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                username = f"{username}_{ms_id[:8]}"

            # Create random password (user will use MS login)
            import secrets
            random_password = secrets.token_urlsafe(32)

            new_user = User(
                username=username,
                email=email,
                password_hash=hash_password(random_password)[0],
                display_name=display_name,
                role=user_role,
                microsoft_user_id=ms_id,
                microsoft_email=email,
                is_active=True,
            )

            # Set permissions based on role
            if user_role == UserRole.ADMIN:
                # Full admin permissions
                new_user.can_view_patients = True
                new_user.can_edit_patients = True
                new_user.can_view_consents = True
                new_user.can_edit_consents = True
                new_user.can_send_messages = True
                new_user.can_export_data = True
                new_user.can_view_tasks = True
                new_user.can_manage_tasks = True
                new_user.can_use_ai = True
                new_user.can_use_scanner = True
            else:
                # Staff permissions (default for non-admin MS users)
                new_user.can_view_patients = True
                new_user.can_edit_patients = True
                new_user.can_view_consents = True
                new_user.can_edit_consents = True
                new_user.can_send_messages = True
                new_user.can_export_data = False
                new_user.can_view_tasks = True
                new_user.can_manage_tasks = False
                new_user.can_use_ai = True
                new_user.can_use_scanner = True

            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            session.expunge(new_user)

            login_user(new_user)
            role_msg = " as Admin" if user_role == UserRole.ADMIN else ""
            st.success(f"Welcome, {display_name}! Your account has been created{role_msg}.")
            st.balloons()
            st.rerun()

    except Exception as e:
        logger.error(f"Error handling MS login: {e}")
        st.error(f"Login error: {e}")
    finally:
        session.close()


def show_user_menu():
    """Show user menu in sidebar when logged in."""
    user = get_current_user()
    if not user:
        return

    with st.sidebar:
        st.divider()
        st.markdown(f"**{user['display_name']}**")
        st.caption(f"Role: {user['role'].title()}")

        # SharePoint sync status indicator
        try:
            from sharepoint_sync import is_sync_enabled, get_sync_status

            if is_sync_enabled():
                sync_status = get_sync_status()
                st.divider()
                st.markdown("**SharePoint Sync**")

                if sync_status.get("in_sync"):
                    st.success("In Sync", icon="☁️")
                elif sync_status.get("remote_exists") and sync_status.get("local_exists"):
                    st.warning("Out of Sync", icon="⚠️")
                elif sync_status.get("local_exists"):
                    st.info("Local only", icon="💾")
                else:
                    st.info("Not synced", icon="☁️")

                if sync_status.get("last_upload"):
                    st.caption(f"Last upload: {sync_status['last_upload'][:16]}")
        except ImportError:
            pass  # SharePoint sync module not available

        st.divider()
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()


# =============================================================================
# Initialization
# =============================================================================

def ensure_admin_exists():
    """Ensure at least one admin user exists.

    NOTE: Default admin creation is disabled. Admins are now configured via
    ADMIN_MS_EMAILS list at the top of this file. Users in that list will
    be automatically granted admin role on Microsoft login.
    """
    # Default admin creation disabled - use Microsoft login with admin emails
    pass
