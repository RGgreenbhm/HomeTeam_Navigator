# Research Report: Spruce Health API Webhooks for Inbound SMS

**Date**: December 8, 2025  
**Status**: Research Complete  
**Priority**: HIGH - Enables real-time consent response capture  
**Researcher**: Claude AI Assistant

---

## Executive Summary

Spruce Health provides a robust webhook system that can capture inbound SMS messages in real-time. This enables automatic detection of patient consent responses (e.g., "Yes" replies) without manual CSV export/import workflows.

**Key Finding**: The `conversationItem.created` event fires when patients send SMS replies, providing message content, contact information, and conversation context.

---

## Webhook System Overview

### What Are Spruce Webhooks?

Spruce Webhooks push real-time notifications to your application when events occur in your Spruce organization. Instead of polling the API for changes, you register an endpoint and Spruce sends HTTP POST requests when:

- Contacts are created, updated, or deleted
- Conversations are created, updated, or deleted  
- Messages (conversation items) are created, updated, deleted, or restored

### Requirements

| Requirement | Detail |
|-------------|--------|
| **API Access** | Must be enabled by Spruce Support |
| **Plan** | Communicator plan required |
| **Endpoint** | HTTPS only (no HTTP) |
| **Response Time** | Must respond with 2XX within 5 seconds |
| **Rate Limit** | 1,000 events per minute per endpoint |

---

## Event Types

### Contact Events

| Event | Description |
|-------|-------------|
| `contact.created` | New contact added to organization |
| `contact.updated` | Contact information modified |
| `contact.deleted` | Contact removed |

### Conversation Events

| Event | Description |
|-------|-------------|
| `conversation.created` | New conversation started |
| `conversation.updated` | Conversation modified (tags, title, etc.) |
| `conversation.deleted` | Conversation deleted |

### Conversation Item Events (Messages) ⭐

| Event | Description |
|-------|-------------|
| `conversationItem.created` | **New message sent or received** |
| `conversationItem.updated` | Message modified |
| `conversationItem.deleted` | Message deleted |
| `conversationItem.restored` | Deleted message restored |

**The `conversationItem.created` event is the key event for capturing inbound SMS consent responses.**

---

## Webhook Payload Structure

### Conversation Item Created (Inbound SMS)

When a patient sends an SMS reply, you receive:

```json
{
  "eventTime": "2025-12-08T14:30:00Z",
  "object": "event",
  "type": "conversationItem.created",
  "data": {
    "object": {
      "apiURL": "https://api.sprucehealth.com/v1/conversationItems/ti_29PN3P8GEXXXX",
      "appURL": "https://api.sprucehealth.com/org/entity_28QNVEPK2XXXX/thread/t_29BJ656OKLG00/message/ti_29PN3P8GEXXXX",
      "attachments": [],
      "author": {
        "displayName": "Patient Name"
      },
      "buttons": null,
      "conversationId": "t_29S7786ETXXXX",
      "createdAt": "2025-12-08T14:30:00Z",
      "direction": "inbound",
      "id": "ti_29PN3P8GEXXXX",
      "isInternalNote": false,
      "modifiedAt": "2025-12-08T14:30:00Z",
      "object": "conversationItem",
      "pages": [],
      "text": "Yes I consent"
    }
  }
}
```

**Key Fields for Consent Detection**:
- `direction`: `"inbound"` indicates patient sent the message
- `text`: The actual message content (check for "Yes", "I consent", etc.)
- `conversationId`: Links to the conversation/patient
- `author.displayName`: Patient's name in Spruce

---

## Mapping Messages to Patients

### Step 1: Get Conversation Details

When you receive a `conversationItem.created` event, use the `conversationId` to fetch the full conversation:

```http
GET https://api.sprucehealth.com/v1/conversations/{conversationId}
Authorization: Bearer {token}
```

### Step 2: Extract Contact Information

The conversation response includes `externalParticipants`:

