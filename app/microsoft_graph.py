"""Microsoft Graph API client for Patient Explorer.

This module provides Microsoft 365 integration with TWO authentication modes:

1. APP-ONLY AUTH (Client Credentials) - DEFERRED TO V1.1
   - Uses ConfidentialClientApplication with client_secret
   - For background/service operations without user sign-in
   - Requires Application permissions with admin consent

2. DELEGATED AUTH (User Sign-In) - V1.0 ACTIVE
   - Uses ms_oauth.py module with PKCE flow
   - User signs in with Microsoft account
   - Access to user's own resources (SharePoint, OneNote, etc.)
   - See ms_oauth.py and DelegatedGraphClient for this mode

For V1.0, use the DelegatedGraphClient from ms_oauth.py after user sign-in.
The GraphClient class in this file (app-only) is deferred to V1.1.

Provides integration with Microsoft 365 services:
- OneNote: Patient notes sync
- SharePoint: Document storage, list management
- Planner: Team task management
- To Do: Personal task lists
- Outlook: Calendar, reminders (future)

Covered under Microsoft BAA when deployed.

Usage (V1.0 - Delegated):
    from ms_oauth import get_user_graph_client, is_user_authenticated

    if is_user_authenticated():
        client = get_user_graph_client()
        notebooks = client.list_notebooks()

Usage (V1.1 - App-Only):
    from microsoft_graph import GraphClient

    client = GraphClient()  # Uses client credentials
    notebooks = client.list_notebooks(user_id="user@domain.com")

Prerequisites for App-Only (V1.1):
    1. Azure AD App Registration
    2. Application permissions: Organization.Read.All, Sites.ReadWrite.All, etc.
    3. Admin consent granted
    4. Environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import httpx
from msal import ConfidentialClientApplication
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class OneNoteNotebook:
    """OneNote notebook metadata."""
    id: str
    name: str
    created: datetime
    sections: List[Dict[str, str]]


@dataclass
class SharePointList:
    """SharePoint list metadata."""
    id: str
    name: str
    web_url: str
    item_count: int


class GraphClient:
    """Client for Microsoft Graph API.

    Uses client credentials (app-only) authentication.
    """

    GRAPH_URL = "https://graph.microsoft.com/v1.0"
    SCOPES = ["https://graph.microsoft.com/.default"]

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Initialize Graph client.

        Args:
            tenant_id: Azure AD tenant ID (defaults to env var)
            client_id: App registration client ID (defaults to env var)
            client_secret: App client secret (defaults to env var)
        """
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET")

        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Missing Azure AD credentials (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)")

        # Initialize MSAL app
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
        )

        self._access_token = None
        self.http_client = httpx.Client(timeout=30.0)

    def _get_token(self, force_refresh: bool = False) -> str:
        """Get or refresh access token.

        Args:
            force_refresh: If True, clear token cache and get fresh token
        """
        if force_refresh:
            # Clear MSAL's internal token cache
            for account in self.app.get_accounts():
                self.app.remove_account(account)
            # Clear internal cache (for client credentials, tokens are stored differently)
            if hasattr(self.app, '_token_cache'):
                self.app._token_cache._cache.clear()

        result = self.app.acquire_token_for_client(scopes=self.SCOPES)

        if "access_token" in result:
            self._access_token = result["access_token"]
            return self._access_token
        else:
            error = result.get("error_description", result.get("error", "Unknown error"))
            raise Exception(f"Failed to acquire token: {error}")

    def get_token_info(self) -> Dict[str, Any]:
        """Get info about the current access token for debugging.

        Returns:
            Dict with token metadata (expiry, scopes in token, etc.)
        """
        import base64
        import json

        token = self._get_token()

        # JWT tokens have 3 parts: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid token format"}

        try:
            # Decode payload (middle part) - add padding if needed
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding

            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)

            return {
                "app_id": claims.get("appid"),
                "tenant": claims.get("tid"),
                "roles": claims.get("roles", []),  # This shows granted permissions
                "exp": claims.get("exp"),  # Expiry timestamp
                "iat": claims.get("iat"),  # Issued at timestamp
                "aud": claims.get("aud"),  # Audience (should be Graph API)
            }
        except Exception as e:
            return {"error": f"Failed to decode token: {e}"}

    def force_new_token(self) -> str:
        """Force acquisition of a completely new token (clears all caches)."""
        return self._get_token(force_refresh=True)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        token = self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make a Graph API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            json: JSON body
            data: Raw body data
            content_type: Content type for raw data

        Returns:
            Response JSON
        """
        url = f"{self.GRAPH_URL}{endpoint}"
        headers = self._get_headers()

        if content_type:
            headers["Content-Type"] = content_type

        response = self.http_client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            content=data,
        )

        if response.status_code >= 400:
            logger.error(f"Graph API error: {response.status_code} - {response.text}")
            raise Exception(f"Graph API error: {response.status_code} - {response.text}")

        if response.status_code == 204:  # No content
            return {}

        return response.json()

    # =========================================================================
    # OneNote Operations
    # =========================================================================

    def list_notebooks(self, user_id: Optional[str] = None, group_id: Optional[str] = None) -> List[OneNoteNotebook]:
        """List OneNote notebooks.

        With app-only auth, must specify user_id or group_id.
        With delegated auth (user_id=None, group_id=None), uses /me endpoint.

        Args:
            user_id: Optional user ID for app-only auth
            group_id: Optional group ID for group notebooks

        Returns:
            List of OneNoteNotebook objects
        """
        if group_id:
            endpoint = f"/groups/{group_id}/onenote/notebooks"
        elif user_id:
            endpoint = f"/users/{user_id}/onenote/notebooks"
        else:
            # Requires delegated auth
            endpoint = "/me/onenote/notebooks"

        result = self._request("GET", endpoint)

        notebooks = []
        for nb in result.get("value", []):
            notebooks.append(OneNoteNotebook(
                id=nb["id"],
                name=nb["displayName"],
                created=datetime.fromisoformat(nb["createdDateTime"].replace("Z", "+00:00")),
                sections=[],
            ))

        return notebooks

    def list_notebook_sections(self, notebook_id: str, user_id: Optional[str] = None, group_id: Optional[str] = None) -> List[Dict[str, str]]:
        """List sections in a notebook.

        Args:
            notebook_id: OneNote notebook ID
            user_id: Optional user ID for app-only auth
            group_id: Optional group ID for group notebooks

        Returns:
            List of section info dicts
        """
        if group_id:
            endpoint = f"/groups/{group_id}/onenote/notebooks/{notebook_id}/sections"
        elif user_id:
            endpoint = f"/users/{user_id}/onenote/notebooks/{notebook_id}/sections"
        else:
            endpoint = f"/me/onenote/notebooks/{notebook_id}/sections"

        result = self._request("GET", endpoint)

        return [
            {"id": s["id"], "name": s["displayName"]}
            for s in result.get("value", [])
        ]

    def create_onenote_page(
        self,
        section_id: str,
        title: str,
        content: str,
    ) -> Dict[str, Any]:
        """Create a new page in a OneNote section.

        Args:
            section_id: OneNote section ID
            title: Page title
            content: HTML content for the page

        Returns:
            Created page info
        """
        # OneNote pages use HTML format
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
        </head>
        <body>
            {content}
        </body>
        </html>
        """

        return self._request(
            "POST",
            f"/me/onenote/sections/{section_id}/pages",
            data=html_content.encode("utf-8"),
            content_type="application/xhtml+xml",
        )

    def get_onenote_page_content(self, page_id: str) -> str:
        """Get the HTML content of a OneNote page.

        Args:
            page_id: OneNote page ID

        Returns:
            Page HTML content
        """
        url = f"{self.GRAPH_URL}/me/onenote/pages/{page_id}/content"
        headers = self._get_headers()
        headers["Accept"] = "text/html"

        response = self.http_client.get(url, headers=headers)

        if response.status_code >= 400:
            raise Exception(f"Failed to get page: {response.status_code}")

        return response.text

    # =========================================================================
    # SharePoint Operations
    # =========================================================================

    def get_sharepoint_site(self, site_path: str) -> Dict[str, Any]:
        """Get SharePoint site info by path.

        Args:
            site_path: Site path (e.g., "southviewteam.sharepoint.com:/sites/PatientExplorer")

        Returns:
            Site info dict
        """
        return self._request("GET", f"/sites/{site_path}")

    def list_sharepoint_sites(self) -> List[Dict[str, Any]]:
        """List SharePoint sites accessible to the app.

        Returns:
            List of site info dicts
        """
        result = self._request("GET", "/sites?search=*")
        return result.get("value", [])

    def list_sharepoint_lists(self, site_id: str) -> List[SharePointList]:
        """List SharePoint lists in a site.

        Args:
            site_id: SharePoint site ID

        Returns:
            List of SharePointList objects
        """
        result = self._request("GET", f"/sites/{site_id}/lists")

        lists = []
        for lst in result.get("value", []):
            lists.append(SharePointList(
                id=lst["id"],
                name=lst["displayName"],
                web_url=lst.get("webUrl", ""),
                item_count=lst.get("list", {}).get("itemCount", 0),
            ))

        return lists

    def get_list_items(
        self,
        site_id: str,
        list_id: str,
        select: Optional[List[str]] = None,
        filter_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get items from a SharePoint list.

        Args:
            site_id: SharePoint site ID
            list_id: List ID
            select: Fields to select
            filter_query: OData filter query

        Returns:
            List of item dicts
        """
        endpoint = f"/sites/{site_id}/lists/{list_id}/items?expand=fields"

        if select:
            endpoint += f"&$select={','.join(select)}"
        if filter_query:
            endpoint += f"&$filter={filter_query}"

        result = self._request("GET", endpoint)
        return result.get("value", [])

    def create_list_item(
        self,
        site_id: str,
        list_id: str,
        fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create an item in a SharePoint list.

        Args:
            site_id: SharePoint site ID
            list_id: List ID
            fields: Field values for the new item

        Returns:
            Created item info
        """
        return self._request(
            "POST",
            f"/sites/{site_id}/lists/{list_id}/items",
            json={"fields": fields},
        )

    def update_list_item(
        self,
        site_id: str,
        list_id: str,
        item_id: str,
        fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an item in a SharePoint list.

        Args:
            site_id: SharePoint site ID
            list_id: List ID
            item_id: Item ID
            fields: Field values to update

        Returns:
            Updated item info
        """
        return self._request(
            "PATCH",
            f"/sites/{site_id}/lists/{list_id}/items/{item_id}/fields",
            json=fields,
        )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def test_connection(self) -> Dict[str, Any]:
        """Test the API connection with diagnostics.

        Returns:
            Dict with success status and diagnostic info
        """
        result = {
            "success": False,
            "auth_type": "client_credentials",
            "error": None,
            "hint": None,
        }

        try:
            # Try to get basic info - this works with Application permissions
            org_result = self._request("GET", "/organization")
            if org_result.get("value"):
                result["success"] = True
                result["organization"] = org_result["value"][0].get("displayName", "Unknown")
                return result
        except Exception as e:
            error_str = str(e)
            result["error"] = error_str

            # Detect common permission issues
            if "403" in error_str or "Authorization_RequestDenied" in error_str:
                result["hint"] = (
                    "Permission denied. This usually means:\n"
                    "1. Using Delegated permissions with client_credentials flow (won't work)\n"
                    "2. Need to use Application permissions instead\n"
                    "3. Or implement OAuth user sign-in flow for delegated permissions"
                )
            elif "401" in error_str:
                result["hint"] = "Authentication failed. Check AZURE_CLIENT_SECRET is correct."

            logger.error(f"Connection test failed: {e}")

        return result

    def get_current_user(self) -> Dict[str, Any]:
        """Get info about the authenticated app/user.

        Returns:
            User/app info dict
        """
        try:
            return self._request("GET", "/me")
        except Exception:
            # App-only auth doesn't have /me, return org info instead
            result = self._request("GET", "/organization")
            if result.get("value"):
                return result["value"][0]
            return {}

    def close(self):
        """Close the HTTP client."""
        self.http_client.close()

    # =========================================================================
    # Microsoft Planner Operations
    # =========================================================================

    def list_my_planner_tasks(self) -> List[Dict[str, Any]]:
        """List all Planner tasks assigned to the current user.

        Returns:
            List of task dicts
        """
        result = self._request("GET", "/me/planner/tasks")
        return result.get("value", [])

    def list_group_plans(self, group_id: str) -> List[Dict[str, Any]]:
        """List Planner plans for a Microsoft 365 group.

        Args:
            group_id: M365 group ID

        Returns:
            List of plan dicts
        """
        result = self._request("GET", f"/groups/{group_id}/planner/plans")
        return result.get("value", [])

    def get_plan_details(self, plan_id: str) -> Dict[str, Any]:
        """Get details for a Planner plan.

        Args:
            plan_id: Plan ID

        Returns:
            Plan details dict
        """
        return self._request("GET", f"/planner/plans/{plan_id}")

    def list_plan_tasks(self, plan_id: str) -> List[Dict[str, Any]]:
        """List all tasks in a Planner plan.

        Args:
            plan_id: Plan ID

        Returns:
            List of task dicts
        """
        result = self._request("GET", f"/planner/plans/{plan_id}/tasks")
        return result.get("value", [])

    def list_plan_buckets(self, plan_id: str) -> List[Dict[str, Any]]:
        """List buckets in a Planner plan.

        Args:
            plan_id: Plan ID

        Returns:
            List of bucket dicts
        """
        result = self._request("GET", f"/planner/plans/{plan_id}/buckets")
        return result.get("value", [])

    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get task details including checklist and description.

        Args:
            task_id: Task ID

        Returns:
            Task details dict
        """
        return self._request("GET", f"/planner/tasks/{task_id}/details")

    def create_planner_task(
        self,
        plan_id: str,
        title: str,
        bucket_id: Optional[str] = None,
        assigned_to: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        priority: int = 5,
    ) -> Dict[str, Any]:
        """Create a new Planner task.

        Args:
            plan_id: Plan ID
            title: Task title
            bucket_id: Optional bucket ID
            assigned_to: List of user IDs to assign
            due_date: Due date in ISO format
            priority: Priority (1=urgent, 3=important, 5=medium, 9=low)

        Returns:
            Created task dict
        """
        body: Dict[str, Any] = {
            "planId": plan_id,
            "title": title,
            "priority": priority,
        }

        if bucket_id:
            body["bucketId"] = bucket_id

        if assigned_to:
            body["assignments"] = {
                user_id: {"@odata.type": "#microsoft.graph.plannerAssignment", "orderHint": " !"}
                for user_id in assigned_to
            }

        if due_date:
            body["dueDateTime"] = due_date

        return self._request("POST", "/planner/tasks", json=body)

    def update_task_progress(
        self,
        task_id: str,
        percent_complete: int,
        etag: str,
    ) -> Dict[str, Any]:
        """Update task completion percentage.

        Args:
            task_id: Task ID
            percent_complete: Completion percentage (0, 50, or 100)
            etag: Current ETag for optimistic concurrency

        Returns:
            Updated task dict
        """
        url = f"{self.GRAPH_URL}/planner/tasks/{task_id}"
        headers = self._get_headers()
        headers["If-Match"] = etag

        response = self.http_client.patch(
            url,
            headers=headers,
            json={"percentComplete": percent_complete},
        )

        if response.status_code >= 400:
            raise Exception(f"Failed to update task: {response.status_code} - {response.text}")

        return response.json() if response.content else {}

    # =========================================================================
    # Microsoft To Do Operations
    # =========================================================================

    def list_todo_lists(self) -> List[Dict[str, Any]]:
        """List all To Do task lists for current user.

        Returns:
            List of task list dicts
        """
        result = self._request("GET", "/me/todo/lists")
        return result.get("value", [])

    def list_todo_tasks(self, list_id: str) -> List[Dict[str, Any]]:
        """List tasks in a To Do list.

        Args:
            list_id: To Do list ID

        Returns:
            List of task dicts
        """
        result = self._request("GET", f"/me/todo/lists/{list_id}/tasks")
        return result.get("value", [])

    def create_todo_task(
        self,
        list_id: str,
        title: str,
        body_content: Optional[str] = None,
        due_date: Optional[str] = None,
        importance: str = "normal",
    ) -> Dict[str, Any]:
        """Create a new To Do task.

        Args:
            list_id: To Do list ID
            title: Task title
            body_content: Task description
            due_date: Due date in ISO format
            importance: low, normal, or high

        Returns:
            Created task dict
        """
        task_body: Dict[str, Any] = {
            "title": title,
            "importance": importance,
        }

        if body_content:
            task_body["body"] = {
                "content": body_content,
                "contentType": "text",
            }

        if due_date:
            task_body["dueDateTime"] = {
                "dateTime": due_date,
                "timeZone": "UTC",
            }

        return self._request("POST", f"/me/todo/lists/{list_id}/tasks", json=task_body)

    def complete_todo_task(self, list_id: str, task_id: str) -> Dict[str, Any]:
        """Mark a To Do task as complete.

        Args:
            list_id: To Do list ID
            task_id: Task ID

        Returns:
            Updated task dict
        """
        return self._request(
            "PATCH",
            f"/me/todo/lists/{list_id}/tasks/{task_id}",
            json={"status": "completed"},
        )

    # =========================================================================
    # User & Group Operations
    # =========================================================================

    def list_my_groups(self) -> List[Dict[str, Any]]:
        """List Microsoft 365 groups the current user is a member of.

        Returns:
            List of group dicts
        """
        result = self._request("GET", "/me/memberOf/microsoft.graph.group?$filter=groupTypes/any(c:c eq 'Unified')")
        return result.get("value", [])

    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Get user info by email address.

        Args:
            email: User email

        Returns:
            User dict
        """
        return self._request("GET", f"/users/{email}")

    def list_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """List members of a group.

        Args:
            group_id: Group ID

        Returns:
            List of member dicts
        """
        result = self._request("GET", f"/groups/{group_id}/members")
        return result.get("value", [])


# =============================================================================
# Patient-Specific Helpers
# =============================================================================

def sync_patient_to_onenote(
    patient_data: Dict[str, Any],
    notebook_id: str,
    section_id: str,
    client: Optional[GraphClient] = None,
) -> Dict[str, Any]:
    """Sync a patient record to OneNote.

    Creates or updates a OneNote page for the patient.

    Args:
        patient_data: Patient information dict
        notebook_id: OneNote notebook ID
        section_id: Section ID for patient notes
        client: Optional existing client

    Returns:
        Created/updated page info
    """
    _client = client or GraphClient()

    # Build HTML content
    html = f"""
    <h1>{patient_data.get('last_name', '')}, {patient_data.get('first_name', '')}</h1>
    <p><strong>MRN:</strong> {patient_data.get('mrn', 'N/A')}</p>
    <p><strong>DOB:</strong> {patient_data.get('date_of_birth', 'N/A')}</p>
    <p><strong>Phone:</strong> {patient_data.get('phone', 'N/A')}</p>

    <h2>APCM Status</h2>
    <p><strong>Enrolled:</strong> {'Yes' if patient_data.get('apcm_enrolled') else 'No'}</p>
    <p><strong>Level:</strong> {patient_data.get('apcm_level', 'N/A')}</p>

    <h2>Consent Status</h2>
    <p><strong>Status:</strong> {patient_data.get('consent_status', 'Pending')}</p>

    <hr/>
    <p><em>Last synced: {datetime.now().isoformat()}</em></p>
    """

    title = f"{patient_data.get('last_name', 'Unknown')}, {patient_data.get('first_name', '')} - {patient_data.get('mrn', 'No MRN')}"

    result = _client.create_onenote_page(section_id, title, html)

    if not client:
        _client.close()

    return result


def create_patient_sharepoint_list_item(
    site_id: str,
    list_id: str,
    patient_data: Dict[str, Any],
    client: Optional[GraphClient] = None,
) -> Dict[str, Any]:
    """Create a patient record in a SharePoint list.

    Args:
        site_id: SharePoint site ID
        list_id: List ID
        patient_data: Patient information
        client: Optional existing client

    Returns:
        Created item info
    """
    _client = client or GraphClient()

    # Map patient data to SharePoint list fields
    # Note: Field names depend on your SharePoint list schema
    fields = {
        "Title": f"{patient_data.get('last_name', '')}, {patient_data.get('first_name', '')}",
        "MRN": patient_data.get("mrn"),
        "DateOfBirth": patient_data.get("date_of_birth"),
        "Phone": patient_data.get("phone"),
        "APCMEnrolled": patient_data.get("apcm_enrolled", False),
        "ConsentStatus": patient_data.get("consent_status", "Pending"),
    }

    result = _client.create_list_item(site_id, list_id, fields)

    if not client:
        _client.close()

    return result
