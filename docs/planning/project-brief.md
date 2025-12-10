# Project Brief: Patient_Explorer

**Status:** Greenfield Development / Phase 1
**Owner:** Robert Green, MD
**Organization:** Green Clinic (Southview Patients)
**Created:** November 29, 2025
**Last Updated:** November 29, 2025

---

## Executive Summary

**Patient_Explorer** is a HIPAA-compliant patient data aggregation and consent management system designed to enable Dr. Robert Green and his Green Clinic care team to capture, organize, and preserve critical patient clinical data during the urgent transition from Allscripts EMR (access ending 12/31/2025) to a future EMR system. The tool combines screenshot/document capture with OCR, consent tracking with multiple verification methods (written, text message timestamp, DocuSign), AI-powered Spruce Health communication parsing, and on-demand care plan generation following a structured APCM-compliant format.

**Primary Problem:** With only ~30 days of remaining Allscripts access, years of curated patient timeline data (diagnosis-specific histories with treatment decisions and outcomes for 1,384 Southview patients) will be permanently lost without immediate action. Simultaneously, consent must be obtained from patients to legally retain their records post-transition, including special APCM billing authorization transfers from Southview to Home Team Medical Services.

**Target Users:** Dr. Robert Green (STL), LaChandra Watts CRNP (PCP), Lindsay Bearden CRNP (PCP), Jenny Linard RN (PCN), and future support staff at Green Clinic.

**Key Value Proposition:** Prevent catastrophic data loss while legally managing patient consent, enabling continuity of care during practice transition through offline-first local storage with Azure cloud sync, all within Green Clinic's isolated HIPAA-compliant Microsoft tenant.

---

## Problem Statement

### Current State & Pain Points

Dr. Robert Green has **~30 days of Allscripts EMR access remaining** (through 12/31/2025) before Southview Clinic's acquisition by UAB Health System severs his access permanently. For years, he has meticulously curated **diagnosis-specific timeline data** in Allscripts using a structured format:

```
-- mm/dd/yyyy: [clinical values] --> [action plan changes]
```

**Examples:**
- **Diabetes**: `-- 11/15/2024: A1c 7.2%, glucose 145, on Metformin 1000mg BID --> increase to Metformin 1000mg TID, recheck A1c in 3 months`
- **Hypertension**: `-- 10/22/2024: BP 142/88, on Lisinopril 10mg daily --> increase to Lisinopril 20mg daily`
- **Thyroid**: `-- 09/10/2024: TSH 4.8, fT4 0.9, on Levothyroxine 75mcg --> increase to 88mcg, recheck in 6 weeks`

This timeline data represents **irreplaceable clinical decision-making history** for ~1,384 patients across multiple chronic conditions (diabetes, hypertension, thyroid disorders, hyperlipidemia, etc.).

**Additional Critical Data Sources:**
1. **OneNote Notebooks** (Sharepoint): Dr. Green has been printing Allscripts worksheets to OneNote for over a year. These notebooks contain OCR-indexed problem lists with nested comments per diagnosis and are stored on Green Clinic's SharePoint drive.

