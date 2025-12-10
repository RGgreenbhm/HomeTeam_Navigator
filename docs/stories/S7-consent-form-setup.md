# Story S7: Consent Form Setup (Microsoft Forms)

**Epic:** Consent Outreach
**Priority:** CRITICAL
**Points:** 5
**Sprint:** Dec 2-8, 2025

---

## User Story

**As a** patient
**I want to** receive a link to complete my consent form
**So that** I can authorize Dr. Green to retain my medical records

---

## Acceptance Criteria

### AC1: Form Creation
- [ ] Microsoft Form created with consent questions
- [ ] APCM election questions included
- [ ] Form accepts token parameter in URL
- [ ] Form is mobile-friendly

### AC2: Form Content
- [ ] Clear explanation of consent purpose
- [ ] Practice transition context provided
- [ ] APCM billing transfer explanation
- [ ] Southview billing revocation option

### AC3: Form Fields
- [ ] Token (hidden, pre-filled from URL)
- [ ] Consent decision (Yes/No)
- [ ] APCM continue with Home Team (Yes/No)
- [ ] APCM revoke Southview billing (Yes/No)
- [ ] Signature/Acknowledgment
- [ ] Date

### AC4: Response Handling
- [ ] Responses flow to Form response spreadsheet
- [ ] Can export responses as CSV
- [ ] Token allows matching to patient record

---

## Technical Tasks

### Task 1: Create Microsoft Form
1. Go to forms.office.com
2. Create new form: "Patient Consent - Dr. Green Practice Transition"
3. Add questions per specification below

### Task 2: Form Questions

**Section 1: Introduction**
```
Dr. Robert Green is transitioning his practice from Southview Medical
Group to Home Team Medical Services, effective January 1, 2026.

This form allows you to provide consent for Dr. Green and his direct
staff to retain and transfer your medical records to continue your care.
```

**Question 1: Consent Token (Hidden)**
- Type: Short answer
- Pre-fill from URL parameter: `token`
- Hidden from patient view

**Question 2: Primary Consent**
```
Do you consent to Dr. Green and his direct clinical staff retaining
your medical records and transferring them to Home Team Medical Services
for continuity of care?
```
- Type: Choice (Yes / No)
- Required

**Question 3: APCM Transfer (Conditional)**
```
If you are currently enrolled in Medicare's Advanced Primary Care
Management (APCM) program, do you authorize Dr. Green to continue
billing APCM services on your behalf through Home Team Medical Services?
```
- Type: Choice (Yes / No / Not Applicable)
- Show if: Prior APCM enrollment indicated

**Question 4: Southview APCM Revocation (Conditional)**
```
Do you wish to revoke any consent for Southview Medical Group to bill
APCM charges on your behalf after December 31, 2025?
```
- Type: Choice (Yes / No)
- Show if: Question 3 = Yes

**Question 5: Acknowledgment**
```
I understand that this consent is voluntary and that I may withdraw
it at any time by contacting Dr. Green's office.
```
- Type: Checkbox (must check to submit)
- Required

**Question 6: Electronic Signature**
```
By typing your full name below, you are providing your electronic
signature confirming your responses above.
```
- Type: Short answer
- Required

### Task 3: Configure Token Pre-fill
1. Get form's shareable link
2. Add token parameter: `?token={consent_token}`
3. Configure form to capture parameter in hidden field

### Task 4: Test Form Flow
1. Generate test token in Patient Explorer
2. Open form with token in URL
3. Submit test response
4. Verify token captured in responses
5. Export and import to Patient Explorer

### Task 5: Document Form URL
```env
# .env addition
MS_CONSENT_FORM_URL=https://forms.office.com/r/XXXXXXX
```

---

## SMS Template Update

Update SMS templates to use form URL:

```python
# sms_templates.py update
CONSENT_FORM_BASE_URL = os.getenv("MS_CONSENT_FORM_URL")

def get_consent_url(token: str) -> str:
    return f"{CONSENT_FORM_BASE_URL}?token={token}"
```

---

## Response Import

### Manual Import (Initial)
1. Download form responses as Excel
2. Use Consent Response page > Bulk Import
3. Match tokens to patients
4. Update consent status

### Future: API Import
- Use Microsoft Graph API to fetch responses
- Automate import on schedule

---

## Form Sharing

### Internal Testing
- Share form link with staff for testing
- Verify mobile experience

### Production
- Do NOT make form publicly searchable
- Share only via tokenized links
- Consider: Require organization sign-in (optional)

---

## Dependencies

- Microsoft 365 account (under BAA)
- Forms license (included in M365)
- Patient Explorer consent tokens functional

---

## Definition of Done

- [ ] Form created and tested
- [ ] Token parameter working
- [ ] All questions display correctly
- [ ] Mobile-friendly
- [ ] Response import tested
- [ ] SMS template updated with form URL
- [ ] Form URL documented in .env

---

## Security Considerations

- Token is unique per patient - prevents unauthorized submissions
- Form under Microsoft 365 BAA - HIPAA compliant
- Responses stored in SharePoint - encrypted
- Don't include PHI in form questions (token links to PHI)

---

## APCM-Specific Notes

APCM elections needed:
1. **Continue with Home Team** - Patient consents to Dr. Green billing APCM at Home Team
2. **Revoke Southview** - Patient revokes Southview's authority to bill APCM after 12/31

Both are required for clean APCM transfer:
- Without (1): Can't bill at Home Team
- Without (2): Southview may continue billing (conflict)

---

*Created: 2025-12-02*