**For SMS conversations with saved contacts:**
```json
{
  "conversation": {
    "type": "phone",
    "externalParticipants": [
      {
        "displayName": "John Smith",
        "contact": "entity_28SQM2TF8XXXX",
        "endpoint": {
          "channel": "phone",
          "displayValue": "(205) 555-1234",
          "rawValue": "+12055551234"
        }
      }
    ]
  }
}
```

**Key Fields**:
- `contact`: Spruce contact ID (use to look up full contact details)
- `endpoint.rawValue`: Phone number in E.164 format

### Step 3: Get Full Contact Details

```http
GET https://api.sprucehealth.com/v1/contacts/{contactId}
Authorization: Bearer {token}
```

Returns full contact information including custom fields, tags, etc.

---

## Registering a Webhook Endpoint

### Create Endpoint via API

```bash
curl --request POST \
  --url https://api.sprucehealth.com/v1/webhooks/endpoints \
  --header 'accept: application/json' \
  --header 'authorization: Bearer <api-token>' \
  --header 'content-type: application/json' \
  --data '{
    "name": "Patient Explorer Consent Webhook",
    "url": "https://your-domain.com/api/spruce/webhooks"
  }'
```

### Response

```json
{
  "id": "webhook_endpoint_123",
  "name": "Patient Explorer Consent Webhook",
  "url": "https://your-domain.com/api/spruce/webhooks",
  "secret": "whsec_XXXXXXXXXXXXXXXXXXXXXXXX",
  "paused": false,
  "createdAt": "2025-12-08T10:00:00Z"
}
```

**⚠️ IMPORTANT**: Save the `secret` immediately! It's only returned once and is needed to verify webhook signatures.

### Manage Endpoints

```python
# List all webhook endpoints
GET /v1/webhooks/endpoints

# Pause/resume an endpoint
POST /v1/webhooks/endpoints/{id}/pause
POST /v1/webhooks/endpoints/{id}/resume

# Delete an endpoint
DELETE /v1/webhooks/endpoints/{id}
```

---

## Signature Verification

Spruce signs all webhook payloads for security. Verify signatures to ensure requests are authentic.

### Header

```
X-Spruce-Signature: <base64-encoded-signature>
```

### Verification (Python)

```python
import hmac
import hashlib
import base64

def verify_spruce_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify that a webhook request came from Spruce.
    
    Args:
        payload: Raw request body bytes
        signature_header: Value of X-Spruce-Signature header
        secret: Webhook endpoint secret from registration
        
    Returns:
        True if signature is valid
    """
    # Decode the signature from base64
    expected_signature = base64.b64decode(signature_header)
    
    # Compute HMAC-SHA256
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).digest()
    
    # Compare securely
    return hmac.compare_digest(computed_signature, expected_signature)
```

### Usage in Flask/FastAPI

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
SPRUCE_WEBHOOK_SECRET = os.getenv("SPRUCE_WEBHOOK_SECRET")

@app.route("/api/spruce/webhooks", methods=["POST"])
def handle_spruce_webhook():
    # Get signature
    signature = request.headers.get("X-Spruce-Signature")
    if not signature:
        return jsonify({"error": "Missing signature"}), 401
    
    # Verify signature
    if not verify_spruce_signature(request.data, signature, SPRUCE_WEBHOOK_SECRET):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process event
    event = request.json
    event_type = event.get("type")
    
    if event_type == "conversationItem.created":
        handle_new_message(event["data"]["object"])
    
    # Must respond with 2XX within 5 seconds
    return jsonify({"status": "received"}), 200
```

---

## Consent Detection Logic

### Python Implementation

```python
import re
from datetime import datetime
from typing import Optional, Dict, Any

# Patterns that indicate consent
CONSENT_PATTERNS = [
    r'\byes\b',
    r'\bi consent\b',
    r'\bi agree\b',
    r'\baccept\b',
    r'\bapprove\b',
    r'\bok\b',
    r'\bsure\b',
]

# Patterns that indicate decline
DECLINE_PATTERNS = [
    r'\bno\b',
    r'\bdecline\b',
    r'\brefuse\b',
    r'\bstop\b',
    r'\bcancel\b',
]

