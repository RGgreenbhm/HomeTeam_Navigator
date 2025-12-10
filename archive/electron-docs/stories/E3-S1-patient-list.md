# Story E3-S1: Implement Patient List View with Data Table

## Status
Draft

## Story
**As a** clinical user,
**I want** to see all patients in a sortable, paginated table,
**so that** I can quickly find and manage patient records.

## Acceptance Criteria
1. Table displays columns: MRN, Name, DOB, Last DOS, Consent Status, APCM Status
2. Table is sortable by clicking column headers
3. Pagination shows 25 patients per page with navigation
4. Total patient count is displayed (e.g., "1-25 of 1,384")
5. Loading state shows skeleton rows
6. Empty state shows "No patients found" with add button

## Tasks / Subtasks
- [ ] Create patient list screen (AC: 1)
  - [ ] Create src/renderer/screens/PatientsScreen.tsx
  - [ ] Set up table layout with headers
  - [ ] Display patient data in rows
- [ ] Implement data fetching (AC: 1, 5)
  - [ ] Create patient:list IPC handler
  - [ ] Use React Query for caching
  - [ ] Show skeleton during load
- [ ] Add sorting (AC: 2)
  - [ ] Click header to toggle sort direction
  - [ ] Visual indicator for active sort column
  - [ ] Persist sort preference in localStorage
- [ ] Implement pagination (AC: 3, 4)
  - [ ] Show 25 patients per page
  - [ ] Previous/Next buttons
  - [ ] Page number display
  - [ ] Total count from query
- [ ] Create empty state (AC: 6)
  - [ ] "No patients found" message
  - [ ] "Add Patient" button
  - [ ] Icon illustration
- [ ] Style table components
  - [ ] Hover state on rows
  - [ ] Zebra striping optional
  - [ ] Fixed header on scroll

## Dev Notes

### Patient List Layout (from Frontend Spec §4.4)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Patients                                      🔍 [Search patients...]      │
├─────────────────────────────────────────────────────────────────────────────┤
│  [All] [APCM Enrolled] [Needs Follow-up] [Pending Consent]                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  MRN ▼  │ Name        │ DOB        │ Last DOS │ Consent  │ APCM    │       │
├─────────┼─────────────┼────────────┼──────────┼──────────┼─────────┼───────┤
│  12345  │ Doe, John   │ 05/15/1960 │ 11/28/25 │ ✓ Signed │ ✓ Enrolled │ ...│
│  12346  │ Smith, Jane │ 03/22/1958 │ 11/01/25 │ ⏳ Pending│ ○ Eligible │ ...│
├─────────────────────────────────────────────────────────────────────────────┤
│                        ◀ Previous  1-25 of 1,384  Next ▶                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### IPC Handler (from Architecture §5.2.1)
```typescript
ipcMain.handle('patient:list', async (event, params?: PatientListParams) => {
  const session = await validateSession(event);

  const { search, limit = 25, offset = 0, sortBy = 'lastName', sortDir = 'asc' } = params || {};

  const query = db.select().from(patients)
    .where(isNull(patients.deletedAt))
    .orderBy(sortDir === 'asc' ? asc(patients[sortBy]) : desc(patients[sortBy]))
    .limit(limit)
    .offset(offset);

  const [results, [{ count }]] = await Promise.all([
    query,
    db.select({ count: sql`count(*)` }).from(patients).where(isNull(patients.deletedAt)),
  ]);

  await auditLog({ action: 'READ', entityType: 'patient', details: { count: results.length } });

  return { patients: results, total: count };
});
```

### React Query Setup
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['patients', page, sortBy, sortDir],
  queryFn: () => window.api.patient.list({ limit: 25, offset: page * 25, sortBy, sortDir }),
  keepPreviousData: true,
});
```

### Table Dependencies
- @tanstack/react-table: ^8.x (headless table)
- Or build with basic HTML table

## Testing
- **Location**: `src/renderer/screens/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Table renders with patient data
  - Clicking header sorts column
  - Pagination updates displayed range
  - Empty state shows when no patients
  - Loading skeleton appears while fetching

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
