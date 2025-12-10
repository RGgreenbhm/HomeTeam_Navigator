# Spruce Health API - SMS Messaging Integration Guide

**Date**: December 8, 2025  
**Purpose**: Configure Spruce API for SMS messaging from Python/Streamlit  
**Status**: Troubleshooting Guide for 400 Bad Request Errors

---

## Executive Summary

This guide addresses the 400 Bad Request errors encountered when attempting to send SMS messages via the Spruce Health API. Based on the official Spruce API documentation, **the approach used in the initial implementation appears to be using incorrect endpoints and request formats.**

### Key Finding

The Spruce API does **NOT** use a simple `/messages` endpoint. Instead, SMS messages must be sent using the **Internal Endpoints** system:

```
POST https://api.sprucehealth.com/v1/internalendpoints/{internalEndpointId}/conversations
```

---

## Root Cause of 400 Errors

### Problem: Incorrect API Endpoint

The existing `phase0/spruce/client.py` implementation uses:

```python
# INCORRECT - This endpoint doesn't exist
POST https://api.sprucehealth.com/v1/messages
{
    "contact_id": "contact_123",
    "type": "sms",
    "body": "Message content"
}
```

### Solution: Correct API Endpoint

The Spruce API requires:

```python
# CORRECT - Use internal endpoints
POST https://api.sprucehealth.com/v1/internalendpoints/{internalEndpointId}/conversations
{
    "destination": {
        "smsOrEmailEndpoint": "+12055551234"
    },
    "message": {
        "body": [
            {
                "type": "text",
                "value": "Message content"
            }
        ]
    }
}
```

---

## Correct API Flow for Sending SMS

### Step 1: Get Your Internal Endpoints

First, retrieve your organization's internal endpoints (Spruce phone numbers):

```python
import requests
import os

SPRUCE_API_TOKEN = os.getenv("SPRUCE_API_TOKEN")
BASE_URL = "https://api.sprucehealth.com/v1"

def get_internal_endpoints():
    """Get all internal endpoints (phone numbers) for the organization."""
    response = requests.get(
        f"{BASE_URL}/internalendpoints",
        headers={
            "Authorization": f"Bearer {SPRUCE_API_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get endpoints: {response.status_code} - {response.text}")
    
    return response.json()
```

### Step 2: Find the Phone Channel Endpoint

Filter for the endpoint with channel type `phone`:

```python
def get_phone_endpoint_id():
    """Get the internal endpoint ID for SMS (phone channel)."""
    endpoints = get_internal_endpoints()
    
    for endpoint in endpoints.get("internalEndpoints", []):
        if endpoint.get("channel") == "phone":
            return endpoint.get("id")
    
    raise Exception("No phone endpoint found for this organization")
```

### Expected Internal Endpoints Response

```json
{
  "internalEndpoints": [
    {
      "id": "ZW50aXR5XzI4UU5WRVBLMk9PMDI6...",
      "channel": "phone",
      "displayValue": "(205) 555-1234",
      "rawValue": "+12055551234",
      "isInternal": true,
      "object": "endpoint"
    },
    {
      "id": "ZW50aXR5XzI4UU5WRVBLMk9PMDI6...",
      "channel": "secure",
      "displayValue": "https://spruce.care/yourorg",
      "isInternal": true,
      "object": "endpoint"
    },
    {
      "id": "ZW50aXR5XzI4UU5WRVBLMk9PMDI6...",
      "channel": "email",
      "displayValue": "yourorg@sprucemail.com",
      "isInternal": true,
      "object": "endpoint"
    }
  ]
}
```

### Step 3: Send SMS Message

```python
def send_sms(phone_number: str, message: str) -> dict:
    """
    Send SMS message to a phone number via Spruce API.
    
    Args:
        phone_number: Destination phone number (E.164 format: +12055551234)
        message: SMS message content
        
    Returns:
        API response dict
    """
    # Get the phone endpoint ID
    endpoint_id = get_phone_endpoint_id()
    
    # Format phone number to E.164 if needed
    formatted_phone = format_phone_e164(phone_number)
    
    # Build request
    url = f"{BASE_URL}/internalendpoints/{endpoint_id}/conversations"
    
    payload = {
        "destination": {
            "smsOrEmailEndpoint": formatted_phone
        },
        "message": {
            "body": [
                {
                    "type": "text",
                    "value": message
                }
            ]
        }
    }
    
    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {SPRUCE_API_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code not in [200, 201]:
        raise Exception(f"SMS send failed: {response.status_code} - {response.text}")
    
    return response.json()


def format_phone_e164(phone: str) -> str:
    """
    Format phone number to E.164 format (+1XXXXXXXXXX).
    
    Examples:
        "205-555-1234" -> "+12055551234"
        "(205) 555-1234" -> "+12055551234"
        "2055551234" -> "+12055551234"
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Handle 10-digit US numbers
    if len(digits) == 10:
        return f"+1{digits}"
    
    # Handle 11-digit numbers starting with 1
    if len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    
    # Already has country code
    if len(digits) > 10:
        return f"+{digits}"
    
    raise ValueError(f"Invalid phone number format: {phone}")
```

