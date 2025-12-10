"""Microsoft 365 Integration Page - Using Delegated Permissions.

Uses OAuth user sign-in for access to OneNote, SharePoint, and other M365 services.
Provides full navigation of all accessible notebooks, sites, and files.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_db

st.set_page_config(
    page_title="M365 Integration - Patient Explorer",
    page_icon="",
    layout="wide",
)

# Initialize database
init_db()

# Import auth after database init
from auth import require_login, show_user_menu

# Require login
user = require_login()
show_user_menu()

st.title("Microsoft 365 Integration")
st.caption("OneNote, SharePoint, and OneDrive integration via delegated permissions")

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
        clear_ms_auth,
    )

    # Handle OAuth callback if returning from Microsoft sign-in
    handle_oauth_callback()

    # Show Microsoft sign-in status
    with st.sidebar:
        st.subheader("Microsoft Account")
        show_ms_login_button()

        if is_user_authenticated():
            st.divider()
            if st.button("Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

    # Check if authenticated with Microsoft
    if is_user_authenticated():
        ms_user = get_ms_user()
        st.success(f"Signed in as: **{ms_user.get('display_name', 'Unknown')}** ({ms_user.get('email', '')})")

        # Get the delegated Graph client
        graph_client = get_user_graph_client()

        if graph_client:
            tabs = st.tabs(["OneNote Explorer", "SharePoint Sites", "OneDrive Files", "Search"])

            # =============================================================================
            # OneNote Explorer Tab - Full Hierarchy
            # =============================================================================
            with tabs[0]:
                st.subheader("OneNote Notebooks")
                st.caption("Browse all accessible notebooks including SharePoint and Teams")

                # Fetch all accessible notebooks
                with st.spinner("Loading notebooks from all sources..."):
                    try:
                        all_notebooks = graph_client.list_all_accessible_notebooks()

                        if all_notebooks:
                            # Group notebooks by source
                            notebooks_by_source = {}
                            for nb in all_notebooks:
                                source = nb.get("_source_name", "Unknown")
                                if source not in notebooks_by_source:
                                    notebooks_by_source[source] = []
                                notebooks_by_source[source].append(nb)

                            # Display summary
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Total Notebooks", len(all_notebooks))
                            col2.metric("Sources", len(notebooks_by_source))
                            personal_count = len([n for n in all_notebooks if n.get("_source") == "personal"])
                            col3.metric("Personal", personal_count)

                            st.divider()

                            # Source filter
                            source_options = ["All Sources"] + list(notebooks_by_source.keys())
                            selected_source = st.selectbox("Filter by Source", source_options)

                            # Filter notebooks
                            if selected_source == "All Sources":
                                filtered_notebooks = all_notebooks
                            else:
                                filtered_notebooks = notebooks_by_source.get(selected_source, [])

                            # Notebook selector
                            if filtered_notebooks:
                                def format_notebook(nb):
                                    source = nb.get("_source_name", "")
                                    name = nb.get("displayName", "Unknown")
                                    if nb.get("_source") == "personal":
                                        return f"{name}"
                                    else:
                                        return f"{name} ({source})"

                                selected_notebook = st.selectbox(
                                    "Select Notebook",
                                    filtered_notebooks,
                                    format_func=format_notebook
                                )

                                if selected_notebook:
                                    st.divider()

                                    # Show notebook hierarchy
                                    st.markdown(f"### {selected_notebook.get('displayName', 'Notebook')}")

                                    source_icon = {
                                        "personal": "",
                                        "site": "",
                                        "group": ""
                                    }.get(selected_notebook.get("_source", ""), "")
                                    st.caption(f"{source_icon} Source: {selected_notebook.get('_source_name', 'Unknown')}")

                                    # Load hierarchy
                                    with st.spinner("Loading notebook structure..."):
                                        try:
                                            hierarchy = graph_client.get_notebook_hierarchy(selected_notebook["id"])

                                            # Display sections directly in notebook
                                            direct_sections = hierarchy.get("sections", [])
                                            section_groups = hierarchy.get("sectionGroups", [])

                                            # Build tree view
                                            st.markdown("#### Structure")

                                            # Store selected items in session state
                                            if "selected_onenote_items" not in st.session_state:
                                                st.session_state.selected_onenote_items = []

                                            def render_section(section, indent=0):
                                                """Render a section with selection checkbox."""
                                                prefix = "&nbsp;" * (indent * 4)
                                                section_name = section.get("displayName", "Untitled")
                                                section_id = section.get("id", "")

                                                col1, col2 = st.columns([0.1, 0.9])
                                                with col1:
                                                    selected = st.checkbox(
                                                        "sel",
                                                        key=f"sec_{section_id}",
                                                        label_visibility="collapsed"
                                                    )
                                                with col2:
                                                    st.markdown(f"{prefix} **{section_name}**")

                                                # Show pages if section is selected
                                                if selected:
                                                    try:
                                                        pages = graph_client.list_section_pages(section_id)
                                                        if pages:
                                                            for page in pages[:10]:  # Limit display
                                                                page_prefix = "&nbsp;" * ((indent + 1) * 4)
                                                                st.markdown(f"{page_prefix} {page.get('title', 'Untitled')}")
                                                            if len(pages) > 10:
                                                                st.caption(f"{page_prefix}... and {len(pages) - 10} more pages")
                                                    except Exception as e:
                                                        st.caption(f"Could not load pages: {e}")

                                                return selected, section_id, section_name

                                            def render_section_group(sg, indent=0):
                                                """Render a section group with its children."""
                                                prefix = "&nbsp;" * (indent * 4)
                                                sg_name = sg.get("displayName", "Untitled")

                                                st.markdown(f"{prefix} **{sg_name}**")

                                                # Render sections in this group
                                                children = sg.get("_children", {})
                                                for section in children.get("sections", []):
                                                    render_section(section, indent + 1)

                                                # Render nested section groups
                                                for nested_sg in children.get("sectionGroups", []):
                                                    render_section_group(nested_sg, indent + 1)

                                            # Render direct sections
                                            if direct_sections:
                                                st.markdown("**Sections:**")
                                                for section in direct_sections:
                                                    render_section(section, 1)

                                            # Render section groups
                                            if section_groups:
                                                st.markdown("**Section Groups:**")
                                                for sg in section_groups:
                                                    render_section_group(sg, 1)

                                            if not direct_sections and not section_groups:
                                                st.info("This notebook appears to be empty.")

                                        except Exception as e:
                                            st.error(f"Error loading notebook structure: {e}")

                        else:
                            st.info("No OneNote notebooks found. Make sure you have Notes.Read permission.")

                    except Exception as e:
                        st.error(f"Error loading notebooks: {e}")
                        st.caption("Make sure Notes.Read.All permission is consented.")

            # =============================================================================
            # SharePoint Sites Tab
            # =============================================================================
            with tabs[1]:
                st.subheader("SharePoint Sites")
                st.caption("Browse document libraries and files")

                try:
                    sites = graph_client.list_sites()

                    if sites:
                        st.metric("Accessible Sites", len(sites))

                        selected_site = st.selectbox(
                            "Select Site",
                            sites,
                            format_func=lambda x: x.get("displayName", x.get("name", "Unknown"))
                        )

                        if selected_site:
                            st.markdown(f"**Site:** {selected_site.get('displayName', selected_site.get('name'))}")
                            st.caption(f"URL: {selected_site.get('webUrl', 'N/A')}")

                            # List drives (document libraries)
                            drives = graph_client.list_site_drives(selected_site["id"])

                            if drives:
                                selected_drive = st.selectbox(
                                    "Select Document Library",
                                    drives,
                                    format_func=lambda x: x.get("name", "Unknown")
                                )

                                if selected_drive:
                                    # Navigation state
                                    if "sp_current_path" not in st.session_state:
                                        st.session_state.sp_current_path = "root"

                                    # Show current path
                                    st.markdown(f"**Path:** `{st.session_state.sp_current_path}`")

                                    col1, col2 = st.columns([1, 4])
                                    with col1:
                                        if st.session_state.sp_current_path != "root":
                                            if st.button(" Up"):
                                                # Go up one level
                                                parts = st.session_state.sp_current_path.split("/")
                                                if len(parts) > 1:
                                                    st.session_state.sp_current_path = "/".join(parts[:-1])
                                                else:
                                                    st.session_state.sp_current_path = "root"
                                                st.rerun()

                                    # List items
                                    try:
                                        items = graph_client.list_drive_items(
                                            selected_drive["id"],
                                            st.session_state.sp_current_path
                                        )

                                        if items:
                                            for item in items[:30]:  # Limit to 30
                                                is_folder = item.get("folder") is not None
                                                icon = "" if is_folder else ""
                                                name = item.get("name", "Unknown")

                                                col1, col2, col3 = st.columns([0.5, 3, 1])
                                                with col1:
                                                    st.markdown(icon)
                                                with col2:
                                                    if is_folder:
                                                        if st.button(name, key=f"folder_{item['id']}"):
                                                            if st.session_state.sp_current_path == "root":
                                                                st.session_state.sp_current_path = name
                                                            else:
                                                                st.session_state.sp_current_path += f"/{name}"
                                                            st.rerun()
                                                    else:
                                                        st.markdown(name)
                                                with col3:
                                                    size = item.get("size", 0)
                                                    if size > 0:
                                                        if size > 1024 * 1024:
                                                            st.caption(f"{size / 1024 / 1024:.1f} MB")
                                                        elif size > 1024:
                                                            st.caption(f"{size / 1024:.1f} KB")
                                                        else:
                                                            st.caption(f"{size} B")

                                            if len(items) > 30:
                                                st.caption(f"... and {len(items) - 30} more items")
                                        else:
                                            st.info("This folder is empty.")
                                    except Exception as e:
                                        st.error(f"Error listing files: {e}")
                            else:
                                st.info("No document libraries found.")
                    else:
                        st.info("No SharePoint sites found.")
                        st.caption("Make sure Sites.Read.All permission is consented.")

                except Exception as e:
                    st.error(f"Error accessing SharePoint: {e}")

            # =============================================================================
            # OneDrive Files Tab
            # =============================================================================
            with tabs[2]:
                st.subheader("My OneDrive Files")
                st.caption("Browse your personal OneDrive")

                try:
                    # Get user's OneDrive
                    drive_info = graph_client._request("GET", "/me/drive")
                    drive_id = drive_info.get("id")

                    if drive_id:
                        # Navigation state
                        if "od_current_path" not in st.session_state:
                            st.session_state.od_current_path = "root"

                        st.markdown(f"**Path:** `{st.session_state.od_current_path}`")

                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.session_state.od_current_path != "root":
                                if st.button(" Up", key="od_up"):
                                    parts = st.session_state.od_current_path.split("/")
                                    if len(parts) > 1:
                                        st.session_state.od_current_path = "/".join(parts[:-1])
                                    else:
                                        st.session_state.od_current_path = "root"
                                    st.rerun()

                        # List items
                        items = graph_client.list_drive_items(drive_id, st.session_state.od_current_path)

                        if items:
                            for item in items[:30]:
                                is_folder = item.get("folder") is not None
                                icon = "" if is_folder else ""
                                name = item.get("name", "Unknown")

                                col1, col2, col3 = st.columns([0.5, 3, 1])
                                with col1:
                                    st.markdown(icon)
                                with col2:
                                    if is_folder:
                                        if st.button(name, key=f"od_folder_{item['id']}"):
                                            if st.session_state.od_current_path == "root":
                                                st.session_state.od_current_path = name
                                            else:
                                                st.session_state.od_current_path += f"/{name}"
                                            st.rerun()
                                    else:
                                        st.markdown(name)
                                with col3:
                                    size = item.get("size", 0)
                                    if size > 0:
                                        if size > 1024 * 1024:
                                            st.caption(f"{size / 1024 / 1024:.1f} MB")
                                        elif size > 1024:
                                            st.caption(f"{size / 1024:.1f} KB")

                            if len(items) > 30:
                                st.caption(f"... and {len(items) - 30} more items")
                        else:
                            st.info("This folder is empty.")

                except Exception as e:
                    st.error(f"Error accessing OneDrive: {e}")
                    st.caption("Make sure Files.Read permission is consented.")

            # =============================================================================
            # Search Tab
            # =============================================================================
            with tabs[3]:
                st.subheader("Search OneNote")
                st.caption("Search across all accessible OneNote pages")

                search_query = st.text_input("Search query", placeholder="Enter search terms...")

                if search_query:
                    with st.spinner("Searching..."):
                        try:
                            results = graph_client.search_pages(search_query)

                            if results:
                                st.success(f"Found {len(results)} matching pages")

                                for page in results[:20]:
                                    with st.expander(page.get("title", "Untitled")):
                                        st.caption(f"Created: {page.get('createdDateTime', 'Unknown')}")
                                        st.caption(f"Modified: {page.get('lastModifiedDateTime', 'Unknown')}")

                                        if st.button("View Content", key=f"view_{page['id']}"):
                                            try:
                                                content = graph_client.get_page_content_as_text(page["id"])
                                                st.text_area("Page Content", content[:2000], height=200)
                                                if len(content) > 2000:
                                                    st.caption("... content truncated")
                                            except Exception as e:
                                                st.error(f"Could not load content: {e}")

                                if len(results) > 20:
                                    st.caption(f"... and {len(results) - 20} more results")
                            else:
                                st.info("No results found.")

                        except Exception as e:
                            st.error(f"Search error: {e}")
                            st.caption("OneNote search requires Notes.Read permission.")

        else:
            st.warning("Could not create Graph client. Please try signing in again.")

    else:
        # Not signed in with Microsoft
        st.info("""
        **Sign in with Microsoft** to access your OneNote notebooks, SharePoint sites, and OneDrive files.

        Click the **Sign in with Microsoft** button in the sidebar to authenticate.

        **What you can access after sign-in:**
        - All OneNote notebooks (personal, SharePoint, and Teams)
        - Full notebook hierarchy (section groups, sections, pages)
        - SharePoint document libraries
        - OneDrive files
        - Search across all OneNote content
        """)

        # Show alternatives while not signed in
        st.divider()
        st.subheader("Alternative: Local Data Storage")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Patient Explorer Features")
            st.markdown("""
            - **Local SQLite Database** - Fast, encrypted patient records
            - **Azure Blob Storage** - HIPAA-compliant PHI sync
            - **Spruce Integration** - SMS messaging
            """)

        with col2:
            st.markdown("### Sync Commands")
            st.code("""