2. **Excel Patient List**: 1,384 Southview patients with columns: MRN (account #), DOB, Patient Name, Address, City, State, Zip, Last Date of Service, Email, Home Phone, Cell Phone.

3. **Spruce Health Communications**: All patient/family communications are in Spruce (owned separately by Dr. Green, survives the transition). Spruce contains patient contact information, consent conversations, and clinical communications - but patient identity within conversations is ambiguous when family members speak for multiple patients.

### Impact of the Problem

**Data Loss Impact:**
- **1,384 patients** at risk of losing curated timeline histories
- **~450 APCM-enrolled patients** have complex care plans at risk
- **Estimated 5-10 years** of clinical timeline data per patient could be lost
- **Irreplaceable clinical context** for treatment decisions and outcomes
- **Continuity of care disruption** for patients transitioning to Green Clinic/Home Team

**Legal/Compliance Impact:**
- **Consent required** from each patient to legally retain records post-transition
- **APCM billing authorization** must transfer from Southview TIN to Home Team TIN
- **HIPAA compliance** required during entire transition period
- **Verbal consent already collected** from ~100% of patients seen in last 4 months, but not yet documented formally
- **Risk of contested record transfers** without proper written/timestamped consent

**Operational Impact:**
- **Single point of failure**: Dr. Green must manually extract data
- **No existing process** for bulk screenshot capture + OCR + organization
- **Consent tracking chaos**: Multiple consent methods (paper, Spruce text, DocuSign) with no centralized tracking
- **Team coordination**: 4 users (Dr. Green, LaChandra, Lindsay, Jenny) need shared access to patient data and consent status

### Why Existing Solutions Fall Short

**Allscripts Limitations:**
- No bulk export of "promoted problem" comments/timelines
- Cannot export curated timeline data in structured format
- Access terminates 12/31/2025 regardless of data extraction status

**OneNote Limitations:**
- Contains data but requires manual review per patient
- No automated extraction despite OCR indexing
- Risk of losing access if Southview demands SharePoint turnover to UAB

**Generic Document Management Tools:**
- Not HIPAA-compliant by default
- No PHI encryption or BAA agreements
- No consent tracking workflows
- No integration with Spruce Health communications
- No care plan generation capabilities matching APCM format requirements

**EMR Systems:**
- Athena One (future target) doesn't accept data in this format
- Migration timeline unclear
- Doesn't solve immediate data extraction urgency

**Microsoft Power Platform/Dataverse:**
- Attempted but proven too unstable (frequent breaking changes)
- Licensing costs too high
- Configuration complexity not justified

### Urgency & Importance

**Critical Deadline: December 31, 2025** (30 days from now)

**Why Now:**
1. **Irreversible data loss** occurs at 12/31/2025 midnight when Allscripts access terminates
2. **Legal exposure** without documented patient consent for record retention
3. **APCM billing disruption** if authorization transfer not documented properly (~450 patients affected)
4. **Patient care continuity** depends on having accessible timeline data post-transition
5. **Team workflow** requires shared database before EMR migration planning can begin
6. Dr. Green is transitioning to private practice specifically to avoid UAB acquisition - this tool is **foundational to business continuity**

**Owner's Statement:** *"Deadlines be damned, I HAVE to make this work."*

---

## Proposed Solution

### Core Concept & Approach

**Patient_Explorer** is a **local-first, offline-capable desktop application** with Azure cloud synchronization that enables:

1. **Rapid Data Capture (Dec 2025)**
   - Screenshot paste/upload from Allscripts and OneNote
   - OCR text extraction via Azure Cognitive Services
   - Manual text snippet paste for quick capture
   - Patient identifier tagging (link captures to patient records)

2. **Consent Management Workflow**
   - Track consent status: Not Asked | Verbal Only | Text Message Timestamped | Written Paper | DocuSign Signed
   - File attachment for scanned consent forms
   - Spruce Health integration to pull text message consent timestamps
   - DocuSign integration for email-based consent
   - APCM billing authorization tracking (Southview TIN → Home Team TIN)
   - Excel import of 1,384-patient baseline list

3. **AI-Powered Spruce Communication Parsing**
   - Microsoft Graph API integration with Spruce Health
   - AI parsing to distinguish patient vs. family member in conversations
   - Context switching detection when new patient names mentioned
   - Confidence scoring with low-confidence flagging for human review
   - Option to associate with existing patient or create new profile

4. **Structured Care Plan Generation**
   - On-demand care plan report following APCM template format
   - Problem list with diagnosis-specific sections: Story, Timeline, Impression, Protocol, Patient Tasks, Team Tasks
   - Medication and allergy sections
   - Health maintenance tracking (vaccines, cancer screenings)
   - Personalized standing orders
   - Output formats: Markdown (with checkboxes), Plain Text (for EMR paste), PDF (future)

5. **Local-First Storage with Cloud Sync**
   - Encrypted SQLite database (SQLCipher) for offline access
   - Azure Blob Storage sync for backup and team sharing
   - Azure Key Vault for encryption key management
   - Works offline during clinic hours, syncs when online

### Key Differentiators

1. **Urgency-Optimized MVP**: Designed for 30-day emergency data extraction, not long-term EMR replacement
2. **Multi-Method Consent Tracking**: Paper + Text + DocuSign + APCM billing transfer in one system
3. **AI Communication Parsing**: Solves the "family member speaks for multiple patients" problem unique to primary care
4. **APCM-Compliant Care Plan Format**: Exact template matching Dr. Green's existing workflow
5. **Offline-First + Cloud Sync**: Works during clinic hours without internet dependency
6. **Cost-Optimized Azure**: Shared Cognitive Services admin account to minimize per-user licensing
7. **Green Clinic Tenant Isolation**: Strict HIPAA separation from Home Team (Phase 2) and Southview data

### Why This Solution Will Succeed

1. **Time-Boxed Scope**: Phase 1A (emergency capture) focused solely on pre-12/31/2025 data extraction
2. **Proven Technology Stack**: TypeScript + SQLite + Azure (all with existing BAA/HIPAA support)
3. **Domain Expert Partnership**: Built iteratively with Dr. Green using BMAD-METHOD question-driven development
4. **Existing Infrastructure**: Green Clinic Microsoft tenant already has BAA, Dr. Green has admin rights
5. **Reusable Architecture**: Phase 2 clones this setup for Home Team Medical Services
6. **Pragmatic Over Perfect**: Manual processes acceptable in Phase 1A (e.g., screenshot paste vs. OneNote API automation)

### High-Level Vision

**Phase 1A (Emergency - Complete by 12/31/2025):**
- Screenshot/text paste capture + OCR
- Patient identifier tagging
- Consent status tracking (manual data entry)
- Local SQLite storage (encrypted)
- Basic patient list with consent fields

**Phase 1B (Jan-Feb 2025):**
- Search by patient/diagnosis/date range
- Care plan report generation (markdown + plain text)
- Azure Blob sync
- Team multi-user access (LaChandra, Lindsay, Jenny)
- Excel import of 1,384-patient list

**Phase 1C (Mar-Apr 2025):**
- Spruce Health API integration (read patient demographics)
- AI communication parsing (assign conversations to patients)
- DocuSign integration for email consent
- OneNote API integration (automated worksheet extraction)

**Phase 2 (Q2 2025 - Future):**
- Clone entire setup for Home Team Medical Services tenant
- Enhanced analytics and reporting
- EMR migration export tools
- Advanced care plan editing UI

---

## Target Users

### Primary User Segment: Primary Care Providers (PCPs)

**Users:**
- **Dr. Robert Green** (Support Team Leader / Collaborating Physician)
- **LaChandra Watts, CRNP** (Primary Care Provider)
- **Lindsay Bearden, CRNP** (Primary Care Provider)

**Demographics:**
- **Role**: Primary care team leaders responsible for patient medical decision-making
- **Patient Panel**: Dr. Green serves as STL for all Green Clinic patients; LaChandra and Lindsay each have dedicated patient panels within that cohort
- **Technical Proficiency**: Moderate; comfortable with EMR systems (Allscripts, Athena) and basic Windows desktop applications
- **Availability**: Clinical hours 8am-5pm; limited time for non-clinical administrative tasks

**Current Behaviors & Workflows:**
1. **Daily Clinical Workflow**:
   - Review patient charts in Allscripts before visits
   - Document encounter notes with problem list updates
   - Print problem list worksheets to OneNote for reference
   - Use Spruce Health for patient messaging and coordination

2. **Problem List Management**:
   - Update timeline entries with format: `-- mm/dd/yyyy: [values] --> [plan changes]`
   - Nest comments under each promoted (active) diagnosis
   - Reference timelines during visits to inform treatment decisions

3. **Care Coordination**:
   - Generate care plans annually during AWV (Annual Wellness Visit)
   - Coordinate with Jenny (RN) on protocol orders and follow-ups
   - Communicate with specialists and home health via Spruce

**Specific Needs & Pain Points:**
- **Need**: Rapid data extraction from Allscripts before 12/31/2025 deadline
- **Pain**: No bulk export tool for curated timeline comments
- **Need**: Shared access to patient data across team
- **Pain**: OneNote notebooks not easily searchable or sharable
- **Need**: Track which patients have consented to record retention
- **Pain**: Multiple consent methods (paper, text, DocuSign) with no central tracking system
- **Need**: Generate APCM-compliant care plans on demand
- **Pain**: Manual copy/paste from Allscripts into Word documents is time-consuming

**Goals:**
- Extract all patient timeline data before Allscripts access terminates
- Maintain legally compliant record retention with documented consent
- Generate care plans for APCM patients within 5 minutes per patient
- Coordinate patient transitions with team members efficiently

---

### Secondary User Segment: Primary Care Nurses (PCNs)

**Users:**
- **Jenny Linard, RN** (current PCN for both LaChandra and Lindsay)
- Future additional nurse (planned to separate teams)

**Demographics:**
- **Role**: Clinical support for PCPs; executes standing orders, coordinates lab work, patient follow-ups
- **Technical Proficiency**: Moderate; familiar with EMR systems and basic office applications
- **Availability**: Clinical hours 8am-5pm; heavy multitasking workload

**Current Behaviors & Workflows:**
1. **Care Coordination**:
   - Review care plans for protocol reminders (e.g., "order A1c q 3 months for diabetes patients")
   - Execute personalized standing orders (e.g., UTI panels, respiratory viral panels)
   - Follow up on lab results and notify PCPs of abnormals
   - Schedule patient appointments for protocol adherence

2. **Patient Communication**:
   - Primary contact for patients via Spruce Health messaging
   - Coordinate with home health agencies and specialists
   - Document patient interactions

**Specific Needs & Pain Points:**
- **Need**: Quick reference to patient protocol orders per diagnosis
- **Pain**: Scattered information across Allscripts + OneNote + personal notes
- **Need**: Track which patients need follow-up labs/appointments
- **Pain**: No automated reminders or task lists linked to care plans
- **Need**: Access same patient database as PCPs for coordination
- **Pain**: Currently relies on verbal communication with PCPs to know patient status

**Goals:**
- Access care plans to execute protocol orders accurately
- Track patient consent status to know who is transitioning to Green Clinic
- Coordinate team tasks efficiently with shared visibility

---

## Goals & Success Metrics

### Business Objectives

- **Zero Data Loss**: Extract 100% of curated timeline data for all 1,384 Southview patients before 12/31/2025
- **Legal Compliance**: Obtain and document consent from ≥90% of Green Clinic patients (estimated ~70-80% of 1,384 Southview patients) by 3/31/2025
- **APCM Continuity**: Successfully transfer APCM billing authorization for all ~450 enrolled patients with documented consent by 2/28/2025
- **Cost Optimization**: Keep Azure service costs <$200/month through shared admin Cognitive Services account
- **Team Adoption**: Achieve 100% adoption by all 4 team members (Dr. Green, LaChandra, Lindsay, Jenny) by 2/15/2025
- **Reusability**: Design architecture to enable Phase 2 cloning for Home Team Medical Services within 1 month

### User Success Metrics

- **Data Capture Speed**: Users can paste screenshot + tag patient + OCR extract in <2 minutes per capture
- **Consent Tracking Efficiency**: User can update consent status for a patient in <30 seconds
- **Care Plan Generation Speed**: Generate complete APCM care plan in <5 minutes per patient
- **Search Performance**: Search patient database by name/MRN and return results in <5 seconds
- **Offline Reliability**: 100% functionality during offline clinical hours with automatic sync when online
- **Data Accuracy**: OCR text extraction accuracy ≥95% for Allscripts worksheet screenshots

### Key Performance Indicators (KPIs)

- **Patient Data Captured**: Number of patients with at least one data capture | Target: 1,384 by 12/31/2025
- **Consent Documentation Rate**: % of Green Clinic patients with documented consent | Target: ≥90% by 3/31/2025
- **APCM Consent Transfer Rate**: % of ~450 APCM patients with billing authorization documented | Target: 100% by 2/28/2025
- **Care Plans Generated**: Number of APCM care plans generated | Target: ≥450 by 4/30/2025
- **Data Extraction Completion**: % of 1,384 patients with timeline data extracted from Allscripts/OneNote | Target: 100% by 12/31/2025
- **Team Usage**: Number of active users per week | Target: 4/4 (100%) by 2/15/2025
- **Azure Cost**: Monthly Azure service costs | Target: <$200/month
- **System Uptime**: % of time database accessible to team | Target: ≥99.5%

---

## MVP Scope

### Core Features (Must Have) - Phase 1A (Complete by 12/31/2025)

- **Screenshot/Image Capture**
  - Paste image from clipboard (Ctrl+V from Allscripts/OneNote)
  - Upload image file (PNG, JPG, PDF)
  - **Rationale**: Primary method for capturing Allscripts worksheet data before access terminates

- **OCR Text Extraction**
  - Azure Cognitive Services Computer Vision API integration
  - Extract text from screenshots automatically on upload
  - Display extracted text for review/editing
  - **Rationale**: Enables searchable, structured data from images

- **Patient Identifier Tagging**
  - Manually associate each capture with a patient (search by name/MRN)
  - Create new patient record if not found
  - **Rationale**: Links captures to patient for organization and retrieval

- **Patient List Management**
  - Excel import of 1,384-patient baseline list (MRN, Name, DOB, Address, Contact Info)
  - Add/edit patient records manually
  - Track fields: MRN, Name, DOB, Address, Phone, Email, Spruce Account (Y/N), Spruce Profile Type
  - **Rationale**: Foundation for all patient-related features

- **Consent Status Tracking**
  - Fields per patient:
    - Consent Status: Not Asked | Verbal Only | Text Message Timestamped | Written Paper | DocuSign Signed | Declined
    - Verbal Consent Date
    - Written Consent Date
    - Text Message Consent Date (timestamped Spruce reply)
    - DocuSign Consent Date
    - Invitation Sent (Y/N + Date)
    - APCM Enrollment Status: Enrolled | Not Enrolled
    - APCM Billing Consent (Southview TIN → Home Team TIN): Yes | No | Date
    - Notes (free text)
  - **Rationale**: Legal requirement for record retention; APCM billing authorization critical

- **Local SQLite Database (Encrypted)**
  - SQLCipher for at-rest encryption
  - Store: Patients, Captures (images + OCR text), Consent Status
  - Offline-first architecture (no internet required for core functionality)
  - **Rationale**: HIPAA compliance + offline clinical workflow support

- **Basic Search**
  - Search patients by: Name, MRN, DOB
  - Filter captures by: Patient, Date Range
  - **Rationale**: Must be able to find patient records quickly

- **File Attachment for Consent Forms**
  - Attach scanned consent form PDFs to patient record
  - Store file references in database, files in encrypted local folder
  - **Rationale**: Legal documentation requirement

### Core Features (Must Have) - Phase 1B (Jan-Feb 2025)

- **Care Plan Report Generation**
  - Generate APCM-compliant care plan following template structure
  - Sections: Demographics, APCM Orientation, People/Groups, Clinical Goals, Medications, Allergies, Active Problem List (with per-diagnosis Story/Timeline/Impression/Protocol/Tasks), Historical Problems, Health Maintenance, Standing Orders
  - Per-diagnosis structure:
    - Header: `[DX NAME] ([ICD code]):`
    - `...Story:` (up to 2,000 chars)
    - `...Timeline:` (up to 4,000 chars, format: `- yyyy/mm/dd:`)
    - `...Impression (as of {LastUpdated}):`
    - `...Protocol:` (with `- order:` and `- trend:` sub-items)
    - `...Patient Tasks:` (multi-line bullets)
    - `...Team Tasks:` (multi-line bullets)
  - Output formats:
    - Markdown (with checkboxes, printable)
    - Plain text (copy/paste to EMR)
  - **Rationale**: Primary deliverable for APCM patients; time-sensitive need

- **Enhanced Search & Filtering**
  - Search by: Patient Name, MRN, Diagnosis, Date Range, Consent Status, APCM Enrollment
  - Sort/filter patient list by multiple criteria
  - **Rationale**: Team needs to prioritize data extraction and consent follow-ups

- **Azure Blob Storage Sync**
  - Encrypted backup of SQLite database to Azure Blob Storage (Green Clinic tenant)
  - Manual "Sync Now" button (automatic sync in Phase 1C)
  - **Rationale**: Data backup + enables team sharing across devices

- **Multi-User Access**
  - Team members log in with Green Clinic Microsoft 365 credentials
  - All users have read/write access (no role-based permissions in Phase 1)
  - **Rationale**: LaChandra, Lindsay, Jenny need shared access to patient data

### Out of Scope for MVP

- ❌ **OneNote API Integration** (Phase 1C) - Manual copy/paste acceptable initially
- ❌ **Spruce Health API Integration** (Phase 1C) - Manual entry of consent data initially
- ❌ **AI Communication Parsing** (Phase 1C) - Not needed for emergency data extraction
- ❌ **DocuSign Integration** (Phase 1C) - Manual tracking acceptable initially
- ❌ **Automatic Sync** (Phase 1C) - Manual "Sync Now" sufficient initially
- ❌ **Advanced Care Plan Editing UI** (Phase 1C) - Direct database editing acceptable initially
- ❌ **PDF Export** (Phase 2) - Markdown + plain text sufficient for MVP
- ❌ **Role-Based Permissions** (Phase 2) - All team members trusted equally
- ❌ **EMR Migration Export** (Phase 2) - Not needed until EMR decision made
- ❌ **Home Team Medical Services Deployment** (Phase 2) - Green Clinic only for Phase 1
- ❌ **Mobile App** - Desktop only
- ❌ **Patient Portal Access** - Staff-only tool

### MVP Success Criteria

**Phase 1A Success (by 12/31/2025):**
- ✅ All 1,384 patients have at least one data capture OR confirmed as "not transitioning to Green Clinic"
- ✅ Consent status tracked for 100% of patients (even if status is "Not Asked")
- ✅ Local SQLite database contains all extracted data, encrypted and backed up to Azure
- ✅ Dr. Green can paste screenshot, tag patient, and OCR extract in <2 minutes
- ✅ Zero data loss from Allscripts termination

**Phase 1B Success (by 2/28/2025):**
- ✅ At least 10 APCM care plans generated successfully using actual patient data
- ✅ All 4 team members can log in and access shared database
- ✅ Care plan generation takes <5 minutes per patient
- ✅ Azure Blob sync working for backup and team sharing
- ✅ ≥90% consent documentation rate for Green Clinic patients

---

## Post-MVP Vision

### Phase 1C Features (Mar-Apr 2025)

**OneNote API Integration:**
- Programmatic extraction of Allscripts worksheets from OneNote notebooks via Microsoft Graph API
- Batch processing to OCR all historical OneNote pages
- **Benefit**: Automates extraction of 1+ year of printed worksheets

**Spruce Health API Integration:**
- Read patient demographics from Spruce (name, DOB, contact info)
- Pull message threads for consent timestamp extraction
- Sync Spruce patient list with Patient_Explorer database
- **Benefit**: Eliminates manual patient data entry

**AI Communication Parsing:**
- AI analyzes Spruce message threads to distinguish patient vs. family member
- Detects context switching when new patient names mentioned
- Confidence scoring with low-confidence flagging for human review
- User can assign conversation segments to specific patients or create new profiles
- **Benefit**: Solves "family member speaks for multiple patients" problem, enables automated patient communication history

**DocuSign Integration:**
- Email consent forms via DocuSign to patients with email on file
- Automatically update consent status when DocuSign completed
- Store completed DocuSign PDFs in patient record
- **Benefit**: Streamlines consent collection for remaining patients

**Automatic Sync:**
- Background Azure Blob sync every 15 minutes when online
- Conflict resolution for multi-user edits
- **Benefit**: Seamless team collaboration without manual sync

**Enhanced Care Plan Editing:**
- In-app UI for editing diagnosis-specific fields (Story, Timeline, Protocol, etc.)
- Template-driven protocol creation per diagnosis type
- Custom protocol per patient/diagnosis
- **Benefit**: Enables team to update care plans between visits without direct database editing

### Phase 2 Features (Q2-Q3 2025)

**Home Team Medical Services Clone:**
- Deploy identical Patient_Explorer instance to Home Team Microsoft tenant
- Separate database for Home Team patients
- Independent Azure resources
- **Benefit**: Enables Dr. Green to manage both Green Clinic and Home Team patient populations with same tool

**EMR Migration Export:**
- Export patient data in HL7 FHIR format for EMR import
- Custom export formats per target EMR (Athena, etc.)
- **Benefit**: Facilitates eventual migration to permanent EMR

**Advanced Analytics:**
- Population health dashboards (e.g., % of diabetes patients with A1c <7%)
- Protocol adherence tracking (e.g., overdue labs per protocol)
- Consent completion tracking visualizations
- **Benefit**: Proactive care management and team performance insights

**Enhanced Security:**
- Role-based access control (PCP vs. RN permissions)
- Audit logging for all PHI access
- Multi-factor authentication
- **Benefit**: Enhanced HIPAA compliance and security for larger team

### Long-Term Vision (1-2 Years)

**Integrated Care Platform:**
- Patient_Explorer becomes the primary care coordination hub for Green Clinic and Home Team
- Direct integration with chosen permanent EMR (Athena or alternative)
- Patient portal for self-service access to care plans and consent management
- Automated care plan updates based on EMR encounter notes
- **Vision**: Patient_Explorer evolves from emergency data extraction tool to long-term primary care management platform

**AI-Augmented Care Plans:**
- AI suggests protocol updates based on latest clinical guidelines
- AI flags patients overdue for protocol orders
- AI generates draft Impression comments from encounter notes
- **Vision**: Reduce PCP administrative burden while maintaining care quality

**Multi-Practice Scalability:**
- Expand beyond Dr. Green's practices to other small primary care practices facing EMR transitions
- SaaS model with per-practice licensing
- **Vision**: Patient_Explorer as a product for small private primary care practices nationwide

### Expansion Opportunities

1. **EMR Transition Consulting**: Offer Patient_Explorer + consulting services to other practices facing EMR transitions/acquisitions
2. **APCM Management Suite**: Specialized features for APCM enrollment, billing, and compliance tracking
3. **Care Coordination Platform**: Expand Spruce integration to full communication hub with task management
4. **Regulatory Reporting**: Automated compliance reporting for MIPS, HEDIS, value-based care programs
5. **Integration Marketplace**: Pre-built integrations with common EMRs (Epic, Cerner, Athena, Allscripts, etc.)

---

## Technical Considerations

### Platform Requirements

- **Target Platforms:** Windows desktop (primary), macOS (future consideration)
- **Browser/OS Support:** Electron-based desktop app (supports Windows 10/11, macOS 10.15+)
- **Performance Requirements:**
  - OCR processing: <10 seconds per screenshot
  - Search results: <5 seconds for any query across 1,384 patients
  - Care plan generation: <5 minutes per patient (including data aggregation)
  - Database sync: <30 seconds for typical daily changes
  - Offline functionality: 100% core features work without internet

### Technology Preferences

- **Frontend:**
  - **Framework**: Electron + React + TypeScript
  - **UI Library**: Material-UI or Ant Design (accessible, professional healthcare aesthetic)
  - **State Management**: Redux Toolkit or Zustand
  - **Forms**: React Hook Form
  - **Rationale**: Electron enables desktop app with offline-first architecture; React/TypeScript align with team skills and maintainability

- **Backend:**
  - **Runtime**: Node.js (embedded in Electron)
  - **API Layer**: Express.js (local API server)
  - **OCR Service**: Azure Cognitive Services Computer Vision API (REST calls)
  - **Rationale**: Node.js ecosystem enables code sharing between frontend/backend; Azure Cognitive Services has HIPAA BAA

- **Database:**
  - **Local**: SQLite with SQLCipher for encryption
  - **Cloud Sync**: Azure Blob Storage (encrypted JSON or SQLite file backups)
  - **Schema Management**: TypeORM or Prisma for migrations
  - **Rationale**: SQLite is battle-tested for local-first apps; SQLCipher provides AES-256 encryption; Azure Blob has BAA

- **Hosting/Infrastructure:**
  - **Desktop App Distribution**: GitHub Releases or Microsoft Intune (Green Clinic tenant)
  - **Azure Resources** (Green Clinic tenant):
    - Azure Cognitive Services (Computer Vision API)
    - Azure Blob Storage (encrypted patient database backups)
    - Azure Key Vault (encryption key management)
  - **Authentication**: Microsoft 365 OAuth (Green Clinic tenant users)
  - **Rationale**: Azure ecosystem has existing BAA; Microsoft 365 auth leverages existing Green Clinic identities

### Architecture Considerations

- **Repository Structure:**
  - Monorepo with `packages/electron-app`, `packages/shared-types`, `packages/azure-services`
  - **Rationale**: Enables code sharing, prepares for Phase 2 multi-tenant deployment

- **Service Architecture:**
  - **Desktop App (Electron)**: Renderer process (React UI) + Main process (Node.js API server + SQLite)
  - **Azure Services**: Stateless REST APIs (Cognitive Services, Blob Storage)
  - **Sync Strategy**: Optimistic UI with conflict-free replicated data types (CRDTs) or last-write-wins with timestamps
  - **Rationale**: Local-first architecture enables offline work; Azure used only for OCR and backup

- **Integration Requirements:**
  - **Phase 1A**: None (standalone desktop app)
  - **Phase 1B**: Azure Blob Storage (file upload), Azure Key Vault (key retrieval), Microsoft 365 OAuth (authentication)
  - **Phase 1C**: Microsoft Graph API (OneNote, Spruce Health if available), DocuSign API
  - **Phase 2**: EMR export APIs (HL7 FHIR), Athena API (if chosen as permanent EMR)

- **Security/Compliance:**
  - **Encryption at Rest**: SQLCipher (AES-256), Azure Blob Storage (Microsoft-managed keys + customer-managed keys in Key Vault)
  - **Encryption in Transit**: TLS 1.2+ for all Azure API calls, HTTPS for any web requests
  - **Authentication**: Microsoft 365 OAuth with MFA enforced via Green Clinic tenant policies
  - **Authorization**: All authenticated Green Clinic users have full access (Phase 1); role-based access in Phase 2
  - **Audit Logging**: Log all PHI access to local encrypted log file + Azure Blob (Phase 1C)
  - **HIPAA Compliance**:
    - Business Associate Agreement (BAA) in place with Microsoft for Azure services
    - Green Clinic Microsoft tenant (southviewteam.com, greenclinicteam.com) is isolated
    - No PHI stored in non-BAA services (e.g., GitHub, npm)
    - Patient data never leaves Green Clinic tenant (strict tenant isolation from Home Team in Phase 1)
  - **Backup/Disaster Recovery**: Daily automated Azure Blob backups, 30-day retention, HIPAA-compliant deletion on retention expiry

---

## Constraints & Assumptions

### Constraints

- **Budget:**
  - Azure Cognitive Services: Estimated $50-100/month (based on ~10,000 OCR transactions/month)
  - Azure Blob Storage: <$20/month (estimated 50GB encrypted patient data)
  - Azure Key Vault: <$10/month
  - **Total Azure Cost Target**: <$200/month
  - **Development Cost**: In-kind via Claude Code + Dr. Green's time (no external contractor budget)
  - **Constraint**: Must use shared Azure Cognitive Services admin account to minimize per-user licensing costs

- **Timeline:**
  - **Phase 1A Deadline**: December 31, 2025 (HARD DEADLINE - Allscripts access terminates)
  - **Phase 1A Duration**: ~30 days from 11/29/2025 (development + data extraction concurrent)
  - **Phase 1B Deadline**: February 28, 2025 (APCM billing authorization transfer deadline)
  - **Phase 1C Target**: April 30, 2025 (consent collection deadline - 90% goal)
  - **Constraint**: Dr. Green must perform data extraction while also seeing patients during Dec 2025 - limited time for capture workflow

- **Resources:**
  - **Development**: Dr. Green + Claude Code (AI pair programming)
  - **Testing**: Dr. Green, LaChandra, Lindsay, Jenny (alpha testers)
  - **Infrastructure**: Green Clinic Microsoft tenant (admin rights: Dr. Green)
  - **Constraint**: Single developer (Dr. Green) with limited coding experience - must prioritize simplicity over sophistication

- **Technical:**
  - **Platform**: Windows desktop only for Phase 1 (Dr. Green's primary OS)
  - **Network**: Intermittent internet access during clinic hours (offline-first required)
  - **Existing Systems**: Must coexist with Allscripts (through 12/31/2025), Spruce Health (ongoing), eventual Athena migration
  - **Data Volume**: ~1,384 patients × ~10 diagnoses/patient × ~50 timeline entries/diagnosis = ~700,000 data points (estimate)
  - **Constraint**: SQLite database size may grow to 1-5GB; must remain performant

### Key Assumptions

- **User Adoption**: Assumes LaChandra, Lindsay, Jenny will adopt tool without extensive training (simple UI required)
- **Consent Collection**: Assumes ≥70% of 1,384 Southview patients will consent to Green Clinic transition (target: 970-1,100 patients)
- **APCM Enrollment**: Assumes all ~450 APCM patients will consent to billing authorization transfer (critical assumption - legal review pending)
- **OCR Accuracy**: Assumes Azure Cognitive Services OCR ≥95% accurate on Allscripts worksheets (validation needed with sample screenshots)
- **Spruce Health API**: Assumes Spruce Health API provides read access to messages and patient data (API documentation review pending)
- **OneNote Access**: Assumes SharePoint OneNote notebooks remain accessible to Dr. Green post-12/31/2025 (risk: Southview may demand turnover to UAB)
- **Azure Tenant Continuity**: Assumes Green Clinic Microsoft tenant remains under Dr. Green's admin control indefinitely
- **No EMR Decision**: Assumes Athena or alternative EMR not selected until Q2 2025 at earliest (Patient_Explorer must be EMR-agnostic for now)
- **Regulatory Compliance**: Assumes text message "Yes" reply with timestamp is legally sufficient consent (legal review: "better than nothing" - formal written consent preferred but not always feasible)
- **Team Stability**: Assumes current team (Dr. Green, LaChandra, Lindsay, Jenny) remains stable through Phase 1 completion

---

## Risks & Open Questions

### Key Risks

- **Allscripts Access Termination Risk (CRITICAL - HIGHEST IMPACT)**
  - **Risk**: Allscripts access terminates before all patient data extracted
  - **Impact**: Permanent data loss for un-extracted patients; care continuity disruption
  - **Mitigation**:
    - Prioritize highest-risk patients first (APCM-enrolled, complex chronic disease)
    - Parallel workflow: Dr. Green extracts data while development occurs
    - Accept manual screenshots as sufficient (don't wait for OneNote API automation)
    - Daily backups to Azure Blob to prevent local data loss during extraction sprint

- **OneNote Access Loss Risk (HIGH IMPACT)**
  - **Risk**: Southview/UAB demands SharePoint turnover, OneNote notebooks become inaccessible
  - **Impact**: Loss of 1+ year of printed Allscripts worksheets with OCR-indexed data
  - **Mitigation**:
    - **Immediate Action**: Export all OneNote pages as PDFs to local encrypted folder (Dec 1-7, 2025)
    - Treat OneNote as "already lost" and prioritize Allscripts direct extraction
    - Phase 1C OneNote API becomes "nice to have" not "must have"

- **Consent Collection Shortfall Risk (MEDIUM-HIGH IMPACT)**
  - **Risk**: <90% consent rate due to patient non-response or refusals
  - **Impact**: Legal exposure for unauthorized record retention; reduced Green Clinic patient panel size
  - **Mitigation**:
    - Multi-channel approach: Paper + Spruce text + DocuSign email
    - Track "invitation sent" separately from "consent received" to prove outreach effort
    - Legal review of text message timestamp consent sufficiency
    - Accept verbal consent as interim with written follow-up

- **APCM Billing Authorization Legal Risk (HIGH IMPACT)**
  - **Risk**: Text message consent not legally sufficient for APCM billing authorization transfer from Southview TIN to Home Team TIN
  - **Impact**: Loss of APCM revenue for ~450 patients; potential CMS audit issues
  - **Mitigation**:
    - Prioritize written/DocuSign consent for all 450 APCM patients
    - Legal review of consent language to ensure covers both record retention AND billing authorization
    - Document separate consent dates for record retention vs. APCM billing authorization

- **OCR Accuracy Risk (MEDIUM IMPACT)**
  - **Risk**: Azure Cognitive Services OCR <95% accurate on Allscripts worksheets (handwriting, poor image quality)
  - **Impact**: Manual cleanup required for every capture; slows data extraction workflow
  - **Mitigation**:
    - Validate OCR accuracy on sample screenshots before Phase 1A launch
    - Provide manual text editing UI for OCR corrections
    - Accept 80-90% accuracy as "good enough" if manual cleanup <1 minute/capture

- **Database Sync Conflict Risk (MEDIUM IMPACT)**
  - **Risk**: Multiple team members edit same patient record offline, creating sync conflicts
  - **Impact**: Data loss or corruption; team confusion
  - **Mitigation**:
    - Last-write-wins with timestamps for Phase 1 (simple conflict resolution)
    - Flag conflicting edits for manual review in Phase 1C
    - Team coordination: Assign patients to team members to minimize overlap

- **Single Point of Failure Risk (MEDIUM IMPACT)**
  - **Risk**: Dr. Green is sole developer; if he becomes unavailable (illness, emergency), project stalls
  - **Impact**: Missed 12/31/2025 deadline; data loss
  - **Mitigation**:
    - Document all code and architecture decisions in BMAD PRD/Architecture docs
    - Daily code commits to GitHub (private repo)
    - Consider backup developer (Pat Rutledge or Pavel Savine) for emergency handoff

- **Scope Creep Risk (MEDIUM IMPACT)**
  - **Risk**: Feature requests (e.g., "Can we add medication refill reminders?") delay Phase 1A completion
  - **Impact**: Missed 12/31/2025 deadline
  - **Mitigation**:
    - BMAD-METHOD structured workflow enforces scope discipline
    - Defer all non-essential features to Phase 1B/1C/2
    - "Deadlines be damned" urgency keeps focus on emergency data extraction

### Open Questions

1. **Spruce Health API Access**:
   - Question: Does Spruce Health API provide read access to message threads and patient demographics?
   - **Action**: Review Spruce Health developer documentation; test API with sample data
   - **Impact**: If no API, Phase 1C Spruce integration becomes manual export/import

2. **OneNote API Permissions**:
   - Question: Can Microsoft Graph API access OneNote notebooks on SharePoint via Green Clinic tenant credentials?
   - **Action**: Test OneNote API with sample notebook; verify permissions
   - **Impact**: If no API access, Phase 1C OneNote integration becomes manual export/import

3. **Legal Review of Text Message Consent**:
   - Question: Is timestamped Spruce "Yes" reply legally sufficient for both record retention AND APCM billing authorization?
   - **Action**: Dr. Green to consult attorney; document legal opinion in project
   - **Impact**: May require prioritizing written/DocuSign consent for APCM patients

4. **DocuSign Integration Complexity**:
   - Question: How complex is DocuSign API integration? Does Green Clinic have existing DocuSign account?
   - **Action**: Review DocuSign API documentation; check for existing account with Pat Rutledge
   - **Impact**: If too complex, defer to Phase 2 and use manual DocuSign workflow in Phase 1C

5. **Excel Import Schema Validation**:
   - Question: What is exact schema of 1,384-patient Excel file? Any data quality issues (duplicates, missing fields)?
   - **Action**: Dr. Green to provide sample Excel file (with PHI redacted or test data)
   - **Impact**: May require data cleaning step before import

6. **Azure Cognitive Services Pricing**:
   - Question: What is actual cost per OCR transaction? Estimated 10,000 transactions/month × cost/transaction = ?
   - **Action**: Check Azure Cognitive Services pricing page; calculate with S1 tier estimate
   - **Impact**: If >$100/month, may need to optimize OCR calls or negotiate Azure credits

7. **Multi-User Authentication Flow**:
   - Question: Should team members log in to desktop app with Microsoft 365 credentials, or use shared device login?
   - **Action**: Discuss with team; decide on authentication UX
   - **Impact**: Affects audit logging and user-specific settings

8. **Care Plan Protocol Defaults**:
   - Question: What are recommended protocol orders per diagnosis type (diabetes, hypertension, etc.)? Should app provide default templates?
   - **Action**: Dr. Green to document protocol defaults per diagnosis in separate reference doc
   - **Impact**: Affects care plan generation logic and database schema

9. **Patient Identifier Primary Key**:
   - Question: Should patient primary key be MRN (account #) or internal UUID? What if MRN duplicates exist across Southview/Home Team?
   - **Action**: Decide on patient ID strategy; plan for Phase 2 multi-practice support
   - **Impact**: Affects database schema and future scalability

10. **Offline Sync Frequency**:
    - Question: How often should app attempt Azure Blob sync when online? Every 15 minutes? On-demand only?
    - **Action**: Discuss with team; balance between data freshness and network overhead
    - **Impact**: Affects sync logic complexity and Azure API call costs

### Areas Needing Further Research

- **HL7 FHIR Export Standards**: Research required export formats for Athena and other EMRs to plan Phase 2 migration
- **HIPAA Audit Logging Requirements**: Determine minimum audit log requirements for HIPAA compliance (who accessed what PHI when)
- **CMS APCM Billing Requirements**: Verify consent documentation requirements for APCM billing authorization transfer (CMS regulations)
- **OCR Handwriting Recognition**: Test Azure Cognitive Services accuracy on handwritten notes (if Allscripts worksheets contain handwriting)
- **SQLite Performance at Scale**: Benchmark SQLite with 1-5GB database size, 1,384 patients, 700,000 data points (ensure <5 second search performance)
- **Electron Auto-Update**: Research Electron auto-update best practices for seamless app updates without disrupting team workflow
- **Azure Cognitive Services Batch Processing**: Investigate if Azure supports batch OCR requests to optimize costs for OneNote bulk extraction
- **Spruce Health Communication Export**: Determine if Spruce provides bulk message export API or requires manual per-conversation retrieval

---

## Appendices

### A. Research Summary

**Allscripts EMR Data Extraction Research:**
- **Finding**: Allscripts does not provide bulk export of "promoted problem" nested comments via standard reports
- **Finding**: Problem list worksheets can be printed to PDF or OneNote, but no API for programmatic extraction
- **Implication**: Screenshot + OCR is the only viable data extraction method for timeline data

**OneNote OCR Capabilities:**
- **Finding**: OneNote has built-in OCR for images, making notebooks searchable
- **Finding**: Microsoft Graph API provides read access to OneNote notebooks on SharePoint
- **Implication**: OneNote API integration (Phase 1C) can automate extraction of historical worksheets, but manual export as PDF backup is prudent given Southview/UAB turnover risk

**Azure Cognitive Services HIPAA Compliance:**
- **Finding**: Azure Cognitive Services has HIPAA Business Associate Agreement (BAA) available
- **Finding**: Computer Vision API OCR accuracy: 90-99% depending on image quality and text clarity
- **Implication**: Suitable for Patient_Explorer with manual review of OCR output

**Spruce Health API Documentation:**
- **Status**: Research pending (Dr. Green to review Spruce developer docs)
- **Known**: Spruce provides REST API for patient messaging and demographics
- **Unknown**: Extent of API access to message history and patient fields

**DocuSign API Integration:**
- **Finding**: DocuSign provides REST API for sending/tracking consent forms
- **Finding**: Typical integration complexity: 2-5 days for basic send/receive workflow
- **Implication**: Feasible for Phase 1C if Green Clinic has DocuSign account

**HIPAA Text Message Consent Legal Review:**
- **Source**: Dr. Green's attorney
- **Guidance**: Timestamped text message "Yes" reply is "better than nothing" and shows good-faith effort to obtain consent
- **Guidance**: Formal written signature preferred, especially for APCM billing authorization
- **Implication**: Multi-channel consent approach required (paper + text + DocuSign)

### B. Stakeholder Input

**Dr. Robert Green (Primary Stakeholder):**
- **Priority**: "Deadlines be damned, I HAVE to make this work" - emergency data extraction is paramount
- **Workflow Preference**: Offline-first with manual workflows acceptable in Phase 1A (don't wait for API automation)
- **Quality Standard**: OCR accuracy ≥80% acceptable if manual cleanup <1 minute/capture
- **Cost Sensitivity**: Keep Azure costs <$200/month to avoid budget approvals
- **Team Coordination**: Shared database with LaChandra, Lindsay, Jenny is essential for distributed data extraction workload

**LaChandra Watts, CRNP & Lindsay Bearden, CRNP (PCPs):**
- **Need**: Quick access to patient timeline data during visits
- **Need**: Ability to generate care plans independently (not wait for Dr. Green)
- **Preference**: Simple UI that "just works" without extensive training

**Jenny Linard, RN (PCN):**
- **Need**: Protocol order reminders per patient to execute standing orders
- **Need**: Track which patients need follow-up labs/appointments
- **Preference**: Task-oriented UI (e.g., "Show me all diabetes patients overdue for A1c")

**Pat Rutledge (CEO, Home Team Medical Services):**
- **Interest**: Potential to clone Patient_Explorer for Home Team practice (Phase 2)
- **Suggestion**: Consider DocuSign integration for consent collection
- **Resource**: Available as backup developer if Dr. Green needs support

**Pavel Savine (CTO, Home Team Medical Services):**
- **Interest**: Backend architecture and security design
- **Resource**: Available for Azure infrastructure setup and HIPAA compliance review

### C. References

**BMAD-METHOD Framework:**
- Structured agile AI-driven development methodology
- Four-phase workflow: Analysis → Planning → Solutioning → Implementation
- Installed in Patient_Explorer project: `npx bmad-method install`

**APCM Care Plan Template:**
- File: `docs/.Template_Careplan_cpMRN_NAME.txt`
- Defines exact structure for care plan generation feature
- Sections: Demographics, Problem List (per-diagnosis Story/Timeline/Protocol), Health Maintenance, Standing Orders

**Green Clinic Microsoft Tenant:**
- Domains: southviewteam.com, greenclinicteam.com
- HIPAA BAA in place with Microsoft
- Admin: Robert Green, MD

**Southview Patient List:**
- Excel file: 1,384 patients
- Columns: MRN, Name, DOB, Address, Contact Info, Last DOS
- To be imported in Phase 1A

**Azure Services:**
- Cognitive Services: https://azure.microsoft.com/en-us/services/cognitive-services/
- Blob Storage: https://azure.microsoft.com/en-us/services/storage/blobs/
- Key Vault: https://azure.microsoft.com/en-us/services/key-vault/

**Spruce Health:**
- Website: https://www.sprucehealth.com/
- Developer API: (pending documentation review)

**DocuSign:**
- API Documentation: https://developers.docusign.com/

---

## Next Steps

### Immediate Actions (Pre-Development)

1. **[Dr. Green]** Export all OneNote pages as PDFs to local encrypted folder (backup against SharePoint loss) - **Deadline: 12/7/2025**
2. **[Dr. Green]** Provide sample Allscripts worksheet screenshots (PHI-redacted) for OCR accuracy validation - **Deadline: 12/2/2025**
3. **[Dr. Green]** Provide Excel file with 1,384 patients (PHI-redacted test data) for import schema design - **Deadline: 12/2/2025**
4. **[Dr. Green]** Review Spruce Health developer API documentation; confirm read access to messages/demographics - **Deadline: 12/5/2025**
5. **[Dr. Green]** Consult attorney on text message consent legal sufficiency; document opinion - **Deadline: 12/10/2025**
6. **[Dr. Green]** Set up Azure resources in Green Clinic tenant:
   - Create Resource Group: `rg-patient-explorer-greenclinic`
   - Create Cognitive Services instance (Computer Vision API)
   - Create Blob Storage account (encrypted)
   - Create Key Vault
   - **Deadline: 12/3/2025**

### PM Handoff

This Project Brief provides the full context for **Patient_Explorer**.

**Next Agent:** Product Manager (John) via `*pm` command

**PM Instructions:**
Please start in **'PRD Generation Mode'** and review this brief thoroughly. Work with Dr. Green to create the PRD section by section following the BMAD PRD template. Key focus areas:

1. **User Stories**: Translate requirements into user stories with acceptance criteria (emphasize Phase 1A emergency data extraction stories)
2. **Functional Requirements**: Detail exact workflows for screenshot capture + OCR + patient tagging + consent tracking
3. **Non-Functional Requirements**: Specify HIPAA compliance requirements, offline-first architecture, search performance (<5 seconds), OCR accuracy (≥95% goal)
4. **Data Model**: Define database schema for Patients, Captures, Consent Status, Care Plans, Diagnoses, Protocols
5. **Epic Breakdown**: Organize features into epics aligned with Phase 1A (emergency extraction), Phase 1B (care plans + team sharing), Phase 1C (API integrations)

**Critical PRD Sections for Architect Handoff:**
- Care plan generation logic (APCM template compliance)
- OCR workflow with manual review UI
- Offline-first sync strategy (SQLite ↔ Azure Blob)
- Multi-user authentication and conflict resolution

Ask clarifying questions as needed. The goal is a comprehensive PRD that enables the Architect (Winston) to design the Azure + Electron architecture with confidence.

---

**End of Project Brief**

*Generated by: BMAD Analyst (Mary)*
*Date: November 29, 2025*
*Next Phase: Product Management (PM) → PRD Creation*
