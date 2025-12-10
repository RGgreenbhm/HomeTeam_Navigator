# Story E1-S2: Implement SQLite + SQLCipher Database Layer

## Status
Draft

## Story
**As a** developer,
**I want** an encrypted SQLite database with SQLCipher,
**so that** patient data is securely stored with AES-256 encryption at rest.

## Acceptance Criteria
1. @journeyapps/sqlcipher package installs and compiles on Windows 10/11
2. Database creates successfully with AES-256 encryption
3. Basic CRUD operations work (create, read, update, delete)
4. Database file is unreadable without the encryption key
5. Drizzle ORM is configured for type-safe queries
6. Database connection is managed in main process only (not renderer)

## Tasks / Subtasks
- [ ] Install SQLCipher dependencies (AC: 1)
  - [ ] npm install @journeyapps/sqlcipher
  - [ ] Verify native bindings compile without errors
  - [ ] Document any Windows-specific build requirements
- [ ] Create database service (AC: 2, 6)
  - [ ] Create src/main/db/database.ts
  - [ ] Implement DatabaseService class
  - [ ] Configure SQLCipher PRAGMA settings per Architecture §6.2
- [ ] Configure Drizzle ORM (AC: 5)
  - [ ] npm install drizzle-orm drizzle-kit
  - [ ] Create src/main/db/drizzle.config.ts
  - [ ] Create initial schema file src/main/db/schema/index.ts
- [ ] Implement encryption key handling (AC: 2, 4)
  - [ ] Create src/main/db/key-manager.ts
  - [ ] Use keytar for Windows Credential Manager storage
  - [ ] Implement deriveKey() with PBKDF2 (256K iterations)
- [ ] Create test table for CRUD verification (AC: 3)
  - [ ] Create simple test schema
  - [ ] Implement insert, select, update, delete operations
  - [ ] Write integration tests
- [ ] Verify encryption (AC: 4)
  - [ ] Test that .db file is binary gibberish without key
  - [ ] Test that wrong key fails to open database
  - [ ] Document encryption verification procedure

## Dev Notes

### SQLCipher PRAGMA Settings (from Architecture §6.2)
```typescript
export const SQLCIPHER_PRAGMAS = {
  cipher: 'aes-256-cbc',
  kdf_iter: 256000,              // PBKDF2 iterations
  cipher_page_size: 4096,
  cipher_use_hmac: true,
  cipher_hmac_algorithm: 'HMAC_SHA512',
  cipher_kdf_algorithm: 'PBKDF2_HMAC_SHA512',
  cache_size: -64000,            // 64MB cache
  journal_mode: 'WAL',
  synchronous: 'NORMAL',
  foreign_keys: true,
};
```

### Key Derivation (from Architecture §6.3)
```typescript
// User password → PBKDF2 → Database key
crypto.pbkdf2(
  password,
  deviceSalt,        // From Windows Credential Manager
  256000,            // iterations
  32,                // key length bytes
  'sha512',
  callback
);
```

### Drizzle Schema Example
```typescript
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';

export const patients = sqliteTable('patients', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  lastName: text('last_name').notNull(),
  firstName: text('first_name'),
  // ... more fields
});
```

### Dependencies
- @journeyapps/sqlcipher: ^5.x (pre-built binaries)
- drizzle-orm: ^0.29+
- drizzle-kit: ^0.20+
- keytar: ^7.x (Windows Credential Manager)
- @paralleldrive/cuid2: ^2.x (ID generation)

## Testing
- **Location**: `src/main/db/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Database initialization with encryption
  - CRUD operations on test table
  - Key derivation produces consistent results
  - Wrong key rejection
- **Coverage Target**: 80% for database service

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story draft | Bob (SM) |

---

## Dev Agent Record
*(To be completed during implementation)*

### Agent Model Used
### Debug Log References
### Completion Notes
### File List

---

## QA Results
*(To be completed by QA agent)*
