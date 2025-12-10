"""Admin Page - User Management and System Settings."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_session, init_db
from database.models import User, UserRole
from sharepoint_sync import (
    is_sync_enabled,
    get_sharepoint_path,
    set_sharepoint_path,
    enable_sync,
    get_sync_status,
    download_from_sharepoint,
    upload_to_sharepoint,
    get_sync_conflicts,
    cleanup_old_backups,
    # Graph API sync functions
    is_graph_sync_available,
    get_sync_mode,
    list_sharepoint_sites,
    list_site_drives,
    list_drive_folders,
    configure_graph_sync,
    get_graph_sync_config,
    download_from_sharepoint_auto,
    upload_to_sharepoint_auto,
    get_sync_status_extended,
)

st.set_page_config(
    page_title="Admin - Patient Explorer",
    page_icon="⚙️",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import (
    require_login,
    get_current_user,
    has_permission,
    show_user_menu,
    create_user,
    hash_password,
)

# Require login and admin role
user = require_login()
show_user_menu()

if user.get("role") != "admin":
    st.error("Access Denied: Admin privileges required")
    st.info("Contact your administrator if you need access to this page.")
    st.stop()

st.title("⚙️ Admin - User Management")
st.markdown("Manage users, roles, and permissions.")
st.divider()


# =============================================================================
# Helper Functions
# =============================================================================

def get_all_users_data():
    """Get all users from database."""
    session = get_session()
    try:
        users = session.query(User).order_by(User.role, User.username).all()
        return users
    finally:
        session.close()


def update_user_in_db(user_id: int, updates: dict) -> bool:
    """Update user fields in database."""
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            session.commit()
            return True
        return False
    finally:
        session.close()


def reset_user_password(user_id: int, new_password: str) -> bool:
    """Reset a user's password."""
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


def delete_user_from_db(user_id: int) -> bool:
    """Delete a user (soft delete - set inactive)."""
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            session.commit()
            return True
        return False
    finally:
        session.close()


# =============================================================================
# Main Content Tabs
# =============================================================================

tabs = st.tabs(["👥 Users", "➕ Add User", "📊 Activity Log", "☁️ SharePoint Sync"])

