# Spruce Health API Research Report

**Date:** December 3, 2025
**Project:** Patient Explorer App
**Research Focus:** Comprehensive analysis of Spruce Health API capabilities

---

## Executive Summary

Spruce Health provides a REST API for managing patient contacts and conversations, with a focus on secure healthcare messaging. The API uses Bearer token authentication and supports pagination for large datasets. Key capabilities include contact management, conversation tracking, and SMS messaging - all under a Business Associate Agreement (BAA) for HIPAA compliance.

**Key Findings:**
- **Authentication:** Bearer token-based (simple, secure)
- **Rate Limiting:** Per-organization enforcement across 60-second and 24-hour windows
- **Pagination:** Variable-sized result sets with token-based navigation
- **Primary Use Cases:** Patient contact management, SMS outreach, conversation tracking
- **HIPAA Status:** ✅ BAA in place with Spruce Health

---

## Table of Contents

1. [API Overview](#1-api-overview)
2. [Authentication](#2-authentication)
3. [Available Endpoints](#3-available-endpoints)
4. [Contact Management](#4-contact-management)
5. [Messaging Capabilities](#5-messaging-capabilities)
6. [Rate Limits & Performance](#6-rate-limits--performance)
7. [Pagination](#7-pagination)
8. [Error Handling](#8-error-handling)
9. [Implementation in Patient Explorer](#9-implementation-in-patient-explorer)
10. [Limitations & Considerations](#10-limitations--considerations)
11. [Best Practices](#11-best-practices)

---

## 1. API Overview

### 1.1 Base Information

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.sprucehealth.com/v1` |
| **Protocol** | HTTPS (REST) |
| **Authentication** | Bearer Token |
| **Content Type** | `application/json` |
| **Documentation** | https://developer.sprucehealth.com/docs/overview |

### 1.2 Core Capabilities

The Spruce API enables:
- **Contact Management** - CRUD operations on patient contacts
- **Conversation Tracking** - Access to message history and threads
- **Call Recording Retrieval** - Access to call records (if applicable)
- **Search & Discovery** - Find contacts by name, phone, or email
- **Messaging** - Send SMS messages to patients

### 1.3 HIPAA Compliance

✅ **Spruce Health has a Business Associate Agreement (BAA) in place**

This makes Spruce a HIPAA-compliant service for:
- Patient contact information storage
- Healthcare-related text messaging
- Secure patient communication workflows

---

## 2. Authentication

### 2.1 Authentication Method

**Type:** Bearer Token Authentication

**Header Format:**
```http
Authorization: Bearer <your-token>
```

### 2.2 Token Acquisition

1. Request access through Spruce Support
2. Administrators generate API credentials in the Spruce web application
3. Navigate to: **API Access Settings** (in admin portal)
4. Generate new token (Base64-encoded)

### 2.3 Token Storage

**Security Best Practices:**
```env
# .env file (gitignored)
SPRUCE_API_TOKEN=your_base64_token_here
SPRUCE_ACCESS_ID=your_access_id  # If applicable
```

**Implementation:**
```python
import os
import httpx

class SpruceClient:
    BASE_URL = "https://api.sprucehealth.com/v1"

    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv("SPRUCE_API_TOKEN")
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
```

### 2.4 Authentication Errors

| Status Code | Meaning | Action |
|-------------|---------|--------|
| **401** | Unauthorized - Invalid token | Verify token is correct |
| **403** | Forbidden - Token disabled | Check token status in admin portal |

---

## 3. Available Endpoints

### 3.1 Contact Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/contacts` | List all contacts (paginated) |
| `GET` | `/contacts/{id}` | Get single contact details |
| `POST` | `/contacts/search` | Search contacts by query |
| `POST` | `/contacts` | Create new contact |
| `PATCH` | `/contacts/{id}` | Update contact |
| `DELETE` | `/contacts/{id}` | Delete contact |

### 3.2 Conversation Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/contacts/{id}/conversations` | Get conversations for a contact |
| `GET` | `/conversations/{id}` | Get conversation details |

### 3.3 Messaging Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/messages` | Send SMS or message |
| `GET` | `/messages/{id}` | Get message status |

### 3.4 Call Recording Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/calls` | List call recordings |
| `GET` | `/calls/{id}` | Get call recording details |

---

## 4. Contact Management

### 4.1 List All Contacts

**Request:**
```http
GET /v1/contacts?limit=100
Authorization: Bearer {token}
```

**Response:**
```json
{
  "contacts": [
    {
      "id": "cnt_abc123",
      "displayName": "John Doe",
      "firstName": "John",
      "lastName": "Doe",
      "phoneNumbers": [
        {
          "value": "+12055551234",
          "displayValue": "(205) 555-1234"
        }
      ],
      "emailAddresses": [
        {
          "address": "john.doe@example.com"
        }
      ],
      "dateOfBirth": "1970-01-15",
      "createdAt": "2024-06-01T10:30:00Z"
    }
  ],
  "hasMore": true,
  "paginationToken": "next_page_token_here"
}
```

### 4.2 Search Contacts

**Request:**
```http
POST /v1/contacts/search
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "John Doe"
}
```

**Response:**
```json
{
  "contacts": [
    {
      "id": "cnt_abc123",
      "displayName": "John Doe",
      "phone": "+12055551234"
    }
  ]
}
```

### 4.3 Contact Data Structure

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Spruce contact ID (unique) |
| `displayName` | String | Full name (primary display) |
| `firstName` | String | Given name |
| `lastName` | String | Family name |
| `phoneNumbers` | Array | Phone numbers (multiple supported) |
| `emailAddresses` | Array | Email addresses (multiple supported) |
| `dateOfBirth` | String | DOB in ISO format (YYYY-MM-DD) |
| `createdAt` | String | Account creation timestamp |

### 4.4 Matching Strategy

**Patient Explorer Implementation:**

1. **Phone Matching (Primary)**
   - Normalize phone numbers (digits only, remove country code)
   - Search Spruce by phone number
   - Exact match required

2. **Name Matching (Secondary)**
   - Combine first + last name
   - Search by full name
   - Manual confirmation if multiple matches

3. **Email Matching (Tertiary)**
   - Search by email address
   - Least reliable (patients often don't have email in Spruce)

```python
def match_patient_to_spruce(patient: Patient, spruce_contacts: List[SpruceContact]) -> Optional[str]:
    """Match patient to Spruce contact ID."""

    # Try phone match first
    if patient.phone:
        normalized_phone = normalize_phone(patient.phone)
        for contact in spruce_contacts:
            if contact.phone and normalize_phone(contact.phone) == normalized_phone:
                return contact.spruce_id

    # Try name match
    for contact in spruce_contacts:
        if (contact.first_name and contact.last_name and
            contact.first_name.lower() == patient.first_name.lower() and
            contact.last_name.lower() == patient.last_name.lower()):
            return contact.spruce_id

    return None  # No match
```

---

## 5. Messaging Capabilities

### 5.1 Send SMS Message

**Request:**
```http
POST /v1/messages
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "sms",
  "to": "+12055551234",
  "body": "Hi John, this is Dr. Green's office. Please complete your consent form: https://forms.office.com/...",
  "contactId": "cnt_abc123"
}
```

**Response:**
```json
{
  "id": "msg_xyz789",
  "status": "sent",
  "sentAt": "2025-12-03T14:30:00Z",
  "contactId": "cnt_abc123"
}
```

### 5.2 Message Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `type` | Yes | Message type (`sms`, `mms`) |
| `to` | Yes | Phone number (E.164 format: +1XXXXXXXXXX) |
| `body` | Yes | Message text (max length varies by carrier) |
| `contactId` | No | Spruce contact ID (for threading) |

### 5.3 SMS Best Practices

**Character Limits:**
- Single SMS: 160 characters
- Multi-part SMS: Up to 1,600 characters (carrier-dependent)
- Include opt-out language: "Reply STOP to opt out"

**Timing:**
- Respect patient time zones
- Avoid late-night sends (after 9 PM)
- Weekend sends acceptable for urgent matters

**Compliance:**
- All messages covered under Spruce BAA
- No PHI in message body (use tokenized links)
- Log all sends for audit trail

### 5.4 Message Status Tracking

**Status Values:**

| Status | Meaning |
|--------|---------|
| `sent` | Message successfully sent to carrier |
| `delivered` | Message delivered to recipient |
| `failed` | Message failed to send |
| `undeliverable` | Phone number invalid or unreachable |

---

## 6. Rate Limits & Performance

### 6.1 Rate Limit Structure

**Enforcement Level:** Per-organization (not per-credential)

**Windows:**
- **60-second window** - Short-term burst protection
- **24-hour window** - Daily quota enforcement

**Response Headers:**
```http
s-ratelimit-limit: 100          # Requests allowed per minute
s-ratelimit-remaining: 87       # Requests remaining this minute
s-ratelimit-daily-limit: 10000  # Requests allowed per day
s-ratelimit-daily-remaining: 9542  # Requests remaining today
```

### 6.2 Rate Limit Handling

**Status Code:** `429 Too Many Requests`

**Response:**
```json
{
  "statusCode": 429,
  "type": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Retry after 60 seconds."
}
```

**Implementation:**
```python
import asyncio
import httpx

async def send_with_rate_limit(messages: List[dict], batch_size=50, delay=1.0):
    """Send messages in batches with rate limiting."""
    results = []

    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]

        for msg in batch:
            try:
                response = await send_message(msg)
                results.append({"success": True, "data": response})
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited - wait and retry
                    await asyncio.sleep(60)
                    response = await send_message(msg)
                    results.append({"success": True, "data": response})
                else:
                    results.append({"success": False, "error": str(e)})

        # Delay between batches
        if i + batch_size < len(messages):
            await asyncio.sleep(delay)

    return results
```

### 6.3 Performance Considerations

**Batch Size Recommendations:**
- **Small campaigns (<100 messages):** Send all at once
- **Medium campaigns (100-500):** Batch in groups of 50
- **Large campaigns (500+):** Batch in groups of 100 with 2-second delays

**Expected Latency:**
- Contact list fetch: ~1-3 seconds for 1,000 contacts
- Single SMS send: ~200-500ms
- Batch SMS send (50): ~10-15 seconds

---

## 7. Pagination

### 7.1 Pagination Mechanism

**Type:** Token-based pagination (not offset-based)

**Request Parameters:**
```http
GET /v1/contacts?limit=100&paginationToken=abc123xyz
```

| Parameter | Description |
|-----------|-------------|
| `limit` | Number of results per page (max usually 100) |
| `paginationToken` | Token from previous response |

**Response Structure:**
```json
{
  "contacts": [...],
  "hasMore": true,
  "paginationToken": "next_token_here"
}
```

### 7.2 Fetching All Pages

```python
def get_all_contacts(client: SpruceClient) -> List[dict]:
    """Fetch all contacts using pagination."""
    all_contacts = []
    pagination_token = None

    while True:
        params = {"limit": 100}
        if pagination_token:
            params["paginationToken"] = pagination_token

        response = client.get("/contacts", params=params)
        data = response.json()

        all_contacts.extend(data.get("contacts", []))

        if not data.get("hasMore"):
            break

        pagination_token = data.get("paginationToken")

    return all_contacts
```

---

## 8. Error Handling

### 8.1 HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| `200` | Success | Process response |
| `401` | Unauthorized | Check API token |
| `403` | Forbidden | Token may be disabled |
| `404` | Not Found | Resource doesn't exist |
| `422` | Unprocessable Entity | Invalid request data or duplicate idempotency key |
| `429` | Rate Limit | Wait and retry |
| `500` | Server Error | Retry with backoff |

### 8.2 Error Response Format

```json
{
  "statusCode": 422,
  "type": "validation_error",
  "message": "Phone number is invalid"
}
```

### 8.3 Implementation

```python
def handle_spruce_response(response: httpx.Response) -> dict:
    """Handle Spruce API responses with error checking."""

    if response.status_code == 403:
        raise PermissionError("Spruce API token is invalid or disabled")

    elif response.status_code == 401:
        raise PermissionError("Spruce API authentication failed")

    elif response.status_code == 429:
        raise RuntimeError("Spruce API rate limit exceeded. Retry after 60s")

    elif response.status_code >= 400:
        try:
            error_data = response.json()
            message = error_data.get("message", response.text)
        except:
            message = response.text
        raise RuntimeError(f"Spruce API error {response.status_code}: {message}")

    return response.json()
```

---

## 9. Implementation in Patient Explorer

### 9.1 Current Implementation

**Location:** `phase0/spruce/client.py`

**Features:**
- Contact fetching with pagination
- Phone-based patient matching
- Name-based search
- SMS sending
- Bulk SMS with rate limiting
- Connection testing

### 9.2 SpruceClient Class

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `test_connection()` | Verify API connectivity |
| `get_contacts(limit=100)` | Fetch all contacts (paginated) |
| `search_contacts(query)` | Search by name/phone/email |
| `find_contact_by_phone(phone)` | Exact phone match |
| `find_contact_by_name(first, last)` | Name-based search |
| `get_contact_conversations(id)` | Fetch conversation history |
| `send_sms(phone, message, contact_id)` | Send SMS message |
| `send_bulk_sms(recipients, template)` | Bulk SMS with personalization |

### 9.3 Integration Points

**Patient Matching Workflow:**
```
1. Load patients from Excel → Patient records in database
2. Fetch all Spruce contacts → SpruceContact list
3. Match patients to contacts → Update patient.spruce_id
4. Store match method → phone, name, email
5. Track match status → spruce_matched = True/False
```

**SMS Outreach Workflow:**
```
1. Generate consent tokens → Unique URL per patient
2. Select patients with spruce_id → Matched patients only
3. Render SMS template → Personalized message with token URL
4. Send via Spruce API → Batch with rate limiting
5. Update consent status → invitation_sent
6. Log outreach date → Track campaign progress
```

### 9.4 Configuration

**Environment Variables:**
```env
SPRUCE_API_TOKEN=your_base64_encoded_token_here
```

**Optional Settings:**
```env
SPRUCE_BATCH_SIZE=50          # Messages per batch
SPRUCE_BATCH_DELAY=1.0        # Seconds between batches
SPRUCE_MAX_RETRIES=3          # Retry attempts on failure
```

---

## 10. Limitations & Considerations

### 10.1 API Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Rate limits** | Can't send 1,000 SMS instantly | Batch sending with delays |
| **Phone format** | Requires E.164 format | Normalize phone numbers |
| **Contact updates** | No bulk update endpoint | Update contacts individually |
| **Search precision** | Text search may return false positives | Verify matches manually |
| **Message length** | SMS character limits | Keep messages concise |

### 10.2 Data Considerations

**Phone Numbers:**
- Spruce expects E.164 format: `+1XXXXXXXXXX`
- Patient data may have various formats: `(205) 555-1234`, `205-555-1234`, etc.
- Normalization required before matching

**Name Matching:**
- Spruce uses `displayName` as primary field
- `firstName` and `lastName` may not always be populated
- Consider nickname variations (e.g., "Bob" vs "Robert")

**Date of Birth:**
- Useful for matching but not always available in Spruce
- ISO format: `YYYY-MM-DD`

### 10.3 Missing Features

**Not currently documented or available:**
- **Webhooks** - No real-time push notifications for incoming messages
- **MMS attachments** - Limited documentation on sending images
- **Message templates** - No server-side template storage
- **Group messaging** - Must send individual messages
- **Message scheduling** - No built-in scheduling (must implement client-side)

### 10.4 HIPAA Considerations

**PHI in Messages:**
- ✅ **DO:** Send tokenized consent links (token is not PHI)
- ✅ **DO:** Use first name only in messages
- ❌ **DON'T:** Include MRN, DOB, or diagnosis in SMS
- ❌ **DON'T:** Include detailed medical information

**Example - Compliant Message:**
```
Hi John, this is Dr. Green's office. Please complete your
consent form: https://forms.office.com/?token=abc123

Questions? Call 205-955-7605.
```

**Example - Non-Compliant Message:**
```
Hi John (MRN: 12345, DOB: 1/15/1970), your diabetes medication
refill is ready. Please confirm.
```

---

## 11. Best Practices

### 11.1 Development Best Practices

**Connection Management:**
```python
# Use context manager for automatic cleanup
with SpruceClient() as client:
    contacts = client.get_contacts()
    # Client automatically closed
```

**Error Handling:**
```python
try:
    result = client.send_sms(phone, message)
    if result["success"]:
        log_success(result)
    else:
        log_failure(result)
except Exception as e:
    log_error(e)
    # Don't stop entire campaign on single failure
```

**Logging:**
```python
# Log aggregate stats, not individual PHI
logger.info(f"Matched {matched_count} of {total_count} patients to Spruce")
logger.info(f"Sent SMS to {sent_count} patients")

# Don't log:
logger.info(f"Matched John Doe (205-555-1234) to cnt_abc123")  # ❌ PHI
```

### 11.2 Testing Best Practices

**Test Environment:**
- Use test API credentials if Spruce provides them
- Test with small batches (5-10 patients) first
- Verify messages on test phone numbers before production

**Validation:**
```python
def validate_before_send(patients: List[Patient]) -> List[str]:
    """Validate patient data before SMS campaign."""
    errors = []

    for patient in patients:
        if not patient.spruce_id:
            errors.append(f"{patient.mrn}: No Spruce match")
        if not patient.phone:
            errors.append(f"{patient.mrn}: No phone number")
        if not patient.consent_token:
            errors.append(f"{patient.mrn}: No consent token")

    return errors
```

### 11.3 Production Best Practices

**Rate Limiting:**
- Start with conservative batch sizes (50 messages)
- Monitor rate limit headers in responses
- Implement exponential backoff for retries

**Monitoring:**
- Track send success rate (target: >95%)
- Monitor delivery status (if available via webhooks/polling)
- Alert on repeated failures

**Audit Trail:**
- Log every SMS send with timestamp
- Record message content (template used, not personalized content)
- Track patient response (form submission)

**Campaign Management:**
- Send in phases (Day 1: 500 patients, Day 2: 500 patients, etc.)
- Schedule reminders (Day 3, Day 7, Day 14)
- Stop sending to patients who respond or opt out

---

## 12. Integration Patterns

### 12.1 Patient Matching Pattern

```python
async def match_all_patients():
    """Match all patients to Spruce contacts."""

    # Fetch all contacts once (cache locally)
    spruce_contacts = await spruce_client.get_contacts()

    # Load patients from database
    patients = db.query(Patient).all()

    # Match each patient
    matched = 0
    for patient in patients:
        spruce_id = match_patient_to_spruce(patient, spruce_contacts)

        if spruce_id:
            patient.spruce_id = spruce_id
            patient.spruce_matched = True
            patient.spruce_match_method = "phone"  # or "name"
            matched += 1
        else:
            patient.spruce_matched = False

    db.commit()

    return {"total": len(patients), "matched": matched}
```

### 12.2 SMS Campaign Pattern

```python
async def send_consent_campaign():
    """Send consent SMS to all matched patients."""

    # Get patients with Spruce match and no consent
    patients = db.query(Patient).filter(
        Patient.spruce_matched == True,
        Patient.consent_status == ConsentStatus.PENDING
    ).all()

    # Batch send with rate limiting
    results = await send_sms_batch(
        patients=patients,
        template_name="consent_initial",
        batch_size=50,
        delay=2.0
    )

    # Update statuses
    for result in results:
        if result["success"]:
            patient = result["patient"]
            patient.consent_status = ConsentStatus.INVITATION_SENT
            patient.last_outreach_date = datetime.now()

    db.commit()

    return results
```

### 12.3 Follow-Up Reminder Pattern

```python
def schedule_followup_reminders():
    """Queue follow-up reminders for non-responders."""

    # Find patients with invitations sent 3+ days ago
    three_days_ago = datetime.now() - timedelta(days=3)

    patients = db.query(Patient).filter(
        Patient.consent_status == ConsentStatus.INVITATION_SENT,
        Patient.last_outreach_date <= three_days_ago
    ).all()

    # Send reminder
    for patient in patients:
        result = spruce_client.send_sms(
            phone_number=patient.phone,
            message=render_template("day_3_reminder", patient),
            contact_id=patient.spruce_id
        )

        if result["success"]:
            patient.outreach_attempts += 1
            patient.last_outreach_date = datetime.now()

    db.commit()
```

---

## 13. Future Enhancements

### 13.1 Potential Features

**Webhooks (If Available):**
- Real-time notification of patient replies
- Automatic consent status updates
- Delivery confirmations

**Two-Way Messaging:**
- Capture patient questions
- Route to staff for response
- Track conversation threads

**Analytics Dashboard:**
- Campaign performance metrics
- Response rate by cohort
- Optimal send times

### 13.2 Integration with Microsoft Forms

**Current Flow:**
```
SMS with token link → Microsoft Form → Manual CSV import → Patient Explorer
```

**Enhanced Flow:**
```
SMS with token link → Microsoft Form → Graph API → Auto-import → Patient Explorer
```

**Implementation:**
- Poll Microsoft Forms API for new responses
- Match responses by consent token
- Auto-update consent status in database

---

## 14. Conclusion

### 14.1 Summary

Spruce Health API provides a robust, HIPAA-compliant platform for patient contact management and SMS outreach. The API is well-suited for the Patient Explorer consent campaign with:

- ✅ Simple authentication (Bearer token)
- ✅ Comprehensive contact management
- ✅ SMS messaging with threading
- ✅ Rate limiting headers for safe batching
- ✅ Pagination for large datasets
- ✅ BAA coverage for HIPAA compliance

### 14.2 Key Takeaways

1. **Phone matching is most reliable** - Use normalized phone numbers for patient matching
2. **Batch SMS carefully** - Respect rate limits with 50-message batches and 1-2 second delays
3. **Log aggregate stats only** - Never log PHI in application logs
4. **Use tokenized links** - Keep PHI out of SMS message bodies
5. **Test before production** - Validate with small cohorts first

### 14.3 Implementation Status in Patient Explorer

| Feature | Status | Notes |
|---------|--------|-------|
| Contact fetching | ✅ Complete | `SpruceClient.get_contacts()` |
| Patient matching | ✅ Complete | Phone and name-based matching |
| SMS sending | ✅ Complete | Single and bulk SMS |
| Rate limiting | ✅ Complete | Batch with delays |
| Error handling | ✅ Complete | Comprehensive error checking |
| Conversation tracking | ⚠️ Partial | Can fetch, not actively used |
| Webhooks | ❌ Not Available | No real-time push notifications |

---

## 15. References

### 15.1 Documentation

- **Spruce Developer Portal:** https://developer.sprucehealth.com/docs/overview
- **Spruce Help Center:** https://help.sprucehealth.com/hc/en-us

### 15.2 Patient Explorer Implementation

- **SpruceClient:** `phase0/spruce/client.py`
- **Data Models:** `phase0/models.py` (SpruceContact)
- **CLI Commands:** `phase0/main.py` (test-spruce, match-spruce)
- **App Integration:** `app/pages/4_Outreach_Campaign.py`

### 15.3 Related Research

- **Microsoft OAuth Integration:** `docs/stories/S5-microsoft-oauth-integration.md`
- **Consent Form Setup:** `docs/stories/S7-consent-form-setup.md`
- **SMS Outreach Campaign:** `docs/stories/S8-sms-outreach-campaign.md`

---

*Generated by Patient Explorer App Agent*
*December 3, 2025*
