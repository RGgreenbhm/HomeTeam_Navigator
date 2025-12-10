# Phase 0B: Consent Outreach Campaign Plan

## Overview

This document outlines the strategy for obtaining patient consent via SMS outreach using Spruce Health, directing patients to a secure consent portal where they can make elections about their medical records and ongoing care.

**Status:** Planning
**Target Start:** December 2025
**Owner:** Robert Green, MD

---

## 1. Campaign Objectives

### Primary Goals
1. **Records Retention Consent**: Obtain documented consent from patients for Dr. Green to maintain access to their medical records after transitioning from Southview
2. **APCM Continuation Elections**: For ~450 patients enrolled in Advanced Primary Care Management (APCM), obtain consent to:
   - Continue APCM services with Dr. Green at Home Team Medical Services
   - Authorize notification to Southview to revoke their billing consent

### Target Populations

| Population | Count | Consent Type | Priority |
|------------|-------|--------------|----------|
| All Spruce-Matched Patients | ~1,195 | Records Retention | High |
| APCM Enrolled Patients | ~450 | APCM Continuation + Records | Critical |
| Non-Spruce Patients | ~188 | Alternative outreach (mail/call) | Medium |

---

## 2. Technical Architecture

### Components

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          CONSENT OUTREACH SYSTEM                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐     ┌──────────────────┐     ┌───────────────────────┐ │
│  │   Spruce    │────▶│  SMS with Link   │────▶│  Secure Consent       │ │
│  │   Health    │     │  (Bulk Notify)   │     │  Portal (Azure)       │ │
│  └─────────────┘     └──────────────────┘     └───────────────────────┘ │
│        │                                              │                  │
│        │                                              ▼                  │
│        │                                    ┌───────────────────────┐   │
│        │                                    │  Patient Elections:   │   │
│        │                                    │  - Records Consent    │   │
│        │                                    │  - APCM Continuation  │   │
│        │                                    │  - Billing Revocation │   │
│        │                                    └───────────────────────┘   │
│        │                                              │                  │
│        ▼                                              ▼                  │
│  ┌─────────────┐                           ┌───────────────────────┐   │
│  │  Streamlit  │◀──────────────────────────│  Webhook/API          │   │
│  │  Dashboard  │     Consent Responses     │  (Updates DB)         │   │
│  └─────────────┘                           └───────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Consent Portal Options

| Option | Pros | Cons | HIPAA Considerations |
|--------|------|------|---------------------|
| **Azure Static Web App + Functions** | Serverless, low cost, HIPAA BAA | Requires Azure setup | Under existing BAA |
| **Microsoft Forms + Power Automate** | No-code, quick to deploy | Limited customization | Under M365 BAA |
| **Typeform + Webhook** | Beautiful UX, fast setup | Needs BAA verification | Verify HIPAA compliance |
| **DocuSign Web Forms** | Legal-grade signatures | Higher cost | HIPAA compliant |
| **Custom Streamlit (Public)** | Full control | Requires hosting setup | Need HIPAA host |

**Recommendation:** Start with **Microsoft Forms** for quick deployment under existing BAA, with upgrade path to custom Azure portal for better tracking.

---

## 3. Spruce Bulk Notification Workflow

### Step 1: Prepare Patient Cohorts

```
Streamlit Dashboard → Export CSV → Spruce Bulk Import
```

Export fields needed:
- Phone number (formatted for Spruce)
- Patient name
- MRN (for tracking)
- APCM status (for message personalization)

### Step 2: Message Templates

#### Template A: General Records Retention (Non-APCM)
```
Hi [FirstName], this is Dr. Robert Green's office.

As you may know, I am transitioning my practice from Southview. To continue
providing you excellent care, I need your consent to maintain your medical
records.

Please visit this secure link to complete your consent:
[CONSENT_LINK]

If you have questions, reply to this message or call [PHONE].

- Dr. Green's Care Team
```

