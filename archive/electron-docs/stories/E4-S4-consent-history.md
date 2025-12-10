# Story E4-S4: Implement Consent History Log

## Status
Draft

## Story
**As a** clinical admin,
**I want** to see the complete history of consent status changes,
**so that** I have an audit trail for compliance purposes.

## Acceptance Criteria
1. Consent history table created in database
2. Each status change creates a history entry
3. History shows: timestamp, previous status, new status, method, user
4. History displayed in patient detail consent tab
5. History entries are immutable (append-only)
6. Export consent history to CSV for auditing

## Tasks / Subtasks
- [ ] Create consent history schema (AC: 1)
  - [ ] Create consentHistory table
  - [ ] Fields: id, patientId, previousStatus, newStatus, method, changedBy, changedAt, notes
  - [ ] Foreign key to patients table
- [ ] Log history on consent changes (AC: 2, 5)
  - [ ] Update patient:updateConsent handler
  - [ ] Insert history record before update
  - [ ] No UPDATE or DELETE allowed on history
- [ ] Create history display component (AC: 3, 4)
  - [ ] Create src/renderer/components/ConsentHistory.tsx
  - [ ] Timeline view of changes
  - [ ] Show all required fields
- [ ] Add export functionality (AC: 6)
  - [ ] consent:exportHistory IPC handler
  - [ ] CSV format with headers
  - [ ] File save dialog

## Dev Notes

### Consent History Schema
```typescript
// src/main/database/schema/consentHistory.ts
export const consentHistory = sqliteTable('consent_history', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  patientId: text('patient_id').notNull().references(() => patients.id),
  previousStatus: text('previous_status', { enum: consentStatusEnum }),
  newStatus: text('new_status', { enum: consentStatusEnum }).notNull(),
  method: text('method', { enum: consentMethodEnum }),
  changedBy: text('changed_by').notNull(),
  changedAt: text('changed_at').notNull(),
  notes: text('notes'),
});
```

### History Timeline Component
```typescript
function ConsentHistory({ patientId }: { patientId: string }) {
  const { data: history } = useQuery({
    queryKey: ['consent-history', patientId],
    queryFn: () => window.api.consent.getHistory({ patientId }),
  });

  return (
    <div className="space-y-4">
      <h3 className="font-medium">Consent History</h3>
      <div className="relative border-l-2 border-gray-200 pl-4">
        {history?.map((entry) => (
          <div key={entry.id} className="mb-4 relative">
            <div className="absolute -left-6 w-3 h-3 bg-blue-500 rounded-full" />
            <div className="text-sm text-gray-500">
              {formatDateTime(entry.changedAt)} by {entry.changedBy}
            </div>
            <div className="mt-1">
              <ConsentBadge status={entry.previousStatus} /> →
              <ConsentBadge status={entry.newStatus} />
            </div>
            {entry.method && (
              <div className="text-sm text-gray-600 mt-1">
                Method: {entry.method}
              </div>
            )}
            {entry.notes && (
              <div className="text-sm text-gray-600 mt-1 italic">
                {entry.notes}
              </div>
            )}
          </div>
        ))}
      </div>
      <button onClick={handleExport}>
        Export History
      </button>
    </div>
  );
}
```

### Visual Timeline
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Consent History                                       [Export CSV]         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ●  11/30/2025 3:45 PM by LaChandra Watts                                  │
│  │  ⏳ Pending  →  ✓ Obtained                                              │
│  │  Method: Verbal                                                          │
│  │  "Patient confirmed consent during phone call"                           │
│  │                                                                          │
│  ●  11/15/2025 10:22 AM by Dr. Green                                       │
│  │  (Initial) →  ⏳ Pending                                                 │
│  │  "Patient created from Allscripts import"                                │
│  │                                                                          │
│  ●  11/10/2025 2:00 PM by System                                           │
│     (Created) →  ⏳ Pending                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### IPC Handlers
```typescript
// Get consent history
ipcMain.handle('consent:getHistory', async (event, { patientId }) => {
  await validateSession(event);

  const history = await db.select().from(consentHistory)
    .where(eq(consentHistory.patientId, patientId))
    .orderBy(desc(consentHistory.changedAt));

  return history;
});

// Export history
ipcMain.handle('consent:exportHistory', async (event, { patientId }) => {
  await validateSession(event);

  const history = await db.select().from(consentHistory)
    .where(eq(consentHistory.patientId, patientId))
    .orderBy(asc(consentHistory.changedAt));

  const csv = [
    'Date,Time,Previous Status,New Status,Method,Changed By,Notes',
    ...history.map(h => [
      formatDate(h.changedAt),
      formatTime(h.changedAt),
      h.previousStatus || 'Initial',
      h.newStatus,
      h.method || '',
      h.changedBy,
      `"${(h.notes || '').replace(/"/g, '""')}"`,
    ].join(',')),
  ].join('\n');

  return csv;
});
```

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - History entry created on consent change
  - History entries are immutable
  - Timeline displays in chronological order
  - Export generates valid CSV
  - History shows correct user attribution

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
