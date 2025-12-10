# Consent Form → Spruce Integration Architecture

**Date**: December 8, 2025
**Status**: Implementation Spec
**Version**: 1.0

---

## Overview

This document describes the architecture for a self-hosted consent form that posts responses directly to Spruce Health, making Spruce the single source of truth for patient communications.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONSENT FORM FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐    │
│  │ Patient      │    │ Azure Static     │    │ Azure Function          │    │
│  │ Explorer App │───>│ Web App          │───>│ (consent-form-handler)  │    │
│  │              │    │ (HTML Form)      │    │                         │    │
│  │ Generates    │    │                  │    │ 1. Validate token       │    │
│  │ token URL    │    │ Patient fills    │    │ 2. Format response      │    │
│  │              │    │ form & submits   │    │ 3. Post to Spruce API   │    │
│  └──────────────┘    └──────────────────┘    └───────────┬─────────────┘    │
│                                                          │                   │
│                                                          ▼                   │
│                                              ┌─────────────────────────┐    │
│                                              │ Spruce Health           │    │
│                                              │ (Patient Conversation)  │    │
│                                              │                         │    │
│                                              │ - Response as message   │    │
│                                              │ - Tagged for tracking   │    │
│                                              │ - Stored securely       │    │
│                                              └───────────┬─────────────┘    │
│                                                          │                   │
│                                                          ▼                   │
│  ┌──────────────┐                            ┌─────────────────────────┐    │
│  │ Patient      │<───────────────────────────│ Sync Module             │    │
│  │ Explorer App │                            │ (pull from Spruce API)  │    │
│  │              │                            │                         │    │
│  │ Updates      │                            │ - GET conversations     │    │
│  │ consent      │                            │ - Parse responses       │    │
│  │ status       │                            │ - Update local DB       │    │
│  └──────────────┘                            └─────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Azure Static Web App (Form Host)

**Purpose**: Host the HTML consent form accessible via tokenized URL

**URL Structure**:
```
https://greenclinic-consent.azurestaticapps.net/?token=ABC123XYZ
```

**Features**:
- Static HTML/CSS/JS (no server needed)
- HTTPS by default (Azure provides cert)
- CDN-backed for fast global access
- Validates token format client-side
- Posts to Azure Function

**Cost**: Free tier sufficient (~$0/month)

---

### 2. Azure Function (Form Handler)

**Purpose**: Process form submissions and post to Spruce

**Endpoint**:
```
POST https://greenclinic-consent-api.azurewebsites.net/api/submit-consent
```

**Flow**:
1. Receive form data + token
2. Validate token against database (optional, can be deferred)
3. Format response as structured message
4. Look up patient's Spruce conversation by phone
5. Post message to conversation OR create new conversation
6. Return success/error to form

**Runtime**: Python 3.10+
**Cost**: Consumption plan (~$0-5/month for expected volume)

---

### 3. Spruce Health (Storage)

**Purpose**: Store consent responses in patient conversations

**Message Format**:
```
📋 CONSENT FORM RESPONSE
========================
Submitted: 2025-12-08 14:30:00 EST
Token: ABC123XYZ

Name: John Smith
DOB: 1970-01-15

Preferred Contact: Text message (SMS)
Consent Given: Yes

Provider Preference: Continue with Dr. Green

Questions/Concerns:
None at this time.

---
[Auto-captured via Patient Explorer Consent Form]
```

**Benefits**:
- Appears in patient's conversation thread
- Staff can see response in Spruce UI
- Fully searchable
- Under existing BAA

---

### 4. Sync Module (Patient Explorer)

**Purpose**: Pull responses from Spruce into local database

**Trigger Options**:
- Manual "Sync Responses" button in app
- Scheduled job (if app is running)
- On-demand when viewing patient

**API Calls**:
```python
# Get recent conversations with consent form responses
GET /v1/conversations?limit=100

# For each conversation, check for form response messages
GET /v1/conversations/{id}/items
```

---

## Token System

### Token Generation (Existing)

Located in: `app/consent_tokens.py`

```python
def create_patient_token(patient_id: int, db) -> str:
    """Generate unique token for patient consent form."""
    token = secrets.token_urlsafe(16)  # 22 chars, URL-safe
    # Store in database with patient_id, created_at, expires_at
    return token
```

### Token URL

```
https://greenclinic-consent.azurestaticapps.net/?token=ABC123XYZ789DEF
```

### Token Validation (Azure Function)

