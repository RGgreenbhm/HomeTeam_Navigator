# Patient Explorer - Product Requirements Document

## Goals

1. Preserve critical patient timeline data from 1,384 Southview patients before Allscripts access terminates on 12/31/2025
2. Enable secure, HIPAA-compliant storage of curated patient information with multi-method consent tracking (paper, Spruce text timestamp, DocuSign)
3. Generate APCM-compliant care plans following Home Team template format (Story/Timeline/Impression/Protocol structure)
4. Support offline-first clinical workflows with local encrypted database, eliminating dependency on cloud connectivity
5. Track patient scheduling and follow-up due dates with staff prioritization for outreach
6. Integrate Spruce Health communications with AI-powered parsing to distinguish patient vs. family member messages
7. Transfer 450+ APCM patient billing authorizations with complete consent documentation chain
8. Provide multi-user access for Green Clinic team (Dr. Green, LaChandra, Lindsay, Jenny) with role-based permissions
9. Deploy on-premises with zero cloud licensing costs using open-source technologies (SQLite, CouchDB)
10. Support future IBM Granite model integration for local AI-powered care plan suggestions

## Background Context

Green Clinic (Dr. Robert Green's private practice serving former Southview patients) faces an emergency data preservation challenge: on December 31, 2025, access to the Allscripts EMR system containing 1,384 patient records will permanently terminate. Unlike typical EMR migrations, the team has meticulously curated timeline data nested within diagnosis records using a specific format (`-- mm/dd/yyyy: [values] --> [action plan]`) that represents years of clinical insight. This curated data exists nowhere else—not in the base Allscripts database exports, but in worksheet views, OneNote notebooks with Surface Pen annotations, and printed screenshots shared among providers.

Patient Explorer solves this crisis while building long-term capability. Phase 1 focuses exclusively on Green Clinic patients using an offline-first architecture with SQLite/SQLCipher local storage and CouchDB synchronization to an on-premises server. This eliminates cloud dependencies, reduces costs by 67-90% compared to Azure-based alternatives, and ensures clinical workflows continue during internet outages common in rural Alabama.

The application incorporates Home Team Medical Services branding (HTnav icons, infographics) and supports the team's existing OneNote + Spruce workflows without requiring Microsoft API integration—users screenshot/paste from OneNote for OCR extraction, preserving the beloved "print to OneNote" + Surface Pen annotation workflow.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-29 | 1.0 | Initial PRD created from Project Brief; on-premises SQLite/CouchDB architecture | John (PM) |
| 2025-11-29 | 1.1 | Added architecture recommendations: per-patient branching conflict resolution, chart checkout system, real-time sync alerts, Sprint 0 spikes, updated tech stack (@journeyapps/sqlcipher, Drizzle ORM), NFR29-35 | Winston (Architect) |
| 2025-11-30 | 1.2 | PO validation: Fixed E7-S12 dependency - AI merge now optional with manual fallback (resolves E7→E13 circular dependency) | Sarah (PO) |

---

## Reference Data Requirements

The system requires medical reference databases for OCR text normalization, validation, and care plan generation.

### Included Reference Databases

| Database | File | Records | Purpose |
|----------|------|---------|---------|
| **Medications** | Ref_Medication_Info.csv | ~10,000+ | Brand→generic mapping, drug class (HIC hierarchy), NDC, RxNorm |
| **CPT Codes** | Ref_CPT Procedure Codes.csv | ~500+ | Procedure code validation, E/M codes, labs, vaccines |
| **ICD-10 Codes** | Ref_ICD Codes.csv | ~10,000+ | Diagnosis code validation, parent hierarchy |
| **Lab Reference Ranges** | Ref_Lab_ReferenceRanges.csv | 65 tests | LOINC codes, normal/critical ranges, age/sex variations |
| **Lab Panels** | Ref_Lab_Panels.csv | 80 mappings | Panel→component groupings (BMP, CMP, CBC, Lipid, etc.) |
| **Vital Signs** | Ref_Vitals_ReferenceRanges.csv | 45 entries | BP classifications (AHA), HR, SpO2, BMI categories |
| **Radiology Studies** | Ref_Radiology_Studies.csv | 60 studies | XR, CT, MRI, US, Nuclear with CPT codes and indications |
| **CVX Immunizations** | Ref_CVX_Immunizations.csv | 55 vaccines | Adult/pediatric vaccines, schedules, CPT codes, NDC |

### Optional Extended Databases (if starter files insufficient)

| Database | Source | Purpose |
|----------|--------|---------|
| **Full LOINC Database** | loinc.org (free registration) | 100,000+ lab codes if starter 65 tests insufficient |
| **Full CVX Database** | CDC IIS (free) | Complete vaccine list if starter 55 vaccines insufficient |

### OCR Matching Requirements

When OCR extracts clinical text, the system shall:
1. **Normalize medication names**: Match brand names to generic equivalents using RXNORM
2. **Validate diagnosis codes**: Confirm ICD-10 format and existence in reference database
3. **Parse lab values**: Extract test name + value, match to LOINC, flag abnormal results
4. **Identify procedures**: Match procedure descriptions to CPT codes
5. **Categorize timeline entries**: Drug changes, lab results, vital signs, imaging, procedures

---

## Functional Requirements

### Phase 1A - Emergency Data Capture (Due 12/31/2025)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | The system shall accept patient timeline data via screenshot upload, image paste (Ctrl+V), or direct text paste | P0 |
| FR2 | The system shall extract text from screenshots using OCR (Azure Cognitive Services Computer Vision API) | P0 |
| FR3 | The system shall allow users to tag extracted data to specific patients using MRN, name, or DOB lookup | P0 |
| FR4 | The system shall track patient consent status with fields: consent_status (Pending\|Obtained\|Declined), consent_method (Paper\|Spruce Text\|DocuSign\|Verbal), consent_date, spruce_message_timestamp, docusign_envelope_id, invitation_sent_date, invitation_method | P0 |
| FR5 | The system shall support manual data entry for consent tracking and APCM enrollment status | P0 |
| FR6 | The system shall display a patient list with columns: MRN, Name, DOB, Address, Phone, Email, Last DOS, Consent Status, APCM Status | P0 |
| FR7 | The system shall store all patient data in local SQLite database with SQLCipher AES-256 encryption | P0 |
| FR8 | The system shall verify BitLocker full-disk encryption is enabled on Windows device at startup, displaying warning if disabled | P0 |
| FR9 | The system shall support basic search and filtering by patient name, MRN, consent status, APCM enrollment | P0 |

### Phase 1B - Care Plans & Team Collaboration (Jan-Feb 2025)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR10 | The system shall generate APCM care plans following Home Team template format with sections: Demographics, APCM Orientation, People Involved, Clinical Goals, General Tasks, Medications, Allergies, Active Problem List (Story/Timeline/Impression/Protocol/Patient Goals/Care Team Tasks per diagnosis), Historical Problems, Health Maintenance, Personalized Standing Orders | P1 |
| FR11 | The system shall export care plans in both markdown (.md) and plain text (.txt) formats | P1 |
| FR12 | The system shall support 4 concurrent users (Dr. Green, LaChandra, Lindsay, Jenny) with role-based permissions | P1 |
| FR13 | The system shall synchronize local SQLite database with on-premises CouchDB server over HTTPS/TLS 1.2+ when network connectivity is available | P1 |
| FR14 | The system shall operate fully offline, queuing sync operations until connectivity returns | P1 |
| FR15 | The system shall provide local OCR fallback using ONNX Runtime when Azure Cognitive Services is unavailable (offline scenario) | P1 |
| FR16 | The system shall import patient lists from Excel files with columns: MRN, DOB, Name, Address, Contact Info, Last DOS | P1 |
| FR17 | The system shall integrate with Spruce Health API (read-only) to retrieve patient communications, demographics, phone/email, family member information | P1 |
| FR18 | The system shall track patient scheduling with fields: next_followup_due_date, contact_priority (auto-calculated), schedule_screenshot_captures, rescheduling_status (Not Contacted\|Contacted\|Scheduled at Home Team\|Declined), original_southview_appt_date, home_team_scheduled_date | P1 |
| FR19 | The system shall display patient follow-up list sorted by contact_priority for staff outreach workflow | P1 |
| FR20 | The system shall log all user actions (logins, patient record access, modifications) with timestamp, user ID, device ID to audit database with 6-year retention (HIPAA §164.312(b) compliance) | P1 |

### Phase 1C - AI Enhancement & Bulk Processing (Mar-Apr 2025)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR21 | The system shall parse Spruce Health conversation threads to distinguish patient vs. family member messages using AI context detection | P2 |
| FR22 | The system shall batch process APCM billing authorization transfers for 450+ patients with consent documentation export | P2 |
| FR23 | The system shall integrate IBM Granite model (local inference via llama.cpp or ONNX Runtime) for care plan content suggestions | P2 |
| FR24 | The system shall support bulk OCR processing of multiple screenshots in queue | P2 |
| FR25 | The system shall extract structured timeline data from OCR text using format detection: `-- mm/dd/yyyy: [values] --> [action plan]` | P2 |
| FR26 | The system shall support Windows Hello or FIDO2 token multi-factor authentication (prepare for HIPAA mandatory MFA requirement) | P2 |

---

## Non-Functional Requirements

### Performance & Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR1 | Local database capacity | 1,384 patients × 50KB avg = ~70MB without degradation |
| NFR2 | OCR text extraction time | < 5 seconds for typical screenshot (1920×1080) |
| NFR3 | Application startup time | < 3 seconds on cold start |
| NFR4 | Search response time | < 500ms for patient lookup |
| NFR5 | Care plan generation time | < 10 seconds for complete APCM care plan |
| NFR6 | Offline operation duration | Unlimited (days/weeks without connectivity) |
| NFR7 | Sync conflict resolution | Per-patient version branching with sync summary dialog; user chooses "Your Version" vs "Team Version"; all competing versions archived for audit; AI-assisted merge option using local IBM Granite |

### Security & Compliance (HIPAA)

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR8 | Encryption at rest (database) | SQLCipher AES-256-CBC with PBKDF2 key derivation |
| NFR9 | Encryption at rest (disk) | BitLocker AES-256 (Windows 10/11 Pro/Enterprise) |
| NFR10 | Encryption in transit | HTTPS/TLS 1.2+ for all CouchDB replication |
| NFR11 | Access control | Unique user IDs, no shared accounts, role-based permissions |
| NFR12 | Session management | Auto-logout after 15 minutes inactivity |
| NFR13 | Audit logging | All access/modifications logged with 6-year retention |
| NFR14 | Audit log integrity | Append-only database, consider WORM storage for tamper-proof |
| NFR15 | MFA readiness | Architecture supports Windows Hello/FIDO2 integration |
| NFR16 | Data backup | Daily Restic backup to local NAS, weekly air-gapped offsite |

### Reliability & Availability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR17 | Offline-first operation | Core features work without any network connectivity |
| NFR18 | Data durability | Zero data loss on application crash or power failure |
| NFR19 | Sync reliability | Automatic retry with exponential backoff on network failure |
| NFR20 | Conflict detection | Log all sync conflicts for manual review |

### Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR21 | Screenshot paste workflow | Ctrl+V directly into patient record captures and OCRs in one action |
| NFR22 | Learning curve | Clinical staff productive within 30 minutes training |
| NFR23 | Accessibility | WCAG 2.1 AA compliance for core workflows |
| NFR24 | Brand consistency | Home Team visual identity (HTnav icons) throughout UI |

### Maintainability

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR25 | Technology stack | Electron + React + TypeScript (modern, well-supported) |
| NFR26 | Database portability | SQLite file can be copied/backed up as single file |
| NFR27 | Update mechanism | Electron auto-updater with code signing |
| NFR28 | Logging | Structured JSON logs with configurable verbosity |

### Real-Time Collaboration

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR29 | Chart checkout system | Prevent simultaneous edits with checkout lock; auto-release after 15 min idle or 30 min max |
| NFR30 | Sync alert notifications | PHI-safe OS notifications ("A colleague updated a patient chart") for chart updates and checkout requests |
| NFR31 | Ping notifications | Allow user to request colleague release chart via Windows toast notification |
| NFR32 | Adaptive polling | CouchDB _changes feed: 2s when focused+patient open, 10s focused+no patient, 60s background |

### Disaster Recovery

| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR33 | Key recovery | Recovery key generated on first launch, displayed once for secure storage; enables database unlock if primary key lost |
| NFR34 | Version escalation | Unresolved conflicts escalate: 0-2 days gentle reminder, 7-10 days stale warning, 15 days admin review/expiration |
| NFR35 | Critical field protection | Consent status, consent date, APCM enrollment fields never auto-merge; require explicit user decision |

---

## User Interface Design Goals

### Design Principles

1. **Clinical Efficiency First**: Minimize clicks for common workflows (paste screenshot → tag patient → save)
2. **Offline-Aware UI**: Clear visual indicators for sync status (synced, pending, offline)
3. **Information Density**: Show relevant patient data without excessive scrolling
4. **Home Team Brand Identity**: Consistent use of HTnav icons, color palette, imagery
5. **Accessibility**: High contrast, keyboard navigation, screen reader support

### Primary Views

#### 1. Patient List View (Dashboard)
- **Purpose**: Central hub for patient management and consent tracking
- **Layout**: Data table with sortable columns, filter sidebar, search bar
- **Icon**: `HTnav_folder.png` or `Media/Navigation/Image_population explorer.png`
- **Key Elements**:
  - Patient table: MRN, Name, DOB, Last DOS, Consent Status (color-coded), APCM Status
  - Quick filters: All, Pending Consent, Obtained, APCM Enrolled
  - Search bar with instant results
  - Sync status indicator (corner badge)

#### 2. Patient Detail View
- **Purpose**: View/edit individual patient record with captured data
- **Layout**: Header with demographics, tabbed sections below
- **Icon**: `HTnav_clipboard.png`
- **Tabs**:
  - **Captures**: Timeline of screenshots/text with OCR results
  - **Consent**: Status tracking with timestamps and method details
  - **Care Plan**: Generated APCM care plan (view/edit/export)
  - **Schedule**: Follow-up tracking and appointment migration
  - **Communications**: Spruce messages (read-only, Phase 1B)

#### 3. Capture Workspace
- **Purpose**: Paste/upload screenshots, OCR extraction, patient tagging
- **Layout**: Drop zone (left), OCR preview (center), patient selector (right)
- **Icon**: `HTnav_magnifying glass.png`
- **Workflow**:
  1. Paste screenshot (Ctrl+V) or click to upload
  2. OCR extracts text automatically
  3. User selects patient from dropdown or creates new
  4. User tags data type (Timeline, Medication, Note, etc.)
  5. Save → data appears in patient's Captures tab

#### 4. Care Plan Generator
- **Purpose**: Create APCM-compliant care plans from captured data
- **Layout**: Patient selector, template preview, export options
- **Icon**: `HTnav_clipboard.png`
- **Sections** (matching template):
  - Demographics (auto-populated from patient record)
  - APCM Orientation checklist
  - Active Problem List with Story/Timeline/Impression/Protocol per diagnosis
  - Medications, Allergies, Health Maintenance
- **Export**: Markdown (.md) or Plain Text (.txt)

#### 5. Follow-Up Queue
- **Purpose**: Staff prioritization for patient outreach and scheduling
- **Layout**: Prioritized list with action buttons
- **Icon**: `HTnav_payclock.png`
- **Columns**: Patient Name, Due Date, Priority (High/Medium/Low), Status, Actions
- **Actions**: Mark Contacted, Schedule Appointment, Decline

#### 6. Settings & Admin
- **Purpose**: Configuration, user management, sync settings
- **Icon**: `HTnav_team.png` (for user management)
- **Sections**:
  - User Management (add/remove users, role assignment)
  - Sync Configuration (server URL, sync frequency)
  - Encryption Status (SQLCipher key, BitLocker check)
  - Audit Log Viewer (filterable by user, date, action)

### Brand Asset Integration

| Icon File | Usage |
|-----------|-------|
| `HTnav_Problem List.png` | Active Problems section in Care Plan |
| `HTnav_Rx_bottle.png` | Medications tab/section |
| `HTnav_allergies.png` | Allergies section |
| `HTnav_clipboard.png` | Care Plans, Notes, Patient Detail |
| `HTnav_stethoscope.png` | Clinical Assessment sections |
| `HTnav_vitals.png` | Vital Signs data |
| `HTnav_syringe.png` | Immunizations |
| `HTnav_beaker icon.png` | Lab Results |
| `HTnav_magnifying glass.png` | Search, Capture Workspace |
| `HTnav_folder.png` | Patient Files, Document Storage |
| `HTnav_team.png` | User Management, Team Roster |
| `HTnav_cellphone.png` | Spruce Communications |
| `HTnav_payclock.png` | Scheduling, Follow-Up Queue |
| `HTnav_$.png` | APCM Billing, Authorization Status |
| `HTnav_ribbon.png` | Status Badges (consent obtained, etc.) |
| `Image_Home Team Logic.png` | Splash Screen, About Dialog |
| `Image_medical records cartoon.png` | Patient Explorer main header |
| `Image_patient onboarding.png` | Consent Workflow screens |

---

## Technical Assumptions

### Architecture: Offline-First Hub-and-Spoke

```
┌─────────────────────────────────────────────────────────────┐
│ Windows 10/11 Pro/Enterprise (BitLocker Required)          │
├─────────────────────────────────────────────────────────────┤
│ Patient Explorer (Electron 28+ / React 18 / TypeScript 5)  │
│   ├─ SQLite 3.x + SQLCipher 4.x (AES-256 encryption)       │
│   ├─ PouchDB (sync adapter for CouchDB replication)        │
│   ├─ OCR: Azure Cognitive Services (online) OR             │
│   │        Tesseract.js/ONNX (offline fallback)            │
│   └─ Node.js 20 LTS runtime                                │
└─────────────────────────────────────────────────────────────┘
                        ↕ HTTPS/TLS 1.2+ (when connected)
┌─────────────────────────────────────────────────────────────┐
│ On-Premises Server (Home Study / Clinic Closet)            │
├─────────────────────────────────────────────────────────────┤
│ CouchDB 3.x (Apache 2.0 license)                           │
│   ├─ Hub database for multi-device sync                    │
│   ├─ BitLocker/LUKS full-disk encryption                   │
│   └─ Daily Restic backups → Local NAS                      │
├─────────────────────────────────────────────────────────────┤
│ Optional: IBM Granite 3B model (Phase 1C)                  │
│   └─ llama.cpp or ONNX Runtime (local AI inference)        │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Desktop Framework** | Electron 28+ | Cross-platform, mature, large ecosystem, auto-update support |
| **Frontend** | React 18 + TypeScript 5 | Component-based, type-safe, extensive tooling |
| **State Management** | Zustand or Redux Toolkit | Lightweight, TypeScript-friendly |
| **Local Database** | SQLite 3 + @journeyapps/sqlcipher 5.x | Zero-cost, FIPS 140-2 certified encryption, pre-built native bindings (avoids build chain complexity) |
| **Database ORM** | Drizzle ORM | Type-safe queries, compile-time schema validation, prevents TypeScript/SQL drift |
| **Sync Layer** | PouchDB 8.x (LevelDB) → CouchDB 3.3+ | PouchDB for sync state only (no PHI); CouchDB for multi-device replication |
| **OCR (Online)** | Azure Cognitive Services | High accuracy, fast, pay-per-use |
| **OCR (Offline)** | Tesseract.js or ONNX | No cloud dependency, acceptable accuracy for structured text |
| **AI (Phase 1C)** | IBM Granite 3B | Open-source, local inference, no cloud dependency |
| **Build/Bundle** | Vite + electron-builder | Fast builds, code signing, auto-update |
| **Testing** | Vitest + Playwright | Unit and E2E testing |

### Key Technical Decisions

1. **SQLite over IndexedDB**: SQLite with SQLCipher provides stronger encryption guarantees and FIPS 140-2 certification required for healthcare
2. **CouchDB over Firebase**: Self-hosted, no vendor BAA required, complete data sovereignty
3. **Electron over web app**: Offline-first requirement, local file system access for screenshots, BitLocker integration
4. **Azure OCR initially**: Fastest path to 12/31 deadline; add local fallback in Phase 1B
5. **No Microsoft Graph API**: Screenshot/paste workflow eliminates OneNote API dependency while preserving team's existing workflow
6. **PouchDB for sync**: Battle-tested CouchDB replication protocol, handles offline/online transitions gracefully

### Infrastructure Requirements

| Component | Specification |
|-----------|---------------|
| **Client Devices** | Windows 10/11 Pro or Enterprise (BitLocker required), 8GB+ RAM, SSD recommended |
| **On-Premises Server** | Mini PC or NUC, 16GB+ RAM, 256GB+ SSD, Windows Server or Ubuntu LTS |
| **Network** | LAN connectivity between devices; internet optional (Azure OCR fallback) |
| **Backup Storage** | NAS with RAID or external USB drive for air-gapped weekly backups |

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Physical Security                                  │
│   └─ Devices in locked office/home study                   │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Full-Disk Encryption                              │
│   └─ BitLocker AES-256 (Windows), LUKS (Linux server)      │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Database Encryption                               │
│   └─ SQLCipher AES-256-CBC with PBKDF2 (256,000 iterations)│
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Transport Encryption                              │
│   └─ HTTPS/TLS 1.2+ for all CouchDB replication            │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Application Security                              │
│   └─ Unique user IDs, role-based access, audit logging     │
├─────────────────────────────────────────────────────────────┤
│ Layer 6: Backup Security                                   │
│   └─ Encrypted Restic backups, air-gapped offsite copies   │
└─────────────────────────────────────────────────────────────┘
```

---

## Epic List

| Epic | Name | Phase | Description |
|------|------|-------|-------------|
| E1 | Core Application Foundation | 1A | Electron app scaffold, SQLite/SQLCipher integration, basic UI shell |
| E2 | Screenshot Capture & OCR | 1A | Paste/upload screenshots, Azure Cognitive Services OCR, text extraction |
| E3 | Patient Data Management | 1A | Patient CRUD, tagging captures to patients, basic search |
| E4 | Consent Tracking | 1A | Multi-method consent status tracking (Paper, Spruce, DocuSign, Verbal) |
| E5 | Security Foundation | 1A | BitLocker check, SQLCipher encryption, audit logging foundation |
| E6 | Care Plan Generation | 1B | APCM template implementation, markdown/text export |
| E7 | Multi-User & Sync | 1B | CouchDB sync, PouchDB integration, user management |
| E8 | Scheduling & Follow-Up | 1B | Follow-up queue, priority calculation, appointment tracking |
| E9 | Spruce Integration | 1B | Spruce Health API read integration, communication display |
| E10 | Offline OCR | 1B | Local Tesseract.js/ONNX OCR fallback for offline operation |
| E11 | AI Communication Parsing | 1C | Family member detection in Spruce conversations |
| E12 | APCM Batch Processing | 1C | Bulk authorization transfer with consent documentation |
| E13 | IBM Granite Integration | 1C | Local AI model for care plan suggestions |
| E14 | Enhanced Timeline Extraction | 1C | Structured parsing of `-- mm/dd/yyyy: [values] --> [action]` format |
| E15 | MFA Implementation | 1C | Windows Hello / FIDO2 integration |

---

## Epic Details

### Epic 1: Core Application Foundation

**Goal**: Establish the Electron application scaffold with SQLite/SQLCipher database and basic UI shell using Home Team branding.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E1-S1 | Initialize Electron + React + TypeScript project | 3 | Project builds, runs, shows blank window |
| E1-S2 | Implement SQLite + SQLCipher database layer | 5 | Database creates, encrypts with AES-256, basic CRUD works |
| E1-S3 | Create main application shell with navigation | 5 | Sidebar navigation, header with branding, content area |
| E1-S4 | Implement patient data model and schema | 3 | Patient table with all required fields, migrations work |
| E1-S5 | Add Home Team branding (icons, colors, splash) | 2 | HTnav icons display correctly, splash screen shows on startup |
| E1-S6 | Implement basic window management | 2 | Minimize, maximize, close; remembers window position |

**Dependencies**: None (foundation epic)
**Total Points**: 20

---

### Epic 2: Screenshot Capture & OCR

**Goal**: Enable users to paste screenshots and extract text using Azure Cognitive Services OCR.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E2-S1 | Implement clipboard paste handler for images | 3 | Ctrl+V captures image from clipboard, displays preview |
| E2-S2 | Add file upload for screenshots | 2 | Drag-drop and file picker support PNG/JPG/BMP |
| E2-S3 | Integrate Azure Cognitive Services Computer Vision API | 5 | API call extracts text from image, returns structured result |
| E2-S4 | Display OCR results with confidence highlighting | 3 | Show extracted text, highlight low-confidence words |
| E2-S5 | Allow manual correction of OCR text | 2 | User can edit extracted text before saving |
| E2-S6 | Store captures with original image and extracted text | 3 | Both image blob and text saved to database |

**Dependencies**: E1 (Core Foundation)
**Total Points**: 18

---

### Epic 3: Patient Data Management

**Goal**: Enable CRUD operations for patients with tagging of captures and basic search.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E3-S1 | Implement patient list view with data table | 5 | Sortable, paginated table with required columns |
| E3-S2 | Create patient detail view with tabs | 5 | Header with demographics, tabbed content area |
| E3-S3 | Add patient search with instant results | 3 | Search by name, MRN, DOB; results update as typing |
| E3-S4 | Implement patient create/edit forms | 3 | Form validation, save to database |
| E3-S5 | Tag captures to patients | 3 | Select patient when saving capture, displays in patient's Captures tab |
| E3-S6 | Import patients from Excel file | 5 | Parse Excel, map columns, bulk insert with duplicate detection |

**Dependencies**: E1 (Core Foundation), E2 (Capture for tagging)
**Total Points**: 24

---

### Epic 4: Consent Tracking

**Goal**: Track multi-method consent status with full audit trail.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E4-S1 | Add consent status fields to patient model | 2 | All consent fields in schema, migrations applied |
| E4-S2 | Create consent tracking form | 3 | Capture all consent methods with timestamps |
| E4-S3 | Display consent status in patient list | 2 | Color-coded badges (Pending=yellow, Obtained=green, Declined=red) |
| E4-S4 | Implement consent history log | 3 | Track all status changes with timestamps |
| E4-S5 | Filter patients by consent status | 2 | Quick filters for Pending, Obtained, Declined |
| E4-S6 | Add APCM enrollment status tracking | 2 | APCM fields, enrollment date, authorization number |

**Dependencies**: E3 (Patient Management)
**Total Points**: 14

---

### Epic 5: Security Foundation

**Goal**: Implement HIPAA-compliant security controls including BitLocker verification and audit logging.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E5-S1 | Implement BitLocker status check on startup | 3 | WMI query checks encryption status, warning if disabled |
| E5-S2 | Create SQLCipher key management | 5 | Secure key derivation, key rotation capability |
| E5-S3 | Implement user authentication | 5 | Login screen, password validation, session management |
| E5-S4 | Add auto-logout on inactivity | 2 | 15-minute timeout, configurable in settings |
| E5-S5 | Create audit log database and logging service | 5 | Log all access/modifications with required fields |
| E5-S6 | Build audit log viewer | 3 | Filterable table, export capability |

**Dependencies**: E1 (Core Foundation)
**Total Points**: 23

---

### Epic 6: Care Plan Generation

**Goal**: Generate APCM-compliant care plans from captured patient data.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E6-S1 | Parse care plan template structure | 3 | Template sections mapped to data model |
| E6-S2 | Create care plan editor UI | 8 | Section-by-section editor matching template format |
| E6-S3 | Auto-populate demographics from patient record | 2 | Name, DOB, address, contacts filled automatically |
| E6-S4 | Implement Active Problem List with Story/Timeline/Impression/Protocol | 8 | Add/edit/reorder diagnoses with all subsections |
| E6-S5 | Export care plan as Markdown | 3 | Well-formatted .md file matching template |
| E6-S6 | Export care plan as Plain Text | 2 | Clean .txt file for EMR paste |
| E6-S7 | Save care plan drafts | 2 | Auto-save, resume editing |

**Dependencies**: E3 (Patient Management)
**Total Points**: 28

---

### Epic 7: Multi-User & Sync

**Goal**: Enable team collaboration with CouchDB synchronization.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E7-S1 | Set up CouchDB server configuration | 3 | Server install docs, HTTPS setup |
| E7-S2 | Implement PouchDB sync adapter | 5 | SQLite ↔ CouchDB replication works |
| E7-S3 | Add sync status indicator to UI | 2 | Badge shows synced/pending/offline status |
| E7-S4 | Handle sync conflicts | 5 | Detect conflicts via PouchDB; create PatientVersion records; trigger sync alerts |
| E7-S5 | Create user management UI | 5 | Add/remove users, assign roles |
| E7-S6 | Implement role-based permissions | 5 | Admin vs. User roles, feature restrictions |
| E7-S7 | Queue operations when offline | 3 | Operations stored, synced when online |
| E7-S8 | Implement chart checkout system | 5 | Acquire/release checkout with 15min idle + 30min max timeout; heartbeat mechanism |
| E7-S9 | Add ping notification for chart requests | 3 | Windows toast API + in-app notification; PHI-safe message text |
| E7-S10 | Create sync summary dialog | 5 | List all conflicts; show "Your Version" vs "Team Version"; resolution options |
| E7-S11 | Implement per-patient version archiving | 5 | Archive competing versions; notify authors; 15-day escalation timeline |
| E7-S12 | Add manual merge with optional AI assist | 3 | Manual side-by-side merge UI; AI merge button disabled until E13 complete; graceful fallback |
| E7-S13 | Implement CouchDB _changes feed listener | 3 | Adaptive polling (2s/10s/60s); real-time checkout awareness |

**Dependencies**: E5 (Security for user auth)
**Optional Enhancement**: E13 (IBM Granite) enables AI-assisted merge in E7-S12
**Total Points**: 52

---

### Epic 8: Scheduling & Follow-Up

**Goal**: Track patient follow-up due dates and prioritize staff outreach.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E8-S1 | Add scheduling fields to patient model | 2 | All scheduling fields in schema |
| E8-S2 | Create follow-up queue view | 5 | Prioritized list with action buttons |
| E8-S3 | Implement priority calculation algorithm | 3 | Auto-calculate based on due date, APCM status |
| E8-S4 | Capture schedule screenshots | 3 | Attach schedule images to patient records |
| E8-S5 | Track rescheduling status | 2 | Status transitions with timestamps |
| E8-S6 | Southview appointment migration tracking | 3 | Original date, new date, status |

**Dependencies**: E3 (Patient Management)
**Total Points**: 18

---

### Epic 9: Spruce Integration

**Goal**: Read patient communications from Spruce Health API.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E9-S1 | Implement Spruce Health API client | 5 | Authentication, rate limiting, error handling |
| E9-S2 | Fetch patient demographics from Spruce | 3 | Name, DOB, phone, email synced |
| E9-S3 | Retrieve conversation threads | 5 | Messages displayed in patient detail |
| E9-S4 | Display communications in patient detail | 3 | Chronological message view |
| E9-S5 | Extract consent timestamp from text messages | 3 | Parse "yes" responses with timestamps |

**Dependencies**: E3 (Patient Management)
**Total Points**: 19

---

### Epic 10: Offline OCR

**Goal**: Provide local OCR capability for offline operation.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E10-S1 | Integrate Tesseract.js or ONNX OCR model | 5 | Local OCR extracts text without network |
| E10-S2 | Implement OCR provider fallback logic | 3 | Use Azure when online, local when offline |
| E10-S3 | Optimize local OCR performance | 3 | Acceptable speed (<10s) for typical screenshots |
| E10-S4 | Compare accuracy between providers | 2 | Document accuracy differences |

**Dependencies**: E2 (Screenshot Capture)
**Total Points**: 13

---

### Epic 11: AI Communication Parsing

**Goal**: Use AI to distinguish patient vs. family member in Spruce conversations.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E11-S1 | Design prompt for family member detection | 3 | Prompt identifies speaker changes in conversations |
| E11-S2 | Integrate with IBM Granite or cloud AI | 5 | API call returns speaker classification |
| E11-S3 | Display speaker attribution in message view | 3 | Messages labeled with detected speaker |
| E11-S4 | Allow manual correction of speaker | 2 | User can override AI classification |

**Dependencies**: E9 (Spruce Integration), E13 (IBM Granite)
**Total Points**: 13

---

### Epic 12: APCM Batch Processing

**Goal**: Process bulk authorization transfers with consent documentation.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E12-S1 | Create APCM patient filter view | 3 | List all 450+ APCM patients with status |
| E12-S2 | Batch export consent documentation | 5 | Generate PDF/CSV of consent records |
| E12-S3 | Track authorization transfer status | 3 | Status per patient (Pending, Submitted, Confirmed) |
| E12-S4 | Generate transfer summary report | 3 | Aggregate report for billing team |

**Dependencies**: E4 (Consent Tracking)
**Total Points**: 14

---

### Epic 13: IBM Granite Integration

**Goal**: Enable local AI inference for care plan suggestions.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E13-S1 | Set up llama.cpp or ONNX Runtime | 5 | Local model runs on server hardware |
| E13-S2 | Download and configure IBM Granite 3B model | 3 | Model loads successfully |
| E13-S3 | Create care plan suggestion prompts | 5 | Prompts generate relevant suggestions |
| E13-S4 | Integrate suggestions into care plan editor | 3 | AI suggestions shown inline |
| E13-S5 | Add user feedback for suggestions | 2 | Accept/reject/edit suggestions |

**Dependencies**: E6 (Care Plan Generation)
**Total Points**: 18

---

### Epic 14: Enhanced Timeline Extraction

**Goal**: Parse structured timeline data from OCR text.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E14-S1 | Detect timeline format in OCR text | 3 | Regex matches `-- mm/dd/yyyy: ... --> ...` pattern |
| E14-S2 | Extract structured timeline entries | 5 | Parse date, values, action into fields |
| E14-S3 | Associate timelines with diagnoses | 3 | Link entries to problem list items |
| E14-S4 | Display timeline in patient detail | 3 | Chronological view with formatting |

**Dependencies**: E2 (OCR), E6 (Care Plan for problem list)
**Total Points**: 14

---

### Epic 15: MFA Implementation

**Goal**: Add multi-factor authentication using Windows Hello or FIDO2.

**Stories**:

| ID | Story | Points | Acceptance Criteria |
|----|-------|--------|---------------------|
| E15-S1 | Integrate Windows Hello API | 5 | Biometric/PIN authentication works |
| E15-S2 | Add FIDO2 security key support | 5 | Hardware key authentication works |
| E15-S3 | Create MFA enrollment flow | 3 | Users can register MFA methods |
| E15-S4 | Enforce MFA at login | 2 | MFA required after password |
| E15-S5 | Document MFA configuration | 1 | Admin guide for setup |

**Dependencies**: E5 (Security Foundation)
**Total Points**: 16

---

## Sprint 0: Technical Spikes

Before Phase 1A development begins, the following technical validations are required:

| Spike | Purpose | Duration | Success Criteria |
|-------|---------|----------|------------------|
| S0-1 | SQLCipher Build Verification | 1 day | @journeyapps/sqlcipher compiles on Windows 10/11; CRUD operations work with AES-256 encryption |
| S0-2 | PouchDB + CouchDB Sync | 1-2 days | Bidirectional replication works; offline queue syncs on reconnect |
| S0-3 | CouchDB _changes Feed | 1 day | Real-time change notifications received; adaptive polling implemented |
| S0-4 | Tesseract.js Accuracy | 1 day | OCR accuracy ≥85% on Allscripts worksheet screenshots; document accuracy gaps |
| S0-5 | Drizzle ORM Evaluation | 0.5 days | Type-safe queries work with SQLCipher; migration system functional |
| S0-6 | Key Recovery Procedure | 0.5 days | Document key recovery flow; test recovery key unlock |

**Sprint 0 Contingencies:**
- If S0-1 fails: Fall back to better-sqlite3 + manual SQLCipher build
- If S0-2 fails: Evaluate direct CouchDB HTTP sync without PouchDB
- If S0-4 shows <70% accuracy: Prioritize Azure OCR, defer Tesseract to Phase 1C

---

## PM Checklist Results

| Check | Status | Notes |
|-------|--------|-------|
| All functional requirements traceable to epics | ✅ | FR1-FR26 mapped to E1-E15 |
| Non-functional requirements addressed | ✅ | Performance, security, usability, real-time collaboration covered |
| Phase 1A deadline achievable | ⚠️ | Aggressive but feasible with E1-E5; Sprint 0 spikes reduce risk |
| HIPAA compliance addressed | ✅ | NFR8-NFR16 + NFR33-35 cover required controls |
| Offline-first architecture validated | ✅ | SQLite/CouchDB sync pattern proven |
| OneNote integration removed | ✅ | Screenshot workflow eliminates API dependency |
| Brand assets cataloged | ✅ | 19 icon types mapped to UI elements |
| Scheduling feature included | ✅ | E8 covers follow-up queue |
| IBM Granite integration planned | ✅ | E13 for Phase 1C; E7-S12 for AI merge |
| Cost reduction achieved | ✅ | Zero licensing costs vs. $1,500-6,500/year Azure |
| Chart checkout system designed | ✅ | NFR29-31 + E7-S8/S9 prevent simultaneous edits |
| Conflict resolution strategy defined | ✅ | Per-patient branching with sync summary dialog (NFR7) |
| Key recovery documented | ✅ | NFR33 + S0-6 spike for disaster recovery |
| Sprint 0 spikes defined | ✅ | 6 technical validations before Phase 1A |

---

## Next Steps

### For Architect (Winston)

Design detailed technical architecture including:
1. SQLite schema with SQLCipher encryption implementation
2. CouchDB replication topology and conflict resolution strategy
3. Electron IPC architecture for secure database access
4. Azure Cognitive Services integration with offline fallback
5. Security boundary diagrams showing encryption layers
6. Deployment topology for on-premises server
7. Backup and disaster recovery procedures

### For UX Designer (Sally)

Create detailed UI/UX specifications including:
1. Wireframes for all primary views (Patient List, Detail, Capture, Care Plan, Follow-Up Queue)
2. Component library using Home Team brand assets (HTnav icons, colors)
3. User flow diagrams for critical paths (capture → tag → save, consent tracking, care plan generation)
4. Accessibility specifications (WCAG 2.1 AA)
5. Offline state visual indicators
6. Mobile/tablet considerations (Surface Pro optimization)

### For Product Owner

Validate PRD completeness:
1. Review all functional requirements against Project Brief
2. Confirm epic prioritization matches Phase 1A deadline
3. Verify consent tracking captures all legal requirements
4. Approve technical assumptions (SQLite/CouchDB vs. alternatives)

---

*Generated by John (PM) using BMAD-METHOD v2.0*
*Document Version: 1.0 | Date: 2025-11-29*
