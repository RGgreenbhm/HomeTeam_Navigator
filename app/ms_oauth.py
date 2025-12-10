"""Microsoft OAuth Authentication for Patient Explorer.

STATUS: V1.0 ACTIVE - Delegated Permissions

This module provides interactive OAuth 2.0 authentication using MSAL for
Streamlit apps. Uses Authorization Code Flow with PKCE for secure user
authentication.

V1.0 uses DELEGATED permissions (user sign-in) for Microsoft Graph API access.
This is the recommended approach for user-facing apps and provides access to:
- User's SharePoint files and folders
- User's OneNote notebooks (with user consent)
- Planner tasks, To Do lists
- All resources the signed-in user has access to

Note: App-only permissions (client credentials flow in microsoft_graph.py)
are deferred to V1.1 for background/service operations.

This module enables:
- User sign-in with Microsoft accounts
- Access to user's SharePoint files and folders
- Access to user's OneNote notebooks
- Delegated permissions (on behalf of user)

Usage:
    from ms_oauth import (
        get_auth_url,
        exchange_code_for_tokens,
        get_user_graph_client,
        is_user_authenticated,
    )

    # In login page
    auth_url = get_auth_url()
    st.link_button("Sign in with Microsoft", auth_url)

    # After redirect with code
    tokens = exchange_code_for_tokens(code)

    # Use delegated client
    client = get_user_graph_client()
    sites = client.list_my_sharepoint_sites()

Prerequisites:
    1. Azure AD App Registration with redirect URI configured
    2. Delegated permissions added and consented
    3. Environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID
    4. Optional: AZURE_CLIENT_SECRET (for confidential clients)
"""

import os
import logging
import secrets
import hashlib
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlencode, quote
from pathlib import Path

import streamlit as st
import httpx
from msal import PublicClientApplication, ConfidentialClientApplication
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# File-based storage for OAuth state (survives Streamlit page reloads)
OAUTH_STATE_FILE = Path(__file__).parent.parent / "data" / ".oauth_pending.json"


# =============================================================================
# Configuration
# =============================================================================

# Azure AD App Registration settings
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")  # Optional for PKCE

# OAuth redirect URI - must match what's registered in Azure AD
# For local Streamlit, this is typically http://localhost:8501
REDIRECT_URI = os.getenv("MS_OAUTH_REDIRECT_URI", "http://localhost:8501")

# Scopes for delegated access
# These permissions enable full M365 management hub capabilities.
# See docs/research/2025-12-04_Azure-AD-App-Permissions-Summary.md for details.
DELEGATED_SCOPES = [
    # Authentication & Profile
    "User.Read",                    # Basic profile
    "offline_access",               # Get refresh token

    # Bookings
    "Bookings.Manage.All",          # Full management of booking businesses
    "Bookings.Read.All",            # Read booking businesses and appointments
    "Bookings.ReadWrite.All",       # Read and write booking businesses
    "BookingsAppointment.ReadWrite.All",  # Read and write booking appointments

    # Calendars
    "Calendars.ReadWrite",          # Read and write user calendars
    "Calendars.ReadWrite.Shared",   # Read and write shared calendars

    # Chat/Teams
    "Chat.Create",                  # Create new chat conversations
    "Chat.Read",                    # Read user chat messages
    "Chat.ReadBasic",               # Read basic chat properties
    "Chat.ReadWrite",               # Read and write chat messages
    "ChatMessage.Read",             # Read chat messages
    "ChatMessage.Send",             # Send chat messages
    "Team.ReadBasic.All",           # Read basic team properties

    # Contacts
    "Contacts.ReadWrite",           # Read and write user contacts

    # Directory
    "Directory.AccessAsUser.All",   # Access directory as signed-in user

    # Files / OneDrive / SharePoint
    "Files.ReadWrite.All",          # Full access to user files
    "Files.ReadWrite.AppFolder",    # Read/write app's folder
    "Files.ReadWrite.Selected",     # Read/write files user selects

    # Groups
    "Group.ReadWrite.All",          # Read and write all groups

    # Mail (read only - security precaution)
    "Mail.Read",                    # Read user mail

    # Notes / OneNote
    "Notes.Create",                 # Create OneNote notebooks
    "Notes.Read",                   # Read OneNote notebooks
    "Notes.Read.All",               # Read all notebooks user can access
    "Notes.ReadWrite",              # Read and write OneNote notebooks
    "Notes.ReadWrite.All",          # Read and write all accessible notebooks
    "Notes.ReadWrite.CreatedByApp", # App-created notebook access

    # People / Presence
    "People.Read",                  # Read user's relevant people
    "People.Read.All",              # Read all relevant people
    "PeopleSettings.Read.All",      # Read people settings
    "Presence.Read",                # Read user presence
    "Presence.ReadWrite",           # Read and write presence

    # Short Notes / Sticky Notes
    "ShortNotes.Read",              # Read user's sticky notes
    "ShortNotes.ReadWrite",         # Read and write sticky notes

    # Sites / SharePoint
    "Sites.Manage.All",             # Full management of all site collections
    "Sites.Read.All",               # Read items in all site collections
    "Sites.ReadWrite.All",          # Read and write all site collections
    "Sites.Selected",               # Access selected sites

    # Tasks / Planner
    "Tasks.Read",                   # Read user tasks
    "Tasks.Read.Shared",            # Read shared tasks
    "Tasks.ReadWrite",              # Read and write user tasks
    "Tasks.ReadWrite.Shared",       # Read and write shared tasks
]

