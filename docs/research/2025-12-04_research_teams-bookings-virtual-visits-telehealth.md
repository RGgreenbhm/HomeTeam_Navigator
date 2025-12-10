# Research Report: Microsoft Teams Bookings & Virtual Visits for Telehealth

**Date:** 2025-12-04
**Researcher:** Claude (AI Assistant)
**Requested By:** User configuring telehealth scheduling with autopilot@southviewteam.com as admin account

---

## Executive Summary

For HIPAA-compliant telehealth visits, **Microsoft Bookings** is the recommended approach over regular Teams meetings. Bookings provides patient-friendly scheduling (no Teams download required), centralized admin control, and—critically—creates calendar-backed meetings that support transcript retrieval via Graph API.

The key insight for your setup: **autopilot@southviewteam.com can serve as a central administrator** who manages all provider schedules and booking pages without being a bookable provider themselves. This enables centralized workflow automation while keeping providers in control of their actual patient visits.

This report covers the complete setup process, from enabling Bookings to configuring transcript access via the Application Access Policy you may have missed.

---

## Background

You need to:
1. Schedule telehealth visits for patients with providers
2. Use autopilot@southviewteam.com as a central admin account
3. Enable transcript retrieval for documentation
4. Maintain HIPAA compliance throughout

---

## Key Findings

### Finding 1: Bookings is Better Than Regular Meetings for Patient Visits

| Feature | Regular Meeting | Bookings | Virtual Appointments (Premium) |
|---------|-----------------|----------|-------------------------------|
| **Best for** | Provider-to-provider | Provider-to-patient | Advanced patient scheduling |
| **Patient needs Teams?** | May be prompted to download | No (browser) | No (browser) |
| **Sender email** | Shows provider's personal email | Organization email | Organization email |
| **Multi-provider scheduling** | No | ✅ Yes | ✅ Yes |
| **SMS reminders** | No | Basic | ✅ Advanced |
| **Queue view** | No | No | ✅ Yes |
| **Analytics** | No | Limited | ✅ Comprehensive |
| **Transcript access via API** | ✅ Yes | ✅ Yes | ✅ Yes |

**Why Bookings wins for telehealth:**

1. **Patient privacy**: Invites come from organization email (e.g., `GreenClinicTelehealth@southviewteam.com`), not provider's personal email
2. **No Teams download**: Patients join via browser with one click—critical for elderly or less tech-savvy patients
3. **Centralized scheduling**: Admin (autopilot) can see all providers' availability in one view
4. **Custom templates**: Create appointment types (15-min follow-up, 30-min new patient, etc.)
5. **Calendar-backed meetings**: Transcripts ARE accessible via Graph API

Source: [Setting Up Bookings for Virtual Visits](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/setting-up-bookings-for-virtual-visits/1265216)

### Finding 2: HIPAA Compliance for Teams Telehealth

Microsoft Teams is HIPAA-compliant when properly configured, but it's not compliant out of the box.

**Requirements:**

| Requirement | Status | Notes |
|-------------|--------|-------|
| BAA in place | ✅ Automatic | Included in Microsoft 365 DPA |
| Enterprise license | ✅ Required | E3/E5 for full compliance features |
| Encryption in transit | ✅ Default | TLS 1.2+ |
| Encryption at rest | ✅ Default | Microsoft-managed keys |
| MFA enabled | ⚠️ Configure | Required for admin accounts |
| Audit logging | ⚠️ Configure | Enable in Compliance Center |
| Recording consent | ⚠️ Configure | Enable explicit consent banner |

**Important:** The base version of Microsoft Teams is NOT HIPAA-compliant. You need Microsoft 365 Business Premium, E3, or E5.

