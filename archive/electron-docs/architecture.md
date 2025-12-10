# Patient Explorer - Technical Architecture Document

**Version**: 1.0
**Date**: November 30, 2025
**Author**: Winston (Architect) - BMAD-METHOD
**Status**: Draft for Review

---

## Table of Contents

1. [Introduction & Scope](#1-introduction--scope)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Data Models](#4-data-models)
5. [IPC Channel Architecture](#5-ipc-channel-architecture)
6. [Security & Encryption](#6-security--encryption)
7. [Infrastructure & Deployment](#7-infrastructure--deployment)
8. [Testing Strategy](#8-testing-strategy)
9. [Appendices](#9-appendices)

---

## 1. Introduction & Scope

### 1.1 Purpose

This document defines the technical architecture for **Patient Explorer**, a HIPAA-compliant desktop application for capturing, organizing, and searching patient data from multiple EMR sources during practice transition.

### 1.2 Audience

- Development team (implementation reference)
- Product Owner (technical validation)
- QA team (test planning)
- Operations (deployment planning)
- Compliance officer (HIPAA verification)

### 1.3 Scope

**Phase 1 (Green Clinic):**
- 1,384 Southview patients from Allscripts EMR
- 4 initial users: Dr. Green, LaChandra Watts CRNP, Lindsay Bearden CRNP, Jenny Linard RN
- Deadline: December 31, 2025 (Allscripts access termination)

**Out of Scope:**
- Home Team Medical Services (Phase 2)
- Direct EMR API integration
- Full EMR functionality

### 1.4 Key Architectural Drivers

| Driver | Constraint | Impact |
|--------|------------|--------|
| **HIPAA Compliance** | PHI must be encrypted at rest and in transit | SQLCipher + TLS required |
| **Offline-First** | Staff work without reliable internet | Local SQLite as source of truth |
| **Multi-Device Sync** | 4+ devices sharing patient data | CouchDB hub-and-spoke replication |
| **Emergency Timeline** | 30 days to capture 1,384 patients | Aggressive scope, proven tech only |
| **Zero Cloud PHI** | PHI cannot reside in cloud storage | On-premises CouchDB, Azure OCR only |

### 1.5 Document Conventions

- **MUST**: Non-negotiable requirement (HIPAA, security)
- **SHOULD**: Strong recommendation (best practice)
- **MAY**: Optional enhancement (Phase 1B/1C)
- **NFR-X**: References Non-Functional Requirement X from PRD

---

## 2. High-Level Architecture

### 2.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │ Allscripts  │   │   Athena    │   │  OneNote    │   │   Spruce    │     │
│  │    EMR      │   │   EMR       │   │ (Screenshots)│   │ (Messages)  │     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘     │
│         │ Screenshot       │ Screenshot      │ Screenshot      │ Paste      │
│         └──────────────────┴─────────────────┴─────────────────┘            │
│                                      │                                       │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        PATIENT EXPLORER                                │  │
│  │                     (Electron Desktop App)                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                    │                                    │                    │
│         ┌─────────┴─────────┐              ┌───────────┴───────────┐       │
│         ▼                   ▼              ▼                       ▼       │
│  ┌─────────────┐     ┌─────────────┐ ┌─────────────┐     ┌─────────────┐   │
│  │   Azure     │     │  CouchDB    │ │   Local     │     │  Windows    │   │
│  │   OCR API   │     │  (Hub)      │ │   SQLite    │     │  Credential │   │
│  │  (BAA)      │     │  On-Prem    │ │  SQLCipher  │     │  Manager    │   │
│  └─────────────┘     └─────────────┘ └─────────────┘     └─────────────┘   │
│      Cloud              On-Premises      Local Device      Local Device     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ELECTRON APPLICATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        RENDERER PROCESS                              │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │    │
│  │  │  React UI     │  │  Zustand      │  │  React Query  │           │    │
│  │  │  Components   │  │  State        │  │  Cache        │           │    │
│  │  └───────┬───────┘  └───────────────┘  └───────────────┘           │    │
│  │          │                                                          │    │
│  │          ▼                                                          │    │
│  │  ┌───────────────────────────────────────────────────────────────┐ │    │
│  │  │                    PRELOAD SCRIPT                              │ │    │
│  │  │              (contextBridge API exposure)                      │ │    │
│  │  └───────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                              IPC Channels                                    │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         MAIN PROCESS                                 │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │    │
│  │  │  IPC Handler  │  │  Session      │  │  Audit        │           │    │
│  │  │  Router       │  │  Manager      │  │  Logger       │           │    │
│  │  └───────┬───────┘  └───────────────┘  └───────────────┘           │    │
│  │          │                                                          │    │
│  │          ▼                                                          │    │
│  │  ┌───────────────────────────────────────────────────────────────┐ │    │
│  │  │                     SERVICE LAYER                              │ │    │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │ │    │
│  │  │  │ Patient  │ │ Capture  │ │ Consent  │ │ CarePlan │         │ │    │
│  │  │  │ Service  │ │ Service  │ │ Service  │ │ Service  │         │ │    │
│  │  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘         │ │    │
│  │  │       └────────────┴────────────┴────────────┘                │ │    │
│  │  └───────────────────────────────────────────────────────────────┘ │    │
│  │          │                                                          │    │
│  │          ▼                                                          │    │
│  │  ┌───────────────────────────────────────────────────────────────┐ │    │
│  │  │                    DATA ACCESS LAYER                           │ │    │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │    │
│  │  │  │   Drizzle    │  │   PouchDB    │  │   Keytar     │        │ │    │
│  │  │  │   (SQLite)   │  │   (Sync)     │  │  (Secrets)   │        │ │    │
│  │  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘        │ │    │
│  │  │         │                 │                                   │ │    │
│  │  │         ▼                 ▼                                   │ │    │
│  │  │  ┌──────────────┐  ┌──────────────┐                          │ │    │
│  │  │  │  SQLCipher   │  │   LevelDB    │                          │ │    │
│  │  │  │  (PHI Data)  │  │  (Sync Only) │                          │ │    │
│  │  │  └──────────────┘  └──────────────┘                          │ │    │
│  │  └───────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Hub-and-Spoke Sync Architecture

```
                              ┌─────────────────────┐
                              │    CouchDB Hub      │
                              │   (On-Premises)     │
                              │                     │
                              │  ┌───────────────┐  │
                              │  │ patient_sync  │  │
                              │  │   database    │  │
                              │  └───────────────┘  │
                              └──────────┬──────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
           ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
           │   Dr. Green     │  │   LaChandra     │  │   Lindsay       │
           │   Surface Pro   │  │   Desktop       │  │   Laptop        │
           │                 │  │                 │  │                 │
           │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
           │ │  SQLCipher  │ │  │ │  SQLCipher  │ │  │ │  SQLCipher  │ │
           │ │  (Source    │ │  │ │  (Source    │ │  │ │  (Source    │ │
           │ │   of Truth) │ │  │ │   of Truth) │ │  │ │   of Truth) │ │
           │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │
           │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │
           │ │  PouchDB    │ │  │ │  PouchDB    │ │  │ │  PouchDB    │ │
           │ │  (Sync)     │◄┼──┼─┤  (Sync)     │◄┼──┼─┤  (Sync)     │ │
           │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │
           └─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.4 Data Flow Patterns

#### 2.4.1 Capture Workflow

```
User                  Renderer              Main Process           External
 │                       │                       │                    │
 │  Paste Screenshot     │                       │                    │
 │──────────────────────▶│                       │                    │
 │                       │  capture:create       │                    │
 │                       │──────────────────────▶│                    │
 │                       │                       │  OCR Request       │
 │                       │                       │───────────────────▶│
 │                       │                       │  OCR Response      │
 │                       │                       │◀───────────────────│
 │                       │                       │                    │
 │                       │                       │ INSERT capture     │
 │                       │                       │ INSERT audit_log   │
 │                       │                       │                    │
 │                       │  Result + OCR Text    │                    │
 │                       │◀──────────────────────│                    │
 │  Display Preview      │                       │                    │
 │◀──────────────────────│                       │                    │
```

#### 2.4.2 Sync Workflow

```
Local Device              PouchDB               CouchDB Hub         Other Device
     │                       │                       │                    │
     │  Change detected      │                       │                    │
     │──────────────────────▶│                       │                    │
     │                       │  Push replication     │                    │
     │                       │──────────────────────▶│                    │
     │                       │                       │  _changes feed     │
     │                       │                       │───────────────────▶│
     │                       │                       │  Pull replication  │
     │                       │                       │◀───────────────────│
     │                       │                       │                    │
     │                       │  Conflict detected    │                    │
     │                       │◀──────────────────────│                    │
     │  Show Sync Dialog     │                       │                    │
     │◀──────────────────────│                       │                    │
```

---

## 3. Technology Stack

### 3.1 Core Technologies

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Desktop Framework** | Electron | 28.x LTS | Cross-platform, mature, auto-update |
| **Frontend** | React | 18.x | Component-based, large ecosystem |
| **Language** | TypeScript | 5.3+ | Type safety, better tooling |
| **State Management** | Zustand | 4.x | Lightweight, TypeScript-native |
| **Local Database** | SQLite + SQLCipher | 3.45 / 5.x | Encrypted, zero-config |
| **ORM** | Drizzle ORM | 0.29+ | Type-safe queries, schema validation |
| **Sync State** | PouchDB | 8.x | CouchDB protocol, offline-first |
| **Sync Hub** | CouchDB | 3.3+ | Master-master replication |
| **Build Tool** | Vite | 5.x | Fast HMR, ESM-native |
| **Bundler** | electron-builder | 24.x | Code signing, auto-update |

### 3.2 External Services

| Service | Provider | Purpose | PHI Exposure |
|---------|----------|---------|--------------|
| **OCR (Online)** | Azure Cognitive Services | Screenshot text extraction | Transient only (not stored) |
| **OCR (Offline)** | Tesseract.js | Offline fallback | None |
| **AI (Phase 1C)** | IBM Granite 3B | Local LLM for merge assist | None (local) |

### 3.3 Development Tools

| Category | Tool | Purpose |
|----------|------|---------|
| **Testing** | Vitest | Unit + integration tests |
| **E2E Testing** | Playwright | End-to-end automation |
| **Linting** | ESLint + Prettier | Code style enforcement |
| **Git Hooks** | Husky + lint-staged | Pre-commit validation |
| **Security Audit** | npm audit + Snyk | Dependency scanning |

### 3.4 Package Selection Rationale

#### 3.4.1 Why @journeyapps/sqlcipher over better-sqlite3?

| Factor | @journeyapps/sqlcipher | better-sqlite3 + manual SQLCipher |
|--------|------------------------|-----------------------------------|
| Pre-built binaries | ✅ Windows/macOS/Linux | ❌ Requires build chain |
| FIPS 140-2 | ✅ Certified | ⚠️ Depends on build |
| Maintenance | ✅ Active | ⚠️ DIY |
| Complexity | Low | High |

#### 3.4.2 Why Drizzle ORM over Prisma/TypeORM?

| Factor | Drizzle ORM | Prisma | TypeORM |
|--------|-------------|--------|---------|
| Bundle size | ~50KB | ~2MB | ~1MB |
| Type safety | Compile-time | Runtime | Runtime |
| SQLite support | Excellent | Good | Good |
| Schema sync | TypeScript-first | Schema file | Decorators |

#### 3.4.3 Why Zustand over Redux Toolkit?

| Factor | Zustand | Redux Toolkit |
|--------|---------|---------------|
| Boilerplate | Minimal | Moderate |
| Bundle size | ~1KB | ~11KB |
| DevTools | Supported | Native |
| Learning curve | Low | Medium |

---

## 4. Data Models

### 4.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Patient     │       │     Capture     │       │     Consent     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │       │ id (PK)         │
│ lastName        │  │    │ patientId (FK)  │◀──────│ patientId (FK)  │◀─┐
│ firstName       │  │    │ captureType     │       │ status          │  │
│ dateOfBirth     │  │    │ sourceEmr       │       │ signedDate      │  │
│ mrn             │  │    │ imageData       │       │ expiresAt       │  │
│ ssn4            │  │    │ ocrText         │       │ signedBy        │  │
│ phone           │  │    │ notes           │       │ witnessedBy     │  │
│ email           │  │    │ createdAt       │       │ documentPath    │  │
│ insurerId       │  │    │ createdBy       │       │ createdAt       │  │
│ version         │  │    │ version         │       │ version         │  │
│ createdAt       │  │    └─────────────────┘       └─────────────────┘  │
│ updatedAt       │  │                                                    │
│ deletedAt       │  │    ┌─────────────────┐       ┌─────────────────┐  │
└─────────────────┘  │    │    CarePlan     │       │   PatientVersion│  │
         │           │    ├─────────────────┤       ├─────────────────┤  │
         │           └───▶│ id (PK)         │       │ id (PK)         │  │
         │                │ patientId (FK)  │◀──────│ patientId (FK)  │──┘
         │                │ planType        │       │ snapshot        │
         │                │ status          │       │ conflictSource  │
         │                │ startDate       │       │ resolvedAt      │
         │                │ content         │       │ resolvedBy      │
         │                │ generatedAt     │       │ createdAt       │
         │                │ generatedBy     │       └─────────────────┘
         │                │ version         │
         │                └─────────────────┘       ┌─────────────────┐
         │                                          │   AuditLog      │
         │                ┌─────────────────┐       ├─────────────────┤
         │                │    Checkout     │       │ id (PK)         │
         │                ├─────────────────┤       │ action          │
         └───────────────▶│ id (PK)         │       │ entityType      │
                          │ patientId (FK)  │       │ entityId        │
                          │ userId          │       │ userId          │
                          │ deviceId        │       │ ipAddress       │
                          │ acquiredAt      │       │ details         │
                          │ lastHeartbeat   │       │ previousHash    │
                          │ expiresAt       │       │ hash            │
                          └─────────────────┘       │ timestamp       │
                                                    └─────────────────┘
```

### 4.2 Drizzle Schema Definitions

```typescript
// src/db/schema/patient.ts
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';

export const patients = sqliteTable('patients', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  lastName: text('last_name').notNull(),
  firstName: text('first_name'),
  middleName: text('middle_name'),
  dateOfBirth: text('date_of_birth'), // ISO 8601: YYYY-MM-DD
  mrn: text('mrn'),
  ssn4: text('ssn4'), // Last 4 digits only
  phone: text('phone'),
  email: text('email'),
  address: text('address'),
  insurerId: text('insurer_id'),
  insurerName: text('insurer_name'),
  pcp: text('pcp'),
  apcmEligible: integer('apcm_eligible', { mode: 'boolean' }).default(false),
  apcmEnrolled: integer('apcm_enrolled', { mode: 'boolean' }).default(false),
  apcmEnrolledDate: text('apcm_enrolled_date'),
  version: integer('version').notNull().default(1),
  createdAt: text('created_at').notNull().$defaultFn(() => new Date().toISOString()),
  updatedAt: text('updated_at').notNull().$defaultFn(() => new Date().toISOString()),
  createdBy: text('created_by').notNull(),
  updatedBy: text('updated_by').notNull(),
  deletedAt: text('deleted_at'),
});

export type Patient = typeof patients.$inferSelect;
export type NewPatient = typeof patients.$inferInsert;
```

```typescript
// src/db/schema/capture.ts
export const captures = sqliteTable('captures', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  patientId: text('patient_id').notNull().references(() => patients.id),
  captureType: text('capture_type', {
    enum: ['screenshot', 'text', 'file', 'ocr_result']
  }).notNull(),
  sourceEmr: text('source_emr', {
    enum: ['allscripts', 'athena', 'onenote', 'spruce', 'other']
  }),
  imageData: text('image_data'), // Base64 or file path
  imagePath: text('image_path'),
  ocrText: text('ocr_text'),
  ocrConfidence: real('ocr_confidence'),
  notes: text('notes'),
  tags: text('tags'), // JSON array
  version: integer('version').notNull().default(1),
  createdAt: text('created_at').notNull().$defaultFn(() => new Date().toISOString()),
  createdBy: text('created_by').notNull(),
});

export type Capture = typeof captures.$inferSelect;
export type NewCapture = typeof captures.$inferInsert;
```

```typescript
// src/db/schema/consent.ts
export const consents = sqliteTable('consents', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  patientId: text('patient_id').notNull().references(() => patients.id),
  consentType: text('consent_type', {
    enum: ['apcm', 'general', 'telehealth', 'data_sharing']
  }).notNull(),
  status: text('status', {
    enum: ['pending', 'signed', 'declined', 'expired', 'revoked']
  }).notNull().default('pending'),
  signedDate: text('signed_date'),
  expiresAt: text('expires_at'),
  signedBy: text('signed_by'),
  witnessedBy: text('witnessed_by'),
  documentPath: text('document_path'),
  notes: text('notes'),
  version: integer('version').notNull().default(1),
  createdAt: text('created_at').notNull().$defaultFn(() => new Date().toISOString()),
  createdBy: text('created_by').notNull(),
});

// CRITICAL: Consent fields are protected from auto-merge
export const PROTECTED_CONSENT_FIELDS = ['status', 'signedDate', 'signedBy'] as const;
```

```typescript
// src/db/schema/checkout.ts
export const checkouts = sqliteTable('checkouts', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  patientId: text('patient_id').notNull().references(() => patients.id),
  userId: text('user_id').notNull(),
  userName: text('user_name').notNull(),
  deviceId: text('device_id').notNull(),
  acquiredAt: text('acquired_at').notNull().$defaultFn(() => new Date().toISOString()),
  lastHeartbeat: text('last_heartbeat').notNull().$defaultFn(() => new Date().toISOString()),
  expiresAt: text('expires_at').notNull(), // 30 min max from acquiredAt
  releasedAt: text('released_at'),
  releaseReason: text('release_reason', {
    enum: ['manual', 'idle_timeout', 'max_timeout', 'ping_request', 'session_end']
  }),
});
```

```typescript
// src/db/schema/audit-log.ts
export const auditLogs = sqliteTable('audit_logs', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  action: text('action', {
    enum: ['CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'SYNC', 'EXPORT', 'CONFLICT']
  }).notNull(),
  entityType: text('entity_type').notNull(),
  entityId: text('entity_id'),
  userId: text('user_id').notNull(),
  userName: text('user_name'),
  deviceId: text('device_id'),
  ipAddress: text('ip_address'),
  details: text('details'), // JSON
  previousHash: text('previous_hash'),
  hash: text('hash').notNull(),
  signature: text('signature'), // Ed25519 signature
  timestamp: text('timestamp').notNull().$defaultFn(() => new Date().toISOString()),
});

// Hash chain ensures tamper detection
export function computeAuditHash(entry: Omit<AuditLog, 'hash' | 'signature'>, previousHash: string): string {
  const payload = JSON.stringify({
    ...entry,
    previousHash,
  });
  return crypto.createHash('sha256').update(payload).digest('hex');
}
```

```typescript
// src/db/schema/patient-version.ts
export const patientVersions = sqliteTable('patient_versions', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  patientId: text('patient_id').notNull().references(() => patients.id),
  snapshot: text('snapshot').notNull(), // JSON of full patient record
  conflictSource: text('conflict_source', {
    enum: ['local', 'remote', 'merged']
  }).notNull(),
  sourceDeviceId: text('source_device_id'),
  sourceUserId: text('source_user_id'),
  resolvedAt: text('resolved_at'),
  resolvedBy: text('resolved_by'),
  resolutionType: text('resolution_type', {
    enum: ['your_version', 'team_version', 'ai_merge', 'manual_merge', 'expired']
  }),
  escalationLevel: integer('escalation_level').default(0), // 0=new, 1=reminder, 2=warning, 3=expired
  createdAt: text('created_at').notNull().$defaultFn(() => new Date().toISOString()),
});
```

### 4.3 Reference Data Tables

```typescript
// src/db/schema/reference-data.ts
export const medications = sqliteTable('ref_medications', {
  id: text('id').primaryKey(),
  genericName: text('generic_name').notNull(),
  brandNames: text('brand_names'), // JSON array
  drugClass: text('drug_class'),
  rxcui: text('rxcui'),
  ndc: text('ndc'),
});

export const labTests = sqliteTable('ref_lab_tests', {
  id: text('id').primaryKey(),
  testName: text('test_name').notNull(),
  loincCode: text('loinc_code'),
  category: text('category'),
  units: text('units'),
  normalRange: text('normal_range'),
});

export const vitalSigns = sqliteTable('ref_vital_signs', {
  id: text('id').primaryKey(),
  vitalName: text('vital_name').notNull(),
  abbreviation: text('abbreviation'),
  units: text('units'),
  normalRange: text('normal_range'),
});

export const radiologyExams = sqliteTable('ref_radiology_exams', {
  id: text('id').primaryKey(),
  examName: text('exam_name').notNull(),
  modality: text('modality'),
  cptCode: text('cpt_code'),
  bodyPart: text('body_part'),
});

export const immunizations = sqliteTable('ref_immunizations', {
  id: text('id').primaryKey(),
  vaccineName: text('vaccine_name').notNull(),
  cvxCode: text('cvx_code'),
  manufacturer: text('manufacturer'),
  routeOfAdmin: text('route_of_admin'),
});
```

---

## 5. IPC Channel Architecture

### 5.1 Channel Naming Convention

```
{domain}:{action}:{subaction?}

Examples:
- patient:list
- patient:get
- patient:create
- capture:create
- sync:status
- checkout:acquire
```

### 5.2 Channel Registry

#### 5.2.1 Patient Channels

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `patient:list` | Invoke | `{ search?, limit?, offset? }` | `Patient[]` | Required |
| `patient:get` | Invoke | `{ id }` | `Patient \| null` | Required |
| `patient:create` | Invoke | `NewPatient` | `Patient` | Required |
| `patient:update` | Invoke | `{ id, data, version }` | `Patient` | Required |
| `patient:delete` | Invoke | `{ id }` | `void` | Admin |
| `patient:search` | Invoke | `{ query, limit? }` | `Patient[]` | Required |
| `patient:timeline` | Invoke | `{ id, limit?, cursor? }` | `TimelineItem[]` | Required |

#### 5.2.2 Capture Channels

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `capture:create` | Invoke | `NewCapture` | `Capture` | Required |
| `capture:list` | Invoke | `{ patientId, limit?, cursor? }` | `Capture[]` | Required |
| `capture:get` | Invoke | `{ id }` | `Capture \| null` | Required |
| `capture:update` | Invoke | `{ id, data }` | `Capture` | Required |
| `capture:delete` | Invoke | `{ id }` | `void` | Required |
| `capture:ocr` | Invoke | `{ imageData }` | `{ text, confidence }` | Required |

#### 5.2.3 Sync Channels

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `sync:status` | Invoke | `void` | `SyncStatus` | Required |
| `sync:trigger` | Invoke | `void` | `void` | Required |
| `sync:conflicts` | Invoke | `void` | `Conflict[]` | Required |
| `sync:resolve` | Invoke | `{ conflictId, resolution }` | `void` | Required |
| `sync:change` | On | N/A | `ChangeEvent` | Required |
| `sync:error` | On | N/A | `SyncError` | Required |

#### 5.2.4 Checkout Channels

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `checkout:acquire` | Invoke | `{ patientId }` | `Checkout \| ConflictError` | Required |
| `checkout:release` | Invoke | `{ patientId }` | `void` | Required |
| `checkout:heartbeat` | Invoke | `{ patientId }` | `void` | Required |
| `checkout:status` | Invoke | `{ patientId }` | `CheckoutStatus` | Required |
| `checkout:ping` | Invoke | `{ patientId, message? }` | `void` | Required |
| `checkout:notification` | On | N/A | `CheckoutNotification` | Required |

#### 5.2.5 Consent Channels

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `consent:list` | Invoke | `{ patientId }` | `Consent[]` | Required |
| `consent:create` | Invoke | `NewConsent` | `Consent` | Required |
| `consent:update` | Invoke | `{ id, data, version }` | `Consent` | Required |
| `consent:revoke` | Invoke | `{ id, reason }` | `Consent` | Required |

#### 5.2.6 Care Plan Channels

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `careplan:generate` | Invoke | `{ patientId, type }` | `CarePlan` | Required |
| `careplan:list` | Invoke | `{ patientId }` | `CarePlan[]` | Required |
| `careplan:get` | Invoke | `{ id }` | `CarePlan` | Required |
| `careplan:export` | Invoke | `{ id, format }` | `ExportResult` | Required |

#### 5.2.7 Audit Channels

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `audit:query` | Invoke | `{ filters, limit?, cursor? }` | `AuditEntry[]` | Admin |
| `audit:export` | Invoke | `{ startDate, endDate, format }` | `ExportResult` | Admin |
| `audit:verify` | Invoke | `{ startId?, endId? }` | `VerifyResult` | Admin |

#### 5.2.8 AI Channels (Phase 1C)

| Channel | Direction | Parameters | Returns | Auth |
|---------|-----------|------------|---------|------|
| `ai:merge-suggest` | Invoke | `{ localVersion, remoteVersion }` | `MergeSuggestion` | Required |
| `ai:cancel` | Invoke | `{ requestId }` | `void` | Required |
| `ai:status` | Invoke | `void` | `AIStatus` | Required |

### 5.3 Preload Script API

```typescript
// src/preload/index.ts
import { contextBridge, ipcRenderer } from 'electron';

const api = {
  // Patient operations
  patient: {
    list: (params?: PatientListParams) => ipcRenderer.invoke('patient:list', params),
    get: (id: string) => ipcRenderer.invoke('patient:get', { id }),
    create: (data: NewPatient) => ipcRenderer.invoke('patient:create', data),
    update: (id: string, data: Partial<Patient>, version: number) =>
      ipcRenderer.invoke('patient:update', { id, data, version }),
    delete: (id: string) => ipcRenderer.invoke('patient:delete', { id }),
    search: (query: string, limit?: number) =>
      ipcRenderer.invoke('patient:search', { query, limit }),
    timeline: (id: string, params?: TimelineParams) =>
      ipcRenderer.invoke('patient:timeline', { id, ...params }),
  },

  // Capture operations
  capture: {
    create: (data: NewCapture) => ipcRenderer.invoke('capture:create', data),
    list: (patientId: string, params?: ListParams) =>
      ipcRenderer.invoke('capture:list', { patientId, ...params }),
    get: (id: string) => ipcRenderer.invoke('capture:get', { id }),
    update: (id: string, data: Partial<Capture>) =>
      ipcRenderer.invoke('capture:update', { id, data }),
    delete: (id: string) => ipcRenderer.invoke('capture:delete', { id }),
    ocr: (imageData: string) => ipcRenderer.invoke('capture:ocr', { imageData }),
  },

  // Sync operations
  sync: {
    status: () => ipcRenderer.invoke('sync:status'),
    trigger: () => ipcRenderer.invoke('sync:trigger'),
    conflicts: () => ipcRenderer.invoke('sync:conflicts'),
    resolve: (conflictId: string, resolution: ConflictResolution) =>
      ipcRenderer.invoke('sync:resolve', { conflictId, resolution }),
    onChange: (callback: (event: ChangeEvent) => void) => {
      const handler = (_: any, event: ChangeEvent) => callback(event);
      ipcRenderer.on('sync:change', handler);
      return () => ipcRenderer.removeListener('sync:change', handler);
    },
    onError: (callback: (error: SyncError) => void) => {
      const handler = (_: any, error: SyncError) => callback(error);
      ipcRenderer.on('sync:error', handler);
      return () => ipcRenderer.removeListener('sync:error', handler);
    },
  },

  // Checkout operations
  checkout: {
    acquire: (patientId: string) => ipcRenderer.invoke('checkout:acquire', { patientId }),
    release: (patientId: string) => ipcRenderer.invoke('checkout:release', { patientId }),
    heartbeat: (patientId: string) => ipcRenderer.invoke('checkout:heartbeat', { patientId }),
    status: (patientId: string) => ipcRenderer.invoke('checkout:status', { patientId }),
    ping: (patientId: string, message?: string) =>
      ipcRenderer.invoke('checkout:ping', { patientId, message }),
    onNotification: (callback: (notification: CheckoutNotification) => void) => {
      const handler = (_: any, notification: CheckoutNotification) => callback(notification);
      ipcRenderer.on('checkout:notification', handler);
      return () => ipcRenderer.removeListener('checkout:notification', handler);
    },
  },

  // Consent operations
  consent: {
    list: (patientId: string) => ipcRenderer.invoke('consent:list', { patientId }),
    create: (data: NewConsent) => ipcRenderer.invoke('consent:create', data),
    update: (id: string, data: Partial<Consent>, version: number) =>
      ipcRenderer.invoke('consent:update', { id, data, version }),
    revoke: (id: string, reason: string) =>
      ipcRenderer.invoke('consent:revoke', { id, reason }),
  },

  // Care plan operations
  carePlan: {
    generate: (patientId: string, type: CarePlanType) =>
      ipcRenderer.invoke('careplan:generate', { patientId, type }),
    list: (patientId: string) => ipcRenderer.invoke('careplan:list', { patientId }),
    get: (id: string) => ipcRenderer.invoke('careplan:get', { id }),
    export: (id: string, format: ExportFormat) =>
      ipcRenderer.invoke('careplan:export', { id, format }),
  },

  // Session info (read-only)
  session: {
    getUser: () => ipcRenderer.invoke('session:user'),
    getDevice: () => ipcRenderer.invoke('session:device'),
  },
};

contextBridge.exposeInMainWorld('api', api);

// Type declaration for renderer
declare global {
  interface Window {
    api: typeof api;
  }
}
```

### 5.4 IPC Handler Pattern

```typescript
// src/main/ipc/patient.handlers.ts
import { ipcMain } from 'electron';
import { validateSession } from '../auth/session';
import { auditLog } from '../audit/logger';
import { PatientService } from '../services/patient.service';

export function registerPatientHandlers(patientService: PatientService) {

  ipcMain.handle('patient:list', async (event, params) => {
    const session = await validateSession(event);
    if (!session) throw new Error('Unauthorized');

    const result = await patientService.list(params);

    // Audit bulk access
    await auditLog({
      action: 'READ',
      entityType: 'patient',
      entityId: null,
      userId: session.userId,
      details: { count: result.length, params },
    });

    return result;
  });

  ipcMain.handle('patient:get', async (event, { id }) => {
    const session = await validateSession(event);
    if (!session) throw new Error('Unauthorized');

    const patient = await patientService.get(id);

    if (patient) {
      await auditLog({
        action: 'READ',
        entityType: 'patient',
        entityId: id,
        userId: session.userId,
      });
    }

    return patient;
  });

  ipcMain.handle('patient:create', async (event, data) => {
    const session = await validateSession(event);
    if (!session) throw new Error('Unauthorized');

    const patient = await patientService.create({
      ...data,
      createdBy: session.userId,
      updatedBy: session.userId,
    });

    await auditLog({
      action: 'CREATE',
      entityType: 'patient',
      entityId: patient.id,
      userId: session.userId,
      details: { lastName: patient.lastName, firstName: patient.firstName },
    });

    return patient;
  });

  ipcMain.handle('patient:update', async (event, { id, data, version }) => {
    const session = await validateSession(event);
    if (!session) throw new Error('Unauthorized');

    const result = await patientService.update(id, {
      ...data,
      updatedBy: session.userId,
    }, version);

    if (result.conflict) {
      await auditLog({
        action: 'CONFLICT',
        entityType: 'patient',
        entityId: id,
        userId: session.userId,
        details: { localVersion: version, serverVersion: result.serverVersion },
      });
      throw new ConflictError(result);
    }

    await auditLog({
      action: 'UPDATE',
      entityType: 'patient',
      entityId: id,
      userId: session.userId,
      details: { fields: Object.keys(data) },
    });

    return result.patient;
  });
}
```

### 5.5 Error Handling

```typescript
// src/main/ipc/errors.ts
export class IPCError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'IPCError';
  }

  toJSON() {
    return {
      code: this.code,
      message: this.message,
      details: this.details,
    };
  }
}

export class UnauthorizedError extends IPCError {
  constructor(message = 'Authentication required') {
    super('UNAUTHORIZED', message);
  }
}

export class ForbiddenError extends IPCError {
  constructor(message = 'Permission denied') {
    super('FORBIDDEN', message);
  }
}

export class ConflictError extends IPCError {
  constructor(details: { localVersion: number; serverVersion: number }) {
    super('CONFLICT', 'Version conflict detected', details);
  }
}

export class CheckoutError extends IPCError {
  constructor(holder: { userName: string; deviceId: string }) {
    super('CHECKOUT_CONFLICT', `Chart is checked out by ${holder.userName}`, holder);
  }
}

export class ValidationError extends IPCError {
  constructor(errors: Record<string, string[]>) {
    super('VALIDATION', 'Validation failed', { errors });
  }
}
```

---

## 6. Security & Encryption

### 6.1 Defense in Depth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 7: Backup Encryption                                                   │
│   Restic AES-256 encrypted backups with separate key                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 6: Audit Integrity                                                     │
│   Hash-chained audit log with Ed25519 device signatures                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 5: Session Security                                                    │
│   Cryptographic session tokens, 15-min idle timeout, HMAC-signed            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Application Security                                                │
│   IPC validation, input sanitization, RBAC, CSP headers                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Transport Encryption                                                │
│   TLS 1.2+ for CouchDB, HTTPS for Azure OCR, certificate pinning            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Database Encryption                                                 │
│   SQLCipher AES-256-CBC with PBKDF2 (256K iterations)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Disk Encryption                                                     │
│   BitLocker AES-256 (Windows 10/11 Pro/Enterprise)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 SQLCipher Configuration

```typescript
// src/main/db/sqlcipher.config.ts
export const SQLCIPHER_PRAGMAS = {
  // HIPAA-recommended settings
  cipher: 'aes-256-cbc',
  kdf_iter: 256000,          // PBKDF2 iterations (increased from default 64000)
  cipher_page_size: 4096,
  cipher_use_hmac: true,     // Page-level HMAC
  cipher_hmac_algorithm: 'HMAC_SHA512',
  cipher_kdf_algorithm: 'PBKDF2_HMAC_SHA512',

  // Performance tuning
  cache_size: -64000,        // 64MB cache
  journal_mode: 'WAL',       // Write-ahead logging
  synchronous: 'NORMAL',     // Balance safety/performance
  foreign_keys: true,
};

export async function initializeDatabase(db: Database, key: string): Promise<void> {
  // Set encryption key (MUST be first operation)
  await db.exec(`PRAGMA key = '${key}'`);

  // Apply HIPAA settings
  for (const [pragma, value] of Object.entries(SQLCIPHER_PRAGMAS)) {
    await db.exec(`PRAGMA ${pragma} = ${value}`);
  }

  // Verify encryption is active
  const result = await db.get('SELECT count(*) FROM sqlite_master');
  if (!result) {
    throw new Error('Database key verification failed');
  }
}
```

### 6.3 Key Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KEY DERIVATION FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐                                                       │
│   │  User Password  │                                                       │
│   │  (min 12 chars) │                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────┐              │
│   │                    PBKDF2-HMAC-SHA512                    │              │
│   │   - Salt: 32 bytes from Windows Credential Manager       │              │
│   │   - Iterations: 256,000                                  │              │
│   │   - Output: 32 bytes                                     │              │
│   └────────────────────────┬────────────────────────────────┘              │
│                            │                                                 │
│                            ▼                                                 │
│                  ┌─────────────────────┐                                    │
│                  │  Database DEK (256)  │                                    │
│                  │  AES-256-CBC Key     │                                    │
│                  └─────────────────────┘                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

```typescript
// src/main/auth/key-manager.ts
import keytar from 'keytar';
import crypto from 'crypto';

const SERVICE_NAME = 'PatientExplorer';
const SALT_ACCOUNT = 'device-salt';

export class KeyManager {
  private deviceSalt: Buffer | null = null;

  async initialize(): Promise<void> {
    // Get or create device-unique salt
    let saltHex = await keytar.getPassword(SERVICE_NAME, SALT_ACCOUNT);

    if (!saltHex) {
      // First launch: generate random salt
      const salt = crypto.randomBytes(32);
      saltHex = salt.toString('hex');
      await keytar.setPassword(SERVICE_NAME, SALT_ACCOUNT, saltHex);
    }

    this.deviceSalt = Buffer.from(saltHex, 'hex');
  }

  async deriveKey(password: string): Promise<string> {
    if (!this.deviceSalt) {
      throw new Error('KeyManager not initialized');
    }

    return new Promise((resolve, reject) => {
      crypto.pbkdf2(
        password,
        this.deviceSalt!,
        256000,          // iterations
        32,              // key length in bytes
        'sha512',
        (err, derivedKey) => {
          if (err) reject(err);
          else resolve(derivedKey.toString('hex'));
        }
      );
    });
  }

  async validatePassword(password: string, expectedHash: string): Promise<boolean> {
    const derivedKey = await this.deriveKey(password);
    return crypto.timingSafeEqual(
      Buffer.from(derivedKey, 'hex'),
      Buffer.from(expectedHash, 'hex')
    );
  }
}
```

### 6.4 Recovery Key System

```typescript
// src/main/auth/recovery.ts
import * as bip39 from 'bip39';
import crypto from 'crypto';

export interface RecoveryKeyResult {
  mnemonic: string[];      // 24-word BIP-39 phrase
  verificationWord: string; // Word to verify user saved it
  verificationIndex: number;
}

export async function generateRecoveryKey(): Promise<RecoveryKeyResult> {
  // Generate 256-bit entropy
  const entropy = crypto.randomBytes(32);

  // Convert to BIP-39 mnemonic (24 words)
  const mnemonic = bip39.entropyToMnemonic(entropy);
  const words = mnemonic.split(' ');

  // Select random word for verification
  const verificationIndex = crypto.randomInt(0, 24);

  return {
    mnemonic: words,
    verificationWord: words[verificationIndex],
    verificationIndex,
  };
}

export async function deriveKeyFromRecovery(mnemonic: string[]): Promise<string> {
  const mnemonicString = mnemonic.join(' ');

  if (!bip39.validateMnemonic(mnemonicString)) {
    throw new Error('Invalid recovery phrase');
  }

  // Derive seed from mnemonic
  const seed = await bip39.mnemonicToSeed(mnemonicString);

  // Use first 32 bytes as recovery DEK
  return seed.slice(0, 32).toString('hex');
}
```

### 6.5 Session Management

```typescript
// src/main/auth/session.ts
import crypto from 'crypto';

interface Session {
  id: string;
  userId: string;
  userName: string;
  deviceId: string;
  createdAt: Date;
  lastActivity: Date;
  expiresAt: Date;
}

const IDLE_TIMEOUT_MS = 15 * 60 * 1000;    // 15 minutes
const MAX_DURATION_MS = 8 * 60 * 60 * 1000; // 8 hours

export class SessionManager {
  private sessions: Map<string, Session> = new Map();
  private hmacKey: Buffer;

  constructor() {
    this.hmacKey = crypto.randomBytes(32);
  }

  createSession(userId: string, userName: string, deviceId: string): string {
    const sessionId = crypto.randomUUID();
    const now = new Date();

    const session: Session = {
      id: sessionId,
      userId,
      userName,
      deviceId,
      createdAt: now,
      lastActivity: now,
      expiresAt: new Date(now.getTime() + MAX_DURATION_MS),
    };

    this.sessions.set(sessionId, session);

    return this.signSession(sessionId);
  }

  private signSession(sessionId: string): string {
    const hmac = crypto.createHmac('sha256', this.hmacKey);
    hmac.update(sessionId);
    const signature = hmac.digest('base64url');
    return `${sessionId}.${signature}`;
  }

  validateSession(token: string): Session | null {
    const [sessionId, signature] = token.split('.');

    // Verify signature
    const expectedSignature = this.signSession(sessionId).split('.')[1];
    if (!crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    )) {
      return null;
    }

    const session = this.sessions.get(sessionId);
    if (!session) return null;

    const now = new Date();

    // Check expiration
    if (now > session.expiresAt) {
      this.sessions.delete(sessionId);
      return null;
    }

    // Check idle timeout
    const idleTime = now.getTime() - session.lastActivity.getTime();
    if (idleTime > IDLE_TIMEOUT_MS) {
      this.sessions.delete(sessionId);
      return null;
    }

    // Update last activity
    session.lastActivity = now;

    return session;
  }

  endSession(sessionId: string): void {
    this.sessions.delete(sessionId);
  }
}
```

### 6.6 Audit Log Integrity

```typescript
// src/main/audit/integrity.ts
import crypto from 'crypto';
import { sign, verify } from '@noble/ed25519';

export class AuditIntegrity {
  private devicePrivateKey: Uint8Array;
  private devicePublicKey: Uint8Array;

  constructor(privateKey: Uint8Array) {
    this.devicePrivateKey = privateKey;
    this.devicePublicKey = sign.getPublicKey(privateKey);
  }

  async signEntry(entry: AuditEntry, previousHash: string): Promise<SignedAuditEntry> {
    // Compute hash chain
    const payload = JSON.stringify({
      ...entry,
      previousHash,
    });
    const hash = crypto.createHash('sha256').update(payload).digest('hex');

    // Sign with device key
    const signature = await sign(
      Buffer.from(hash, 'hex'),
      this.devicePrivateKey
    );

    return {
      ...entry,
      previousHash,
      hash,
      signature: Buffer.from(signature).toString('base64'),
    };
  }

  async verifyChain(entries: SignedAuditEntry[]): Promise<VerifyResult> {
    const errors: string[] = [];

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];

      // Verify hash chain
      if (i > 0) {
        if (entry.previousHash !== entries[i - 1].hash) {
          errors.push(`Chain break at entry ${entry.id}`);
        }
      }

      // Recompute hash
      const payload = JSON.stringify({
        action: entry.action,
        entityType: entry.entityType,
        entityId: entry.entityId,
        userId: entry.userId,
        timestamp: entry.timestamp,
        details: entry.details,
        previousHash: entry.previousHash,
      });
      const expectedHash = crypto.createHash('sha256').update(payload).digest('hex');

      if (entry.hash !== expectedHash) {
        errors.push(`Hash mismatch at entry ${entry.id}`);
      }

      // Verify signature (if public key available)
      if (entry.signature && entry.devicePublicKey) {
        const valid = await verify(
          Buffer.from(entry.signature, 'base64'),
          Buffer.from(entry.hash, 'hex'),
          Buffer.from(entry.devicePublicKey, 'hex')
        );

        if (!valid) {
          errors.push(`Invalid signature at entry ${entry.id}`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      entriesVerified: entries.length,
    };
  }
}
```

### 6.7 Transport Security

```typescript
// src/main/sync/tls-config.ts
import https from 'https';
import fs from 'fs';

export function createSecureAgent(caCertPath: string): https.Agent {
  return new https.Agent({
    ca: fs.readFileSync(caCertPath),
    rejectUnauthorized: true,
    minVersion: 'TLSv1.2',
    // Certificate pinning (optional, recommended)
    checkServerIdentity: (host, cert) => {
      // Verify expected certificate fingerprint
      const expectedFingerprint = process.env.COUCHDB_CERT_FINGERPRINT;
      if (expectedFingerprint && cert.fingerprint256 !== expectedFingerprint) {
        throw new Error('Certificate fingerprint mismatch');
      }
    },
  });
}

// CouchDB client with TLS
export function createCouchDbClient(config: CouchDbConfig): nano.ServerScope {
  const agent = createSecureAgent(config.caCertPath);

  return nano({
    url: config.url,
    requestDefaults: {
      agent,
      auth: {
        username: config.username,
        password: config.password,
      },
    },
  });
}
```

### 6.8 HIPAA Compliance Matrix

| Control | Requirement | Implementation | Status |
|---------|-------------|----------------|--------|
| **§164.312(a)(1)** | Access Control | Session-based auth, RBAC, checkout system | ✅ |
| **§164.312(a)(2)(i)** | Unique User ID | User ID in all audit entries | ✅ |
| **§164.312(a)(2)(iii)** | Auto Logoff | 15-min idle timeout | ✅ |
| **§164.312(a)(2)(iv)** | Encryption | SQLCipher AES-256, BitLocker | ✅ |
| **§164.312(b)** | Audit Controls | Hash-chained audit log with signatures | ✅ |
| **§164.312(c)(1)** | Integrity | Hash chain, WORM export | ✅ |
| **§164.312(d)** | Authentication | Password + device binding | ✅ |
| **§164.312(e)(1)** | Transmission Security | TLS 1.2+, certificate pinning | ✅ |
| **§164.312(e)(2)(ii)** | Encryption in Transit | HTTPS for all network traffic | ✅ |

---

## 7. Infrastructure & Deployment

### 7.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GREEN CLINIC NETWORK                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      ON-PREMISES SERVER                                │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │   CouchDB 3.3   │  │  Restic Backup  │  │   NAS (RAID-1)      │   │  │
│  │  │   (Sync Hub)    │──│  (Scheduled)    │──│   Backup Target     │   │  │
│  │  │   Port 6984     │  │                 │  │                     │   │  │
│  │  └────────┬────────┘  └─────────────────┘  └─────────────────────┘   │  │
│  │           │ HTTPS/TLS 1.2+                                            │  │
│  └───────────┼───────────────────────────────────────────────────────────┘  │
│              │                                                               │
│   ┌──────────┴──────────────────────────────────────────────────┐           │
│   │                    CLINIC LAN / VPN                          │           │
│   └──────────┬─────────────────┬─────────────────┬──────────────┘           │
│              │                 │                 │                          │
│   ┌──────────▼──────┐ ┌───────▼───────┐ ┌──────▼───────┐                   │
│   │ Dr. Green       │ │ LaChandra     │ │ Lindsay      │   ... more        │
│   │ Surface Pro 9   │ │ Desktop       │ │ Laptop       │                   │
│   │ ┌─────────────┐ │ │ ┌───────────┐ │ │ ┌──────────┐ │                   │
│   │ │ SQLCipher   │ │ │ │ SQLCipher │ │ │ │SQLCipher │ │                   │
│   │ │ (Local DB)  │ │ │ │ (Local DB)│ │ │ │(Local DB)│ │                   │
│   │ └─────────────┘ │ │ └───────────┘ │ │ └──────────┘ │                   │
│   │ Patient Explorer│ │ PatientExplorer│ │PatientExplorer│                   │
│   └─────────────────┘ └───────────────┘ └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
              │
              │ HTTPS (OCR API Only)
              ▼
     ┌────────────────────┐
     │  Azure Cognitive   │
     │    Services        │
     │  (OCR - no PHI     │
     │   storage)         │
     └────────────────────┘
```

### 7.2 Server Requirements

| Component | Specification | Rationale |
|-----------|--------------|-----------|
| **OS** | Ubuntu 22.04 LTS or Windows Server 2022 | Long-term support |
| **CPU** | 4+ cores | Concurrent sync |
| **RAM** | 16 GB minimum | CouchDB views |
| **Storage** | 500 GB SSD (NVMe) | Low latency |
| **Network** | 1 Gbps Ethernet | 4-6 users |
| **UPS** | 30+ min battery | Graceful shutdown |

### 7.3 CouchDB Configuration

```ini
; /opt/couchdb/etc/local.ini

[couchdb]
uuid = <auto-generated>
database_dir = /var/lib/couchdb/data
view_index_dir = /var/lib/couchdb/index
max_document_size = 67108864 ; 64MB

[chttpd]
port = 6984
bind_address = 0.0.0.0
require_valid_user = true

[ssl]
enable = true
cert_file = /etc/couchdb/ssl/server.crt
key_file = /etc/couchdb/ssl/server.key
cacert_file = /etc/couchdb/ssl/ca.crt

[admins]
admin = <pbkdf2-password-hash>

[log]
level = info
file = /var/log/couchdb/couch.log

[compactions]
_default = [{db_fragmentation, "70%"}, {view_fragmentation, "60%"}]
```

### 7.4 Client Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Windows 10 Pro (21H2+) | Windows 11 Pro |
| **CPU** | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| **RAM** | 8 GB | 16 GB |
| **Storage** | 256 GB SSD | 512 GB NVMe |
| **BitLocker** | Required | Required |
| **Network** | WiFi 5 | WiFi 6 |

### 7.5 Backup Strategy

| Layer | Tool | Frequency | Retention | Location |
|-------|------|-----------|-----------|----------|
| **Replication** | CouchDB | Continuous | N/A | Each device |
| **Server Backup** | Restic | Hourly | 24h/7d/4w/12m | NAS |
| **Offsite** | Manual | Weekly | 12 weekly | Air-gapped |
| **Client Export** | App | On-demand | User-managed | Local |

### 7.6 Auto-Update Configuration

```yaml
# electron-builder.yml
appId: com.greenclinic.patient-explorer
productName: Patient Explorer
copyright: Copyright © 2025 Green Clinic

win:
  target:
    - target: nsis
      arch: [x64]
  sign: "./scripts/sign.js"
  signingHashAlgorithms: [sha256]
  certificateSubjectName: "Green Clinic LLC"

nsis:
  oneClick: false
  perMachine: true
  createDesktopShortcut: true

publish:
  provider: generic
  url: https://updates.greenclinic.local/patient-explorer
  channel: stable
```

### 7.7 Disaster Recovery

| Scenario | RTO | RPO | Procedure |
|----------|-----|-----|-----------|
| Client failure | 2 hours | 0 | Install, auth, sync |
| Server failure | 4 hours | 1 hour | Restore from Restic |
| Site loss | 24 hours | 1 week | Offsite restore |
| Corruption | 1 hour | Per-patient | Version archive |

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

```
                    ┌───────────────────┐
                    │   E2E Tests       │  5-10 tests
                    │   (Playwright)    │  Critical flows
                    ├───────────────────┤
                    │  Integration      │  50-100 tests
                    │   Tests           │  Service + DB
                    ├───────────────────┤
                    │                   │
                    │   Unit Tests      │  500+ tests
                    │   (Vitest)        │  Components,
                    │                   │  utils, logic
                    └───────────────────┘
```

### 8.2 Test Categories

| Category | Tool | Scope | Coverage Target |
|----------|------|-------|-----------------|
| **Unit** | Vitest | Pure functions, components | 80% |
| **Integration** | Vitest + SQLite | Services + database | 70% |
| **IPC** | Vitest | Main ↔ Renderer | 90% |
| **E2E** | Playwright | Full user flows | Critical paths |
| **Security** | Custom | Encryption, audit | 100% |
| **Performance** | Vitest bench | Startup, queries | NFR targets |

### 8.3 HIPAA Test Cases

| Test | Verification | Pass Criteria |
|------|--------------|---------------|
| Database encryption | Read raw file | No plaintext PHI |
| Session timeout | Wait 15 min | Auto-logout |
| Audit chain | Verify hashes | All valid |
| TLS enforcement | MITM attempt | Connection refused |
| Access logging | PHI read | Audit entry created |

### 8.4 Coverage Requirements

| Phase | Overall | Services | Blocking? |
|-------|---------|----------|-----------|
| Sprint 0 | None | None | No |
| Phase 1A | 60% | 80% | Yes |
| Phase 1B | 70% | 85% | Yes |
| Phase 1C | 75% | 90% | Yes |

### 8.5 Test Data

**CRITICAL**: No real PHI in tests. Use synthetic data from `@faker-js/faker`.

```typescript
// test-utils/generators.ts
import { faker } from '@faker-js/faker';

export function generateTestPatient() {
  return {
    id: faker.string.uuid(),
    lastName: faker.person.lastName().toUpperCase(),
    firstName: faker.person.firstName(),
    dateOfBirth: faker.date.birthdate({ min: 30, max: 90, mode: 'age' })
      .toISOString().split('T')[0],
    mrn: `MRN${faker.string.numeric(6)}`,
    ssn4: faker.string.numeric(4),
    phone: faker.phone.number(),
  };
}
```

---

## 9. Appendices

### Appendix A: ADR Template

```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[Why is this decision needed?]

## Decision
[What is the decision?]

## Consequences
[What are the positive and negative outcomes?]

## Alternatives Considered
[What other options were evaluated?]
```

### Appendix B: Sprint 0 Spikes

| Spike | Duration | Success Criteria |
|-------|----------|------------------|
| S0-1: SQLCipher Build | 1 day | Windows compile + CRUD |
| S0-2: PouchDB Sync | 1-2 days | Bidirectional replication |
| S0-3: _changes Feed | 1 day | Real-time notifications |
| S0-4: Tesseract.js | 1 day | ≥85% accuracy on Allscripts |
| S0-5: Drizzle ORM | 0.5 days | Type-safe queries |
| S0-6: Key Recovery | 0.5 days | Recovery flow documented |

### Appendix C: Glossary

| Term | Definition |
|------|------------|
| **APCM** | Advanced Primary Care Management (CMS program) |
| **BAA** | Business Associate Agreement (HIPAA) |
| **DEK** | Data Encryption Key |
| **PHI** | Protected Health Information |
| **RTO** | Recovery Time Objective |
| **RPO** | Recovery Point Objective |
| **WORM** | Write Once Read Many |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-30 | Winston (Architect) | Initial draft |

---

*Generated by Winston (Architect) using BMAD-METHOD v2.0*
