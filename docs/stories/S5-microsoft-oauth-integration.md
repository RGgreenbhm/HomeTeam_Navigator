# Story S5: Microsoft OAuth Integration

**Epic:** Authentication & Security
**Priority:** HIGH
**Points:** 8
**Sprint:** Dec 2-8, 2025

---

## User Story

**As a** clinical staff member
**I want to** sign in with my Microsoft work account
**So that** I can access Patient Explorer securely and connect to OneNote

---

## Acceptance Criteria

### AC1: Login Flow
- [ ] User clicks "Sign in with Microsoft" button
- [ ] Redirected to Microsoft login page
- [ ] Can authenticate with southviewteam.com or greenclinicteam.com credentials
- [ ] Supports MFA (Microsoft handles 2FA)
- [ ] Returns to app after successful login

### AC2: Session Management
- [ ] Session created after successful OAuth
- [ ] Session persists across page navigation
- [ ] Logout button available
- [ ] Session expires after inactivity (configurable)

### AC3: Token Handling
- [ ] Access token stored in session (not persisted)
- [ ] Refresh token used for silent token renewal
- [ ] Token errors handled gracefully
- [ ] Re-authentication prompted when tokens expire

### AC4: User Display
- [ ] User's name shown in header after login
- [ ] User's email available for audit logging
- [ ] Profile photo displayed (optional)

---

## Technical Tasks

### Task 1: Azure App Registration
- [ ] Register app in Azure Portal
- [ ] Configure for southviewteam.com tenant
- [ ] Add redirect URI for Streamlit
- [ ] Generate client secret
- [ ] Add Notes.Read, Notes.Read.All, offline_access permissions
- [ ] Grant admin consent

### Task 2: Implement MicrosoftAuth Class
```python
# app/microsoft_auth.py
class MicrosoftAuth:
    def __init__(self, client_id, client_secret, tenant_id):
        # MSAL configuration
        pass

    def get_auth_url(self) -> str:
        # Generate authorization URL
        pass

    def get_token_from_code(self, code: str) -> dict:
        # Exchange code for tokens
        pass

    def get_token_silent(self, account) -> dict:
        # Silent token refresh
        pass
```

### Task 3: Streamlit Integration
```python
# In app pages
def require_auth():
    if "ms_token" not in st.session_state:
        auth_url = auth.get_auth_url()
        st.markdown(f"[Sign in with Microsoft]({auth_url})")
        st.stop()
    return st.session_state["ms_user"]
```

### Task 4: Callback Handler
- [ ] Handle OAuth callback in Streamlit
- [ ] Parse authorization code from URL
- [ ] Exchange code for tokens
- [ ] Store tokens in session
- [ ] Redirect to main app

### Task 5: Environment Configuration
```env
MS_CLIENT_ID=xxx
MS_CLIENT_SECRET=xxx
MS_TENANT_ID=southviewteam.com
MS_REDIRECT_URI=http://localhost:8501/callback
```

---

## Dependencies

- Azure subscription with Entra ID access
- Admin consent for app permissions
- MSAL Python library (`pip install msal`)

---

## Definition of Done

- [ ] User can sign in with Microsoft
- [ ] Session persists across navigation
- [ ] Logout works correctly
- [ ] Tokens refresh automatically
- [ ] Error handling for auth failures
- [ ] Unit tests for auth class
- [ ] Manual testing on both machines

---

## Notes

- Microsoft requires delegated auth for OneNote (effective March 2025)
- This authentication will also be used for OneNote access
- MFA is handled by Microsoft, user completes once per session
- Daily re-authentication acceptable per user's workflow

---

*Created: 2025-12-02*
