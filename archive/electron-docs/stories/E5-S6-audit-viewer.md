# Story E5-S6: Build Audit Log Viewer

## Status
Draft

## Story
**As a** clinical admin,
**I want** to view and filter audit logs in the application,
**so that** I can review access patterns and investigate security events.

## Acceptance Criteria
1. Audit log viewer accessible from Settings (admin only)
2. Table displays: Timestamp, User, Action, Entity Type, Entity ID
3. Filter by date range, user, action type, entity type
4. Search by entity ID or details content
5. Expandable rows show full details JSON
6. Export filtered results to CSV

## Tasks / Subtasks
- [ ] Create audit log screen (AC: 1, 2)
  - [ ] Create src/renderer/screens/AuditLogScreen.tsx
  - [ ] Admin-only route guard
  - [ ] Paginated table display
- [ ] Add filter controls (AC: 3)
  - [ ] Date range picker
  - [ ] User dropdown
  - [ ] Action type checkboxes
  - [ ] Entity type checkboxes
- [ ] Implement search (AC: 4)
  - [ ] Search input for entity ID
  - [ ] Full-text search in details
- [ ] Add expandable details (AC: 5)
  - [ ] Click row to expand
  - [ ] Pretty-print JSON details
  - [ ] Syntax highlighting
- [ ] Add export button (AC: 6)
  - [ ] Export current filtered view
  - [ ] CSV format
  - [ ] File save dialog

## Dev Notes

### Audit Log Screen Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Audit Logs                                                [Export CSV]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Date Range: [11/01/2025] to [11/30/2025]    User: [All Users ▼]           │
│                                                                             │
│  Actions: ☑ READ  ☑ CREATE  ☑ UPDATE  ☐ DELETE  ☑ LOGIN  ☑ LOGOUT         │
│  Entities: ☑ patient  ☑ consent  ☑ system  ☐ carePlan                      │
│                                                                             │
│  Search: [Search by entity ID or details...      ]                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Timestamp          │ User          │ Action  │ Entity Type │ Entity ID    │
├─────────────────────┼───────────────┼─────────┼─────────────┼──────────────┤
│▼ 11/30/25 3:45 PM   │ L. Watts      │ UPDATE  │ patient     │ abc-123      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  {                                                                  │   │
│  │    "before": { "consentStatus": "pending" },                        │   │
│  │    "after": { "consentStatus": "obtained" },                        │   │
│  │    "changedFields": ["consentStatus", "consentDate"]                │   │
│  │  }                                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  11/30/25 3:42 PM   │ L. Watts      │ READ    │ patient     │ abc-123      │
│  11/30/25 3:40 PM   │ L. Watts      │ LOGIN   │ system      │              │
│  11/30/25 2:15 PM   │ Dr. Green     │ CREATE  │ patient     │ def-456      │
├─────────────────────────────────────────────────────────────────────────────┤
│                      ◀ Previous   Page 1 of 47   Next ▶                     │
│                        Showing 1-25 of 1,168 entries                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Audit Log Table Component
```typescript
function AuditLogTable({ filters }: { filters: AuditFilters }) {
  const [page, setPage] = useState(0);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', filters, page],
    queryFn: () => window.api.audit.list({
      ...filters,
      limit: 25,
      offset: page * 25,
    }),
  });

  return (
    <table className="w-full">
      <thead>
        <tr className="bg-gray-100">
          <th>Timestamp</th>
          <th>User</th>
          <th>Action</th>
          <th>Entity Type</th>
          <th>Entity ID</th>
        </tr>
      </thead>
      <tbody>
        {data?.logs.map((log) => (
          <Fragment key={log.id}>
            <tr
              onClick={() => setExpandedRow(expandedRow === log.id ? null : log.id)}
              className="cursor-pointer hover:bg-gray-50"
            >
              <td>{formatDateTime(log.timestamp)}</td>
              <td>{log.username || 'System'}</td>
              <td><ActionBadge action={log.action} /></td>
              <td>{log.entityType}</td>
              <td className="font-mono text-sm">{log.entityId || '—'}</td>
            </tr>
            {expandedRow === log.id && log.details && (
              <tr>
                <td colSpan={5} className="bg-gray-50 p-4">
                  <pre className="text-sm overflow-auto">
                    {JSON.stringify(JSON.parse(log.details), null, 2)}
                  </pre>
                </td>
              </tr>
            )}
          </Fragment>
        ))}
      </tbody>
    </table>
  );
}
```

