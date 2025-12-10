# Story E5-S5: Create Audit Log Database and Logging Service

## Status
Draft

## Story
**As a** HIPAA compliance officer,
**I want** all access and modifications to patient data logged,
**so that** we have a complete audit trail for compliance and security reviews.

## Acceptance Criteria
1. Audit log table created with required HIPAA fields
2. Automatic logging of all patient record access (READ, CREATE, UPDATE, DELETE)
3. Automatic logging of authentication events (LOGIN, LOGOUT, FAILED)
4. Log entries are append-only (no UPDATE or DELETE)
5. Logs include timestamp, user, action, entity, and details
6. Logs exportable for compliance review

## Tasks / Subtasks
- [ ] Create audit log schema (AC: 1)
  - [ ] Create auditLogs table
  - [ ] Fields: id, timestamp, userId, action, entityType, entityId, details, ipAddress
  - [ ] Index on timestamp for queries
- [ ] Implement logging service (AC: 2, 3, 5)
  - [ ] auditLog() function for main process
  - [ ] Capture context automatically
  - [ ] Structured details as JSON
- [ ] Integrate with all IPC handlers (AC: 2, 3)
  - [ ] Add logging to patient handlers
  - [ ] Add logging to auth handlers
  - [ ] Add logging to consent handlers
- [ ] Enforce append-only (AC: 4)
  - [ ] No UPDATE/DELETE IPC for audit logs
  - [ ] Database triggers if needed
- [ ] Add export functionality (AC: 6)
  - [ ] Export filtered logs to CSV
  - [ ] Date range filter
  - [ ] User/action type filter

## Dev Notes

### Audit Log Schema
```typescript
// src/main/database/schema/auditLogs.ts
export const auditActionEnum = [
  'CREATE', 'READ', 'UPDATE', 'DELETE',
  'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'AUTO_LOGOUT',
  'UPDATE_CONSENT', 'UPDATE_APCM',
  'BULK_IMPORT', 'EXPORT',
  'KEY_ROTATION', 'SECURITY_CHECK', 'LOCKOUT_TRIGGERED',
] as const;

export const entityTypeEnum = [
  'patient', 'capture', 'consent', 'carePlan', 'user', 'system', 'security',
] as const;

export const auditLogs = sqliteTable('audit_logs', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  timestamp: text('timestamp').notNull().$defaultFn(() => new Date().toISOString()),
  userId: text('user_id'),  // null for system events
  username: text('username'),
  action: text('action', { enum: auditActionEnum }).notNull(),
  entityType: text('entity_type', { enum: entityTypeEnum }).notNull(),
  entityId: text('entity_id'),  // ID of affected record
  details: text('details'),     // JSON string for additional context
  ipAddress: text('ip_address'),
  userAgent: text('user_agent'),
});

// Index for efficient querying
export const auditLogsTimestampIdx = index('audit_logs_timestamp_idx')
  .on(auditLogs.timestamp);
```

### Audit Logging Service
```typescript
// src/main/services/audit/auditService.ts
import { db } from '../database';
import { auditLogs, AuditAction, EntityType } from '../database/schema';

interface AuditLogParams {
  action: AuditAction;
  entityType: EntityType;
  entityId?: string;
  details?: Record<string, unknown>;
  userId?: string;
  username?: string;
}

let currentSession: { userId: string; username: string } | null = null;

export function setAuditSession(session: { userId: string; username: string } | null): void {
  currentSession = session;
}

export async function auditLog(params: AuditLogParams): Promise<void> {
  const logEntry = {
    action: params.action,
    entityType: params.entityType,
    entityId: params.entityId,
    details: params.details ? JSON.stringify(params.details) : undefined,
    userId: params.userId ?? currentSession?.userId,
    username: params.username ?? currentSession?.username,
    timestamp: new Date().toISOString(),
  };

  try {
    await db.insert(auditLogs).values(logEntry);
  } catch (error) {
    // Audit logging should never fail silently
    console.error('Failed to write audit log:', error);
    // Consider backup logging mechanism (file, etc.)
  }
}

// Convenience wrappers
export async function logPatientAccess(
  action: 'CREATE' | 'READ' | 'UPDATE' | 'DELETE',
  patientId: string,
  details?: Record<string, unknown>
): Promise<void> {
  await auditLog({
    action,
    entityType: 'patient',
    entityId: patientId,
    details,
  });
}

export async function logAuthEvent(
  action: 'LOGIN_SUCCESS' | 'LOGIN_FAILED' | 'LOGOUT' | 'AUTO_LOGOUT',
  details?: Record<string, unknown>
): Promise<void> {
  await auditLog({
    action,
    entityType: 'system',
    details,
  });
}
```

