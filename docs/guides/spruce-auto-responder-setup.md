# Spruce Auto-Responder Setup Guide

**Date**: December 8, 2025
**Purpose**: Configure Spruce's native auto-reply for SMS privacy disclaimer
**Time Required**: ~5 minutes

---

## Overview

Spruce Health has a built-in auto-responder feature that can automatically reply to incoming SMS messages. We'll use this to send the privacy disclaimer when patients reply to our outreach texts.

**Benefits of Using Native Spruce Auto-Reply:**
- No webhook hosting required
- No persistent web server needed
- Configured directly in Spruce UI
- Works immediately, 24/7
- No additional cost

---

## Setup Steps

### Step 1: Access Spruce Settings

1. Log into **Spruce Web App** at [app.sprucehealth.com](https://app.sprucehealth.com)
2. Click the **gear icon** (Settings) in the bottom-left corner
3. Navigate to **Team Settings** → **Auto-Responders**

### Step 2: Create New Auto-Responder

1. Click **"+ Create Auto-Responder"** button
2. Configure the following settings:

#### Name
```
SMS Privacy Disclaimer
```

#### Trigger
- Select: **"When a message is received"**
- Channel: **SMS/Text messages**
- From: **Any contact** (or filter to specific tags if needed)

#### Response Message
```
Thanks for replying. For private health matters, please call 205-955-7605. SMS is not secure. Reply STOP to opt out.
```

**Alternative - Longer Version:**
```
Thanks for your reply. Note: SMS is not secure for private health info. For confidential matters, call 205-955-7605 or use our patient portal. Continued texting implies consent to SMS with this understanding.
```

#### Active Hours
- **Recommended**: All hours (24/7)
- **Alternative**: Business hours only (8 AM - 5 PM)

#### Frequency
- **Once per conversation** (so patients don't get the same message repeatedly)
- Or: **Once per 24 hours** (if you want reminders)

### Step 3: Save and Activate

1. Click **"Save Auto-Responder"**
2. Ensure the toggle is **ON** (active)
3. Test by sending yourself a text and replying

---

## Testing the Auto-Responder

### Test Procedure

1. **Send Test SMS**
   - Use the Patient Explorer app or Spruce directly
   - Send a test message to your own phone number

2. **Reply to the SMS**
   - Reply with any text (e.g., "Test reply")

3. **Verify Auto-Response**
   - You should receive the privacy disclaimer within seconds
   - Check Spruce conversation to confirm it was sent

4. **Reply Again**
   - If set to "once per conversation", you should NOT get another auto-reply
   - This prevents spam if patients send multiple messages

---

## HIPAA Compliance Notes

### Why This Message Is Compliant

| Element | Compliance |
|---------|------------|
| **No PHI** | Message contains no patient-specific information |
| **Informed Consent** | Warns patients that SMS is not secure |
| **Secure Alternative** | Offers phone call as secure option |
| **Opt-Out** | Provides STOP mechanism |
| **Under BAA** | All messages stored in Spruce (BAA in place) |

### What NOT to Include in Auto-Replies

- Patient names
- Appointment details
- Diagnosis or treatment information
- Insurance information
- Any identifiable health information

---

## Message Variants

### Standard (Recommended)
```
Thanks for replying. For private health matters, please call 205-955-7605. SMS is not secure. Reply STOP to opt out.
```
*124 characters, 1 SMS segment*

### With Implied Consent
```
Thanks for your reply. Note: SMS is not secure for private health info. For confidential matters, call 205-955-7605 or use our patient portal. Continued texting implies consent to SMS with this understanding.
```
*209 characters, 2 SMS segments*

### Minimal
```
For health questions, please call 205-955-7605. SMS is not secure. STOP to opt out.
```
*85 characters, 1 SMS segment*

---

## Troubleshooting

### Auto-Reply Not Sending

1. **Check Active Status**: Ensure toggle is ON
2. **Check Hours**: If set to business hours only, test during those times
3. **Check Frequency**: If set to "once per conversation", try a new conversation
4. **Check Filters**: If filtered by tags, ensure test contact has required tag

### Multiple Auto-Replies Sending

1. **Check Frequency Setting**: Set to "once per conversation" to prevent repeats
2. **Check for Duplicate Rules**: Ensure no other auto-responders are active

### Staff Getting Auto-Replies

- Auto-responders should only trigger on **external** messages
- Check that your staff numbers are marked as **team members** in Spruce

---

## Integration with Patient Explorer

### Flow Overview

```
1. Patient Explorer sends SMS with consent form link
                    ↓
2. Patient receives SMS
                    ↓
3. Patient replies (any text)
                    ↓
4. Spruce Auto-Responder sends privacy disclaimer
                    ↓
5. Patient clicks link → fills form → posts to Spruce
                    ↓
6. Patient Explorer pulls responses from Spruce API
```

### No Code Required

The auto-responder runs entirely within Spruce - no changes to Patient Explorer code needed for this feature.

---

## Alternative: Custom Webhook (For V1.1+)

If more sophisticated logic is needed (e.g., different responses based on message content), you can use Spruce Webhooks instead:

```python
# This would run on a hosted server
@app.route("/api/spruce/webhook", methods=["POST"])
def handle_sms_reply(req):
    message = req.json["data"]["object"]["text"]

    if "yes" in message.lower() or "consent" in message.lower():
        send_confirmation_message()
    else:
        send_privacy_disclaimer()
```

However, this requires:
- Hosted webhook endpoint
- Spruce webhook registration
- Additional maintenance

**Recommendation**: Use native auto-responder for V1.0, upgrade to webhook if custom logic needed.

---

## Checklist

Before launching SMS campaign:

- [ ] Auto-responder created in Spruce
- [ ] Message tested with personal phone
- [ ] Frequency set to "once per conversation"
- [ ] Active 24/7 or during business hours as needed
- [ ] Staff phone numbers excluded from trigger
- [ ] Office phone number correct in message

---

*Created: December 8, 2025*
*For: Patient Explorer V1.0 - Consent Outreach Campaign*