# -----------------------------------------------------------------------------
# Tab 1: User List
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("User Management")

    # Refresh button
    if st.button("🔄 Refresh", key="refresh_users"):
        st.rerun()

    users = get_all_users_data()

    if users:
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Users", len(users))
        with col2:
            active_count = len([u for u in users if u.is_active])
            st.metric("Active", active_count)
        with col3:
            admin_count = len([u for u in users if u.role == UserRole.ADMIN])
            st.metric("Admins", admin_count)
        with col4:
            recent_logins = len([u for u in users if u.last_login and
                                 (datetime.utcnow() - u.last_login).days < 7])
            st.metric("Active (7 days)", recent_logins)

        st.divider()

        # User table
        user_data = []
        for u in users:
            user_data.append({
                "ID": u.id,
                "Username": u.username,
                "Display Name": u.display_name,
                "Email": u.email,
                "Role": u.role.value.title(),
                "Active": "✅" if u.is_active else "❌",
                "Last Login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "Never",
            })

        df = pd.DataFrame(user_data)
        st.dataframe(df, hide_index=True, use_container_width=True)

        st.divider()

        # User editor
        st.subheader("Edit User")

        user_options = [(u.id, f"{u.display_name} ({u.username})") for u in users]
        selected_user_id = st.selectbox(
            "Select User to Edit",
            options=[opt[0] for opt in user_options],
            format_func=lambda x: next((opt[1] for opt in user_options if opt[0] == x), "")
        )

        if selected_user_id:
            selected_user = next((u for u in users if u.id == selected_user_id), None)

            if selected_user:
                # Don't allow editing yourself
                is_current_user = selected_user.id == user.get("id")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**User Info**")

                    new_display_name = st.text_input(
                        "Display Name",
                        value=selected_user.display_name,
                        disabled=is_current_user
                    )

                    new_email = st.text_input(
                        "Email",
                        value=selected_user.email,
                        disabled=is_current_user
                    )

                    new_role = st.selectbox(
                        "Role",
                        options=[r for r in UserRole],
                        format_func=lambda r: r.value.title(),
                        index=[r for r in UserRole].index(selected_user.role),
                        disabled=is_current_user,
                        help="Admin: Full access | Provider: Clinical access | Staff: Limited | ReadOnly: View only"
                    )

                    is_active = st.checkbox(
                        "Account Active",
                        value=selected_user.is_active,
                        disabled=is_current_user
                    )

                with col2:
                    st.markdown("**Permissions**")

                    permissions = {
                        "can_view_patients": ("View Patients", selected_user.can_view_patients),
                        "can_edit_patients": ("Edit Patients", selected_user.can_edit_patients),
                        "can_view_consents": ("View Consents", selected_user.can_view_consents),
                        "can_edit_consents": ("Edit Consents", selected_user.can_edit_consents),
                        "can_send_messages": ("Send Messages (Spruce)", selected_user.can_send_messages),
                        "can_export_data": ("Export Data (PHI)", selected_user.can_export_data),
                        "can_view_tasks": ("View Tasks", selected_user.can_view_tasks),
                        "can_manage_tasks": ("Manage Tasks", selected_user.can_manage_tasks),
                        "can_use_ai": ("Use AI Features", selected_user.can_use_ai),
                        "can_use_scanner": ("Use Document Scanner", selected_user.can_use_scanner),
                    }

                    new_permissions = {}
                    for perm_key, (perm_label, perm_value) in permissions.items():
                        new_permissions[perm_key] = st.checkbox(
                            perm_label,
                            value=perm_value,
                            key=f"perm_{selected_user.id}_{perm_key}",
                            disabled=is_current_user
                        )

                # Save changes button
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    if st.button("💾 Save Changes", type="primary", disabled=is_current_user, use_container_width=True):
                        updates = {
                            "display_name": new_display_name,
                            "email": new_email,
                            "role": new_role,
                            "is_active": is_active,
                            **new_permissions
                        }

                        if update_user_in_db(selected_user_id, updates):
                            st.success("✅ User updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update user")

                with col2:
                    # Password reset
                    if st.button("🔑 Reset Password", disabled=is_current_user, use_container_width=True):
                        st.session_state["show_password_reset"] = selected_user_id

                with col3:
                    # Deactivate
                    if selected_user.is_active and not is_current_user:
                        if st.button("🚫 Deactivate", use_container_width=True):
                            if update_user_in_db(selected_user_id, {"is_active": False}):
                                st.success("User deactivated")
                                st.rerun()

                if is_current_user:
                    st.info("You cannot edit your own account here. Contact another admin.")

                # Password reset dialog
                if st.session_state.get("show_password_reset") == selected_user_id:
                    st.divider()
                    st.markdown("### Reset Password")

                    new_password = st.text_input("New Password", type="password", key="new_pass")
                    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pass")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Set Password", type="primary"):
                            if new_password and new_password == confirm_password:
                                if len(new_password) >= 6:
                                    if reset_user_password(selected_user_id, new_password):
                                        st.success("✅ Password reset successfully!")
                                        st.session_state["show_password_reset"] = None
                                        st.rerun()
                                    else:
                                        st.error("Failed to reset password")
                                else:
                                    st.error("Password must be at least 6 characters")
                            else:
                                st.error("Passwords don't match")
                    with col2:
                        if st.button("Cancel"):
                            st.session_state["show_password_reset"] = None
                            st.rerun()

    else:
        st.info("No users found. Create the first user below.")


