# Spruce Health API Capabilities

**Date:** 2025-12-02
**Status:** Research Complete
**Priority:** HIGH - Core integration for consent outreach

---

## Executive Summary

Spruce Health API enables:
- Automated SMS messaging for consent outreach
- Patient contact management with tags and routing
- Webhook integration for real-time events
- Deep linking between Spruce and Patient Explorer

API is included at **no additional cost** with Spruce subscription.

---

## API Capabilities

### 1. Messaging

| Feature | Capability |
|---------|------------|
| Send SMS | Trigger outbound SMS to patients |
| Secure Messages | Send in-app secure messages |
| Fax | Send faxes programmatically |
| Group SMS | Send to multiple recipients |
| Message Templates | Use pre-defined message formats |

### 2. Contact Management

| Feature | Capability |
|---------|------------|
| Get Contacts | Retrieve patient contact list |
| Search Contacts | Find by name, phone, email |
| Contact Cards | Store additional patient info |
| Tags | Categorize contacts for routing |
| Create Contacts | Add new patients programmatically |

### 3. Conversations

| Feature | Capability |
|---------|------------|
| Get Threads | Retrieve conversation history |
| Message Events | Track message status |
| Attachments | Handle document/photo uploads |
| Read Receipts | Track message engagement |

### 4. Webhooks/Events

| Event | Description |
|-------|-------------|
| Message Received | Patient sends message/reply |
| Message Sent | Outbound message confirmed |
| Call Events | Incoming/outgoing call tracking |
| Contact Updated | Patient info changed |

### 5. Deep Linking

| Feature | Capability |
|---------|------------|
| Open Conversation | Link to specific patient thread |
| Create Message | Pre-populate message compose |
| View Contact | Jump to patient card |

---

## Authentication

### API Token Generation

1. Log in to Spruce web app
2. Go to Settings > Integrations & API
3. Generate API token
4. Store securely in `.env`

```env
SPRUCE_API_TOKEN=your_base64_encoded_token
SPRUCE_ACCESS_ID=your_access_id
```

### Request Headers

```python
headers = {
    "Authorization": f"Bearer {SPRUCE_API_TOKEN}",
    "Content-Type": "application/json",
    "X-Spruce-Access-ID": SPRUCE_ACCESS_ID
}
```

---

## API Endpoints (Documented)

### Get All Contacts

```
GET https://api.sprucehealth.com/v1/contacts
```

**Response:**
```json
{
  "contacts": [
    {
      "id": "contact_123",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+12055551234",
      "email": "john@example.com",
      "tags": ["apcm", "green-clinic"],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Search Contacts

```
GET https://api.sprucehealth.com/v1/contacts/search?q=Smith
```

### Send SMS Message

```
POST https://api.sprucehealth.com/v1/messages
Content-Type: application/json

{
  "contact_id": "contact_123",
  "type": "sms",
  "body": "Hi John, please complete your consent form: https://..."
}
```

### Get Conversations

```
GET https://api.sprucehealth.com/v1/conversations
```

### Post to Conversation

```
POST https://api.sprucehealth.com/v1/conversations/{id}/messages
{
  "body": "Message content",
  "type": "sms"
}
```

---

## Current Implementation (phase0/spruce/client.py)

### SpruceClient Class

```python
class SpruceClient:
    def __init__(self):
        self.api_token = os.getenv("SPRUCE_API_TOKEN")
        self.access_id = os.getenv("SPRUCE_ACCESS_ID")
        self.base_url = "https://api.sprucehealth.com/v1"

    def get_all_contacts(self):
        """Retrieve all Spruce contacts"""
        response = httpx.get(
            f"{self.base_url}/contacts",
            headers=self._headers()
        )
        return response.json().get("contacts", [])

    def search_contacts(self, query):
        """Search contacts by name/phone"""
        response = httpx.get(
            f"{self.base_url}/contacts/search",
            params={"q": query},
            headers=self._headers()
        )
        return response.json().get("contacts", [])

    def send_sms(self, contact_id, message):
        """Send SMS to contact"""
        response = httpx.post(
            f"{self.base_url}/messages",
            json={
                "contact_id": contact_id,
                "type": "sms",
                "body": message
            },
            headers=self._headers()
        )
        return response.json()
```

---

## Consent Outreach Workflow

### Automated Campaign Flow

```
1. Load patients from Excel
         ↓
2. Match to Spruce contacts (by phone/name)
         ↓
3. Generate consent tokens for each patient
         ↓
4. Send initial SMS via Spruce API
         ↓
5. Track message delivery status
         ↓
6. Wait for response (webhook or form submission)
         ↓
7. Send follow-up reminders (Day 3, 7, 14)
         ↓
8. Update consent status in SharePoint/DB
```

### SMS Template Variables

```python
template_vars = {
    "patient_name": patient.first_name,
    "consent_url": f"https://forms.office.com/...?token={token}",
    "office_phone": "205-955-7605",
    "provider_name": "Dr. Robert Green"
}

message = sms_templates.render("initial_outreach", **template_vars)
spruce_client.send_sms(contact_id, message)
```

---

## CRM-Like Features (Per User Notes)

### Tag-Based Routing

Spruce supports tags on contacts for routing:
- `apcm` - APCM enrolled patients
- `green-clinic` - Dr. Green's patients
- `consent-pending` - Awaiting consent response
- `high-priority` - Urgent follow-up needed

### Contact Cards

Store additional metadata:
- MRN (for internal reference)
- Consent status
- Last outreach date
- Notes

### Rules Engine

Spruce routing rules can:
- Auto-assign conversations by tag
- Route to specific team members
- Trigger follow-up reminders

---

## Testing Notes

### Test Organization Setup

1. Create separate Spruce test organization
2. Contact Team Spruce to enable API
3. Test SMS won't deliver (unregistered number)
4. But API responses will indicate success

### Test vs Production

| Aspect | Test | Production |
|--------|------|------------|
| SMS Delivery | Blocked | Active |
| API Responses | Full | Full |
| Rate Limits | Standard | Standard |
| Webhooks | Available | Available |

---

## Rate Limits

- Typical API: 100 requests/minute
- SMS: Subject to carrier limits
- Bulk operations: Batch in groups of 50

---

## Webhook Integration (Future)

### Available Events

```json
{
  "event": "message.received",
  "data": {
    "contact_id": "contact_123",
    "message": "Yes, I consent",
    "received_at": "2025-12-02T10:30:00Z"
  }
}
```

### Webhook Setup

1. Configure webhook URL in Spruce settings
2. Receive POST requests for events
3. Parse and update Patient Explorer database

---

## Integration Partners

Spruce has established integrations with:
- Keragon (healthcare automation)
- Athena Health
- Akute Health
- Hint Health

---

## Recommendations

### Immediate (Phase 0)

1. **Test SMS sending** with real Spruce credentials
2. **Implement bulk SMS** for campaign launch
3. **Track delivery status** in database
4. **Use tags** for consent status tracking

### Future (Phase 1+)

1. **Webhook integration** for real-time response handling
2. **Deep linking** from Patient Explorer to Spruce
3. **Contact card sync** with patient metadata
4. **Conversation threading** for context

---

## References

- [Spruce API Documentation](https://help.sprucehealth.com/hc/en-us/articles/23003250146459-Spruce-API)
- [Spruce Public API](https://sprucehealth.com/spruce-api)
- [Secure Messaging with Patients](https://help.sprucehealth.com/hc/en-us/articles/23003230656667-Secure-Messaging-with-Patients)

---

*Generated: 2025-12-02 by BMAD Research Agent*