---

## Complete Updated SpruceClient Class

```python
"""
Spruce Health API Client for SMS Messaging
Updated: December 8, 2025

Corrected to use the proper internal endpoints API.
"""

import os
import requests
from typing import Optional, List, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SpruceEndpoint:
    """Represents a Spruce internal endpoint (phone, email, secure, fax)."""
    id: str
    channel: str  # "phone", "email", "secure", "fax"
    display_value: str
    raw_value: Optional[str] = None


class SpruceClient:
    """
    Spruce Health API Client.
    
    Handles authentication and provides methods for:
    - Listing contacts
    - Sending SMS messages
    - Managing conversations
    
    Environment Variables Required:
        SPRUCE_API_TOKEN: Bearer token from Spruce Settings > Integrations & API
    """
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("SPRUCE_API_TOKEN")
        if not self.api_token:
            raise ValueError("SPRUCE_API_TOKEN environment variable not set")
        
        self.base_url = "https://api.sprucehealth.com/v1"
        self._phone_endpoint_id: Optional[str] = None
        self._endpoints_cache: Optional[List[SpruceEndpoint]] = None
    
    def _headers(self) -> dict:
        """Get standard headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        response = requests.request(
            method,
            url,
            headers=self._headers(),
            **kwargs
        )
        
        # Log rate limit info
        if "s-ratelimit-remaining" in response.headers:
            remaining = response.headers.get("s-ratelimit-remaining")
            limit = response.headers.get("s-ratelimit-limit")
            logger.debug(f"Rate limit: {remaining}/{limit} remaining")
        
        return response
    
    # =========================================================================
    # INTERNAL ENDPOINTS
    # =========================================================================
    
    def get_internal_endpoints(self, force_refresh: bool = False) -> List[SpruceEndpoint]:
        """
        Get all internal endpoints for the organization.
        
        Internal endpoints include:
        - Phone numbers (for SMS)
        - Email addresses
        - Secure messaging links
        - Fax numbers
        
        Returns:
            List of SpruceEndpoint objects
        """
        if self._endpoints_cache and not force_refresh:
            return self._endpoints_cache
        
        response = self._request("GET", "/internalendpoints")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get internal endpoints: {response.status_code} - {response.text}")
        
        data = response.json()
        endpoints = []
        
        for ep in data.get("internalEndpoints", []):
            endpoints.append(SpruceEndpoint(
                id=ep.get("id"),
                channel=ep.get("channel"),
                display_value=ep.get("displayValue", ""),
                raw_value=ep.get("rawValue")
            ))
        
        self._endpoints_cache = endpoints
        return endpoints
    
    def get_phone_endpoint_id(self) -> str:
        """
        Get the internal endpoint ID for the phone channel (SMS).
        
        This ID is required for sending SMS messages.
        
        Returns:
            The endpoint ID string
            
        Raises:
            Exception if no phone endpoint exists
        """
        if self._phone_endpoint_id:
            return self._phone_endpoint_id
        
        endpoints = self.get_internal_endpoints()
        
        for ep in endpoints:
            if ep.channel == "phone":
                self._phone_endpoint_id = ep.id
                logger.info(f"Found phone endpoint: {ep.display_value}")
                return ep.id
        
        raise Exception("No phone endpoint found. Ensure your Spruce organization has a phone number.")
    
    # =========================================================================
    # SMS MESSAGING
    # =========================================================================
    
    def send_sms(self, phone_number: str, message: str, idempotency_key: Optional[str] = None) -> dict:
        """
        Send an SMS message to a phone number.
        
        IMPORTANT: This sends to a raw phone number, not a Spruce contact ID.
        The message will appear in Spruce and create/update a conversation.
        
        Args:
            phone_number: Destination phone number (any format, will be normalized)
            message: SMS message content (max ~1600 chars for single SMS)
            idempotency_key: Optional key to prevent duplicate sends (max 255 chars)
            
        Returns:
            API response containing requestId and conversation info
            
        Raises:
            Exception on API error
        """
        # Get phone endpoint
        endpoint_id = self.get_phone_endpoint_id()
        
        # Format phone number
        formatted_phone = self._format_phone_e164(phone_number)
        
        # Build payload
        payload = {
            "destination": {
                "smsOrEmailEndpoint": formatted_phone
            },
            "text": message
        }
        
        # Optional idempotency key
        headers = self._headers()
        if idempotency_key:
            headers["s-idempotency-key"] = idempotency_key[:255]
        
        # Make request
        url = f"/internalendpoints/{endpoint_id}/conversations"
        
        response = requests.post(
            f"{self.base_url}{url}",
            json=payload,
            headers=headers
        )
        
        if response.status_code not in [200, 201]:
            error_detail = self._parse_error(response)
            raise Exception(f"SMS send failed: {error_detail}")
        
        result = response.json()
        logger.info(f"SMS sent successfully. RequestID: {result.get('requestId')}")
        
        return result
    
    def send_sms_to_contact(self, contact_id: str, message: str) -> dict:
        """
        Send SMS to an existing Spruce contact.
        
        This first looks up the contact's phone number, then sends via SMS.
        
        Args:
            contact_id: Spruce contact ID (e.g., "entity_28SQM2TF8XXXX")
            message: SMS message content
            
        Returns:
            API response
        """
        # Get contact details
        contact = self.get_contact(contact_id)
        
        phone = contact.get("phone") or contact.get("mobilePhone")
        if not phone:
            raise Exception(f"Contact {contact_id} has no phone number")
        
        return self.send_sms(phone, message)
    
    def _format_phone_e164(self, phone: str) -> str:
        """
        Format phone number to E.164 format (+1XXXXXXXXXX for US).
        
        Args:
            phone: Phone number in any format
            
        Returns:
            E.164 formatted phone number
        """
        if not phone:
            raise ValueError("Phone number is required")
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if len(digits) == 10:
            # US 10-digit: 2055551234 -> +12055551234
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            # US 11-digit: 12055551234 -> +12055551234
            return f"+{digits}"
        elif len(digits) > 11:
            # International or already has country code
            return f"+{digits}"
        else:
            raise ValueError(f"Invalid phone number: {phone} (got {len(digits)} digits)")
    
    def _parse_error(self, response: requests.Response) -> str:
        """Parse error response from API."""
        try:
            error_data = response.json()
            return f"{response.status_code} - {error_data.get('type', 'unknown')}: {error_data.get('message', response.text)}"
        except:
            return f"{response.status_code} - {response.text}"
    
    # =========================================================================
    # CONTACTS
    # =========================================================================
    
    def get_contacts(self, limit: int = 100, pagination_token: str = "") -> dict:
        """
        Get all contacts in the organization.
        
        Args:
            limit: Max contacts to return (default 100)
            pagination_token: Token for pagination (from previous response)
            
        Returns:
            Dict with 'contacts' list and optional 'paginationToken'
        """
        params = {"limit": limit}
        if pagination_token:
            params["paginationToken"] = pagination_token
        
        response = self._request("GET", "/contacts", params=params)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get contacts: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_all_contacts(self) -> List[dict]:
        """Get all contacts, handling pagination automatically."""
        all_contacts = []
        pagination_token = ""
        
        while True:
            result = self.get_contacts(limit=100, pagination_token=pagination_token)
            all_contacts.extend(result.get("contacts", []))
            
            pagination_token = result.get("paginationToken", "")
            if not pagination_token:
                break
        
        return all_contacts
    
    def get_contact(self, contact_id: str) -> dict:
        """Get a specific contact by ID."""
        response = self._request("GET", f"/contacts/{contact_id}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get contact: {response.status_code} - {response.text}")
        
        return response.json()
    
    def search_contacts(self, query: str) -> List[dict]:
        """
        Search contacts by name, phone, or email.
        
        Args:
            query: Search term
            
        Returns:
            List of matching contacts
        """
        response = self._request("POST", "/contacts/search", json={"query": query})
        
        if response.status_code != 200:
            raise Exception(f"Failed to search contacts: {response.status_code} - {response.text}")
        
        return response.json().get("contacts", [])
    
    # =========================================================================
    # CONVERSATIONS
    # =========================================================================
    
    def get_conversations(self, limit: int = 50) -> List[dict]:
        """Get recent conversations."""
        response = self._request("GET", "/conversations", params={"limit": limit})
        
        if response.status_code != 200:
            raise Exception(f"Failed to get conversations: {response.status_code} - {response.text}")
        
        return response.json().get("conversations", [])
    
    def post_to_conversation(self, conversation_id: str, message: str) -> dict:
        """
        Post a message to an existing conversation.
        
        Args:
            conversation_id: Spruce conversation ID
            message: Message content
            
        Returns:
            API response
        """
        response = self._request(
            "POST",
            f"/conversations/{conversation_id}/messages",
            json={"text": message}
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to post message: {response.status_code} - {response.text}")
        
        return response.json()


# =============================================================================
# STREAMLIT INTEGRATION HELPERS
# =============================================================================

def create_sms_sender_ui():
    """Streamlit UI component for sending SMS."""
    import streamlit as st
    
    st.subheader("Send SMS via Spruce")
    
    # Initialize client
    try:
        client = SpruceClient()
        
        # Show connected phone number
        endpoints = client.get_internal_endpoints()
        phone_endpoints = [ep for ep in endpoints if ep.channel == "phone"]
        
        if phone_endpoints:
            st.success(f"Connected to Spruce: {phone_endpoints[0].display_value}")
        else:
            st.error("No phone number configured in Spruce")
            return
        
    except Exception as e:
        st.error(f"Failed to connect to Spruce: {e}")
        return
    
    # SMS form
    with st.form("sms_form"):
        phone = st.text_input("Phone Number", placeholder="(205) 555-1234")
        message = st.text_area("Message", max_chars=1600)
        
        submitted = st.form_submit_button("Send SMS")
        
        if submitted:
            if not phone or not message:
                st.error("Phone number and message are required")
            else:
                try:
                    result = client.send_sms(phone, message)
                    st.success(f"SMS sent! Request ID: {result.get('requestId')}")
                except Exception as e:
                    st.error(f"Failed to send SMS: {e}")


def send_bulk_sms(patients: list, template: str, client: Optional[SpruceClient] = None):
    """
    Send SMS to multiple patients with rate limiting.
    
    Args:
        patients: List of dicts with 'phone' and 'name' keys
        template: Message template with {name} placeholder
        client: Optional SpruceClient instance
        
    Returns:
        Results dict with success/failure counts
    """
    import time
    
    if client is None:
        client = SpruceClient()
    
    results = {"sent": 0, "failed": 0, "errors": []}
    
    for i, patient in enumerate(patients):
        try:
            phone = patient.get("phone")
            name = patient.get("name", "Patient")
            
            if not phone:
                results["failed"] += 1
                results["errors"].append(f"{name}: No phone number")
                continue
            
            # Personalize message
            message = template.format(name=name, **patient)
            
            # Send with idempotency key
            idempotency_key = f"bulk_{patient.get('id', i)}_{int(time.time())}"
            client.send_sms(phone, message, idempotency_key=idempotency_key)
            
            results["sent"] += 1
            
            # Rate limiting: 100 requests/minute max
            if (i + 1) % 50 == 0:
                logger.info(f"Sent {i + 1} messages, pausing for rate limit...")
                time.sleep(30)  # 30 second pause every 50 messages
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{patient.get('name', 'Unknown')}: {str(e)}")
    
    return results
```

