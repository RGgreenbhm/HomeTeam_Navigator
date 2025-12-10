# Microsoft OAuth 2.0 for OneNote Integration

**Date:** 2025-12-02
**Status:** Research Complete
**Priority:** HIGH - Required for Green Clinic Team Notebook access

---

## Executive Summary

Microsoft Graph OneNote API **will no longer support app-only authentication effective March 31, 2025**. All OneNote access must use **delegated (user) authentication**. This is favorable for Patient Explorer because:

1. User signs in with their own Microsoft account
2. Application accesses only notebooks the user can access
3. Aligns with HIPAA "minimum necessary" principle
4. Can leverage existing Microsoft 365 BAA

---

## Technical Implementation

### Required App Registration

1. **Register app in Microsoft Entra ID** (formerly Azure AD)
2. **Required values to save:**
   - Application ID (client_id)
   - Client Secret (for web apps) or Certificate
   - Redirect URI (e.g., `http://localhost:8501/callback` for Streamlit)

### OAuth 2.0 Authorization Code Flow

#### Step 1: Authorization Request

```
GET https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
?client_id={application_id}
&response_type=code
&redirect_uri={redirect_uri}
&scope=Notes.Read Notes.Read.All offline_access
&state={random_state}
```

**Tenant options:**
- `common` - Personal + Work/School accounts (recommended)
- `organizations` - Work/School only
- `consumers` - Personal Microsoft accounts only
- `southviewteam.com` - Specific tenant (most secure)

#### Step 2: Token Exchange

```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={application_id}
&client_secret={secret}
&code={authorization_code}
&redirect_uri={redirect_uri}
&grant_type=authorization_code
&scope=Notes.Read Notes.Read.All offline_access
```

#### Step 3: Access OneNote

```
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks
Authorization: Bearer {access_token}
```

### Required Permissions (Scopes)

| Scope | Type | Description |
|-------|------|-------------|
| `Notes.Read` | Delegated | Read user notebooks |
| `Notes.Read.All` | Delegated | Read all notebooks user can access |
| `Notes.ReadWrite` | Delegated | Read/write notebooks (if editing needed) |
| `offline_access` | Delegated | Get refresh tokens |

### Refresh Token Handling

```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={application_id}
&client_secret={secret}
&refresh_token={refresh_token}
&grant_type=refresh_token
&scope=Notes.Read Notes.Read.All offline_access
```

---

## OneNote API Endpoints

### List Notebooks
```
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks
```

### List Sections in Notebook
```
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks/{notebook-id}/sections
```

### List Pages in Section
```
GET https://graph.microsoft.com/v1.0/me/onenote/sections/{section-id}/pages
```

### Get Page Content
```
GET https://graph.microsoft.com/v1.0/me/onenote/pages/{page-id}/content
Accept: text/html
```

### SharePoint-Hosted Notebooks (Green Clinic Team Notebook)

For notebooks on SharePoint (southviewteam.com), use:
```
GET https://graph.microsoft.com/v1.0/sites/{site-id}/onenote/notebooks
```

Or via the user's accessible notebooks:
```
GET https://graph.microsoft.com/v1.0/me/onenote/notebooks?$filter=isShared eq true
```

---

## Python Implementation for Streamlit

### Required Libraries
```bash
pip install msal streamlit requests
```

### Authentication Module

```python
# app/microsoft_auth.py
import msal
import streamlit as st
from urllib.parse import urlencode

class MicrosoftAuth:
    def __init__(self, client_id, client_secret, tenant_id="common"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.redirect_uri = "http://localhost:8501/callback"
        self.scopes = ["Notes.Read", "Notes.Read.All", "offline_access"]

        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=self.authority,
            client_credential=client_secret
        )

    def get_auth_url(self):
        """Generate authorization URL for user login"""
        return self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=st.session_state.get("auth_state", "")
        )

    def get_token_from_code(self, code):
        """Exchange authorization code for tokens"""
        result = self.app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        return result

    def get_token_silent(self, account):
        """Get token silently using cached credentials"""
        result = self.app.acquire_token_silent(
            scopes=self.scopes,
            account=account
        )
        return result
```

### OneNote Client

