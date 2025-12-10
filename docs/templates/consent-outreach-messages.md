# Patient Consent Outreach Messages

**Created**: December 8, 2025
**Purpose**: SMS and email templates for practice transition consent outreach
**HIPAA Status**: Compliant - no PHI in messages

---

## SMS Outreach Message (160 char limit per segment)

### Option A: Single SMS (~155 chars)
```
Dr. Green's practice has important updates. Please visit the link below for information about our new location and to share any questions: [LINK]
```

### Option B: Two-Part SMS (for longer URL)
**Part 1:**
```
Important: Dr. Green's primary care practice is relocating. Please follow the personalized link below for details and to share questions or concerns.
```

**Part 2:**
```
Your form: [PERSONALIZED_LINK]
```

### Option C: Concise (~120 chars)
```
Dr. Green's practice is moving. Please complete this brief form for important updates: [LINK]
```

---

## Email Outreach Message

**Subject Line Options:**
1. `Important Update: Dr. Green's Primary Care Practice`
2. `Action Required: Dr. Green's Practice Location Change`
3. `Your Personalized Update from Dr. Green's Office`

**Email Body:**

```
Dear [PATIENT_NAME],

We are reaching out with important information about Dr. Green's primary care practice.

Our team is transitioning to a new location, and we want to ensure you have all the
information you need about this change and how it may affect your care.

Please click the link below to access a personalized form where you can:
- Confirm your contact preferences
- Ask questions about the transition
- Share any concerns you may have

Your Personalized Form: [PERSONALIZED_LINK]

This form is secure and your responses will be handled confidentially.

If you have immediate questions, please call our office at [PHONE_NUMBER].

Thank you for being a valued member of our practice.

Warm regards,
Dr. Robert Green and the Home Team Medical Services Staff
```

---

## SMS Auto-Reply (When Patient Responds)

### Option A: Concise (~160 chars)
```
Thank you for your reply. Note: SMS is not secure for private health info. For confidential matters, please call [PHONE] or use our secure patient portal.
```

### Option B: With Consent Language (~280 chars, 2 segments)
```
Thank you for responding. Please note: SMS messages may be intercepted by third parties. For private health matters, call [PHONE] or use a secure portal. Continued texting implies consent to SMS communication with this understanding.
```

### Option C: Very Concise (~120 chars)
```
Thanks for replying. For privacy, please call [PHONE] for health questions. SMS is not secure. Reply STOP to opt out.
```

---

## Form Configuration

### Microsoft Forms Setup

**Form Title:** `Practice Transition - Patient Response Form`

**Form Fields:**

1. **Name** (Required, Short text)
   - "Your full name as it appears in our records"

2. **Date of Birth** (Required, Date)
   - "For verification purposes"

3. **Preferred Contact Method** (Required, Choice)
   - Phone call
   - Text message (SMS)
   - Email
   - Secure patient portal
   - Mail

4. **Contact Preference Confirmation** (Required, Choice)
   - "Yes, I consent to receive communications via my preferred method above"
   - "No, please contact me by mail only"

5. **Questions or Concerns** (Optional, Long text)
   - "Please share any questions or concerns about the practice transition"

6. **Preferred Provider** (Optional, Choice)
   - "I would like to continue care with Dr. Green at the new location"
   - "I would like information about transferring my records to another provider"
   - "I need more information before deciding"

7. **APCM Acknowledgment** (If applicable, Choice)
   - "I understand my APCM enrollment status and wish to continue with Home Team"
   - "I have questions about APCM billing"
   - "Not applicable"

---

## Token-Based URL Generation

The app generates personalized URLs with tracking tokens:

```
https://forms.microsoft.com/r/YOUR_FORM_ID?token=ABC123XYZ
```

**Token Purpose:**
- Links response to specific patient
- Tracks who has responded
- Enables follow-up for non-responders

**Implementation:** See `app/consent_tokens.py`

---

## Compliance Checklist

Before sending, verify:

- [ ] Message contains NO PHI (diagnoses, conditions, appointment details)
- [ ] Link goes to secure (HTTPS) form
- [ ] Patient has a way to opt-out (STOP for SMS, unsubscribe for email)
- [ ] Auto-reply warns about SMS insecurity
- [ ] Responses are stored securely (Forms + Azure)
- [ ] Staff trained on handling responses

---

## Spruce Tag for Campaign

When sending via Spruce, tag patients with:
- `consent_pending` - Before outreach
- `consent_obtained` - After form completion
- `consent_declined` - If they opt out
- `unreachable` - If message fails

---

*Document Version: 1.0*
*For: Home Team Medical Services - Green Clinic Transition*
