"""Team Tasks - Microsoft Planner and To Do integration via delegated permissions."""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db

st.set_page_config(
    page_title="Team Tasks - Patient Explorer",
    page_icon="",
    layout="wide",
)

# Initialize database for auth
init_db()

# Import auth after database init
from auth import require_login, require_permission, has_permission, show_user_menu

# Require login and tasks view permission
user = require_login()
require_permission("view_tasks")
show_user_menu()

# Check manage permission for later use
can_manage_tasks = has_permission("manage_tasks")

st.title("Team Tasks")
st.markdown("Track team progress on patient outreach and consent collection tasks.")
st.divider()


def format_due_date(due_str: str | None) -> str:
    """Format due date for display."""
    if not due_str:
        return "No due date"
    try:
        due = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
        now = datetime.now(due.tzinfo)
        diff = (due - now).days
        if diff < 0:
            return f"**:red[Overdue by {-diff} days]**"
        elif diff == 0:
            return "**:orange[Due today]**"
        elif diff <= 3:
            return f"**:orange[Due in {diff} days]**"
        else:
            return f"Due {due.strftime('%b %d')}"
    except Exception:
        return due_str


def priority_label(priority: int) -> str:
    """Convert priority number to label."""
    labels = {1: "Urgent", 3: "Important", 5: "Medium", 9: "Low"}
    return labels.get(priority, "Normal")


# =============================================================================
# Microsoft OAuth Sign-In
# =============================================================================

