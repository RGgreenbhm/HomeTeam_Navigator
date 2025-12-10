# Story S8: SMS Outreach Campaign Launch

**Epic:** Consent Outreach
**Priority:** CRITICAL
**Points:** 8
**Sprint:** Dec 9-15, 2025
**Depends On:** S7 (Consent Form Setup)

---

## User Story

**As a** clinical staff member
**I want to** send consent SMS messages to all matched patients
**So that** patients receive their personalized consent form links

---

## Acceptance Criteria

### AC1: Campaign Preparation
- [ ] Patient list imported and Spruce-matched
- [ ] Consent tokens generated for all patients
- [ ] SMS templates selected per patient type (APCM vs non-APCM)
- [ ] Campaign preview shows message count and content

### AC2: Batch Sending
- [ ] Can send SMS in batches (50 at a time)
- [ ] Progress indicator shows sending status
- [ ] Errors logged and displayed
- [ ] Retry option for failed sends

### AC3: Tracking
- [ ] Each send logged with timestamp
- [ ] Patient record updated with outreach date
- [ ] Consent status changed to "invitation_sent"
- [ ] Audit trail maintained

### AC4: Follow-Up Scheduling
- [ ] Day 3 reminder queued automatically
- [ ] Day 7 reminder queued
- [ ] Day 14 final SMS queued
- [ ] Follow-up queue shows pending reminders

---

## Technical Tasks

### Task 1: Campaign Page Enhancement
```python
# app/pages/4_Outreach_Campaign.py enhancements

def send_campaign_batch(patients: List[Patient], template_name: str):
    """Send SMS to batch of patients"""
    results = []
    for patient in patients:
        if not patient.spruce_contact_id:
            results.append({"patient": patient, "status": "no_spruce_match"})
            continue

        try:
            # Generate consent URL
            consent_url = get_consent_url(patient.consent_token)

            # Render template
            message = render_template(
                template_name,
                patient_name=patient.preferred_name or patient.first_name,
                consent_url=consent_url,
                office_phone="205-955-7605"
            )

            # Send via Spruce
            response = spruce_client.send_sms(
                contact_id=patient.spruce_contact_id,
                message=message
            )

            # Update patient record
            patient.consent_status = ConsentStatus.INVITATION_SENT
            patient.last_outreach_date = datetime.now()
            db.commit()

            results.append({"patient": patient, "status": "sent"})

        except Exception as e:
            results.append({"patient": patient, "status": "error", "error": str(e)})

    return results
```

### Task 2: Rate Limiting
```python
# Respect Spruce API limits
import asyncio

async def send_with_rate_limit(patients: List[Patient], batch_size=50, delay=1.0):
    """Send in batches with delay between batches"""
    for i in range(0, len(patients), batch_size):
        batch = patients[i:i+batch_size]
        await send_campaign_batch(batch)
        if i + batch_size < len(patients):
            await asyncio.sleep(delay)  # 1 second between batches
```

### Task 3: Campaign Dashboard
- [ ] Total patients in campaign
- [ ] Sent count
- [ ] Pending count
- [ ] Error count
- [ ] Response rate (consented / sent)

### Task 4: Follow-Up Automation
```python
# Schedule follow-up reminders
def schedule_followups(patient: Patient):
    """Queue follow-up reminders after initial send"""
    if patient.consent_status == ConsentStatus.INVITATION_SENT:
        # Day 3 reminder
        create_scheduled_task(
            patient_id=patient.id,
            task_type="followup_sms",
            template="day_3_reminder",
            scheduled_for=patient.last_outreach_date + timedelta(days=3)
        )
        # Day 7 reminder
        create_scheduled_task(
            patient_id=patient.id,
            task_type="followup_sms",
            template="day_7_reminder",
            scheduled_for=patient.last_outreach_date + timedelta(days=7)
        )
        # Day 14 final
        create_scheduled_task(
            patient_id=patient.id,
            task_type="followup_sms",
            template="day_14_final",
            scheduled_for=patient.last_outreach_date + timedelta(days=14)
        )
```

### Task 5: Export SMS List
- [ ] Export phone numbers + messages for manual send (backup)
- [ ] CSV format: phone, message, token
- [ ] Can be used if API fails

---

## SMS Templates (Review)

### Initial Outreach (Non-APCM)
```
Hi {name}, this is Dr. Green's office.

As you know, Dr. Green is transitioning to Home Team Medical. Please
complete this quick form to consent to record transfer:

{consent_url}

Questions? Call 205-955-7605.

- Dr. Green's Care Team
```

### Initial Outreach (APCM)
```
Hi {name}, this is Dr. Green's office.

Dr. Green is transitioning to Home Team Medical. As an APCM patient,
please complete this form to continue your care and APCM benefits:

{consent_url}

Questions? Call 205-955-7605.

- Dr. Green's Care Team
```

### Day 3 Reminder
```
Hi {name}, friendly reminder to complete your consent form for
Dr. Green's practice transition:

{consent_url}

Takes just 2 minutes. Thank you!
```

### Day 7 Reminder
```
Hi {name}, we still need your consent response. Dr. Green wants to
continue your care at Home Team Medical.

Please complete the form today: {consent_url}

Call 205-955-7605 with questions.
```

### Day 14 Final
```
Hi {name}, this is our final reminder. Please complete your consent
form by Dec 31 to ensure continuity of care:

{consent_url}

No response = we cannot transfer your records.
```

---

## Metrics to Track

| Metric | Target |
|--------|--------|
| Send success rate | >95% |
| Response rate (Day 7) | >30% |
| Response rate (Day 14) | >50% |
| Final consent rate | >70% |

---

## Dependencies

- S7: Consent Form Setup (form URL available)
- Spruce API credentials configured
- All patients have consent tokens
- Patient-Spruce matching complete

---

## Definition of Done

- [ ] Can send initial SMS to all matched patients
- [ ] Rate limiting prevents API errors
- [ ] Tracking updated for each send
- [ ] Follow-up reminders scheduled
- [ ] Dashboard shows campaign progress
- [ ] Error handling for failed sends
- [ ] Audit logging complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Spruce rate limits | Batch with delays |
| Wrong phone numbers | Use Spruce-matched contacts only |
| Message too long | Character count validation |
| Patient opt-out | Honor Spruce unsubscribes |

---

## Campaign Schedule

| Date | Action | Target |
|------|--------|--------|
| Dec 9 | Initial send (batch 1) | 500 patients |
| Dec 10 | Initial send (batch 2) | 500 patients |
| Dec 11 | Initial send (batch 3) | 384 patients |
| Dec 12 | Day 3 reminders | Batch 1 |
| Dec 13 | Day 3 reminders | Batch 2 |
| Dec 14 | Day 3 reminders | Batch 3 |
| Dec 16 | Day 7 reminders | Batch 1 |
| Dec 17 | Day 7 reminders | Batch 2 |
| Dec 18 | Day 7 reminders | Batch 3 |
| Dec 23 | Day 14 final | Batch 1 |
| Dec 24 | Day 14 final | Batch 2 |
| Dec 25 | Day 14 final | Batch 3 |
| Dec 26-31 | Phone outreach | Non-responders |

---

*Created: 2025-12-02*
