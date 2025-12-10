# Microsoft Forms Consent Form - FINAL DRAFT

**Document Status:** APPROVED - Ready for Implementation
**Created:** December 1, 2025
**Updated:** December 2, 2025
**Owner:** Robert Green, MD
**Legal Review:** Susan Doughton - Approved

---

## Form Overview

**Form Title:** Dr. Green's Practice Transition - Patient Consent Form
**Form URL:** https://forms.office.com/r/dwMVMk3ZP9
**QR Code:** `..Workspace_Reference/` (PNG file)
**Purpose:** Collect patient consent for records retention and APCM continuation elections

---

## Form Structure

### Page 1: Welcome & Verification

**Header:**
> **Important Information About Your Care**
> Dr. Robert Green's Practice Transition

**Introduction Text:**
> Dear Patient,
>
> Dr. Robert Green is transitioning his practice from **Southview Medical Group** to **Home Team Medical Services**, effective **January 1, 2026**.
>
> To ensure continuity of your care, we need your consent regarding your medical records and ongoing services.
>
> This form takes about 2 minutes to complete.

**Your Reference Token:**
- Field Name: `token`
- Type: Text (short answer)
- Required: Yes
- Help text: "Enter the token from your text message link (16 characters)"

**Identity Verification:**
> To verify your identity, please enter your date of birth:
- Field: Date of Birth
- Type: Date picker
- Required: Yes
- Help text: "Format: MM/DD/YYYY"

---

### Page 2: Records Retention Consent

**Section Header:**
> **Medical Records Consent**

**Explanation Text:**
> Your medical records contain important information about your health history, medications, test results, and treatment plans. To continue providing you with excellent care, Dr. Green needs your consent to maintain access to these records at Home Team Medical Services.
>
> **What this means:**
> - Dr. Green's team will retain a copy of your medical records
> - Your records will be stored securely and remain confidential
> - You can request a copy of your records at any time
> - This consent can be revoked by contacting our office in writing

**Consent Question 1 (Required):**
> I consent to Dr. Robert Green, MD and his direct clinical staff at Home Team Medical Services to access, retain, and maintain copies of my medical records for the purpose of continuity of care following the transition from Southview Medical Group.

- Type: Multiple choice (Required)
- Options:
  - ☑ **Yes, I consent** - I want Dr. Green to maintain my medical records
  - ☐ **No, I do not consent** - I understand this may affect continuity of my care

---

### Page 3: APCM Patients Only

**Note:** This page should be shown to ALL patients. APCM patients will answer; non-APCM patients can select "Not Applicable."

**Section Header:**
> **Advanced Primary Care Management (APCM) Elections**

**Explanation Text:**
> If you are currently enrolled in Advanced Primary Care Management (APCM), this section allows you to make elections about continuing these services with Dr. Green at Home Team Medical Services.
>
> APCM provides enhanced care coordination services including:
> - Proactive health monitoring
> - Care team coordination
> - Personalized care planning
> - Priority access to your care team

**APCM Question 1 (Required):**
> Do you want to **continue** your APCM care coordination services with Dr. Green at Home Team Medical Services?

- Type: Multiple choice (Required)
- Options:
  - ☑ **Yes, continue APCM** - I want to continue receiving APCM services with Dr. Green at Home Team
  - ☐ **No, discontinue APCM** - I do not wish to continue APCM services with Dr. Green
  - ☐ **Not Applicable** - I am not currently enrolled in APCM

**APCM Question 2 (Required if Yes to Q1):**
> Do you authorize Dr. Green's office to notify Southview Medical Group that you are transferring your APCM consent to Home Team Medical Services?
>
> *This means Southview Medical Group will no longer bill Medicare for APCM services on your behalf after December 31, 2025. This prevents duplicate billing and ensures your APCM benefits transfer properly.*

- Type: Multiple choice (Required)
- Options:
  - ☑ **Yes, notify Southview** - I authorize notification to transfer my APCM consent
  - ☐ **No, do not notify** - I will handle this separately
  - ☐ **Not Applicable** - I selected "No" or "Not Applicable" above

---

### Page 4: Electronic Signature & Confirmation

**Section Header:**
> **Your Signature**

**Explanation Text:**
> Please confirm your identity and consent by providing the information below.

**Full Legal Name (Required):**
> Please type your full legal name as it appears on your insurance card:
- Type: Text (short answer)
- Required: Yes

**Date of Birth Confirmation (Required):**
> Please confirm your date of birth:
- Type: Date picker
- Required: Yes

