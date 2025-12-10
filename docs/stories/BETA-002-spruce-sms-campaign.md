# BETA-002: Spruce SMS Consent Outreach Campaign

**Priority**: CRITICAL
**Sprint**: Beta Launch (Dec 3, 2025)
**Owner**: Dr. Green + Jenny (execution), Agent Team (tooling)
**Status**: Ready for Implementation
**Depends On**: BETA-001 (Microsoft Forms setup)

---

## User Story

**As a** staff member at Green Clinic
**I want to** send personalized consent request SMS messages to all patients via Spruce
**So that** patients can easily consent to records retention before the December 31 deadline

---

## Acceptance Criteria

### SMS Content
- [ ] Messages personalized with patient's first name (or preferred name)
- [ ] Clear explanation of what's needed
- [ ] Unique consent link per patient
- [ ] Office phone number for questions
- [ ] APCM patients receive APCM-specific messaging

### Campaign Execution
- [ ] Export CSV from Streamlit with: Name, Phone, Consent URL, SMS Message
- [ ] Upload to Spruce for bulk SMS
- [ ] Rate limit: Max 100 messages per day (Spruce recommendation)
- [ ] Best timing: Tuesday-Thursday, 10am-2pm

### Follow-up Sequence
- [ ] Day 0: Initial outreach
- [ ] Day 3: First reminder to non-responders
- [ ] Day 7: Second reminder (more urgent)
- [ ] Day 14: Final SMS reminder
- [ ] Day 21+: Phone call for persistent non-responders

### Tracking
- [ ] Mark patients as "outreach_sent" after initial SMS
- [ ] Track outreach attempts in Streamlit
- [ ] Filter for non-responders for follow-ups

---

## Technical Implementation

### SMS Templates (Already Implemented in `sms_templates.py`)

**Non-APCM Initial:**
```
Hi {name}, this is Dr. Robert Green's office.

As you may know, I am transitioning my practice from Southview. To continue
providing you excellent care, I need your consent to maintain your medical records.

Please visit this secure link to complete your consent:
{consent_url}

Questions? Reply here or call (205) 955-7605.

- Dr. Green's Care Team
```

**APCM Initial:**
```
Hi {name}, this is Dr. Robert Green's office.

As an APCM patient, I want to continue providing your care coordination services
after my transition to Home Team Medical Services in January 2026.

Please visit this link to:
- Continue APCM with Dr. Green
- Confirm records retention consent

{consent_url}

Questions? Reply or call (205) 955-7605.

- Dr. Green's Care Team
```

### Spruce Export Format

The Outreach Campaign page exports CSV with columns:
| Column | Description |
|--------|-------------|
| MRN | For internal tracking |
| Name | Patient full name |
| Preferred | Preferred name if different |
| Phone | Mobile number for SMS |
| Consent_URL | Personalized Microsoft Forms link |
| Token | Consent token (for reference) |
| APCM | Yes/No |
| SMS_Message | Pre-formatted message ready to send |

### Spruce Bulk SMS Process

1. Download CSV from Streamlit Outreach Campaign page
2. Open Spruce web or desktop app
3. Navigate to Bulk Notifications feature
4. Upload CSV (Phone, Name, SMS_Message columns)
5. Review preview
6. Send batch (respect 100/day limit)
7. Monitor for replies in Spruce

---

## Workflow Steps

### Day 0: Initial Campaign Launch

1. **Generate Tokens** (Streamlit)
   - Go to Outreach Campaign > Generate Tokens
   - Select "All patients without tokens" or "APCM patients only (priority)"
   - Click "Generate Tokens"

2. **Configure Form URL** (Streamlit sidebar)
   - Paste Microsoft Forms base URL
   - System appends patient tokens automatically

3. **Export for Spruce**
   - Click "Download Spruce SMS Export"
   - File: `spruce_sms_YYYYMMDD_HHMM.csv`

4. **Send via Spruce**
   - Upload CSV to Spruce bulk notification
   - Verify phone numbers
   - Send batch

5. **Update Tracking**
   - Streamlit automatically marks tokens as "invitation_sent"
   - Outreach date recorded

### Day 3, 7, 14: Follow-up Campaigns

1. **Filter Non-Responders** (Streamlit)
   - Consent Tracking page > Filter by "No Response"
   - Note: Need to import Forms responses first to know who responded

2. **Generate Follow-up Export**
   - Export non-responders with follow-up messaging
   - Templates auto-adjust based on days since initial outreach

3. **Send Follow-up Batch**
   - Same Spruce process
   - Use appropriate urgency level message

---

## Success Metrics

| Metric | Target | Tracking |
|--------|--------|----------|
| SMS Delivery Rate | >95% | Spruce reports |
| Response Rate (Day 7) | >30% | Streamlit dashboard |
| Consent Rate (Day 14) | >50% | Streamlit dashboard |
| Final Consent Rate | >80% | By Dec 31 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Patients don't check SMS | Email backup for non-responders |
| Wrong phone numbers | Verify against Spruce matches first |
| Spruce rate limits | Stay under 100/day, spread over time |
| Link doesn't work | Test links before bulk send |
| Form confusion | Clear instructions + phone support |

---

## Definition of Done

- [ ] First batch of 25 patients contacted successfully
- [ ] At least 5 responses received and processed
- [ ] Follow-up workflow tested on Day 3
- [ ] Staff trained on export/import process
- [ ] FAQ document created for patient questions

---

## Related Stories

- BETA-001: Microsoft Forms Consent Portal Setup
- BETA-003: Power Automate Workflow (Optional)
- BETA-004: Daily Consent Import Routine

---

*Created: 2025-12-02 by BMAD Agent Team*