# -----------------------------------------------------------------------------
# Tab 2: Add User
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Add New User")

    with st.form("add_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("Username *", help="Unique identifier for login")
            new_display = st.text_input("Display Name *", help="Name shown in the app")
            new_user_email = st.text_input("Email *", help="User's email address")

        with col2:
            new_user_password = st.text_input("Initial Password *", type="password", help="Min 6 characters")
            confirm_new_password = st.text_input("Confirm Password *", type="password")
            new_user_role = st.selectbox(
                "Role *",
                options=[r for r in UserRole],
                format_func=lambda r: r.value.title(),
                index=3,  # Default to READONLY
                help="Determines base permission level"
            )

        st.markdown("---")
        st.markdown("**Permission Presets**")
        st.caption("Permissions are set based on role. You can customize them after creation.")

        # Show what permissions the role grants
        role_descriptions = {
            UserRole.ADMIN: "Full access to all features including user management",
            UserRole.PROVIDER: "Full clinical access (view/edit patients, consents, AI, scanner, tasks)",
            UserRole.STAFF: "Limited access (no PHI export, no task management)",
            UserRole.READONLY: "View only (no edits, no messages, no AI, no scanner)"
        }
        st.info(role_descriptions.get(new_user_role, ""))

        submitted = st.form_submit_button("➕ Create User", type="primary", use_container_width=True)

        if submitted:
            # Validation
            errors = []

            if not new_username or len(new_username) < 3:
                errors.append("Username must be at least 3 characters")

            if not new_display:
                errors.append("Display name is required")

            if not new_user_email or "@" not in new_user_email:
                errors.append("Valid email is required")

            if not new_user_password or len(new_user_password) < 6:
                errors.append("Password must be at least 6 characters")

            if new_user_password != confirm_new_password:
                errors.append("Passwords don't match")

            # Check for existing user
            session = get_session()
            try:
                existing = session.query(User).filter(
                    (User.username == new_username) | (User.email == new_user_email)
                ).first()
                if existing:
                    if existing.username == new_username:
                        errors.append("Username already exists")
                    else:
                        errors.append("Email already exists")
            finally:
                session.close()

            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    create_user(
                        username=new_username,
                        email=new_user_email,
                        password=new_user_password,
                        display_name=new_display,
                        role=new_user_role,
                    )
                    st.success(f"✅ User '{new_username}' created successfully!")
                    st.balloons()

                except Exception as e:
                    st.error(f"Failed to create user: {e}")


# -----------------------------------------------------------------------------
# Tab 3: Activity Log
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("User Activity")

    st.info("Activity logging shows user login history and recent actions.")

    users = get_all_users_data()

    if users:
        activity_data = []
        for u in users:
            activity_data.append({
                "User": u.display_name,
                "Username": u.username,
                "Role": u.role.value.title(),
                "Last Login": u.last_login.strftime("%Y-%m-%d %H:%M:%S") if u.last_login else "Never",
                "Last Activity": u.last_activity.strftime("%Y-%m-%d %H:%M:%S") if u.last_activity else "Never",
                "Created": u.created_at.strftime("%Y-%m-%d") if u.created_at else "Unknown",
                "Status": "Active" if u.is_active else "Inactive"
            })

        df = pd.DataFrame(activity_data)
        st.dataframe(df, hide_index=True, use_container_width=True)

        st.divider()

        # Quick stats
        st.markdown("### Login Statistics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Recent Logins (Last 7 Days)**")
            recent = [u for u in users if u.last_login and
                      (datetime.utcnow() - u.last_login).days < 7]
            if recent:
                for u in recent:
                    days_ago = (datetime.utcnow() - u.last_login).days
                    if days_ago == 0:
                        time_str = "Today"
                    elif days_ago == 1:
                        time_str = "Yesterday"
                    else:
                        time_str = f"{days_ago} days ago"
                    st.caption(f"• {u.display_name} - {time_str}")
            else:
                st.caption("No recent logins")

        with col2:
            st.markdown("**Inactive Users (No login > 30 days)**")
            inactive = [u for u in users if u.is_active and (
                not u.last_login or (datetime.utcnow() - u.last_login).days > 30
            )]
            if inactive:
                for u in inactive:
                    if u.last_login:
                        days_ago = (datetime.utcnow() - u.last_login).days
                        st.caption(f"• {u.display_name} - {days_ago} days ago")
                    else:
                        st.caption(f"• {u.display_name} - Never logged in")
            else:
                st.caption("All users active")

    else:
        st.info("No users to display.")


# -----------------------------------------------------------------------------
# Tab 4: SharePoint Sync
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("SharePoint File Sync")
    st.markdown("""
    Sync the patient database with SharePoint for multi-user access.
    This allows you and other team members to share the same database.
    """)

    st.divider()

    # Get extended sync status
    sync_status = get_sync_status_extended()
    sync_mode = sync_status.get("sync_mode", "none")
    graph_available = sync_status.get("graph_available", False)

    # ==========================================================================
    # Microsoft Sign-In Section
    # ==========================================================================
    st.markdown("### Step 1: Sign in with Microsoft")

    try:
        from ms_oauth import is_user_authenticated, get_ms_user, show_ms_login_button, clear_ms_auth

        if is_user_authenticated():
            ms_user = get_ms_user()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"Signed in as: **{ms_user.get('display_name')}** ({ms_user.get('email')})")
            with col2:
                if st.button("Sign Out", use_container_width=True):
                    clear_ms_auth()
                    st.rerun()
        else:
            st.info("Sign in with your Microsoft account to browse and select a SharePoint folder.")
            show_ms_login_button()

    except ImportError:
        st.warning("Microsoft OAuth module not available. Using file path mode only.")
    except Exception as e:
        st.error(f"OAuth error: {e}")

    st.divider()

    # ==========================================================================
    # SharePoint Folder Selection (Graph API)
    # ==========================================================================
    if graph_available:
        st.markdown("### Step 2: Select SharePoint Folder")

        # Initialize session state for folder browser
        if "sp_selected_site" not in st.session_state:
            st.session_state.sp_selected_site = None
        if "sp_selected_drive" not in st.session_state:
            st.session_state.sp_selected_drive = None
        if "sp_current_path" not in st.session_state:
            st.session_state.sp_current_path = "root"

        # Show current configuration if exists
        graph_config = get_graph_sync_config()
        if graph_config:
            st.success(f"**Current sync folder:** {graph_config.get('site_name', 'Unknown')} / {graph_config.get('drive_name', 'Unknown')} / {graph_config.get('folder_path', 'root')}")

        # Site selection
        with st.expander("Browse SharePoint Sites", expanded=not graph_config):
            sites = list_sharepoint_sites()

            if sites:
                site_options = {s["name"]: s for s in sites if s.get("name")}
                selected_site_name = st.selectbox(
                    "Select Site",
                    options=[""] + list(site_options.keys()),
                    key="site_selector"
                )

                if selected_site_name:
                    selected_site = site_options[selected_site_name]
                    st.session_state.sp_selected_site = selected_site

                    # Drive selection
                    drives = list_site_drives(selected_site["id"])
                    if drives:
                        drive_options = {d["name"]: d for d in drives if d.get("name")}
                        selected_drive_name = st.selectbox(
                            "Select Document Library",
                            options=[""] + list(drive_options.keys()),
                            key="drive_selector"
                        )

                        if selected_drive_name:
                            selected_drive = drive_options[selected_drive_name]
                            st.session_state.sp_selected_drive = selected_drive

                            # Folder browser
                            st.markdown("**Select Folder:**")

                            current_path = st.session_state.sp_current_path
                            folders = list_drive_folders(selected_drive["id"], current_path)

                            # Navigation
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if current_path != "root":
                                    if st.button("⬆️ Up"):
                                        # Go up one level
                                        if "/" in current_path:
                                            st.session_state.sp_current_path = "/".join(current_path.split("/")[:-1]) or "root"
                                        else:
                                            st.session_state.sp_current_path = "root"
                                        st.rerun()
                            with col2:
                                st.caption(f"Current: /{current_path}" if current_path != "root" else "Current: / (root)")

                            # Folder list
                            if folders:
                                for folder in folders:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        if st.button(f"📁 {folder['name']}", key=f"folder_{folder['id']}"):
                                            if current_path == "root":
                                                st.session_state.sp_current_path = folder['name']
                                            else:
                                                st.session_state.sp_current_path = f"{current_path}/{folder['name']}"
                                            st.rerun()
                                    with col2:
                                        if st.button("Select", key=f"select_{folder['id']}", type="primary"):
                                            folder_path = folder['name'] if current_path == "root" else f"{current_path}/{folder['name']}"
                                            success, message = configure_graph_sync(
                                                site_id=selected_site["id"],
                                                drive_id=selected_drive["id"],
                                                folder_path=folder_path,
                                                site_name=selected_site_name,
                                                drive_name=selected_drive_name,
                                            )
                                            if success:
                                                st.success(message)
                                                st.rerun()
                                            else:
                                                st.error(message)
                            else:
                                st.info("No subfolders. You can select this folder or create a new one.")

                            # Select current folder or create new
                            st.markdown("---")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Use This Folder", type="primary", use_container_width=True):
                                    folder_path = "" if current_path == "root" else current_path
                                    success, message = configure_graph_sync(
                                        site_id=selected_site["id"],
                                        drive_id=selected_drive["id"],
                                        folder_path=folder_path,
                                        site_name=selected_site_name,
                                        drive_name=selected_drive_name,
                                    )
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)

                            with col2:
                                new_folder_name = st.text_input("New folder name", placeholder="PatientExplorer")
                                if st.button("📁 Create & Select", use_container_width=True) and new_folder_name:
                                    try:
                                        from ms_oauth import get_user_graph_client
                                        client = get_user_graph_client()
                                        if client:
                                            parent = "" if current_path == "root" else current_path
                                            client.create_folder(selected_drive["id"], parent, new_folder_name)
                                            folder_path = new_folder_name if current_path == "root" else f"{current_path}/{new_folder_name}"
                                            success, message = configure_graph_sync(
                                                site_id=selected_site["id"],
                                                drive_id=selected_drive["id"],
                                                folder_path=folder_path,
                                                site_name=selected_site_name,
                                                drive_name=selected_drive_name,
                                            )
                                            if success:
                                                st.success(f"Created folder and configured sync: {folder_path}")
                                                st.rerun()
                                    except Exception as e:
                                        st.error(f"Error creating folder: {e}")

                    else:
                        st.warning("No document libraries found in this site")
            else:
                st.warning("No SharePoint sites found. Make sure you have access to at least one site.")

        st.divider()

    # ==========================================================================
    # Alternative: File Path Mode
    # ==========================================================================
    if not graph_available:
        st.markdown("### Alternative: File Path Mode")
        st.caption("If you have SharePoint mapped as a drive, you can use file path mode.")

        col1, col2 = st.columns([3, 1])

        with col1:
            current_path = get_sharepoint_path() or ""
            new_path = st.text_input(
                "SharePoint Folder Path",
                value=current_path,
                placeholder="e.g., S:\\PatientExplorer",
                help="Path to the SharePoint folder (mapped drive)"
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Save Path", type="primary", use_container_width=True):
                if new_path:
                    success, message = set_sharepoint_path(new_path)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        st.divider()

    # ==========================================================================
    # Sync Status & Actions
    # ==========================================================================
    st.markdown("### Step 3: Sync Database")

    # Show sync mode
    mode_display = {
        "graph": "Microsoft Graph API (OAuth)",
        "file_path": "Mapped Drive / File Path",
        "none": "Not configured"
    }
    st.info(f"**Sync Mode:** {mode_display.get(sync_mode, 'Unknown')}")

    if sync_mode != "none":
        # Status cards
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Local Database**")
            if sync_status.get("local_exists"):
                size_kb = sync_status.get("local_size", 0) / 1024
                st.success(f"Found ({size_kb:.1f} KB)")
                if sync_status.get("local_modified"):
                    st.caption(f"Modified: {sync_status.get('local_modified', 'Unknown')[:19]}")
            else:
                st.warning("Not found")

        with col2:
            st.markdown("**Last Sync**")
            if sync_status.get("last_upload"):
                st.caption(f"Upload: {sync_status['last_upload'][:16]}")
                st.caption(f"By: {sync_status.get('last_upload_user', 'Unknown')}")
            if sync_status.get("last_download"):
                st.caption(f"Download: {sync_status['last_download'][:16]}")
            if not sync_status.get("last_upload") and not sync_status.get("last_download"):
                st.caption("Never synced")

        with col3:
            st.markdown("**Graph Config**")
            if sync_mode == "graph" and sync_status.get("graph_config"):
                gc = sync_status["graph_config"]
                st.caption(f"Site: {gc.get('site_name', 'Unknown')}")
                st.caption(f"Folder: {gc.get('folder_path', 'root')}")
            elif sync_mode == "file_path":
                st.caption(f"Path: {get_sharepoint_path() or 'Not set'}")
            else:
                st.caption("Not configured")

        st.markdown("---")

        # Sync Actions
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Download from SharePoint**")
            st.caption("Get latest data from SharePoint")
            if st.button(
                "⬇️ Download Latest",
                type="secondary",
                use_container_width=True,
                key="download_btn"
            ):
                with st.spinner("Downloading..."):
                    username = user.get("display_name", user.get("username", "admin"))
                    success, message = download_from_sharepoint_auto(username=username)
                    if success:
                        st.success(message)
                        st.info("Refresh the page to load new data.")
                    else:
                        st.error(message)

        with col2:
            st.markdown("**Upload to SharePoint**")
            st.caption("Save local changes to SharePoint")
            if st.button(
                "⬆️ Upload Changes",
                type="primary",
                use_container_width=True,
                disabled=not sync_status.get("local_exists"),
                key="upload_btn"
            ):
                with st.spinner("Uploading..."):
                    username = user.get("display_name", user.get("username", "admin"))
                    success, message = upload_to_sharepoint_auto(username=username)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        with col3:
            st.markdown("**Maintenance**")
            st.caption("Clean up old backup files")
            if st.button("🧹 Cleanup Backups", use_container_width=True, key="cleanup_btn"):
                deleted = cleanup_old_backups(keep_count=5)
                if deleted > 0:
                    st.success(f"Deleted {deleted} old backup(s)")
                else:
                    st.info("No old backups to clean up")

    else:
        st.warning("Please sign in with Microsoft and select a SharePoint folder to enable sync.")


# =============================================================================
# Sidebar - Admin Info
# =============================================================================
with st.sidebar:
    st.divider()
    st.subheader("🛡️ Admin Panel")
    st.caption("Logged in as Administrator")

    # SharePoint sync quick status
    if is_sync_enabled():
        sync_status = get_sync_status()
        st.markdown("**☁️ SharePoint Sync**")
        if sync_status.get("in_sync"):
            st.caption("Status: In Sync")
        elif sync_status.get("remote_exists"):
            st.caption("Status: Out of Sync")
        else:
            st.caption("Status: Not synced yet")

        if sync_status.get("last_upload"):
            st.caption(f"Last upload: {sync_status['last_upload'][:10]}")

        st.divider()

    st.markdown("**Quick Actions:**")
    if st.button("📋 Export User List", use_container_width=True):
        users = get_all_users_data()
        if users:
            export_data = []
            for u in users:
                export_data.append({
                    "username": u.username,
                    "display_name": u.display_name,
                    "email": u.email,
                    "role": u.role.value,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                })

            import json
            json_str = json.dumps(export_data, indent=2)

            st.download_button(
                "📥 Download JSON",
                data=json_str,
                file_name=f"users_export_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
