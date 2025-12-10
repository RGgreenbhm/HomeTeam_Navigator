# Medicare Advanced Primary Care Management (APCM) Compliance Guide

**Home Team Medical Services**  
*Primary Care that Comes to You*

**Document Date**: November 30, 2025  
**Effective Date**: CY 2024 (effective January 1, 2024)  
**Author**: Dr. Robert Green, MD  
**Purpose**: Medicare Audit Compliance & Team Workflow Reference

---

## Executive Summary

Advanced Primary Care Management (APCM) is a Medicare payment model finalized in the CY 2024 Physician Fee Schedule that recognizes the comprehensive, longitudinal care coordination services provided by primary care practices. This guide documents the compliance requirements for Home Team Medical Services to ensure proper billing, documentation, and audit readiness.

**Key Takeaway**: APCM services must be documented monthly, require explicit patient consent, and demand a comprehensive care plan addressing chronic conditions.

---

## Table of Contents

1. [APCM Code Definitions](#1-apcm-code-definitions)
2. [Patient Eligibility Requirements](#2-patient-eligibility-requirements)
3. [Consent Requirements](#3-consent-requirements)
4. [Care Plan Requirements](#4-care-plan-requirements)
5. [Monthly Service Documentation](#5-monthly-service-documentation)
6. [Billing & Coding Guidelines](#6-billing--coding-guidelines)
7. [Medicare Audit Checklist](#7-medicare-audit-checklist)
8. [Team Roles & Responsibilities](#8-team-roles--responsibilities)
9. [Appendix: Home Team APCM Workflow](#appendix-home-team-apcm-workflow)

---

## 1. APCM Code Definitions

APCM services are billed using three HCPCS G-codes based on patient complexity:

| Code | Description | Qualifying Conditions | 2024 Payment* |
|------|-------------|----------------------|---------------|
| **G0556** | APCM services for single high-risk condition | 1 chronic condition expected to last ≥12 months placing patient at significant risk | ~$67/month |
| **G0557** | APCM services for multiple high-risk conditions | 2+ chronic conditions expected to last ≥12 months placing patient at significant risk | ~$128/month |
| **G0558** | APCM services for multiple conditions (QMB) | 2+ chronic conditions in Qualified Medicare Beneficiary; no beneficiary cost-sharing | ~$128/month |

*Payment rates are approximate and subject to geographic adjustments and annual updates.

### Code Selection Logic

```
IF patient has QMB status AND 2+ qualifying chronic conditions:
    → Bill G0558 (no patient copay)
ELSE IF patient has 2+ qualifying chronic conditions:
    → Bill G0557
ELSE IF patient has 1 qualifying chronic condition:
    → Bill G0556
```

### Home Team Database Mapping

Per our `app/database/models.py`, APCM levels map as follows:
- `APCMLevel.LEVEL_1` = G0556 (1 DX)
- `APCMLevel.LEVEL_2` = G0557 (2+ DX)
- `APCMLevel.LEVEL_3` = G0558 (QMB with 2+ DX)

---

## 2. Patient Eligibility Requirements

### Inclusion Criteria

To be eligible for APCM services, a Medicare beneficiary must meet ALL of the following:

1. **Enrolled in Medicare Part B** (traditional Medicare; not Medicare Advantage unless specified)

2. **Established Patient Relationship**: 
   - Has had at least one evaluation and management (E/M) visit within the prior 12 months with the billing practitioner or their practice

3. **Chronic Condition(s)**:
   - Has at least ONE chronic condition expected to last 12 months or until death
   - Condition must place the patient at significant risk of death, acute exacerbation, or functional decline

4. **Designated Practitioner**: 
   - Patient has designated (or been assigned by CMS) a single practitioner to furnish APCM services
   - Only ONE practitioner may bill APCM for a patient in any given calendar month

5. **Consent Obtained**: 
   - Written or verbal consent documented in medical record (see Section 3)

### Qualifying Chronic Conditions (Examples)

The following conditions commonly qualify for APCM (ICD-10 codes should be documented):

| Category | Example Conditions | ICD-10 Examples |
|----------|-------------------|-----------------|
| **Cardiovascular** | Hypertension, Heart Failure, CAD, Atrial Fibrillation | I10, I50.x, I25.x, I48.x |
| **Metabolic** | Diabetes Mellitus (Type 1 or 2), Hyperlipidemia, Obesity | E10.x, E11.x, E78.x, E66.x |
| **Respiratory** | COPD, Chronic Asthma | J44.x, J45.x |
| **Renal** | Chronic Kidney Disease (Stage 3-5) | N18.x |
| **Neurological** | Dementia, Parkinson's Disease, CVA sequelae | F03.x, G20, I69.x |
| **Mental Health** | Major Depression, Anxiety Disorders | F32.x, F33.x, F41.x |
| **Musculoskeletal** | Rheumatoid Arthritis, Osteoarthritis | M05.x, M06.x, M15-M19 |

### Exclusion Criteria

Do NOT bill APCM for patients who:
- Are enrolled in Medicare Advantage (unless practice has separate MA contract)
- Are receiving hospice care (Medicare Part A hospice benefit)
- Are not established patients of the practice
- Have not provided consent
- Are already receiving APCM from another practitioner

---

## 3. Consent Requirements

### ⚠️ CRITICAL: Patient Consent is Required Before Billing

**Consent must be obtained BEFORE the first APCM claim is submitted.**

### Required Consent Elements

Patient consent (verbal or written) must include acknowledgment of the following:

| Element | Patient Must Understand |
|---------|------------------------|
| **Services Provided** | Description of APCM care coordination services they will receive |
| **Single Practitioner** | Only one practitioner may bill APCM for them at a time |
| **Cost-Sharing** | For G0556/G0557: Patient may have copay/coinsurance obligations; For G0558: No cost-sharing |
| **Right to Decline** | Patient may discontinue APCM services at any time |
| **Information Sharing** | Consent to share relevant health information with other treating providers |

### Documentation Requirements

**In the medical record, document:**

1. Date consent was obtained
2. Method of consent (verbal or written)
3. Name of staff member who obtained consent
4. Patient's (or authorized representative's) acknowledgment of the required elements

### Sample Consent Documentation

```
APCM CONSENT DOCUMENTATION
Date: [DATE]
Patient: [NAME] (MRN: [MRN])
Consent Method: ☐ Verbal  ☐ Written

The patient (or authorized representative) was informed of and acknowledged:
- The Advanced Primary Care Management services that will be provided
- That only one practitioner may bill Medicare for these services at a time
- The potential cost-sharing obligations (G0556/G0557) OR that there is no 
  cost-sharing (G0558/QMB)
- The right to discontinue services at any time
- Consent to share health information with treating providers

Consent Obtained By: [Staff Name], [Title]
Patient/Representative Signature (if written): _______________
```

### Home Team Workflow Integration

Per our database schema (`app/database/models.py`), track:
- `consent_status`: Enum tracking consent workflow status
- `apcm_continue_ht`: Boolean for APCM continuation with Home Team
- `apcm_revoke_sv`: Boolean for authorization to revoke Southview billing

---

## 4. Care Plan Requirements

### ⚠️ AUDIT REQUIREMENT: Comprehensive Care Plan Must Exist

A **written, comprehensive care management plan** must be established and maintained in the medical record.

### Required Care Plan Elements

| Element | Description | Documentation Location |
|---------|-------------|------------------------|
| **Problem List** | All conditions being managed, with ICD-10 codes | EHR Problem List |
| **Treatment Goals** | Patient-centered goals for each condition | Care Plan Note |
| **Symptom Management** | Plan for managing symptoms and preventing exacerbations | Care Plan Note |
| **Medications** | Current medication list with management notes | EHR Medication List |
| **Community/Social Services** | Referrals to community resources as needed | Care Plan Note |
| **Care Team** | List of practitioners involved in patient's care | Care Plan Note |
| **Scheduled Services** | Planned appointments, labs, imaging, referrals | Care Plan Note |
| **Advance Care Planning** | ACP discussion status, advance directives on file | Care Plan Note |

### Care Plan Template

```markdown
# APCM CARE MANAGEMENT PLAN
Patient: [Name]                    MRN: [MRN]
Date Created: [DATE]               Last Updated: [DATE]
APCM Level: ☐ G0556 (1 DX)  ☐ G0557 (2+ DX)  ☐ G0558 (QMB)

## Active Chronic Conditions (Qualifying)
1. [Condition] - ICD-10: [Code] - Status: [Stable/Unstable]
2. [Condition] - ICD-10: [Code] - Status: [Stable/Unstable]

## Patient-Centered Goals
1. [Goal with measurable outcome]
2. [Goal with measurable outcome]

## Current Medications
[Medication list or reference to EHR medication list]

## Symptom Management Plan
[Description of symptom monitoring and intervention plan]

## Care Team
- PCP: [Name, credentials]
- Attending Physician: [Name, MD]
- Specialists: [List]
- Other care team members: [List]

## Scheduled Services (Next 30 days)
- [Scheduled appointments, labs, referrals]

## Community/Social Services
- [Referrals to community resources, transportation, meals, etc.]

## Advance Care Planning
- ACP Discussion: ☐ Completed  ☐ Pending  ☐ Patient declined
- Advance Directive on File: ☐ Yes  ☐ No
- Healthcare Proxy: [Name if applicable]
```

---

## 5. Monthly Service Documentation

### ⚠️ AUDIT REQUIREMENT: Services Must Be Documented Each Month Billed

APCM is billed monthly. For each month a claim is submitted, documentation must support that care management services were provided.

### Minimum Monthly Activities

The following activities should be documented monthly to support APCM billing:

| Activity | Description | Required? |
|----------|-------------|-----------|
| **Care Plan Review** | Review/update comprehensive care plan | Yes |
| **Medication Reconciliation** | Review current medications, assess adherence | Yes |
| **Care Coordination** | Communicate with other providers, manage transitions | As needed |
| **Patient/Caregiver Communication** | Phone, secure message, or in-person contact | Recommended |
| **Health Status Assessment** | Assess current symptoms, functional status | Recommended |
| **Care Plan Modification** | Update plan based on changes in health status | As needed |

### Documentation Format

For each calendar month, create a progress note documenting APCM activities:

```markdown
# APCM MONTHLY PROGRESS NOTE
Patient: [Name]                    MRN: [MRN]
Service Month: [Month/Year]        APCM Code: [G0556/G0557/G0558]
Billing Provider: [Name, credentials]

## Care Plan Review
- Care plan reviewed on [DATE]
- Changes: [None / Describe changes]

## Medication Reconciliation
- Medications reviewed on [DATE]
- Total active medications: [#]
- Changes: [None / Describe changes]
- Adherence concerns: [None / Describe]

## Care Coordination Activities
- [Describe communications with other providers, referrals, etc.]

## Patient/Caregiver Contact
- Contact type: ☐ Phone  ☐ Secure Message  ☐ In-Person  ☐ Other
- Date: [DATE]
- Summary: [Brief summary of communication]

## Health Status
- Current status: ☐ Stable  ☐ Improved  ☐ Declined
- Symptoms: [Active symptoms or "No active symptoms"]
- Functional status: [Any changes noted]

## Plan for Next Month
- [Scheduled appointments, pending referrals, goals]

Documented By: [Staff Name, Title]
Date: [DATE]
Supervising Practitioner: [Name, credentials]
```

### Time Tracking (Optional but Recommended)

While APCM does not have a minimum time requirement like some other care management codes (e.g., CCM requires 20+ minutes), tracking time spent can support audit defense:

- Document approximate time spent on APCM activities
- Include clinical staff and practitioner time separately
- Note that APCM is designed to recognize ongoing, longitudinal care coordination

---

## 6. Billing & Coding Guidelines

### Billing Rules

| Rule | Requirement |
|------|-------------|
| **Frequency** | Once per calendar month per patient |
| **Who May Bill** | Physicians (MD/DO), NPs, PAs, CNSs, CNMs |
| **Place of Service** | Any setting; commonly office (11) or home (12) |
| **Supervision** | General supervision for auxiliary personnel |
| **Incident-To** | Clinical staff may perform services incident-to the billing practitioner |

### Modifier Requirements

| Modifier | When Required |
|----------|---------------|
| **None typically required** | Standard APCM billing |
| **-95 (Synchronous Telehealth)** | If applicable telehealth services included |

### Claims Submission

- **Submit monthly**: Claims may be submitted at the end of each calendar month
- **ICD-10 Codes**: Include all qualifying chronic condition ICD-10 codes on the claim
- **NPI**: Bill under the NPI of the practitioner furnishing/supervising APCM services

### Avoiding Duplicate Billing

APCM may **NOT** be billed in the same month as certain other services:

| Service | Conflict Rule |
|---------|--------------|
| **CCM (99490, 99491, etc.)** | Cannot bill both in same month |
| **PCM (99426, 99427)** | Cannot bill both in same month |
| **TCM (99495, 99496)** | Can bill TCM; APCM starts after TCM period |
| **BHI (99484)** | Can bill both if distinct services |
| **E/M Visits** | Can bill E/M visits in addition to APCM |

---

## 7. Medicare Audit Checklist

### ⚠️ CRITICAL: Use This Checklist for Audit Readiness

For each APCM patient/month billed, ensure the following documentation exists:

#### Patient Eligibility ✓

- [ ] Patient is enrolled in Medicare Part B
- [ ] Patient had E/M visit with practice within prior 12 months
- [ ] At least one qualifying chronic condition documented (ICD-10)
- [ ] Patient designated this practice/practitioner for APCM
- [ ] Patient is not enrolled in hospice
- [ ] Patient is not receiving APCM from another practitioner

#### Consent ✓

- [ ] Consent obtained BEFORE first claim submission
- [ ] Consent date documented
- [ ] Consent method documented (verbal or written)
- [ ] All required consent elements acknowledged
- [ ] Staff member who obtained consent documented

#### Care Plan ✓

- [ ] Comprehensive written care plan exists
- [ ] Problem list with ICD-10 codes included
- [ ] Patient-centered treatment goals documented
- [ ] Medication list current
- [ ] Care team identified
- [ ] Care plan dated and updated within past 12 months

#### Monthly Documentation ✓

- [ ] APCM progress note exists for billed month
- [ ] Care plan review documented
- [ ] Medication reconciliation documented
- [ ] Care coordination activities noted (if any)
- [ ] Patient/caregiver contact noted (if any)
- [ ] Billing practitioner identified
- [ ] Date of service within billed month

#### Billing Accuracy ✓

- [ ] Correct APCM code selected (G0556/G0557/G0558)
- [ ] Qualifying ICD-10 codes on claim match documentation
- [ ] No duplicate billing for CCM/PCM in same month
- [ ] Only one APCM claim per patient per month
- [ ] Claim submitted under correct billing NPI

---

## 8. Team Roles & Responsibilities

### Home Team Medical Services APCM Team Structure

Per our practice model, APCM services involve the following team members:

| Role | Team Member(s) | APCM Responsibilities |
|------|---------------|----------------------|
| **Attending Physician** | Robert Green, MD | Overall supervision, care plan approval, complex case review, audit compliance |
| **Primary Care Provider (PCP)** | LaChandra Watts, CRNP; Lindsay Bearden, CRNP | Patient visits, care plan creation/updates, medication management, billing provider |
| **Primary Care Nurse** | Jenny Linard, RN | Care coordination, patient outreach, medication reconciliation, documentation |
| **Administrative Support** | [TBD] | Consent tracking, claims submission, eligibility verification |

### Supervision Requirements

- **General Supervision**: The billing practitioner does not need to be physically present when clinical staff perform APCM activities
- **Incident-To**: Clinical staff activities count toward APCM when performed under the general supervision of the billing practitioner
- **Documentation**: Clinical staff may document services; supervising practitioner must be identified

### Monthly APCM Workflow by Role

#### Clinical Staff (RN/MA)
1. Generate list of APCM patients at start of month
2. Review upcoming appointments and care needs
3. Conduct outreach calls/messages as needed
4. Perform medication reconciliation
5. Coordinate referrals and care transitions
6. Document activities in APCM monthly note
7. Flag complex cases for PCP/Attending review

#### Primary Care Provider (NP/PA)
1. Review flagged complex cases
2. Update care plans based on changes in health status
3. Address urgent clinical needs
4. Supervise clinical staff activities
5. Approve/co-sign monthly documentation
6. Bill APCM under their NPI

#### Attending Physician (MD)
1. Provide oversight and consultation on complex cases
2. Review APCM program compliance monthly
3. Address quality/audit concerns
4. Support care team with specialist coordination

---

## Appendix: Home Team APCM Workflow

### Monthly APCM Cycle

```
Day 1-5: Generate monthly APCM patient list
         Verify eligibility for each patient
         Export from Patient_Explorer APCM Patients page

Day 1-15: Clinical staff outreach
          - Review care plans
          - Medication reconciliation
          - Patient/caregiver contact
          - Care coordination activities

Day 15-25: PCP review
           - Update care plans as needed
           - Address clinical issues
           - Review documentation

Day 25-30: Documentation finalization
           - Complete APCM monthly notes
           - PCP co-signature/approval
           - Ready for billing submission

Day 30+: Claims submission
         - Submit APCM claims for month
         - Track for denials/issues
```

### Integration with Patient_Explorer

Our Patient_Explorer application (`app/pages/3_APCM_Patients.py`) supports APCM workflow:

- **Patient List**: View all APCM-enrolled patients with level (G0556/G0557/G0558)
- **Status Tracking**: Track consent status, Spruce match, outreach status
- **Consent Elections**: Record APCM continuation and authorization elections
- **Export**: Generate lists for Spruce bulk SMS outreach

### Documentation Storage

| Document Type | Storage Location |
|--------------|------------------|
| Care Plans | athenahealth EHR |
| APCM Monthly Notes | athenahealth EHR |
| Consent Documentation | athenahealth EHR + Patient_Explorer |
| Patient Lists | Patient_Explorer (local encrypted database) |
| Billing Claims | athenahealth Practice Management |

---

## References & Resources

### Official CMS Sources

- CMS CY 2024 Physician Fee Schedule Final Rule (November 2023)
- Medicare Learning Network (MLN) Matters Articles
- Medicare Administrative Contractor (MAC) Local Coverage Articles
  - For Alabama: Palmetto GBA (Jurisdiction J)

### Internal References

- `CLAUDE.md` - Project documentation and HIPAA guidelines
- `app/database/models.py` - APCM data model definitions
- `docs/phase0b-consent-outreach-plan.md` - Consent campaign documentation

### Recommended Actions

1. **Verify with MAC**: Confirm requirements with Palmetto GBA for Alabama-specific guidance
2. **Legal Review**: Have compliance counsel review consent documentation
3. **Staff Training**: Train all team members on APCM documentation requirements
4. **Audit Readiness**: Conduct internal audit of APCM documentation quarterly

---

**Document Version**: 1.0  
**Last Updated**: November 30, 2025  
**Next Review**: January 2026 (after CY 2025 fee schedule updates)

---

*This document is for internal use by Home Team Medical Services and is intended as operational guidance. It does not constitute legal or regulatory advice. Always verify requirements with official CMS sources and your Medicare Administrative Contractor.*