# Graph API base URL
GRAPH_URL = "https://graph.microsoft.com/v1.0"


# =============================================================================
# PKCE Helper Functions
# =============================================================================

def _generate_code_verifier() -> str:
    """Generate a random code verifier for PKCE."""
    return secrets.token_urlsafe(32)


def _generate_code_challenge(verifier: str) -> str:
    """Generate code challenge from verifier using S256 method."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _generate_state() -> str:
    """Generate random state for CSRF protection."""
    return secrets.token_urlsafe(16)


# =============================================================================
# File-Based OAuth State Persistence
# =============================================================================

def _save_pending_oauth(state: str, code_verifier: str):
    """Save pending OAuth state to file (survives page reload).

    Args:
        state: CSRF state parameter
        code_verifier: PKCE code verifier
    """
    try:
        OAUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "state": state,
            "code_verifier": code_verifier,
            "created_at": datetime.now().isoformat(),
        }
        with open(OAUTH_STATE_FILE, "w") as f:
            json.dump(data, f)
        logger.info(f"Saved OAuth state: {state[:8]}...")
    except Exception as e:
        logger.error(f"Failed to save OAuth state: {e}")


def _load_pending_oauth() -> Optional[Dict[str, str]]:
    """Load pending OAuth state from file.

    Returns:
        Dict with state and code_verifier, or None if not found/expired
    """
    try:
        if not OAUTH_STATE_FILE.exists():
            return None

        with open(OAUTH_STATE_FILE, "r") as f:
            data = json.load(f)

        # Check if state is too old (15 minutes max)
        created_at = datetime.fromisoformat(data.get("created_at", "2000-01-01"))
        if datetime.now() - created_at > timedelta(minutes=15):
            logger.warning("OAuth state expired")
            _clear_pending_oauth()
            return None

        return data
    except Exception as e:
        logger.error(f"Failed to load OAuth state: {e}")
        return None


def _clear_pending_oauth():
    """Remove pending OAuth state file."""
    try:
        if OAUTH_STATE_FILE.exists():
            OAUTH_STATE_FILE.unlink()
    except Exception as e:
        logger.error(f"Failed to clear OAuth state: {e}")


# =============================================================================
# Session State Management
# =============================================================================

def _init_oauth_state():
    """Initialize OAuth state in Streamlit session."""
    if "ms_oauth_tokens" not in st.session_state:
        st.session_state.ms_oauth_tokens = None
    if "ms_oauth_user" not in st.session_state:
        st.session_state.ms_oauth_user = None
    if "ms_oauth_state" not in st.session_state:
        st.session_state.ms_oauth_state = None
    if "ms_oauth_code_verifier" not in st.session_state:
        st.session_state.ms_oauth_code_verifier = None


def is_user_authenticated() -> bool:
    """Check if user is authenticated with Microsoft.

    Returns:
        True if user has valid tokens
    """
    _init_oauth_state()
    tokens = st.session_state.ms_oauth_tokens

    if not tokens:
        return False

    # Check if token is expired
    expires_at = tokens.get("expires_at")
    if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
        # Token expired - try to refresh
        if tokens.get("refresh_token"):
            try:
                new_tokens = refresh_tokens(tokens["refresh_token"])
                if new_tokens:
                    st.session_state.ms_oauth_tokens = new_tokens
                    return True
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
        return False

    return True


def get_ms_user() -> Optional[Dict[str, Any]]:
    """Get the authenticated Microsoft user info.

    Returns:
        User info dict or None if not authenticated
    """
    _init_oauth_state()
    return st.session_state.ms_oauth_user


def clear_ms_auth():
    """Clear Microsoft authentication state."""
    _init_oauth_state()
    st.session_state.ms_oauth_tokens = None
    st.session_state.ms_oauth_user = None
    st.session_state.ms_oauth_state = None
    st.session_state.ms_oauth_code_verifier = None


# =============================================================================
# OAuth Flow Functions
# =============================================================================

def get_auth_url() -> str:
    """Generate the Microsoft OAuth authorization URL.

    Returns:
        URL to redirect user for authentication
    """
    _init_oauth_state()

    if not AZURE_CLIENT_ID or not AZURE_TENANT_ID:
        raise ValueError("AZURE_CLIENT_ID and AZURE_TENANT_ID must be set")

    # Generate PKCE values
    code_verifier = _generate_code_verifier()
    code_challenge = _generate_code_challenge(code_verifier)
    state = _generate_state()

    # Store in session for verification
    st.session_state.ms_oauth_code_verifier = code_verifier
    st.session_state.ms_oauth_state = state

    # Also save to file (survives page reload after OAuth redirect)
    _save_pending_oauth(state, code_verifier)

    # Build authorization URL
    params = {
        "client_id": AZURE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(DELEGATED_SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",  # Always show account picker
    }

    auth_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/authorize?{urlencode(params)}"

    return auth_url


def exchange_code_for_tokens(code: str, state: str) -> Optional[Dict[str, Any]]:
    """Exchange authorization code for tokens.

    Args:
        code: Authorization code from redirect
        state: State parameter for CSRF verification

    Returns:
        Token dict or None if exchange fails
    """
    _init_oauth_state()

    # Try to get state from session first, then from file
    expected_state = st.session_state.ms_oauth_state
    code_verifier = st.session_state.ms_oauth_code_verifier

    # If session state is empty, try to load from file (after page reload)
    if not expected_state or not code_verifier:
        pending = _load_pending_oauth()
        if pending:
            expected_state = pending.get("state")
            code_verifier = pending.get("code_verifier")
            logger.info(f"Loaded OAuth state from file: {expected_state[:8]}...")

    # Verify state
    if state != expected_state:
        logger.error(f"State mismatch: expected {expected_state}, got {state}")
        return None

    if not code_verifier:
        logger.error("No code verifier found in session or file")
        return None

    # Token endpoint
    token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"

    # Build token request
    data = {
        "client_id": AZURE_CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
        "scope": " ".join(DELEGATED_SCOPES),
    }

    # Add client secret if available (for confidential clients)
    if AZURE_CLIENT_SECRET:
        data["client_secret"] = AZURE_CLIENT_SECRET

    try:
        with httpx.Client() as client:
            response = client.post(token_url, data=data)

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None

            tokens = response.json()

            # Calculate expiry time
            expires_in = tokens.get("expires_in", 3600)
            tokens["expires_at"] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

            # Store tokens
            st.session_state.ms_oauth_tokens = tokens

            # Get user info
            _fetch_and_store_user_info(tokens["access_token"])

            # Clear PKCE values from session and file
            st.session_state.ms_oauth_code_verifier = None
            st.session_state.ms_oauth_state = None
            _clear_pending_oauth()

            return tokens

    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        return None


def refresh_tokens(refresh_token: str) -> Optional[Dict[str, Any]]:
    """Refresh access token using refresh token.

    Args:
        refresh_token: The refresh token

    Returns:
        New token dict or None if refresh fails
    """
    token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"

    data = {
        "client_id": AZURE_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": " ".join(DELEGATED_SCOPES),
    }

    if AZURE_CLIENT_SECRET:
        data["client_secret"] = AZURE_CLIENT_SECRET

    try:
        with httpx.Client() as client:
            response = client.post(token_url, data=data)

            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.status_code}")
                return None

            tokens = response.json()
            expires_in = tokens.get("expires_in", 3600)
            tokens["expires_at"] = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

            return tokens

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return None


def _fetch_and_store_user_info(access_token: str):
    """Fetch user info from Graph API and store in session."""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{GRAPH_URL}/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code == 200:
                user_info = response.json()
                st.session_state.ms_oauth_user = {
                    "id": user_info.get("id"),
                    "display_name": user_info.get("displayName"),
                    "email": user_info.get("mail") or user_info.get("userPrincipalName"),
                    "job_title": user_info.get("jobTitle"),
                }
    except Exception as e:
        logger.error(f"Failed to fetch user info: {e}")


# =============================================================================
# Delegated Graph Client
# =============================================================================

class DelegatedGraphClient:
    """Microsoft Graph client using delegated (user) permissions.

    Unlike the app-only GraphClient in microsoft_graph.py, this client
    makes requests on behalf of the signed-in user.
    """

    def __init__(self, access_token: str):
        """Initialize with user's access token.

        Args:
            access_token: OAuth access token from user authentication
        """
        self.access_token = access_token
        self.http_client = httpx.Client(timeout=30.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make a Graph API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            json: JSON body
            params: Query parameters

        Returns:
            Response JSON
        """
        url = f"{GRAPH_URL}{endpoint}"

        response = self.http_client.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            json=json,
            params=params,
        )

        if response.status_code >= 400:
            logger.error(f"Graph API error: {response.status_code} - {response.text}")
            raise Exception(f"Graph API error: {response.status_code} - {response.text}")

        if response.status_code == 204:
            return {}

        return response.json()

    # =========================================================================
    # User Info
    # =========================================================================

    def get_me(self) -> Dict[str, Any]:
        """Get current user's profile."""
        return self._request("GET", "/me")

    # =========================================================================
    # SharePoint Sites & Drives
    # =========================================================================

    def list_sites(self, search: str = "*") -> List[Dict[str, Any]]:
        """List SharePoint sites the user has access to.

        Args:
            search: Search query (default "*" for all)

        Returns:
            List of site info dicts
        """
        result = self._request("GET", f"/sites?search={search}")
        return result.get("value", [])

    def get_site(self, site_id: str) -> Dict[str, Any]:
        """Get a specific SharePoint site.

        Args:
            site_id: Site ID or "hostname:/sites/sitename" format

        Returns:
            Site info dict
        """
        return self._request("GET", f"/sites/{site_id}")

    def list_site_drives(self, site_id: str) -> List[Dict[str, Any]]:
        """List document libraries (drives) in a SharePoint site.

        Args:
            site_id: SharePoint site ID

        Returns:
            List of drive info dicts
        """
        result = self._request("GET", f"/sites/{site_id}/drives")
        return result.get("value", [])

    def list_drive_items(
        self,
        drive_id: str,
        folder_path: str = "root",
    ) -> List[Dict[str, Any]]:
        """List items in a drive folder.

        Args:
            drive_id: Drive ID
            folder_path: Folder path (default "root")

        Returns:
            List of item dicts
        """
        if folder_path == "root":
            endpoint = f"/drives/{drive_id}/root/children"
        else:
            endpoint = f"/drives/{drive_id}/root:/{folder_path}:/children"

        result = self._request("GET", endpoint)
        return result.get("value", [])

    def get_drive_item(self, drive_id: str, item_path: str) -> Dict[str, Any]:
        """Get a specific drive item by path.

        Args:
            drive_id: Drive ID
            item_path: Item path from root

        Returns:
            Item info dict
        """
        return self._request("GET", f"/drives/{drive_id}/root:/{item_path}")

    def download_file(self, drive_id: str, item_path: str) -> bytes:
        """Download a file from SharePoint.

        Args:
            drive_id: Drive ID
            item_path: File path from root

        Returns:
            File content as bytes
        """
        # Get download URL
        item = self._request("GET", f"/drives/{drive_id}/root:/{item_path}")
        download_url = item.get("@microsoft.graph.downloadUrl")

        if not download_url:
            raise Exception("No download URL available")

        # Download file
        response = self.http_client.get(download_url)
        if response.status_code != 200:
            raise Exception(f"Download failed: {response.status_code}")

        return response.content

    def upload_file(
        self,
        drive_id: str,
        folder_path: str,
        filename: str,
        content: bytes,
    ) -> Dict[str, Any]:
        """Upload a file to SharePoint.

        Args:
            drive_id: Drive ID
            folder_path: Folder path from root
            filename: Name for the uploaded file
            content: File content as bytes

        Returns:
            Uploaded item info
        """
        # For files < 4MB, use simple upload
        if len(content) < 4 * 1024 * 1024:
            upload_path = f"{folder_path}/{filename}" if folder_path else filename
            url = f"{GRAPH_URL}/drives/{drive_id}/root:/{upload_path}:/content"

            response = self.http_client.put(
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/octet-stream",
                },
                content=content,
            )

            if response.status_code not in [200, 201]:
                raise Exception(f"Upload failed: {response.status_code} - {response.text}")

            return response.json()
        else:
            # For larger files, would need upload session
            raise NotImplementedError("Large file upload not yet implemented")

    def create_folder(
        self,
        drive_id: str,
        parent_path: str,
        folder_name: str,
    ) -> Dict[str, Any]:
        """Create a folder in SharePoint.

        Args:
            drive_id: Drive ID
            parent_path: Parent folder path (use "" for root)
            folder_name: Name for new folder

        Returns:
            Created folder info
        """
        if parent_path:
            endpoint = f"/drives/{drive_id}/root:/{parent_path}:/children"
        else:
            endpoint = f"/drives/{drive_id}/root/children"

        return self._request(
            "POST",
            endpoint,
            json={
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail",
            },
        )

    # =========================================================================
    # OneNote Operations - Comprehensive Hierarchy Support
    # =========================================================================

    def list_notebooks(self) -> List[Dict[str, Any]]:
        """List user's personal OneNote notebooks.

        Returns:
            List of notebook dicts
        """
        result = self._request("GET", "/me/onenote/notebooks")
        return result.get("value", [])

    def list_all_accessible_notebooks(self) -> List[Dict[str, Any]]:
        """List ALL OneNote notebooks accessible to the user.

        This includes:
        - Personal notebooks (OneDrive)
        - SharePoint site notebooks (Teams)
        - Group notebooks

        Returns:
            List of notebook dicts with source info
        """
        all_notebooks = []

        # 1. Personal notebooks
        try:
            personal = self._request("GET", "/me/onenote/notebooks")
            for nb in personal.get("value", []):
                nb["_source"] = "personal"
                nb["_source_name"] = "My Notebooks"
                all_notebooks.append(nb)
        except Exception as e:
            logger.warning(f"Could not fetch personal notebooks: {e}")

        # 2. SharePoint site notebooks
        try:
            sites = self.list_sites()
            for site in sites:
                try:
                    site_notebooks = self._request(
                        "GET",
                        f"/sites/{site['id']}/onenote/notebooks"
                    )
                    for nb in site_notebooks.get("value", []):
                        nb["_source"] = "site"
                        nb["_source_id"] = site["id"]
                        nb["_source_name"] = site.get("displayName", site.get("name", "Unknown Site"))
                        all_notebooks.append(nb)
                except Exception:
                    # Site may not have OneNote or access denied
                    pass
        except Exception as e:
            logger.warning(f"Could not fetch site notebooks: {e}")

        # 3. Group notebooks (Teams)
        try:
            groups = self.list_groups()
            for group in groups:
                try:
                    group_notebooks = self._request(
                        "GET",
                        f"/groups/{group['id']}/onenote/notebooks"
                    )
                    for nb in group_notebooks.get("value", []):
                        nb["_source"] = "group"
                        nb["_source_id"] = group["id"]
                        nb["_source_name"] = group.get("displayName", "Unknown Group")
                        all_notebooks.append(nb)
                except Exception:
                    # Group may not have OneNote or access denied
                    pass
        except Exception as e:
            logger.warning(f"Could not fetch group notebooks: {e}")

        return all_notebooks

    def list_groups(self) -> List[Dict[str, Any]]:
        """List Microsoft 365 groups the user is a member of.

        Returns:
            List of group dicts
        """
        try:
            result = self._request(
                "GET",
                "/me/memberOf/microsoft.graph.group?$filter=groupTypes/any(c:c eq 'Unified')"
            )
            return result.get("value", [])
        except Exception:
            return []

    def list_notebook_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        """List sections directly in a notebook (not in section groups).

        Args:
            notebook_id: Notebook ID

        Returns:
            List of section dicts
        """
        result = self._request("GET", f"/me/onenote/notebooks/{notebook_id}/sections")
        return result.get("value", [])

    def list_notebook_section_groups(self, notebook_id: str) -> List[Dict[str, Any]]:
        """List section groups in a notebook.

        Args:
            notebook_id: Notebook ID

        Returns:
            List of section group dicts
        """
        result = self._request("GET", f"/me/onenote/notebooks/{notebook_id}/sectionGroups")
        return result.get("value", [])

    def list_section_group_sections(self, section_group_id: str) -> List[Dict[str, Any]]:
        """List sections within a section group.

        Args:
            section_group_id: Section Group ID

        Returns:
            List of section dicts
        """
        result = self._request("GET", f"/me/onenote/sectionGroups/{section_group_id}/sections")
        return result.get("value", [])

    def list_nested_section_groups(self, section_group_id: str) -> List[Dict[str, Any]]:
        """List nested section groups within a section group.

        Args:
            section_group_id: Parent Section Group ID

        Returns:
            List of section group dicts
        """
        result = self._request("GET", f"/me/onenote/sectionGroups/{section_group_id}/sectionGroups")
        return result.get("value", [])

    def get_notebook_hierarchy(self, notebook_id: str) -> Dict[str, Any]:
        """Get the full hierarchical structure of a notebook.

        Returns nested structure with section groups and sections.

        Args:
            notebook_id: Notebook ID

        Returns:
            Dict with notebook info and nested children
        """
        def get_section_group_children(sg_id: str, depth: int = 0) -> Dict[str, Any]:
            """Recursively get section group children."""
            if depth > 5:  # Prevent infinite recursion
                return {"sections": [], "sectionGroups": []}

            sections = []
            try:
                sections = self.list_section_group_sections(sg_id)
            except Exception:
                pass

            nested_groups = []
            try:
                nested = self.list_nested_section_groups(sg_id)
                for sg in nested:
                    sg["_children"] = get_section_group_children(sg["id"], depth + 1)
                    nested_groups.append(sg)
            except Exception:
                pass

            return {
                "sections": sections,
                "sectionGroups": nested_groups,
            }

        # Get notebook info
        try:
            notebook = self._request("GET", f"/me/onenote/notebooks/{notebook_id}")
        except Exception:
            notebook = {"id": notebook_id, "displayName": "Unknown"}

        # Get direct sections
        sections = []
        try:
            sections = self.list_notebook_sections(notebook_id)
        except Exception:
            pass

        # Get section groups with their children
        section_groups = []
        try:
            sgs = self.list_notebook_section_groups(notebook_id)
            for sg in sgs:
                sg["_children"] = get_section_group_children(sg["id"])
                section_groups.append(sg)
        except Exception:
            pass

        return {
            "notebook": notebook,
            "sections": sections,
            "sectionGroups": section_groups,
        }

    def list_section_pages(self, section_id: str) -> List[Dict[str, Any]]:
        """List pages in a section.

        Args:
            section_id: Section ID

        Returns:
            List of page dicts
        """
        result = self._request("GET", f"/me/onenote/sections/{section_id}/pages")
        return result.get("value", [])

    def get_page_content(self, page_id: str) -> str:
        """Get the HTML content of a OneNote page.

        Args:
            page_id: Page ID

        Returns:
            Page HTML content
        """
        url = f"{GRAPH_URL}/me/onenote/pages/{page_id}/content"
        response = self.http_client.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "text/html",
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get page: {response.status_code}")

        return response.text

    def get_page_content_as_text(self, page_id: str) -> str:
        """Get OneNote page content as plain text (stripped HTML).

        Args:
            page_id: Page ID

        Returns:
            Plain text content
        """
        import re
        html = self.get_page_content(page_id)
        # Simple HTML tag stripping
        text = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def search_pages(self, query: str) -> List[Dict[str, Any]]:
        """Search across all OneNote pages.

        Args:
            query: Search query string

        Returns:
            List of matching page dicts
        """
        from urllib.parse import quote
        encoded_query = quote(query)
        result = self._request("GET", f"/me/onenote/pages?$search={encoded_query}")
        return result.get("value", [])

    def close(self):
        """Close the HTTP client."""
        self.http_client.close()