### Integration with IPC Handlers
```typescript
// Example: patient:get handler with audit logging
ipcMain.handle('patient:get', async (event, { id }) => {
  const session = await validateSession(event);

  const [patient] = await db.select().from(patients)
    .where(eq(patients.id, id));

  if (!patient) {
    throw new Error('Patient not found');
  }

  // Audit log the access
  await auditLog({
    action: 'READ',
    entityType: 'patient',
    entityId: id,
    details: { mrn: patient.mrn },
  });

  return patient;
});

// Example: patient:update with before/after
ipcMain.handle('patient:update', async (event, { id, ...updates }) => {
  const session = await validateSession(event);

  // Get current state for audit
  const [before] = await db.select().from(patients).where(eq(patients.id, id));

  const [after] = await db.update(patients)
    .set({ ...updates, updatedAt: new Date().toISOString() })
    .where(eq(patients.id, id))
    .returning();

  // Log with diff
  await auditLog({
    action: 'UPDATE',
    entityType: 'patient',
    entityId: id,
    details: {
      before: sanitizeForAudit(before),
      after: sanitizeForAudit(after),
      changedFields: Object.keys(updates),
    },
  });

  return after;
});
```

### Export IPC Handler
```typescript
ipcMain.handle('audit:export', async (event, { startDate, endDate, actions, entityTypes }) => {
  const session = await validateSession(event);
  if (session.role !== 'admin') {
    throw new Error('Admin access required');
  }

  let query = db.select().from(auditLogs);

  if (startDate) {
    query = query.where(gte(auditLogs.timestamp, startDate));
  }
  if (endDate) {
    query = query.where(lte(auditLogs.timestamp, endDate));
  }
  if (actions?.length) {
    query = query.where(inArray(auditLogs.action, actions));
  }
  if (entityTypes?.length) {
    query = query.where(inArray(auditLogs.entityType, entityTypes));
  }

  const logs = await query.orderBy(asc(auditLogs.timestamp));

  // Generate CSV
  const csv = [
    'Timestamp,User,Action,Entity Type,Entity ID,Details',
    ...logs.map(log => [
      log.timestamp,
      log.username || 'System',
      log.action,
      log.entityType,
      log.entityId || '',
      `"${(log.details || '').replace(/"/g, '""')}"`,
    ].join(',')),
  ].join('\n');

  // Log the export
  await auditLog({
    action: 'EXPORT',
    entityType: 'system',
    details: { type: 'audit_logs', count: logs.length },
  });

  return csv;
});
```

### HIPAA Audit Requirements Reference
| Field | HIPAA Requirement | Implementation |
|-------|------------------|----------------|
| Timestamp | Date/time of access | ISO 8601 timestamp |
| User ID | Who accessed | userId, username |
| Action | What was done | action enum |
| Patient | Which record | entityId (patient ID) |
| Data | What was accessed | entityType, details JSON |

## Testing
- **Location**: `src/main/services/audit/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Audit log creates entry
  - All required fields captured
  - Details stored as JSON
  - Export generates valid CSV
  - No UPDATE/DELETE operations exist
  - Failed logging doesn't crash app

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