#### Template B: APCM Patients
```
Hi [FirstName], this is Dr. Robert Green's office.

As an Advanced Primary Care Management (APCM) patient, I want to continue
providing your care coordination services after my transition from Southview
to Home Team Medical Services in January 2026.

Please visit this secure link to:
✓ Continue APCM services with Dr. Green at Home Team
✓ Authorize us to notify Southview about your choice
✓ Confirm records retention consent

[CONSENT_LINK]

Questions? Reply here or call [PHONE].

- Dr. Green's Care Team
```

### Step 3: Spruce Bulk Notification Setup

1. **Create Patient List in Spruce**
   - Tag patients: `consent-outreach-dec2025`
   - Separate tags: `apcm-enrolled`, `non-apcm`

2. **Use Spruce Bulk Notifications**
   - Navigate: Settings → Notifications → Bulk Messages
   - Select patient tag
   - Compose message with personalization tokens
   - Schedule send time (recommend: 10am-2pm weekdays)

3. **Track Responses**
   - Spruce timestamps all replies
   - Export conversation data via API for Streamlit dashboard

---

## 4. Secure Consent Portal Design

### URL Structure
```
https://consent.greenclinic.com/[unique-token]
```

Each patient gets a unique link that:
- Identifies them without requiring login
- Expires after 30 days
- Can only be used once (prevent forwarding)

