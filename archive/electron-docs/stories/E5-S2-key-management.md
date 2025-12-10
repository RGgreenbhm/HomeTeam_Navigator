# Story E5-S2: Create SQLCipher Key Management

## Status
Draft

## Story
**As a** clinical admin,
**I want** secure management of the database encryption key,
**so that** patient data remains encrypted at rest with proper key handling.

## Acceptance Criteria
1. Encryption key derived from user master password using PBKDF2
2. Key stored securely using Windows Credential Manager (DPAPI)
3. Key rotation capability available in Settings
4. Failed unlock attempts trigger lockout (5 attempts = 30 min)
5. Key derivation parameters logged to audit (not the key itself)
6. Recovery mechanism using admin-generated recovery key

## Tasks / Subtasks
- [ ] Implement key derivation (AC: 1)
  - [ ] Use PBKDF2 with 600,000 iterations
  - [ ] SHA-256 hash function
  - [ ] 32-byte (256-bit) output for SQLCipher
  - [ ] Random salt per database
- [ ] Integrate Windows Credential Manager (AC: 2)
  - [ ] Use keytar npm package
  - [ ] Store derived key blob
  - [ ] Retrieve on app startup
- [ ] Add key rotation (AC: 3)
  - [ ] Re-key database with new password
  - [ ] SQLCipher REKEY command
  - [ ] Update stored credentials
- [ ] Implement lockout mechanism (AC: 4)
  - [ ] Track failed attempts
  - [ ] 30-minute lockout after 5 failures
  - [ ] Show countdown timer
- [ ] Add recovery key (AC: 6)
  - [ ] Generate 24-word BIP39-style recovery phrase
  - [ ] Admin can generate/view once
  - [ ] Recovery key derives same database key

## Dev Notes

### Key Derivation Implementation
```typescript
// src/main/services/security/keyManagement.ts
import crypto from 'crypto';

const PBKDF2_ITERATIONS = 600_000;
const KEY_LENGTH = 32; // 256 bits for SQLCipher

interface KeyDerivationParams {
  salt: Buffer;
  iterations: number;
  algorithm: 'sha256';
}

export async function deriveKey(
  password: string,
  salt?: Buffer
): Promise<{ key: Buffer; params: KeyDerivationParams }> {
  const finalSalt = salt || crypto.randomBytes(32);

  const key = await new Promise<Buffer>((resolve, reject) => {
    crypto.pbkdf2(
      password,
      finalSalt,
      PBKDF2_ITERATIONS,
      KEY_LENGTH,
      'sha256',
      (err, derivedKey) => {
        if (err) reject(err);
        else resolve(derivedKey);
      }
    );
  });

  return {
    key,
    params: {
      salt: finalSalt,
      iterations: PBKDF2_ITERATIONS,
      algorithm: 'sha256',
    },
  };
}

// Convert to SQLCipher hex format
export function keyToHex(key: Buffer): string {
  return `x'${key.toString('hex')}'`;
}
```

### Windows Credential Manager Integration
```typescript
// src/main/services/security/credentialStore.ts
import keytar from 'keytar';

const SERVICE_NAME = 'PatientExplorer';
const ACCOUNT_NAME = 'DatabaseKey';

export async function storeCredential(keyBlob: Buffer, salt: Buffer): Promise<void> {
  // Store key and salt as JSON
  const credential = JSON.stringify({
    key: keyBlob.toString('base64'),
    salt: salt.toString('base64'),
  });

  await keytar.setPassword(SERVICE_NAME, ACCOUNT_NAME, credential);
}

export async function retrieveCredential(): Promise<{ key: Buffer; salt: Buffer } | null> {
  const credential = await keytar.getPassword(SERVICE_NAME, ACCOUNT_NAME);

  if (!credential) return null;

  const { key, salt } = JSON.parse(credential);
  return {
    key: Buffer.from(key, 'base64'),
    salt: Buffer.from(salt, 'base64'),
  };
}

export async function deleteCredential(): Promise<void> {
  await keytar.deletePassword(SERVICE_NAME, ACCOUNT_NAME);
}
```

### Key Rotation
```typescript
// src/main/services/security/keyRotation.ts
export async function rotateKey(
  db: Database,
  currentPassword: string,
  newPassword: string
): Promise<void> {
  // Verify current password works
  const current = await retrieveCredential();
  if (!current) throw new Error('No existing credential found');

  // Derive new key
  const { key: newKey, params } = await deriveKey(newPassword);

  // SQLCipher REKEY operation
  await db.exec(`PRAGMA rekey = ${keyToHex(newKey)}`);

  // Update stored credential
  await storeCredential(newKey, params.salt);

  await auditLog({
    action: 'KEY_ROTATION',
    entityType: 'security',
    details: {
      algorithm: params.algorithm,
      iterations: params.iterations,
      // Never log the actual key!
    },
  });
}
```

### Lockout Mechanism
```typescript
// src/main/services/security/lockout.ts
const MAX_ATTEMPTS = 5;
const LOCKOUT_DURATION_MS = 30 * 60 * 1000; // 30 minutes

interface LockoutState {
  failedAttempts: number;
  lockoutUntil: number | null;
}

let lockoutState: LockoutState = {
  failedAttempts: 0,
  lockoutUntil: null,
};

export function isLockedOut(): { locked: boolean; remainingMs: number } {
  if (!lockoutState.lockoutUntil) {
    return { locked: false, remainingMs: 0 };
  }

  const remaining = lockoutState.lockoutUntil - Date.now();
  if (remaining <= 0) {
    lockoutState = { failedAttempts: 0, lockoutUntil: null };
    return { locked: false, remainingMs: 0 };
  }

  return { locked: true, remainingMs: remaining };
}

export function recordFailedAttempt(): void {
  lockoutState.failedAttempts++;

  if (lockoutState.failedAttempts >= MAX_ATTEMPTS) {
    lockoutState.lockoutUntil = Date.now() + LOCKOUT_DURATION_MS;

    auditLog({
      action: 'LOCKOUT_TRIGGERED',
      entityType: 'security',
      details: { attempts: lockoutState.failedAttempts },
    });
  }
}

export function resetAttempts(): void {
  lockoutState = { failedAttempts: 0, lockoutUntil: null };
}
```

### Recovery Key Generation (BIP39-style)
```typescript
import { generateMnemonic, mnemonicToSeedSync } from 'bip39';

export function generateRecoveryPhrase(): string {
  return generateMnemonic(256); // 24 words
}

export function deriveKeyFromRecovery(phrase: string): Buffer {
  const seed = mnemonicToSeedSync(phrase);
  return seed.slice(0, 32); // First 256 bits
}
```

### Dependencies
- **keytar**: ^7.9.x for Windows Credential Manager
- **bip39**: ^3.1.x for recovery phrase generation

## Testing
- **Location**: `src/main/services/security/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Key derivation produces consistent output
  - Credential store/retrieve works
  - Key rotation updates database
  - Lockout triggers after 5 failures
  - Lockout resets after duration
  - Recovery phrase derives correct key

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