---

## Common 400 Error Causes and Solutions

### Error 1: Invalid Endpoint

**Error Message:**
```json
{
    "statusCode": 400,
    "type": "invalid_input",
    "message": "invalid input"
}
```

**Cause:** Using wrong API endpoint or missing `internalEndpointId`.

**Solution:** Use the correct endpoint structure:
```python
# Get endpoint ID first
endpoint_id = client.get_phone_endpoint_id()

# Then use in URL
url = f"/internalendpoints/{endpoint_id}/conversations"
```

---

### Error 2: Invalid Phone Number Format

**Error Message:**
```json
{
    "statusCode": 400,
    "type": "invalid_input",
    "message": "Invalid phone number"
}
```

**Cause:** Phone number not in E.164 format.

**Solution:** Always format phone numbers correctly:
```python
# WRONG
phone = "205-555-1234"
phone = "(205) 555-1234"

# CORRECT
phone = "+12055551234"
```

---

### Error 3: Missing Required Fields

**Error Message:**
```json
{
    "statusCode": 400,
    "type": "invalid_input", 
    "message": "destination is required"
}
```

**Cause:** Request body missing required structure.

**Solution:** Include proper `destination` object:
```python
# WRONG
payload = {
    "contact_id": "...",
    "body": "Message"
}

# CORRECT
payload = {
    "destination": {
        "smsOrEmailEndpoint": "+12055551234"
    },
    "text": "Message"
}
```