# Push data to Azure
python -m phase0 sync-push --interactive

# Pull data from Azure
python -m phase0 sync-pull --interactive
            """)

except ImportError as e:
    st.error(f"Microsoft OAuth module not available: {e}")
    st.caption("Make sure ms_oauth.py is in the app directory and MSAL is installed.")

except Exception as e:
    st.error(f"Error initializing Microsoft integration: {e}")
    import traceback
    st.code(traceback.format_exc())

# =============================================================================
# Configuration Info
# =============================================================================

st.divider()

with st.expander("Configuration & Permissions"):
    st.markdown("""
    **Required Environment Variables:**
    - `AZURE_TENANT_ID` - Your Azure AD tenant ID
    - `AZURE_CLIENT_ID` - App registration client ID
    - `MS_OAUTH_REDIRECT_URI` - OAuth redirect URI (default: http://localhost:8501)

    **Delegated Permissions Required:**

    | Permission | Purpose |
    |------------|---------|
    | `User.Read` | Basic profile |
    | `Notes.Read` | Read personal notebooks |
    | `Notes.Read.All` | Read all accessible notebooks |
    | `Sites.Read.All` | Read SharePoint sites and their notebooks |
    | `Files.Read.All` | Read OneDrive and SharePoint files |
    | `Group.Read.All` | Read group memberships (for Teams notebooks) |

    **Note:** These are delegated permissions - the user signs in and grants access
    to their own resources. No admin consent required for most permissions.
    """)