Source: [Microsoft Teams HIPAA Compliance 2025](https://www.hipaajournal.com/microsoft-teams-hipaa-compliant/)

### Finding 3: Transcript Access Requires Application Access Policy

**This is the PowerShell step you likely missed.**

For application-level transcript access (background automation), you need to configure an Application Access Policy via Teams PowerShell. Without it, you'll get:

> "Application is not allowed to perform operations on the user"

**The fix:**

```powershell
# Install module
Install-Module -Name MicrosoftTeams -Force -AllowClobber

# Connect (sign in as autopilot@southviewteam.com)
Connect-MicrosoftTeams

# Create policy with your app's Client ID
New-CsApplicationAccessPolicy `
    -Identity "Transcript-MCP-Policy" `
    -AppIds "<your-client-id>" `
    -Description "Allow transcript access for telehealth documentation"

# Grant tenant-wide
Grant-CsApplicationAccessPolicy -PolicyName "Transcript-MCP-Policy" -Global

# Wait 30 minutes for propagation!
```

Source: [Configure Application Access Policy](https://learn.microsoft.com/en-us/graph/cloud-communication-online-meeting-application-access-policy)

### Finding 4: Meeting Organizer = Provider (Not autopilot)

In Bookings, the **provider assigned to the appointment** is the meeting organizer. This matters for transcript retrieval.

**Correct API call:**
```http
GET /users/drsmith@southviewteam.com/onlineMeetings/{id}/transcripts  ✅
```

**Incorrect API call:**
```http
GET /users/autopilot@southviewteam.com/onlineMeetings/{id}/transcripts  ❌
```

The Application Access Policy must be granted to the providers (or tenant-wide) for transcript access to work.

---

## Step-by-Step Setup Guide

### Step 1: Enable Bookings for Your Organization

1. Go to **Microsoft 365 Admin Center** → **Settings** → **Org settings**
2. Search for **Bookings**
3. Configure:
   ```
   ✅ Allow your organization to use Bookings
   ✅ Allow Microsoft to send SMS text notifications
   ✅ Require staff approvals before adding them to booking pages (optional)
   ```
4. Click **Save**

### Step 2: Create a Booking Page

1. Open **Teams** (or go to outlook.office.com/bookings)
2. Go to **Apps** → Search for **Bookings**
3. Click **Get started** or **Create a booking page**
4. Configure:
   ```
   Business name: Green Clinic Telehealth
   Business type: Healthcare
   Business address: [Your clinic address]
   Business phone: [Your phone]
   ```
5. Click **Save**

### Step 3: Add autopilot as Administrator

This allows autopilot to manage schedules without being a bookable provider.

**Option A: Via Bookings UI**
1. Open the Booking page in Teams
2. Go to **Staff** → **Add new staff**
3. Search for `autopilot@southviewteam.com`
4. Set role to **Administrator**
5. **Uncheck** "Events on Outlook calendar affect availability"
6. Click **Save**

**Option B: Via PowerShell (for admin-only access without appearing in staff list)**
```powershell
# Connect to Exchange Online
Connect-ExchangeOnline

# Find the Bookings mailbox
Get-Mailbox -RecipientTypeDetails SchedulingMailbox

# Grant autopilot full access (admin without being bookable)
Add-MailboxPermission -Identity "GreenClinicTelehealth@southviewteam.com" `
    -User "autopilot@southviewteam.com" `
    -AccessRights FullAccess `
    -AutoMapping:$false

Add-RecipientPermission -Identity "GreenClinicTelehealth@southviewteam.com" `
    -Trustee "autopilot@southviewteam.com" `
    -AccessRights SendAs `
    -Confirm:$false
```

Source: [Bookings Shared Mailbox Setup](https://office365itpros.com/2022/07/22/microsoft-bookings-app/)

### Step 4: Add Providers as Staff

1. Go to **Staff** → **Add new staff**
2. Search for each provider (e.g., `drsmith@southviewteam.com`)
3. Configure:
   ```
   Role: Team member (or Administrator if they manage own schedule)
   ✅ Events on Outlook calendar affect availability
   ✅ Use business hours (or set custom hours per provider)
   ```
4. Click **Save**
5. Provider receives email to approve membership (if staff approvals enabled)

Repeat for each provider.

### Step 5: Create Service Types (Appointment Templates)

Go to **Services** → **Add a service**

**Example: New Patient Telehealth Visit**
```
Service name: New Patient Telehealth Visit
Description: Initial telehealth consultation for new patients
Duration: 30 minutes
Buffer time before: 5 minutes
Buffer time after: 5 minutes
Default price: [Your fee or leave blank]
Maximum attendees: 1

Online meetings:
✅ Add online meeting (this creates Teams meeting)

Assign staff: [Select which providers offer this service]

Custom fields (optional):
  - Reason for visit (required, text)
  - Insurance provider (optional, dropdown)
  - Preferred pharmacy (optional, text)
  - Current medications (optional, text area)
```

**Example: Follow-up Visit**
```
Service name: Follow-up Telehealth Visit
Duration: 15 minutes
Buffer time: 5 minutes
✅ Add online meeting
```

**Example: Medication Review**
```
Service name: Medication Review
Duration: 10 minutes
Buffer time: 5 minutes
✅ Add online meeting
```

### Step 6: Configure Booking Page Settings

Go to **Booking page** settings:

```
General:
  ✅ Allow online booking
  ✅ Require email verification for customers
  ✅ Send meeting invite to customer

Scheduling:
  Time zone: Pacific Standard Time (or your local)
  Minimum lead time: 1 hour (prevent last-minute bookings)
  Maximum lead time: 60 days
  Time slot increments: 15 minutes

Notifications:
  ✅ Email notifications: On
  ✅ SMS notifications: On (if enabled tenant-wide)
  ✅ Send reminders: 24 hours before

Privacy:
  ✅ Show staff names on booking page
  ✅ Allow customers to choose a specific staff member
```

### Step 7: Configure Application Access Policy for Transcripts

```powershell
# ============================================
# STEP 1: Install Required Module
# ============================================
Install-Module -Name MicrosoftTeams -Force -AllowClobber

# ============================================
# STEP 2: Connect to Teams
# ============================================
Connect-MicrosoftTeams
# Sign in with autopilot@southviewteam.com (or admin account)

# ============================================
# STEP 3: Create the Policy
# ============================================
# Replace <your-client-id> with your Entra ID app registration Client ID
New-CsApplicationAccessPolicy `
    -Identity "Telehealth-Transcript-Policy" `
    -AppIds "<your-client-id>" `
    -Description "Allow transcript access for telehealth visits"

# ============================================
# STEP 4: Grant the Policy
# ============================================

# Option A: Grant to specific providers
Grant-CsApplicationAccessPolicy `
    -PolicyName "Telehealth-Transcript-Policy" `
    -Identity "drsmith@southviewteam.com"

Grant-CsApplicationAccessPolicy `
    -PolicyName "Telehealth-Transcript-Policy" `
    -Identity "drjones@southviewteam.com"

# Option B: Grant tenant-wide (all users)
Grant-CsApplicationAccessPolicy `
    -PolicyName "Telehealth-Transcript-Policy" `
    -Global

# ============================================
# STEP 5: Verify (wait 30 minutes first!)
# ============================================
Get-CsApplicationAccessPolicy

Get-CsOnlineUser -Identity "drsmith@southviewteam.com" | `
    Select-Object DisplayName, ApplicationAccessPolicy
```

### Step 8: Enable Auto-Recording (Optional)

**Option A: Via Teams Admin Center (all telehealth meetings)**

1. Go to **Teams Admin Center** → **Meetings** → **Meeting policies**
2. Select **Global** policy (or create custom "Telehealth" policy)
3. Configure:
   ```
   Recording & transcription:
   ✅ Meeting recording: On
   ✅ Transcription: On
   ✅ Recording automatically expires: 120 days (or your retention policy)

   Recording consent:
   ✅ Explicit recording consent: On (shows banner to patients)
   ```

**Option B: Via PowerShell**
```powershell
# Create telehealth-specific policy
New-CsTeamsMeetingPolicy -Identity "Telehealth-Policy" `
    -AllowCloudRecording $true `
    -AllowTranscription $true `
    -ExplicitRecordingConsent Enabled `
    -RecordingStorageMode OneDriveForBusiness

# Assign to providers
Grant-CsTeamsMeetingPolicy -Identity "drsmith@southviewteam.com" `
    -PolicyName "Telehealth-Policy"
```

### Step 9: Test the Setup

1. **Book a test appointment** via the Bookings page
2. **Join as provider** and start the meeting
3. **Start recording** (should show consent banner to patient)
4. **End meeting** and wait 5-10 minutes
5. **Test transcript API**:

```http
# Get provider's meetings
GET https://graph.microsoft.com/v1.0/users/drsmith@southviewteam.com/onlineMeetings

# Get transcripts for a specific meeting
GET https://graph.microsoft.com/v1.0/users/drsmith@southviewteam.com/onlineMeetings/{meeting-id}/transcripts

# Download transcript content
GET https://graph.microsoft.com/v1.0/users/drsmith@southviewteam.com/onlineMeetings/{meeting-id}/transcripts/{transcript-id}/content?$format=text/vtt
```

---

## Using autopilot@southviewteam.com Effectively

### Recommended Roles

| Task | autopilot Can Do? | How |
|------|-------------------|-----|
| Create/modify booking pages | ✅ | Bookings Administrator role |
| Add/remove providers | ✅ | Bookings Administrator role |
| View all provider schedules | ✅ | Bookings Administrator role |
| Book appointments on behalf of patients | ✅ | Schedule via Bookings UI |
| Access transcripts via API | ✅ | Application Access Policy (grant to providers) |
| Create Teams meetings directly | ✅ | Calendar access via Graph |
| Be a bookable provider | ❌ | Intentionally excluded |

### Complete autopilot Setup Checklist

```
[ ] 1. Bookings Administrator on all booking pages
[ ] 2. Application Access Policy granted (for API access)
[ ] 3. Exchange Online permissions (for calendar management)
[ ] 4. Service principal created (for automated API calls)
[ ] 5. Graph API permissions configured:
       - Calendars.ReadWrite
       - OnlineMeetings.ReadWrite.All
       - OnlineMeetingTranscript.Read.All
       - Sites.ReadWrite.All (for SharePoint storage)
```

### Automation Possibilities

With autopilot + MCP server + Graph API:

1. **Schedule telehealth visits** programmatically via Bookings API
2. **Pull transcripts** after visits end (5-10 min delay)
3. **Generate visit summaries** using Azure Claude
4. **Store documentation** in SharePoint
5. **Update patient records** (if EHR integration available)
6. **Send follow-up messages** via Spruce

---

## Teams Premium: Virtual Appointments (Optional Upgrade)

If you have or plan to get Teams Premium licenses, you unlock additional features:

### Queue View
- Real-time view of all scheduled appointments for the day
- See when patients join the lobby
- One-click to admit patient
- Send reminder to late/no-show patients

### Advanced SMS
- Automatic appointment reminders (24h, 1h before)
- Join link sent via SMS
- Confirmation and cancellation notifications
- Custom SMS templates

### Analytics Dashboard
- Total appointments by provider
- Average wait time
- Average visit duration
- No-show rate
- Patient satisfaction scores (if surveys enabled)

### Enabling Virtual Appointments App

1. **Teams Admin Center** → **Teams apps** → **Setup policies**
2. Add **Virtual Appointments** to pinned apps for healthcare staff
3. Or: Users can find it via Teams Apps → Search "Virtual Appointments"

Source: [Teams Premium Virtual Appointments](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/the-connected-clinic-virtual-appointments-made-easy/3771001)

---

## HIPAA Compliance Checklist

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **BAA in place** | Microsoft 365 DPA includes BAA automatically | ✅ |
| **Encryption in transit** | Teams uses TLS 1.2+ | ✅ |
| **Encryption at rest** | Microsoft-managed encryption keys | ✅ |
| **Access controls** | Configure Conditional Access policies | ⚠️ Configure |
| **Audit logging** | Enable unified audit log in Compliance Center | ⚠️ Configure |
| **Patient identity verification** | Train staff on verification protocols | ⚠️ Process |
| **Recording consent** | Enable explicit recording consent banner | ⚠️ Configure |
| **Data retention** | Set transcript/recording retention policies | ⚠️ Configure |
| **Minimum necessary** | Limit who can access patient meeting data | ⚠️ Configure |

### Configuring Recording Consent

```
Teams Admin Center → Meetings → Meeting policies → [Your Policy]
✅ Explicit recording consent: On
```

Or via PowerShell:
```powershell
Set-CsTeamsMeetingPolicy -Identity "Telehealth-Policy" `
    -ExplicitRecordingConsent Enabled
```

This shows patients a consent banner when recording starts, which is important for HIPAA compliance.

### Configuring Audit Logging

1. Go to **Microsoft Purview Compliance Portal**
2. Navigate to **Audit**
3. Ensure **Unified audit log** is enabled
4. Configure retention (default 90 days, extend if needed)

---

## Troubleshooting

### "Application is not allowed to perform operations on the user"

**Cause:** Application Access Policy not configured or not propagated.

**Fix:**
```powershell
# Verify policy exists
Get-CsApplicationAccessPolicy

# Verify policy is granted to user
Get-CsOnlineUser -Identity "drsmith@southviewteam.com" | `
    Select-Object DisplayName, ApplicationAccessPolicy

# Wait 30 minutes after policy changes
```

### "Transcript not found" for a meeting that had transcription

**Causes:**
1. Meeting not created via Bookings/calendar (ad-hoc meeting)
2. Graph hasn't indexed the transcript yet (wait 5-10 minutes)
3. Using wrong user ID in API path (must be meeting organizer)
4. Recording wasn't enabled or transcription wasn't turned on

**Fix:**
- Ensure meetings are scheduled via Bookings (creates calendar events)
- Wait 5-10 minutes after meeting ends
- Use the provider's user ID (meeting organizer), not autopilot

### Patients can't join meeting

**Causes:**
1. Meeting link expired or invalid
2. Lobby settings blocking external users
3. Browser compatibility issues

**Fix:**
- Check Teams meeting policy allows external participants
- Ensure "People in my organization" auto-admit is configured
- Recommend Chrome or Edge browser for patients

### Bookings not showing in Teams

**Causes:**
1. Bookings not enabled for organization
2. User doesn't have appropriate license
3. App policy blocking Bookings

**Fix:**
1. Enable Bookings in M365 Admin Center
2. Verify user has Business Premium, E3, or E5 license
3. Check Teams app setup policies

---

## Quick Reference

### Bookings Setup Summary

```
1. Enable Bookings (M365 Admin Center → Org settings)
2. Create booking page (Teams → Apps → Bookings)
3. Add autopilot as Administrator
4. Add providers as Staff
5. Create service types (New Patient, Follow-up)
6. Configure booking page settings
7. Set up Application Access Policy (PowerShell)
8. Enable auto-recording (Teams Admin Center)
9. Test transcript retrieval via Graph API
```

### Key API Endpoints

```http
# List provider's meetings
GET /users/{provider-id}/onlineMeetings

# Get transcripts for a meeting
GET /users/{provider-id}/onlineMeetings/{meeting-id}/transcripts

# Download transcript content (VTT format)
GET /users/{provider-id}/onlineMeetings/{meeting-id}/transcripts/{transcript-id}/content?$format=text/vtt

# Download transcript content (plain text)
GET /users/{provider-id}/onlineMeetings/{meeting-id}/transcripts/{transcript-id}/content?$format=text/plain
```

### Required Permissions

```
Delegated:
- Calendars.ReadWrite
- OnlineMeetings.ReadWrite
- OnlineMeetingTranscript.Read.All

Application:
- Calendars.ReadWrite
- OnlineMeetings.ReadWrite.All
- OnlineMeetingTranscript.Read.All

Additional:
- Application Access Policy (via PowerShell)
```

---

## Sources & References

1. [Microsoft Teams HIPAA Compliance 2025](https://www.hipaajournal.com/microsoft-teams-hipaa-compliant/) - Compliance requirements
2. [Virtual Appointments in Teams](https://learn.microsoft.com/en-us/microsoft-365/frontline/virtual-appointments) - Official documentation
3. [Setting Up Bookings for Virtual Visits](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/setting-up-bookings-for-virtual-visits/1265216) - Healthcare-specific guide
4. [Manage Bookings App in Teams](https://learn.microsoft.com/en-us/microsoftteams/bookings-app-admin) - Admin configuration
5. [Add Staff to Bookings](https://learn.microsoft.com/en-us/microsoft-365/bookings/add-staff) - Staff management
6. [Bookings Shared Mailbox Setup](https://office365itpros.com/2022/07/22/microsoft-bookings-app/) - PowerShell admin access
7. [Teams Meeting Transcripts API](https://learn.microsoft.com/en-us/microsoftteams/platform/graph-api/meeting-transcripts/overview-transcripts) - Graph API reference
8. [Teams Premium Virtual Appointments](https://techcommunity.microsoft.com/blog/healthcareandlifesciencesblog/the-connected-clinic-virtual-appointments-made-easy/3771001) - Premium features
9. [Configure Application Access Policy](https://learn.microsoft.com/en-us/graph/cloud-communication-online-meeting-application-access-policy) - PowerShell setup
10. [Grant-CsApplicationAccessPolicy](https://learn.microsoft.com/en-us/powershell/module/teams/grant-csapplicationaccesspolicy) - PowerShell reference

---

*Research conducted: 2025-12-04*
*Generated by Claude via /research-topic command*