try:
    from ms_oauth import (
        handle_oauth_callback,
        show_ms_login_button,
        is_user_authenticated,
        get_user_graph_client,
        get_ms_user,
    )

    # Handle OAuth callback if returning from Microsoft sign-in
    handle_oauth_callback()

    # Sidebar - Microsoft sign-in
    with st.sidebar:
        st.subheader("Microsoft Account")
        show_ms_login_button()

        if is_user_authenticated():
            st.divider()
            st.subheader("Settings")

            view_mode = st.radio(
                "View",
                ["My Tasks", "Local Tasks"],
                help="Choose task view"
            )

            show_completed = st.checkbox("Show completed tasks", value=False)

            st.divider()
            if st.button("Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

    # Check if authenticated with Microsoft
    if is_user_authenticated():
        ms_user = get_ms_user()
        graph_client = get_user_graph_client()

        if graph_client and view_mode == "My Tasks":
            # =============================================================================
            # Planner Tasks (Delegated)
            # =============================================================================
            st.subheader("My Planner Tasks")

            try:
                # Note: Planner access via delegated permissions
                # User needs to be a member of a group with a Planner plan
                tasks_result = graph_client._request("GET", "/me/planner/tasks")
                planner_tasks = tasks_result.get("value", [])

                if not show_completed:
                    planner_tasks = [t for t in planner_tasks if t.get("percentComplete", 0) < 100]

                if planner_tasks:
                    for task in sorted(planner_tasks, key=lambda x: x.get("dueDateTime") or ""):
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                        with col1:
                            title = task.get("title", "Untitled")
                            st.markdown(f"**{title}**")

                        with col2:
                            st.caption(format_due_date(task.get("dueDateTime")))

                        with col3:
                            st.caption(priority_label(task.get("priority", 5)))

                        with col4:
                            percent = task.get("percentComplete", 0)
                            if percent == 100:
                                st.success("Done")
                            elif percent == 50:
                                st.warning("WIP")
                            else:
                                st.info("Todo")
                else:
                    st.info("No Planner tasks assigned to you.")

            except Exception as e:
                st.warning(f"Could not load Planner tasks: {e}")
                st.caption("Make sure Tasks.Read permission is consented and you're a member of a group with Planner.")

            st.divider()

            # =============================================================================
            # To Do Lists (Delegated)
            # =============================================================================
            st.subheader("My To Do Lists")

            try:
                lists_result = graph_client._request("GET", "/me/todo/lists")
                todo_lists = lists_result.get("value", [])

                if todo_lists:
                    selected_list = st.selectbox(
                        "Select List",
                        todo_lists,
                        format_func=lambda x: x.get("displayName", "Unknown")
                    )

                    if selected_list:
                        tasks_result = graph_client._request("GET", f"/me/todo/lists/{selected_list['id']}/tasks")
                        tasks = tasks_result.get("value", [])

                        if not show_completed:
                            tasks = [t for t in tasks if t.get("status") != "completed"]

                        if tasks:
                            for task in tasks:
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    status_icon = "" if task.get("status") == "completed" else ""
                                    importance = task.get("importance", "normal")
                                    imp_icon = "" if importance == "high" else ("" if importance == "normal" else "")
                                    st.markdown(f"{status_icon} {imp_icon} {task.get('title', 'Untitled')}")
                                with col2:
                                    if task.get("dueDateTime"):
                                        due = task["dueDateTime"].get("dateTime", "")
                                        st.caption(format_due_date(due))
                        else:
                            st.info("No tasks in this list.")
                else:
                    st.info("No To Do lists found.")

            except Exception as e:
                st.warning(f"Could not load To Do lists: {e}")
                st.caption("Make sure Tasks.ReadWrite permission is consented.")

        else:
            # Show local tasks view
            view_mode = "Local Tasks"

    else:
        # Not signed in - show info and local tasks
        st.info("""
        **Sign in with Microsoft** in the sidebar to access Planner and To Do tasks.

        While not signed in, you can use the **Local Task List** below.
        """)
        view_mode = "Local Tasks"

except ImportError as e:
    st.warning(f"Microsoft OAuth module not available: {e}")
    view_mode = "Local Tasks"

except Exception as e:
    st.warning(f"Error with Microsoft integration: {e}")
    view_mode = "Local Tasks"

# =============================================================================
# Local Task Tracking (Always Available)
# =============================================================================

if view_mode == "Local Tasks" or not is_user_authenticated():
    st.divider()
    st.subheader("Local Task List")
    st.caption("Simple task tracking for this session (no sign-in required)")

    # Initialize local tasks in session state
    if "local_tasks" not in st.session_state:
        st.session_state.local_tasks = [
            {"id": 1, "title": "Review patient consent responses", "done": False, "priority": "high"},
            {"id": 2, "title": "Follow up with unreachable patients", "done": False, "priority": "medium"},
            {"id": 3, "title": "Update APCM enrollment list", "done": False, "priority": "medium"},
        ]

    # Display tasks
    for task in st.session_state.local_tasks:
        col1, col2, col3 = st.columns([0.5, 4, 1])

        with col1:
            done = st.checkbox(
                "Done",
                value=task["done"],
                key=f"task_{task['id']}",
                label_visibility="collapsed"
            )
            task["done"] = done

        with col2:
            priority_colors = {"high": "red", "medium": "orange", "low": "green"}
            color = priority_colors.get(task["priority"], "gray")

            if done:
                st.markdown(f"~~{task['title']}~~")
            else:
                st.markdown(f"**{task['title']}** :{color}[{task['priority']}]")

        with col3:
            st.caption(task["priority"].title())

    st.divider()

    # Add new task
    with st.expander("Add New Task"):
        with st.form("add_task"):
            new_title = st.text_input("Task title", placeholder="Enter task description...")
            new_priority = st.selectbox("Priority", ["high", "medium", "low"], index=1)

            if st.form_submit_button("Add Task", type="primary"):
                if new_title:
                    max_id = max([t["id"] for t in st.session_state.local_tasks], default=0)
                    st.session_state.local_tasks.append({
                        "id": max_id + 1,
                        "title": new_title,
                        "done": False,
                        "priority": new_priority,
                    })
                    st.rerun()

    # Clear completed
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Completed Tasks"):
            st.session_state.local_tasks = [t for t in st.session_state.local_tasks if not t["done"]]
            st.rerun()

    with col2:
        completed = sum(1 for t in st.session_state.local_tasks if t["done"])
        total = len(st.session_state.local_tasks)
        st.caption(f"Completed: {completed}/{total}")

# =============================================================================
# Configuration Info
# =============================================================================

st.divider()

with st.expander("Configuration & Permissions"):
    st.markdown("""
    **Required for Microsoft Tasks:**
    - Sign in with Microsoft account (sidebar)
    - Delegated permissions: `Tasks.Read`, `Tasks.ReadWrite`

    **Planner Access:**
    - Must be a member of a Microsoft 365 group
    - Group must have a Planner plan created

    **To Do Access:**
    - Available to all Microsoft accounts
    - Personal task lists sync automatically

    **Note:** This uses delegated permissions - you access your own tasks
    after signing in. No admin consent required.
    """)