---

### Error 4: Invalid JSON Syntax

**Error Message:**
```json
{
    "statusCode": 400,
    "type": "invalid_input",
    "message": "Request body could not be read properly"
}
```

**Cause:** Malformed JSON in request body.

**Solution:** Ensure proper JSON encoding:
```python
# Use json parameter, not data
response = requests.post(url, json=payload)  # CORRECT
response = requests.post(url, data=payload)  # WRONG
```

---

### Error 5: Unregistered Account (Test Org)

**Error Message:**
```json
{
    "statusCode": 400,
    "type": "account_unregistered",
    "message": "Account is not registered for SMS"
}
```

**Cause:** Test organization or unregistered phone number.

**Solution:** This is expected for test accounts. Contact Team Spruce to:
1. Mark your test org as a test org (SMS won't deliver but API works)
2. Or enable API on your production org

---

### Error 6: Rate Limit Exceeded

**Response:**
```
HTTP 429 Too Many Requests
s-ratelimit-remaining: 0
```

**Cause:** Exceeded 100 requests/minute.

**Solution:** Implement rate limiting:
```python
import time

for i, patient in enumerate(patients):
    send_sms(...)
    
    # Pause every 50 messages
    if (i + 1) % 50 == 0:
        time.sleep(30)
```

---

## Environment Variables

```env
# Required
SPRUCE_API_TOKEN=your_bearer_token_here

# Optional (for logging/debugging)
SPRUCE_LOG_LEVEL=DEBUG
```

---

## Testing Checklist

### Before Sending Real Messages

- [ ] API token is valid (test with GET /contacts)
- [ ] Phone endpoint ID retrieved successfully
- [ ] Phone numbers are in E.164 format
- [ ] Request body structure matches documentation
- [ ] Idempotency keys are unique per message
- [ ] Rate limiting is implemented for bulk sends

### Test Sequence

```python
# 1. Verify authentication
client = SpruceClient()
contacts = client.get_contacts(limit=1)
print("Auth OK")

# 2. Get internal endpoints
endpoints = client.get_internal_endpoints()
print(f"Found {len(endpoints)} endpoints")

# 3. Find phone endpoint
phone_id = client.get_phone_endpoint_id()
print(f"Phone endpoint: {phone_id}")

# 4. Send test SMS (to yourself)
result = client.send_sms("+1YOUR_NUMBER", "Test from Patient Explorer")
print(f"Sent! Request ID: {result.get('requestId')}")
```

---

## Alternative: Using Existing Conversations

If you want to send to an existing conversation instead of creating new ones:

```python
def send_to_existing_conversation(conversation_id: str, message: str):
    """Post message to an existing Spruce conversation."""
    response = requests.post(
        f"{BASE_URL}/conversations/{conversation_id}/messages",
        json={"text": message},
        headers=headers
    )
    return response.json()
```

---

## References

- [Spruce API Overview](https://developer.sprucehealth.com/docs/overview)
- [Send Message from Internal Endpoint](https://developer.sprucehealth.com/reference/postmessagefromendpoint)
- [List Internal Endpoints](https://developer.sprucehealth.com/reference/internalendpoints)
- [Spruce Webhooks](https://developer.sprucehealth.com/docs/webhooks-overview)
- [Spruce API Help Article](https://help.sprucehealth.com/hc/en-us/articles/23003250146459-Spruce-API)

---

## Summary of Required Changes

| Component | Old (Broken) | New (Correct) |
|-----------|--------------|---------------|
| **Endpoint** | `/v1/messages` | `/v1/internalendpoints/{id}/conversations` |
| **Phone Format** | Various | E.164 (`+12055551234`) |
| **Body Structure** | `{"contact_id", "body"}` | `{"destination": {...}, "message": {"body": [{"type": "text", "value": "..."}]}}` |
| **Auth Header** | May have extra headers | Just `Authorization: Bearer <token>` |

---

*Document Version: 1.0*  
*Created: December 8, 2025*  
*Based on Spruce API Documentation as of December 2025*
