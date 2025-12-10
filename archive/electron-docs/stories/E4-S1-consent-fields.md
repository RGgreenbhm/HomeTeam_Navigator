# Story E4-S1: Add Consent Status Fields to Patient Model

## Status
Draft

## Story
**As a** developer,
**I want** to add consent-related fields to the patient data model,
**so that** the application can track consent status for each patient.

## Acceptance Criteria
1. Patient schema includes consentStatus field (enum: pending, obtained, declined)
2. consentMethod field tracks how consent was obtained (verbal, written, text, electronic)
3. consentDate field stores when consent was obtained
4. consentWitness field stores witness name if applicable
5. Database migration adds fields without data loss
6. TypeScript types are updated to reflect new fields

## Tasks / Subtasks
- [ ] Update patient schema (AC: 1, 2, 3, 4)
  - [ ] Add consentStatus column (text enum)
  - [ ] Add consentMethod column (text, nullable)
  - [ ] Add consentDate column (text, ISO date, nullable)
  - [ ] Add consentWitness column (text, nullable)
  - [ ] Add consentNotes column (text, nullable)
- [ ] Create database migration (AC: 5)
  - [ ] Generate migration with Drizzle kit
  - [ ] Set default consentStatus to 'pending'
  - [ ] Test migration on existing data
- [ ] Update TypeScript types (AC: 6)
  - [ ] Update Patient interface
  - [ ] Add ConsentStatus enum type
  - [ ] Add ConsentMethod enum type
- [ ] Update IPC handlers
  - [ ] Include consent fields in patient:get
  - [ ] Include consent fields in patient:list
  - [ ] Allow consent fields in patient:update

## Dev Notes

### Schema Changes (Drizzle ORM)
```typescript
// src/main/database/schema/patients.ts
export const consentStatusEnum = ['pending', 'obtained', 'declined'] as const;
export const consentMethodEnum = ['verbal', 'written', 'text', 'electronic'] as const;

export const patients = sqliteTable('patients', {
  // ... existing fields ...

  // Consent fields
  consentStatus: text('consent_status', { enum: consentStatusEnum })
    .notNull()
    .default('pending'),
  consentMethod: text('consent_method', { enum: consentMethodEnum }),
  consentDate: text('consent_date'), // ISO date string
  consentWitness: text('consent_witness'),
  consentNotes: text('consent_notes'),
});
```

### TypeScript Types
```typescript
// src/shared/types/patient.ts
export type ConsentStatus = 'pending' | 'obtained' | 'declined';
export type ConsentMethod = 'verbal' | 'written' | 'text' | 'electronic';

export interface Patient {
  // ... existing fields ...
  consentStatus: ConsentStatus;
  consentMethod?: ConsentMethod;
  consentDate?: string;
  consentWitness?: string;
  consentNotes?: string;
}
```

### Migration Command
```bash
# Generate migration
npx drizzle-kit generate:sqlite

# Apply migration
npx drizzle-kit push:sqlite
```

### Consent Status Definitions
| Status | Description |
|--------|-------------|
| `pending` | Patient has not been asked or hasn't responded |
| `obtained` | Patient consented via any method |
| `declined` | Patient explicitly declined consent |

### Consent Method Definitions
| Method | Description |
|--------|-------------|
| `verbal` | In-person or phone verbal consent |
| `written` | Signed physical consent form |
| `text` | Consent via SMS/text message |
| `electronic` | Digital signature or portal consent |

## Testing
- **Location**: `src/main/database/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Migration runs without error
  - Default consentStatus is 'pending'
  - Consent fields are retrievable
  - Invalid status values are rejected
  - Nullable fields accept null

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story draft | Bob (SM) |

---

## Dev Agent Record
### Agent Model Used
### Debug Log References
### Completion Notes
### File List

---

## QA Results