**Today's Date:**
> Today's Date:
- Type: Date picker
- Required: Yes
- Default: Current date

**Electronic Signature Agreement (Required):**
> ☐ **I understand and agree** that by typing my name above, I am providing my electronic signature, which is the legal equivalent of my handwritten signature for the purposes of this consent form. I understand that a copy of this completed form will be retained by Home Team Medical Services and posted to my medical chart at Southview Medical Group for standard compliance documentation.

- Type: Checkbox (Required - must be checked to submit)

---

### Page 5: Confirmation (After Submit)

**Thank You Message:**
> ## Thank You!
>
> Your consent has been recorded.
>
> **Confirmation Number:** [Auto-generated by Forms]
> **Date/Time:** [Timestamp]
>
> A copy of your responses will be sent to you via text message.
>
> **Questions?**
> - **Phone:** (205) 955-7605
> - **Email:** info@hometeammed.com
> - **Text:** Reply to the message you received
>
> We look forward to continuing to care for you at Home Team Medical Services.
>
> *— Dr. Green's Care Team*

---

## Microsoft Forms Setup Instructions

### Step 1: Create the Form
1. Go to https://forms.microsoft.com
2. Sign in with your Microsoft 365 account
3. Click "New Form"
4. Title: "Dr. Green's Practice Transition - Patient Consent Form"

### Step 2: Add Questions
Copy the questions exactly as shown above. For each:
- Set Required = Yes where indicated
- Add Help text where shown
- Use the exact wording for legal compliance

### Step 3: Configure Settings
1. Click ⚙️ Settings
2. Set "Who can fill out this form" = **Anyone can respond**
3. Set "Record name" = **No** (we verify via DOB)
4. Set "One response per person" = **No** (allow corrections)
5. Enable "Get email notification of each response" = **Yes**

### Step 4: Get the Shareable Link
1. Click "Collect responses"
2. Select "Anyone can respond"
3. Copy the link (format: `https://forms.microsoft.com/r/XXXXXXX`)
4. Paste into Streamlit Outreach Campaign sidebar

### Step 5: Test
1. Open the link in an incognito/private browser
2. Complete the form with test data
3. Verify response appears in Forms
4. Export to Excel to confirm all fields captured

---

## Data Mapping to Streamlit

| Form Field | Database Field | Notes |
|------------|----------------|-------|
| Token | Patient.consent_token | Lookup patient by token |
| DOB | Patient.date_of_birth | Verify identity |
| Records Consent | Consent.status | CONSENTED or DECLINED |
| APCM Continue | Patient.apcm_continue_with_hometeam | Boolean |
| Southview Notify | Patient.apcm_revoke_southview_billing | Boolean |
| Full Name | Audit trail | For records |
| Timestamp | Consent.response_date | Auto-captured |

---

## Legal Compliance Notes

**Electronic Signature Statement:**
The form includes explicit acknowledgment that typing their name constitutes an electronic signature with legal equivalence to a handwritten signature.

**Documentation Retention:**
The form states that responses will be:
1. Retained by Home Team Medical Services
2. Posted to patient's Southview chart for compliance

**HIPAA Compliance:**
- Form is on Microsoft 365 under existing BAA
- No PHI displayed on form (patient enters DOB for verification)
- Token system prevents enumeration attacks

**Legal Review:**
Susan Doughton has reviewed and approved this consent language as sufficient for the practice transition.

---

## Sample Consent Language Summary

### Records Retention Consent
> "I consent to Dr. Robert Green, MD and his direct clinical staff at Home Team Medical Services to access, retain, and maintain copies of my medical records for the purpose of continuity of care following the transition from Southview Medical Group."

### APCM Continuation Consent
> "I elect to continue my enrollment in the Advanced Primary Care Management (APCM) program with Dr. Robert Green, MD at Home Team Medical Services."

### Southview Billing Transfer Authorization
> "I authorize Dr. Green's office to notify Southview Medical Group that I am transferring my APCM consent to Home Team Medical Services. This means Southview Medical Group will no longer bill Medicare for APCM services on my behalf after December 31, 2025."

### Electronic Signature Acknowledgment
> "I understand and agree that by typing my name above, I am providing my electronic signature, which is the legal equivalent of my handwritten signature for the purposes of this consent form. I understand that a copy of this completed form will be retained by Home Team Medical Services and posted to my medical chart at Southview Medical Group for standard compliance documentation."

---

*Document finalized: December 2, 2025*
*Legal review: Susan Doughton - Approved*
*Ready for implementation in Microsoft Forms*