def get_user_graph_client() -> Optional[DelegatedGraphClient]:
    """Get a Graph client for the authenticated user.

    Returns:
        DelegatedGraphClient or None if not authenticated
    """
    _init_oauth_state()

    if not is_user_authenticated():
        return None

    tokens = st.session_state.ms_oauth_tokens
    if not tokens or "access_token" not in tokens:
        return None

    return DelegatedGraphClient(tokens["access_token"])


# =============================================================================
# Streamlit OAuth Handler
# =============================================================================

def handle_oauth_callback() -> bool:
    """Handle OAuth callback if code is present in URL.

    Call this at the start of your app to process OAuth redirects.

    Returns:
        True if OAuth callback was handled
    """
    _init_oauth_state()

    # Check for authorization code in query params
    query_params = st.query_params

    code = query_params.get("code")
    state = query_params.get("state")

    if code and state:
        # Exchange code for tokens
        tokens = exchange_code_for_tokens(code, state)

        # Clear query params
        st.query_params.clear()

        if tokens:
            st.success("Successfully signed in with Microsoft!")
            return True
        else:
            st.error("Failed to complete Microsoft sign-in")
            return False

    # Check for error
    error = query_params.get("error")
    if error:
        error_desc = query_params.get("error_description", "Unknown error")
        st.error(f"Microsoft sign-in error: {error_desc}")
        st.query_params.clear()
        return False

    return False


def show_ms_login_button():
    """Display Microsoft sign-in button."""
    _init_oauth_state()

    if is_user_authenticated():
        user = get_ms_user()
        st.success(f"Signed in as: {user.get('display_name', 'Unknown')}")

        if st.button("Sign out of Microsoft"):
            clear_ms_auth()
            st.rerun()
    else:
        try:
            auth_url = get_auth_url()

            # Use markdown link since Streamlit doesn't have native OAuth
            st.markdown(
                f'<a href="{auth_url}" target="_self">'
                '<button style="background-color: #0078d4; color: white; '
                'padding: 10px 20px; border: none; border-radius: 4px; '
                'cursor: pointer; font-size: 14px;">'
                '🔐 Sign in with Microsoft'
                '</button></a>',
                unsafe_allow_html=True,
            )
        except ValueError as e:
            st.warning(f"Microsoft OAuth not configured: {e}")
            st.caption("Set AZURE_CLIENT_ID and AZURE_TENANT_ID in .env")