### Portal Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PATIENT CONSENT PORTAL                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Page 1: Welcome & Verification                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  "Welcome, [Patient Name]"                               │   │
│  │                                                          │   │
│  │  Please verify your date of birth to continue:           │   │
│  │  [  DOB Input  ]                                         │   │
│  │                                                          │   │
│  │  [Continue →]                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Page 2: Practice Transition Information                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  "Important Update About Your Care"                      │   │
│  │                                                          │   │
│  │  [Video or infographic about Dr. Green's transition]     │   │
│  │                                                          │   │
│  │  Key points:                                             │   │
│  │  • Dr. Green is moving to Home Team Medical Services     │   │
│  │  • Your care continuity is our priority                  │   │
│  │  • You have choices about your records and care          │   │
│  │                                                          │   │
│  │  [I Understand, Continue →]                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Page 3: Consent Elections                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  "Your Choices"                                          │   │
│  │                                                          │   │
│  │  ☐ I consent to Dr. Green maintaining access to my      │   │
│  │    medical records for continuity of care                │   │
│  │                                                          │   │
│  │  [If APCM patient, show additional options:]            │   │
│  │                                                          │   │
│  │  ☐ I want to CONTINUE my APCM care coordination         │   │
│  │    services with Dr. Green at Home Team                  │   │
│  │                                                          │   │
│  │  ☐ I authorize Dr. Green's office to notify Southview   │   │
│  │    that I no longer consent to APCM billing there        │   │
│  │                                                          │   │
│  │  [Submit My Choices]                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Page 4: Confirmation                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ✓ Thank you! Your choices have been recorded.           │   │
│  │                                                          │   │
│  │  Confirmation #: [UNIQUE_ID]                             │   │
│  │  Date/Time: [TIMESTAMP]                                  │   │
│  │                                                          │   │
│  │  A copy has been sent to your phone.                     │   │
│  │                                                          │   │
│  │  Questions? Call us at [PHONE]                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Model Updates

### New Fields for Patient Table

```python
# app/database/models.py additions

class Patient(Base):
    # ... existing fields ...

    # APCM Status
    apcm_enrolled = Column(Boolean, default=False)
    apcm_enrollment_date = Column(DateTime)
    apcm_authorization_number = Column(String(50))

    # Consent Portal
    consent_token = Column(String(100), unique=True)  # Unique link token
    consent_token_expires = Column(DateTime)
    consent_portal_visited = Column(DateTime)

    # APCM Elections (for APCM patients)
    apcm_continue_with_hometeam = Column(Boolean)
    apcm_revoke_southview_billing = Column(Boolean)
    apcm_election_date = Column(DateTime)
```

### Consent Status Expansion

```python
class ConsentStatus(enum.Enum):
    PENDING = "pending"
    INVITATION_SENT = "invitation_sent"
    PORTAL_VISITED = "portal_visited"
    CONSENTED = "consented"
    DECLINED = "declined"
    NO_RESPONSE = "no_response"
    PARTIAL = "partial"  # Some elections made but not all
```

---

## 6. Streamlit Dashboard Enhancements

### New Pages Needed

1. **APCM Patient Management** (`pages/3_APCM_Patients.py`)
   - Import APCM patient list from Excel
   - Track APCM-specific consent elections
   - Export list for Spruce bulk messaging

2. **Outreach Campaign** (`pages/4_Outreach_Campaign.py`)
   - Generate unique consent links per patient
   - Track link clicks and completions
   - Export phone lists for Spruce

3. **Consent Analytics** (`pages/5_Consent_Analytics.py`)
   - Real-time consent rate dashboard
   - APCM vs non-APCM breakdown
   - Timeline of responses

---

## 7. Implementation Phases

### Phase 0B-1: Quick Start (Week 1)
- [ ] Create Microsoft Form for consent
- [ ] Generate unique tokens for patients in Streamlit
- [ ] Build URL generator that embeds token in Form URL
- [ ] Test Spruce bulk notification with 10 patients
- [ ] Track responses manually in Streamlit

### Phase 0B-2: Automation (Week 2-3)
- [ ] Build Power Automate flow: Form submission → Update Streamlit DB
- [ ] Add APCM patient import from Excel
- [ ] Create APCM-specific consent form variant
- [ ] Automate Spruce export from Streamlit

### Phase 0B-3: Custom Portal (Week 4+)
- [ ] Deploy Azure Static Web App for consent portal
- [ ] Implement DOB verification
- [ ] Add webhook to update Streamlit database
- [ ] Add consent confirmation SMS via Spruce

---

## 8. Compliance Considerations

### HIPAA Requirements
- [ ] All patient data transmitted over HTTPS/TLS
- [ ] Consent portal under BAA (Microsoft, Azure)
- [ ] Audit log of all consent submissions
- [ ] Unique tokens prevent unauthorized access
- [ ] DOB verification adds identity confirmation layer

### Legal Documentation
- [ ] Consent language reviewed by attorney
- [ ] Separate consent for records vs. APCM billing
- [ ] Timestamped electronic consent is legally valid
- [ ] Confirmation sent to patient as receipt

### Record Retention
- [ ] Store all consent responses in SQLite database
- [ ] Backup to Azure Blob Storage
- [ ] Maintain for HIPAA-required retention period (6 years)

---

## 9. Success Metrics

| Metric | Target | Tracking Method |
|--------|--------|-----------------|
| SMS Delivery Rate | >95% | Spruce delivery reports |
| Portal Click-Through | >50% | Token URL analytics |
| Records Consent Rate | >80% | Streamlit dashboard |
| APCM Continuation Rate | >90% | Streamlit dashboard |
| Response Time (median) | <48 hours | Timestamp analysis |
| No-Response Follow-up | 100% after 7 days | Automated reminder |

---

## 10. Message Timing Strategy

### Initial Outreach Wave 1 (Week 1)
- APCM patients first (highest priority)
- Send Tuesday-Thursday, 10am-2pm
- 100 patients per day max (Spruce limits)

### Outreach Wave 2 (Week 2)
- Non-APCM Spruce-matched patients
- Same timing strategy
- Skip patients who already responded

### Follow-up Reminders
- Day 3: Gentle reminder to non-responders
- Day 7: Second reminder with urgency
- Day 14: Final reminder before phone outreach

### Non-Spruce Patients
- Mail physical consent forms
- Phone call follow-up
- DocuSign for those with email

---

## Next Steps

1. **Immediate**: Upload APCM patient Excel file
2. **This Week**: Draft consent form language for legal review
3. **This Week**: Test Spruce bulk notification with small batch
4. **Next Week**: Build consent portal (Microsoft Forms or custom)
5. **Ongoing**: Monitor consent rates and adjust messaging

---

*Document created: November 30, 2025*
*Last updated: November 30, 2025*
