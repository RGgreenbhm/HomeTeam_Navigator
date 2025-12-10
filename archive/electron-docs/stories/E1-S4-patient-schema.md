# Story E1-S4: Implement Patient Data Model and Schema

## Status
Draft

## Story
**As a** developer,
**I want** a complete patient data model with Drizzle ORM schema,
**so that** patient records can be stored and queried type-safely.

## Acceptance Criteria
1. Patient table schema matches Architecture §4.2 specification
2. All required patient fields are defined with proper types
3. Drizzle migrations work correctly
4. TypeScript types are auto-generated from schema
5. Indexes are created for search fields (lastName, mrn, dateOfBirth)
6. Soft delete is implemented via deletedAt timestamp

## Tasks / Subtasks
- [ ] Create patient schema (AC: 1, 2)
  - [ ] Create src/main/db/schema/patient.ts
  - [ ] Define all fields from Architecture §4.2
  - [ ] Add proper column types and constraints
  - [ ] Add default values where appropriate
- [ ] Add search indexes (AC: 5)
  - [ ] Index on lastName (case-insensitive search)
  - [ ] Index on mrn (exact match)
  - [ ] Composite index on lastName + firstName
- [ ] Configure soft delete (AC: 6)
  - [ ] Add deletedAt nullable timestamp field
  - [ ] Document soft delete query pattern
- [ ] Set up migrations (AC: 3)
  - [ ] Create drizzle.config.ts
  - [ ] Generate initial migration
  - [ ] Test migration applies successfully
- [ ] Export TypeScript types (AC: 4)
  - [ ] Export Patient type from schema
  - [ ] Export NewPatient type for inserts
  - [ ] Create shared types in src/shared/types/patient.ts

## Dev Notes

### Patient Schema (from Architecture §4.2)
```typescript
// src/main/db/schema/patient.ts
import { sqliteTable, text, integer, real, index } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';

export const patients = sqliteTable('patients', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  lastName: text('last_name').notNull(),
  firstName: text('first_name'),
  middleName: text('middle_name'),
  dateOfBirth: text('date_of_birth'),       // ISO 8601: YYYY-MM-DD
  mrn: text('mrn'),
  ssn4: text('ssn4'),                        // Last 4 digits only
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
  deletedAt: text('deleted_at'),             // Soft delete
}, (table) => ({
  lastNameIdx: index('idx_patients_last_name').on(table.lastName),
  mrnIdx: index('idx_patients_mrn').on(table.mrn),
  dobIdx: index('idx_patients_dob').on(table.dateOfBirth),
  nameIdx: index('idx_patients_name').on(table.lastName, table.firstName),
}));

export type Patient = typeof patients.$inferSelect;
export type NewPatient = typeof patients.$inferInsert;
```

### Drizzle Config
```typescript
// drizzle.config.ts
import type { Config } from 'drizzle-kit';

export default {
  schema: './src/main/db/schema/*.ts',
  out: './drizzle',
  driver: 'better-sqlite3',  // Compatible with sqlcipher
  dbCredentials: {
    url: './patient-explorer.db',
  },
} satisfies Config;
```

### Soft Delete Pattern
```typescript
// Always filter out soft-deleted records
const activePatients = await db
  .select()
  .from(patients)
  .where(isNull(patients.deletedAt));

// Soft delete
await db
  .update(patients)
  .set({ deletedAt: new Date().toISOString() })
  .where(eq(patients.id, patientId));
```

## Testing
- **Location**: `src/main/db/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Schema creates table with all columns
  - Insert patient returns generated ID
  - Query by lastName works (case-insensitive)
  - Soft delete filters correctly
- **Coverage**: 80% for schema operations

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