def detect_consent_response(message_text: str) -> Optional[str]:
    """
    Analyze message text to detect consent or decline.
    
    Returns:
        'consent' if patient consented
        'decline' if patient declined
        None if unclear
    """
    text = message_text.lower().strip()
    
    # Check for consent patterns
    for pattern in CONSENT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 'consent'
    
    # Check for decline patterns
    for pattern in DECLINE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 'decline'
    
    return None


def handle_new_message(message_data: Dict[str, Any]):
    """
    Process an inbound message from Spruce webhook.
    """
    # Only process inbound messages
    if message_data.get("direction") != "inbound":
        return
    
    # Skip internal notes
    if message_data.get("isInternalNote"):
        return
    
    message_text = message_data.get("text", "")
    conversation_id = message_data.get("conversationId")
    message_id = message_data.get("id")
    timestamp = message_data.get("createdAt")
    
    # Detect consent
    consent_status = detect_consent_response(message_text)
    
    if consent_status:
        # Get patient contact from conversation
        contact_info = get_contact_from_conversation(conversation_id)
        
        if contact_info:
            # Update patient record
            update_patient_consent(
                phone=contact_info.get("phone"),
                contact_id=contact_info.get("id"),
                consent_status=consent_status,
                message_text=message_text,
                message_id=message_id,
                timestamp=timestamp
            )
            
            print(f"Consent detected: {consent_status} from {contact_info.get('displayName')}")
    else:
        # Log for manual review
        print(f"Unclear response, needs manual review: {message_text[:100]}")


def get_contact_from_conversation(conversation_id: str) -> Optional[Dict]:
    """
    Fetch contact details from a conversation ID.
    """
    import requests
    
    # Get conversation details
    response = requests.get(
        f"https://api.sprucehealth.com/v1/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {SPRUCE_API_TOKEN}"}
    )
    
    if response.status_code != 200:
        return None
    
    conversation = response.json()
    
    # Extract first external participant
    participants = conversation.get("externalParticipants", [])
    if not participants:
        return None
    
    participant = participants[0]
    contact_id = participant.get("contact")
    
    if contact_id:
        # Fetch full contact details
        contact_response = requests.get(
            f"https://api.sprucehealth.com/v1/contacts/{contact_id}",
            headers={"Authorization": f"Bearer {SPRUCE_API_TOKEN}"}
        )
        if contact_response.status_code == 200:
            return contact_response.json()
    
    # Return endpoint info if no contact
    endpoint = participant.get("endpoint", {})
    return {
        "phone": endpoint.get("rawValue"),
        "displayName": participant.get("displayName")
    }
```

---

## Azure Function Webhook Receiver

For production, deploy an Azure Function to receive webhooks:

```python
# function_app.py
import azure.functions as func
import json
import logging
import os
import hmac
import hashlib
import base64

app = func.FunctionApp()

