# BETA-001: Microsoft Forms Consent Portal Setup

**Priority**: CRITICAL
**Sprint**: Beta Launch (Dec 3, 2025)
**Owner**: Dr. Robert Green (creation), Agent Team (documentation)
**Status**: Ready for Implementation

---

## User Story

**As a** patient of Dr. Green
**I want to** receive a secure link and complete a consent form on my phone
**So that** I can authorize Dr. Green to maintain my medical records during the practice transition

---

## Acceptance Criteria

### Form Structure
- [ ] Form titled "Dr. Green Practice Transition - Patient Consent"
- [ ] Page 1: Practice transition explanation (read-only text)
- [ ] Page 2: Consent choices with clear options
- [ ] Page 3: Confirmation and signature fields
- [ ] Mobile-responsive layout
- [ ] Works in all major browsers

### Consent Questions (Required)
- [ ] "I consent to Dr. Robert Green and his direct staff maintaining access to my medical records after the transition from Southview Medical Group"
- [ ] Patient name confirmation field
- [ ] Date field (auto-populated if possible)

### APCM Patient Questions (Conditional)
- [ ] "I elect to continue Advanced Primary Care Management (APCM) services with Dr. Green at Home Team Medical Services" (Yes/No)
- [ ] "I authorize Dr. Green's team to notify Southview Medical Group that I am transferring my APCM consent to Home Team Medical Services effective January 1, 2026" (Yes/No)
- [ ] "I understand that by making this election, Southview Medical Group will no longer bill Medicare for APCM services on my behalf after December 31, 2025" (Acknowledgment checkbox)

### Token Tracking
- [ ] Form URL accepts `?token=XXXXX` parameter
- [ ] Token field visible in form responses
- [ ] Hidden field or auto-populated from URL if possible

### Form Settings
- [ ] Anyone can respond (no M365 login required for patients)
- [ ] Record responder name: Optional
- [ ] One response per person: No (allow resubmission)
- [ ] Notification on submission: Yes (to admin email)

---

## Technical Notes

### URL Pattern
```
https://forms.microsoft.com/r/{FORM_ID}?token={PATIENT_TOKEN}
```

### Token Extraction in Power Automate
Power Automate can extract the token from form responses if added as a question, or use URL parsing logic.

### Sample Form Content

**Page 1 Header:**
```
Important Information About Your Medical Care

Dr. Robert Green is transitioning his practice from Southview Medical Group to
Home Team Medical Services effective January 1, 2026.

To continue providing you with excellent care, we need your consent to maintain
your medical records. Your privacy and the security of your health information
remain our top priority.

This form takes less than 2 minutes to complete.
```

**Page 2 Questions:**
```
1. Records Retention Consent (Required)
   [ ] I consent to Dr. Robert Green maintaining access to my medical records
   [ ] I do not consent

2. [If APCM Patient] APCM Service Continuation
   ○ Yes, continue my APCM services with Dr. Green at Home Team
   ○ No, I do not wish to continue APCM with Dr. Green
   ○ I need more information before deciding

3. [If APCM + Yes] Southview Notification Authorization
   [ ] I authorize notification to Southview about my APCM transfer
```

**Page 3 Confirmation:**
```
Please confirm your identity:

Your Full Name: ________________
Today's Date: ________________ (auto-filled)

Your Reference Token: ________________ (from your SMS link)

By submitting this form, I confirm that I have read and understand the
information provided and that my responses are accurate.

[Submit]
```

---

## Integration with Streamlit

### Existing Components Used
- `consent_tokens.py` - Token generation (already implemented)
- `app/pages/4_Outreach_Campaign.py` - Token generation UI, export for Spruce
- `app/pages/11_Consent_Response.py` - Bulk import from Forms export
- `sms_templates.py` - SMS message with consent URL

### Workflow
1. Streamlit generates tokens for patients
2. Outreach Campaign page exports CSV with personalized URLs
3. Staff uploads CSV to Spruce for bulk SMS
4. Patients receive SMS, click link, complete Forms
5. Staff exports Forms responses to Excel
6. Staff imports Excel into Streamlit via Consent Response page
7. Database updated, dashboard reflects new consents

---

## Definition of Done

- [ ] Microsoft Form created and tested on mobile device
- [ ] Form URL documented and added to Streamlit config
- [ ] Test submission with sample token successful
- [ ] Bulk import tested with 3+ sample responses
- [ ] Staff training document created

---

## Related Stories

- BETA-002: Spruce SMS Campaign Execution
- BETA-003: Power Automate Workflow (Optional Enhancement)
- BETA-004: Daily Consent Import Routine

---

*Created: 2025-12-02 by BMAD Agent Team*
