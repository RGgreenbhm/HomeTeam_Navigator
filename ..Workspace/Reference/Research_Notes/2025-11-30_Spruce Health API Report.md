# Spruce Health API

*Developer Documentation Review & Workflow Proposals*

---

## Executive Summary

The Spruce Health API provides a comprehensive RESTful interface for managing patient contacts, conversations, and communications within your healthcare organization. This report summarizes the available data endpoints and proposes workflow automations to enhance patient care coordination across your team.

---

## 1. API Overview

### Authentication & Access

The Spruce API uses Bearer token authentication. API access requires the Communicator plan and must be enabled by Spruce Support. After activation, administrators can generate and manage API credentials from Settings > Integrations & API in the web application.

### Rate Limits

Rate limits are enforced per organization (not per credential) with both per-minute and daily limits. Response headers include `s-ratelimit-limit`, `s-ratelimit-remaining`, `s-ratelimit-daily-limit`, and `s-ratelimit-daily-remaining` to monitor usage.

---

## 2. Data Available from Spruce Health API

### 2.1 Contact Management

The API provides full CRUD operations for patient and contact records:

| Endpoint | Description |
|----------|-------------|
| **GET /contacts** | List all contacts with pagination support |
| **POST /contacts** | Create new contact (requires name, phone, fax, or email) |
| **PATCH /contacts/{id}** | Update existing contact information |
| **POST /contacts/search** | Search contacts with complex filters |

**Contact Data Fields Available:**

- Personal information: givenName, familyName, displayName, gender
- Contact details: phoneNumbers (with labels), emailAddresses, faxNumbers
- Organization data: category (patient/other), tags, customContactFields
- Status indicators: hasAccount, hasPendingInvite, canEdit, canDelete
- Integration links: integrationLinks for EHR connections

### 2.2 Conversation Management

Full access to conversation threads across all channels:

| Endpoint | Description |
|----------|-------------|
| **GET /conversations** | List all conversations with orderBy options (created/last_message) |
| **GET /conversations/{id}** | Retrieve specific conversation details |
| **PATCH /conversations/{id}** | Update conversation properties (tags, archived status) |
| **GET /conversationItems** | List messages within a conversation with direction tracking |

**Conversation Data Fields:**

- Type: secure, phone (SMS), email, fax
- Participants: externalParticipants (patients), internalMemberIds (team)
- Timestamps: createdAt, lastMessageAt
- Status: archived, isReadOnly, tags
- Message items: text, attachments, author, direction (inbound/outbound), isInternalNote

### 2.3 Messaging Capabilities

Send messages across multiple channels from a unified API:

| Endpoint | Description |
|----------|-------------|
| **POST /messages** | Send SMS, secure message, email, or fax from internal endpoint |
| **POST /conversations/{id}/messages** | Post message to existing conversation (including internal notes) |
| **POST /scheduled-messages** | Schedule messages for future delivery |
| **POST /media** | Upload images, videos, and files for message attachments |

### 2.4 Organization Resources

- **Internal Endpoints:** Phone numbers, fax numbers, email addresses, and Spruce Links
- **Phone Lines:** List all organization phone lines
- **Organization Members:** Access team member IDs for paging and assignments
- **Contact Tags:** List, create, and manage tags for organizing contacts
- **Conversation Tags:** List and manage tags for categorizing conversations

### 2.5 Webhooks (Real-Time Events)

Subscribe to real-time notifications for changes in your organization:

| Event Type | Trigger |
|------------|---------|
| contact.created/updated/deleted | When patient records are added or modified |
| conversation.created/updated/deleted | When conversations are started or changed |
| conversationItem.created/updated | When new messages are sent or received |

---

## 3. Proposed Patient Care Workflow Automations

### 3.1 Automated Appointment Reminders

**Use Case:** Reduce no-shows by sending automated reminders via SMS or secure message.

**Implementation:**

1. Connect your scheduling system to trigger API calls when appointments are booked
2. Use POST /scheduled-messages to schedule reminders 24-48 hours before appointment
3. Use POST /messages to send day-of confirmations
4. Tag contacts with appointment-related tags for tracking

**Team Benefit:** Frees front desk staff from manual reminder calls; standardizes patient communication.

### 3.2 EHR-Spruce Contact Synchronization

**Use Case:** Keep patient demographics synchronized between your EHR and Spruce.

**Implementation:**

1. Set up webhook endpoint to receive contact.created events
2. When patients are added in EHR, use POST /contacts to create Spruce contact
3. Use PATCH /contacts/{id} to update when EHR records change
4. Apply tags from EHR (provider, status, plan) to Spruce contacts

**Team Benefit:** Eliminates duplicate data entry; ensures all team members have current patient information.

### 3.3 New Patient Onboarding Automation

**Use Case:** Streamline the onboarding process for new patients joining your practice.

**Implementation:**

1. Use POST /contacts to create patient record with all demographics
2. Trigger welcome sequence via POST /messages with secure messaging
3. Schedule follow-up touchpoints using scheduled messages
4. Apply 'New Patient' tag for team visibility and tracking

**Team Benefit:** Consistent onboarding experience; automatic task distribution across team members.

### 3.4 Care Follow-Up & Check-In System

**Use Case:** Proactively reach out to patients post-visit or post-procedure.

**Implementation:**

1. After visit completion in EHR, trigger scheduled follow-up messages
2. Use webhooks to monitor patient responses (conversationItem.created)
3. Auto-tag conversations needing clinical review vs. administrative response
4. Route urgent responses to appropriate team members

**Team Benefit:** Improves patient outcomes through proactive care; reduces manual follow-up tracking.

### 3.5 Conversation Documentation to EHR

**Use Case:** Automatically sync important patient communications to their medical record.

**Implementation:**

1. Subscribe to conversationItem.created webhook events
2. Filter for clinical-relevant conversations using tags or keywords
3. Use GET /conversations/{id} to retrieve full context
4. Push formatted conversation summary to EHR via your EHR's API

**Team Benefit:** Complete patient record without manual documentation; supports care continuity.

---

## 4. Implementation Considerations

### Prerequisites

- Spruce Communicator plan subscription
- API access enabled by Spruce Support
- Development/engineering resources (or use Keragon/Morf Health for no-code)
- Test organization for development and testing

### No-Code Alternatives

If you lack development resources, Spruce recommends integration partners:

- **Keragon:** HIPAA-compliant automation platform with visual workflow builder
- **Morf Health:** Healthcare-focused integration solution

### Security & Compliance

- All API communications are HIPAA-compliant
- Webhooks use SHA256 signature verification
- Store API credentials securely; rotate as needed
- Webhook endpoints must support HTTPS

---

## 5. Recommended Next Steps

1. **Request API Access:** Contact Spruce Support via your app to enable API for your organization
2. **Create Test Environment:** Set up a separate test organization for development
3. **Prioritize Workflows:** Select 1-2 high-impact automations to implement first
4. **Define Success Metrics:** Establish KPIs for each workflow (e.g., no-show rate reduction)
5. **Plan Rollout:** Train team members on new automated workflows

---

*For complete API documentation, visit: [developer.sprucehealth.com](https://developer.sprucehealth.com)*