```python
# app/onenote_client.py
import requests

class OneNoteClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0/me/onenote"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def list_notebooks(self):
        """List all accessible notebooks"""
        response = requests.get(
            f"{self.base_url}/notebooks",
            headers=self.headers
        )
        return response.json().get("value", [])

    def list_sections(self, notebook_id):
        """List sections in a notebook"""
        response = requests.get(
            f"{self.base_url}/notebooks/{notebook_id}/sections",
            headers=self.headers
        )
        return response.json().get("value", [])

    def list_pages(self, section_id):
        """List pages in a section"""
        response = requests.get(
            f"{self.base_url}/sections/{section_id}/pages",
            headers=self.headers
        )
        return response.json().get("value", [])

    def get_page_content(self, page_id):
        """Get HTML content of a page"""
        response = requests.get(
            f"{self.base_url}/pages/{page_id}/content",
            headers={**self.headers, "Accept": "text/html"}
        )
        return response.text

    def find_green_clinic_notebook(self):
        """Find the Green Clinic Team Notebook"""
        notebooks = self.list_notebooks()
        for nb in notebooks:
            if "Green Clinic" in nb.get("displayName", ""):
                return nb
        return None
```

---

## Streamlit Integration Pattern

### Login Flow in Streamlit

```python
# In Streamlit page
import streamlit as st
from microsoft_auth import MicrosoftAuth

auth = MicrosoftAuth(
    client_id=st.secrets["MS_CLIENT_ID"],
    client_secret=st.secrets["MS_CLIENT_SECRET"],
    tenant_id="southviewteam.com"  # Restrict to org
)

# Check for callback
query_params = st.query_params
if "code" in query_params:
    # Exchange code for token
    result = auth.get_token_from_code(query_params["code"])
    if "access_token" in result:
        st.session_state["ms_token"] = result["access_token"]
        st.session_state["ms_refresh"] = result.get("refresh_token")
        st.rerun()

# Login button
if "ms_token" not in st.session_state:
    auth_url = auth.get_auth_url()
    st.markdown(f"[Sign in with Microsoft]({auth_url})")
else:
    st.success("Signed in to Microsoft 365")
    # Use OneNote client...
```

---

## Security Considerations

### HIPAA Alignment

1. **User-delegated access** = User responsible for what they access
2. **Tenant restriction** = Limit to southviewteam.com/greenclinicteam.com
3. **Audit logging** = Microsoft Graph provides audit trails
4. **Token storage** = Store encrypted, expire after session

### Multi-Factor Authentication (MFA)

- MFA is handled by Microsoft's login page
- User completes 2FA during initial auth
- Refresh tokens allow subsequent silent auth
- Daily MFA re-authentication is acceptable per user's workflow

### Token Security

```python
# Store tokens securely in session
st.session_state["ms_token"] = access_token  # In-memory only
# Never persist access tokens to disk
# Refresh tokens can be encrypted if persisted
```

---

## App Registration Steps (Azure Portal)

1. Go to [Azure Portal](https://portal.azure.com) > Microsoft Entra ID > App registrations
2. Click "New registration"
3. Name: "Patient Explorer - Green Clinic"
4. Supported account types: "Accounts in this organizational directory only (southviewteam.com)"
5. Redirect URI: Web > `http://localhost:8501/callback`
6. Click Register
7. Copy Application (client) ID
8. Go to Certificates & secrets > New client secret
9. Copy the secret value immediately (won't be shown again)
10. Go to API permissions > Add permission > Microsoft Graph > Delegated
11. Add: Notes.Read, Notes.Read.All, offline_access
12. Grant admin consent (if admin)

---

## Environment Variables

```env
# .env additions for OneNote
MS_CLIENT_ID=your_application_id
MS_CLIENT_SECRET=your_client_secret
MS_TENANT_ID=southviewteam.com
MS_REDIRECT_URI=http://localhost:8501/callback
```

---

## References

- [Microsoft Graph OneNote API Overview](https://learn.microsoft.com/en-us/graph/integrate-with-onenote)
- [Get access on behalf of a user](https://learn.microsoft.com/en-us/graph/auth-v2-user)
- [Microsoft Graph Permissions Reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [Why MS Graph API for OneNote requires Delegated access](https://learn.microsoft.com/en-us/answers/questions/2280453/why-ms-graph-api-for-onenote-are-updated-to-use-de)
- [MSAL Python Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-python)

---

## Next Steps

1. [ ] Register app in Azure Portal for southviewteam.com
2. [ ] Implement MicrosoftAuth class in Streamlit app
3. [ ] Add OneNoteClient with Green Clinic notebook discovery
4. [ ] Test login flow with Dr. Green's account
5. [ ] Implement page content extraction for patient worksheets
6. [ ] Connect to Azure Claude for worksheet parsing

---

*Generated: 2025-12-02 by BMAD Research Agent*
