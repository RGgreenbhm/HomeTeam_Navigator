# Story E5-S3: Implement User Authentication

## Status
Draft

## Story
**As a** clinical user,
**I want** to log in with my credentials,
**so that** only authorized users can access patient data.

## Acceptance Criteria
1. Login screen displays on app launch
2. Username and password authentication
3. Session persists until logout or timeout
4. Login failures show generic error message
5. Successful login logged to audit trail
6. Current user displayed in header with logout option

## Tasks / Subtasks
- [ ] Create login screen (AC: 1, 2)
  - [ ] Create src/renderer/screens/LoginScreen.tsx
  - [ ] Username and password fields
  - [ ] Login button with loading state
  - [ ] Remember username checkbox
- [ ] Implement authentication service (AC: 2, 3)
  - [ ] Password hashing with Argon2
  - [ ] Session token generation
  - [ ] Session storage in main process
- [ ] Handle login failures (AC: 4)
  - [ ] Generic "Invalid credentials" message
  - [ ] No indication which field is wrong
  - [ ] Rate limiting integration
- [ ] Add audit logging (AC: 5)
  - [ ] Log successful logins
  - [ ] Log failed attempts
  - [ ] Include timestamp and source
- [ ] Display user in header (AC: 6)
  - [ ] Show username/display name
  - [ ] Dropdown with logout option
  - [ ] Profile settings link

## Dev Notes

### User Schema
```typescript
// src/main/database/schema/users.ts
export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  username: text('username').notNull().unique(),
  displayName: text('display_name').notNull(),
  passwordHash: text('password_hash').notNull(),
  role: text('role', { enum: ['admin', 'user'] }).notNull().default('user'),
  createdAt: text('created_at').notNull().$defaultFn(() => new Date().toISOString()),
  lastLoginAt: text('last_login_at'),
  isActive: integer('is_active', { mode: 'boolean' }).notNull().default(true),
});
```

### Login Screen Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                                                             │
│                    ┌────────────────────────────────┐                       │
│                    │      [Patient Explorer]        │                       │
│                    │        Home Team Logo          │                       │
│                    └────────────────────────────────┘                       │
│                                                                             │
│                    ┌────────────────────────────────┐                       │
│                    │  Username                      │                       │
│                    │  ┌────────────────────────────┐│                       │
│                    │  │ robert.green              ││                       │
│                    │  └────────────────────────────┘│                       │
│                    │                                │                       │
│                    │  Password                      │                       │
│                    │  ┌────────────────────────────┐│                       │
│                    │  │ ••••••••                  ││                       │
│                    │  └────────────────────────────┘│                       │
│                    │                                │                       │
│                    │  ☑ Remember username          │                       │
│                    │                                │                       │
│                    │  ┌────────────────────────────┐│                       │
│                    │  │        Sign In             ││                       │
│                    │  └────────────────────────────┘│                       │
│                    │                                │                       │
│                    │  ⚠ Invalid credentials        │                       │
│                    └────────────────────────────────┘                       │
│                                                                             │
│                    Version 1.0.0                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Authentication Service
```typescript
// src/main/services/auth/authService.ts
import argon2 from 'argon2';
import crypto from 'crypto';

interface Session {
  userId: string;
  username: string;
  displayName: string;
  role: 'admin' | 'user';
  token: string;
  createdAt: Date;
  expiresAt: Date;
}

const sessions = new Map<string, Session>();
const SESSION_DURATION_MS = 8 * 60 * 60 * 1000; // 8 hours

export async function hashPassword(password: string): Promise<string> {
  return argon2.hash(password, {
    type: argon2.argon2id,
    memoryCost: 65536,     // 64 MB
    timeCost: 3,           // 3 iterations
    parallelism: 4,        // 4 threads
  });
}

export async function verifyPassword(hash: string, password: string): Promise<boolean> {
  return argon2.verify(hash, password);
}

export async function createSession(user: User): Promise<Session> {
  const token = crypto.randomBytes(32).toString('hex');
  const now = new Date();

  const session: Session = {
    userId: user.id,
    username: user.username,
    displayName: user.displayName,
    role: user.role,
    token,
    createdAt: now,
    expiresAt: new Date(now.getTime() + SESSION_DURATION_MS),
  };

  sessions.set(token, session);
  return session;
}

export function validateSession(token: string): Session | null {
  const session = sessions.get(token);

  if (!session) return null;
  if (new Date() > session.expiresAt) {
    sessions.delete(token);
    return null;
  }

  return session;
}

export function destroySession(token: string): void {
  sessions.delete(token);
}
```

### IPC Handlers
```typescript
ipcMain.handle('auth:login', async (event, { username, password }) => {
  // Check lockout
  const lockout = isLockedOut();
  if (lockout.locked) {
    return { success: false, error: 'Account locked', remainingMs: lockout.remainingMs };
  }

  // Find user
  const [user] = await db.select().from(users)
    .where(and(
      eq(users.username, username),
      eq(users.isActive, true)
    ));

  if (!user) {
    recordFailedAttempt();
    await auditLog({ action: 'LOGIN_FAILED', details: { username, reason: 'user_not_found' } });
    return { success: false, error: 'Invalid credentials' };
  }

  // Verify password
  const valid = await verifyPassword(user.passwordHash, password);
  if (!valid) {
    recordFailedAttempt();
    await auditLog({ action: 'LOGIN_FAILED', details: { username, reason: 'invalid_password' } });
    return { success: false, error: 'Invalid credentials' };
  }

  // Create session
  resetAttempts();
  const session = await createSession(user);

  // Update last login
  await db.update(users)
    .set({ lastLoginAt: new Date().toISOString() })
    .where(eq(users.id, user.id));

  await auditLog({ action: 'LOGIN_SUCCESS', userId: user.id, details: { username } });

  return {
    success: true,
    session: {
      token: session.token,
      user: {
        id: user.id,
        username: user.username,
        displayName: user.displayName,
        role: user.role,
      },
    },
  };
});

ipcMain.handle('auth:logout', async (event) => {
  const session = getCurrentSession(event);
  if (session) {
    destroySession(session.token);
    await auditLog({ action: 'LOGOUT', userId: session.userId });
  }
  return { success: true };
});

ipcMain.handle('auth:validate', async (event) => {
  const session = getCurrentSession(event);
  return { valid: !!session, session };
});
```

### Dependencies
- **argon2**: ^0.31.x for password hashing

## Testing
- **Location**: `src/main/services/auth/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Successful login creates session
  - Wrong password returns generic error
  - Unknown user returns generic error
  - Session validation works
  - Session expiry works
  - Logout destroys session
  - Audit logs created for login events

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