```python
def validate_token(token: str) -> Optional[dict]:
    """Validate token and return patient info."""
    # Option A: Check against local database (requires DB access)
    # Option B: Decode JWT if using signed tokens
    # Option C: Accept all well-formed tokens, match later via phone
    pass
```

---

## Spruce Auto-Responder Setup

**Configure in Spruce UI** (not via API):

1. Go to **Spruce Web App** → **Settings** → **Auto-Responders**
2. Create new auto-responder:
   - **Name**: `SMS Privacy Disclaimer`
   - **Trigger**: When any SMS is received
   - **Message**:
     ```
     Thanks for replying. For private health matters, please call
     205-955-7605. SMS is not secure. Reply STOP to opt out.
     ```
   - **Active Hours**: All day (or business hours only)

This handles the privacy disclaimer without any hosted webhook.

---

## Security Considerations

### HTTPS Everywhere
- Azure Static Web App: HTTPS by default
- Azure Function: HTTPS by default
- Spruce API: HTTPS only

### Token Security
- Tokens are single-use or time-limited
- Tokens don't contain PHI
- Token → Patient mapping stored locally

### Data Flow
- Form data encrypted in transit (TLS)
- Spruce storage encrypted at rest
- No PHI stored in Azure Static Web App
- Azure Function is ephemeral (no persistent storage)

### HIPAA Compliance
| Component | BAA Coverage |
|-----------|--------------|
| Azure Static Web App | ✅ Via Azure BAA |
| Azure Function | ✅ Via Azure BAA |
| Spruce Health | ✅ Existing BAA |
| Patient Explorer (local) | ✅ Local encrypted storage |

---

## Implementation Files

```
Project_Patient_Explorer_App/
├── azure-function/
│   ├── function_app.py          # Main function code
│   ├── requirements.txt         # Python dependencies
│   ├── host.json               # Function configuration
│   └── local.settings.json     # Local dev settings (gitignored)
│
├── consent-form/
│   ├── index.html              # Main form page
│   ├── style.css               # Form styling
│   ├── script.js               # Form validation & submit
│   └── staticwebapp.config.json # Azure Static Web App config
│
└── architecture/
    └── Consent_Form_Spruce_Integration.md  # This document
```

---

## Deployment Steps

### Step 1: Create Azure Static Web App

```bash
# Using Azure CLI
az staticwebapp create \
  --name greenclinic-consent \
  --resource-group GreenClinic \
  --location "East US 2" \
  --source ./consent-form \
  --sku Free
```

### Step 2: Create Azure Function App

```bash
# Create Function App
az functionapp create \
  --name greenclinic-consent-api \
  --resource-group GreenClinic \
  --consumption-plan-location "East US 2" \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --storage-account stgreenclinic

# Configure environment variables
az functionapp config appsettings set \
  --name greenclinic-consent-api \
  --resource-group GreenClinic \
  --settings "SPRUCE_API_TOKEN=<token>"
```

### Step 3: Deploy Function Code

```bash
cd azure-function
func azure functionapp publish greenclinic-consent-api
```

### Step 4: Configure Spruce Auto-Responder

Manual step in Spruce web UI (see above).

### Step 5: Update Patient Explorer

Add new environment variable:
```env
CONSENT_FORM_URL=https://greenclinic-consent.azurestaticapps.net
```

---

## Cost Estimate

| Component | Tier | Monthly Cost |
|-----------|------|--------------|
| Azure Static Web App | Free | $0 |
| Azure Function | Consumption | ~$0-2 |
| Azure Storage (logs) | Standard | ~$1 |
| **Total** | | **~$1-3/month** |

---

## Alternative: All-in-One Azure Function

Instead of Static Web App + Function, could use a single Azure Function that:
1. Serves the HTML form (GET request)
2. Processes submissions (POST request)

```python
@app.route(route="consent", methods=["GET", "POST"])
def consent_form(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "GET":
        return serve_html_form(req.params.get("token"))
    else:
        return process_submission(req.get_json())
```

**Pro**: Single deployment
**Con**: Slightly more complex, less CDN optimization

---

## Next Steps

1. [ ] Create HTML consent form
2. [ ] Create Azure Function code
3. [ ] Test locally with Azure Functions Core Tools
4. [ ] Deploy to Azure
5. [ ] Configure Spruce auto-responder
6. [ ] Update Patient Explorer to generate new form URLs
7. [ ] Add sync module to pull responses from Spruce

---

*Created: December 8, 2025*
*For: Patient Explorer V1.0*