@app.route(route="spruce-webhook", methods=["POST"])
def spruce_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to receive Spruce webhooks.
    """
    logging.info('Spruce webhook received')
    
    # Verify signature
    signature = req.headers.get("X-Spruce-Signature")
    secret = os.environ.get("SPRUCE_WEBHOOK_SECRET")
    
    if not signature or not secret:
        return func.HttpResponse("Unauthorized", status_code=401)
    
    body = req.get_body()
    
    expected_sig = base64.b64decode(signature)
    computed_sig = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    
    if not hmac.compare_digest(expected_sig, computed_sig):
        return func.HttpResponse("Invalid signature", status_code=401)
    
    # Parse event
    try:
        event = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)
    
    event_type = event.get("type")
    logging.info(f"Event type: {event_type}")
    
    # Handle conversation item created (new message)
    if event_type == "conversationItem.created":
        message_data = event.get("data", {}).get("object", {})
        
        # Only process inbound messages
        if message_data.get("direction") == "inbound":
            process_inbound_message(message_data)
    
    return func.HttpResponse("OK", status_code=200)


def process_inbound_message(message_data: dict):
    """Process an inbound SMS message for consent detection."""
    text = message_data.get("text", "").lower()
    conversation_id = message_data.get("conversationId")
    
    # Simple consent detection
    if any(word in text for word in ["yes", "consent", "agree", "ok"]):
        logging.info(f"CONSENT DETECTED in conversation {conversation_id}")
        # TODO: Update patient database
        # TODO: Send confirmation message
        
    elif any(word in text for word in ["no", "decline", "stop"]):
        logging.info(f"DECLINE DETECTED in conversation {conversation_id}")
        # TODO: Update patient database
        
    else:
        logging.info(f"UNCLEAR RESPONSE: {text[:100]}")
        # TODO: Queue for manual review
```

---

## Retry Behavior & Error Handling

### Spruce Retry Policy

- If your endpoint doesn't respond with 2XX, Spruce retries every 2 minutes
- Maximum 10 retry attempts
- After 10 failures, the event is dropped

### Best Practices

1. **Respond quickly** (within 5 seconds) with 200 OK
2. **Process asynchronously** - queue events for background processing
3. **Implement idempotency** - events may be delivered more than once
4. **Log all events** for debugging and audit trail
5. **Monitor endpoint health** - set up alerts for failures

### Event Ordering

Events are sent in order but may arrive out of order. Handle accordingly:
- Use `eventTime` for sequencing
- Don't assume strict ordering
- Store message IDs to detect duplicates

---

## Implementation Checklist

### Prerequisites
- [ ] Spruce API access enabled (contact Team Spruce)
- [ ] API token generated in Spruce Settings > Integrations & API
- [ ] Communicator plan active

### Webhook Setup
- [ ] Deploy HTTPS endpoint (Azure Function recommended)
- [ ] Register webhook endpoint via API
- [ ] Save webhook secret securely in environment variables
- [ ] Implement signature verification
- [ ] Test with sample events

### Consent Processing
- [ ] Implement consent pattern detection
- [ ] Map conversation IDs to patient records
- [ ] Update Patient Explorer database on consent
- [ ] Queue unclear responses for manual review
- [ ] Send confirmation messages (optional)

### Monitoring
- [ ] Log all webhook events
- [ ] Alert on signature verification failures
- [ ] Monitor response times (<5 seconds)
- [ ] Track consent detection accuracy

---

## Environment Variables

```env
# Spruce API
SPRUCE_API_TOKEN=your_bearer_token
SPRUCE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Azure Function (if using)
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

---

## Security Considerations

1. **Always verify signatures** - Reject requests without valid signatures
2. **Use HTTPS only** - Spruce won't send to HTTP endpoints
3. **Protect secrets** - Store webhook secret in secure vault (e.g., Azure Key Vault)
4. **Rate limiting** - Implement rate limiting on your endpoint
5. **Input validation** - Validate all webhook data before processing
6. **Audit logging** - Log all consent-related events for compliance

---

## Comparison: Webhooks vs. Manual Export

| Aspect | Webhooks | Manual CSV Export |
|--------|----------|-------------------|
| **Latency** | Real-time (~seconds) | Manual (hours/days) |
| **Effort** | Automated | Staff time required |
| **Reliability** | Consistent | Human error risk |
| **Scalability** | Handles any volume | Limited by staff capacity |
| **Setup Complexity** | Higher initial setup | Simple |
| **Maintenance** | Monitor endpoint health | None |

**Recommendation**: Use webhooks for production to enable real-time consent tracking. Keep manual export as a backup/audit mechanism.

---

## References

- [Spruce Webhooks Overview](https://developer.sprucehealth.com/docs/webhooks-overview)
- [Create Webhook Endpoint](https://developer.sprucehealth.com/reference/createwebhookendpoint)
- [List Webhook Endpoints](https://developer.sprucehealth.com/reference/listwebhookendpoints)
- [Spruce API Overview](https://developer.sprucehealth.com/docs/overview)
- [Spruce API Help Article](https://help.sprucehealth.com/hc/en-us/articles/23003250146459-Spruce-API)

---

*Research completed: December 8, 2025*  
*Ready for implementation pending Spruce API access confirmation*