### Filter Component
```typescript
function AuditFilters({ filters, onChange }: AuditFiltersProps) {
  const { data: users } = useQuery({
    queryKey: ['users-list'],
    queryFn: () => window.api.user.list(),
  });

  return (
    <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
      <div className="flex gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Date Range</label>
          <div className="flex gap-2 items-center">
            <DatePicker
              value={filters.startDate}
              onChange={(d) => onChange({ ...filters, startDate: d })}
            />
            <span>to</span>
            <DatePicker
              value={filters.endDate}
              onChange={(d) => onChange({ ...filters, endDate: d })}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">User</label>
          <select
            value={filters.userId || ''}
            onChange={(e) => onChange({ ...filters, userId: e.target.value || undefined })}
          >
            <option value="">All Users</option>
            {users?.map((u) => (
              <option key={u.id} value={u.id}>{u.displayName}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Actions</label>
        <div className="flex flex-wrap gap-2">
          {actionTypes.map((action) => (
            <label key={action} className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={filters.actions?.includes(action) ?? true}
                onChange={(e) => {
                  const actions = filters.actions || actionTypes;
                  onChange({
                    ...filters,
                    actions: e.target.checked
                      ? [...actions, action]
                      : actions.filter(a => a !== action),
                  });
                }}
              />
              {action}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Search</label>
        <input
          type="text"
          placeholder="Search by entity ID or details..."
          value={filters.search || ''}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="w-full px-3 py-2 border rounded"
        />
      </div>
    </div>
  );
}
```

### Action Badge Component
```typescript
const actionStyles: Record<string, string> = {
  CREATE: 'bg-green-100 text-green-800',
  READ: 'bg-blue-100 text-blue-800',
  UPDATE: 'bg-yellow-100 text-yellow-800',
  DELETE: 'bg-red-100 text-red-800',
  LOGIN_SUCCESS: 'bg-green-100 text-green-800',
  LOGIN_FAILED: 'bg-red-100 text-red-800',
  LOGOUT: 'bg-gray-100 text-gray-800',
  AUTO_LOGOUT: 'bg-orange-100 text-orange-800',
};

function ActionBadge({ action }: { action: string }) {
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${actionStyles[action] || 'bg-gray-100'}`}>
      {action}
    </span>
  );
}
```

### IPC Handler for Listing
```typescript
ipcMain.handle('audit:list', async (event, params) => {
  const session = await validateSession(event);
  if (session.role !== 'admin') {
    throw new Error('Admin access required');
  }

  const { startDate, endDate, userId, actions, entityTypes, search, limit = 25, offset = 0 } = params;

  let query = db.select().from(auditLogs);

  // Apply filters
  const conditions = [];

  if (startDate) conditions.push(gte(auditLogs.timestamp, startDate));
  if (endDate) conditions.push(lte(auditLogs.timestamp, endDate));
  if (userId) conditions.push(eq(auditLogs.userId, userId));
  if (actions?.length) conditions.push(inArray(auditLogs.action, actions));
  if (entityTypes?.length) conditions.push(inArray(auditLogs.entityType, entityTypes));
  if (search) {
    conditions.push(or(
      like(auditLogs.entityId, `%${search}%`),
      like(auditLogs.details, `%${search}%`)
    ));
  }

  if (conditions.length) {
    query = query.where(and(...conditions));
  }

  const [logs, [{ count }]] = await Promise.all([
    query.orderBy(desc(auditLogs.timestamp)).limit(limit).offset(offset),
    db.select({ count: sql`count(*)` }).from(auditLogs).where(and(...conditions)),
  ]);

  return { logs, total: count };
});
```

## Testing
- **Location**: `src/renderer/screens/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Admin-only access enforced
  - Table displays log entries
  - Filters reduce results
  - Search works on entity ID
  - Expanded row shows details
  - Export generates CSV file

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
