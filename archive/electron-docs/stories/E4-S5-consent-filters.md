# Story E4-S5: Filter Patients by Consent Status

## Status
Draft

## Story
**As a** clinical user,
**I want** to filter the patient list by consent status,
**so that** I can focus on patients needing consent follow-up.

## Acceptance Criteria
1. Filter tabs appear above patient list: All, Pending, Obtained, Declined
2. Clicking tab filters list to matching consent status
3. Count badge shows number of patients per status
4. Active tab is visually highlighted
5. Filter persists during session
6. URL updates to reflect filter state

## Tasks / Subtasks
- [ ] Create filter tabs component (AC: 1, 4)
  - [ ] Create src/renderer/components/ConsentFilterTabs.tsx
  - [ ] Tab for each status plus "All"
  - [ ] Active state styling
- [ ] Add count badges (AC: 3)
  - [ ] Query count per status
  - [ ] Display next to tab label
  - [ ] Update on data changes
- [ ] Implement filtering logic (AC: 2)
  - [ ] Update patient:list IPC to accept filter
  - [ ] Apply WHERE clause for status
  - [ ] Update React Query key
- [ ] Handle URL state (AC: 5, 6)
  - [ ] useSearchParams for filter state
  - [ ] Update URL on tab change
  - [ ] Restore filter from URL on mount

## Dev Notes

### Filter Tabs Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [All (1,384)]  [⏳ Pending (892)]  [✓ Obtained (487)]  [✕ Declined (5)]    │
├─────────────────────────────────────────────────────────────────────────────┤
│  MRN ▼  │ Name        │ DOB        │ Last DOS │ Consent  │ APCM    │       │
├─────────┼─────────────┼────────────┼──────────┼──────────┼─────────┼───────┤
│  12345  │ Doe, John   │ 05/15/1960 │ 11/28/25 │ ⏳ Pending│ ○ Eligible │ ...│
│  12346  │ Smith, Jane │ 03/22/1958 │ 11/01/25 │ ⏳ Pending│ ○ Eligible │ ...│
└─────────────────────────────────────────────────────────────────────────────┘
```

### ConsentFilterTabs Component
```typescript
interface FilterTab {
  id: ConsentStatus | 'all';
  label: string;
  icon?: string;
  className: string;
}

const filterTabs: FilterTab[] = [
  { id: 'all', label: 'All', className: 'bg-gray-100 text-gray-800' },
  { id: 'pending', label: 'Pending', icon: '⏳', className: 'bg-yellow-100 text-yellow-800' },
  { id: 'obtained', label: 'Obtained', icon: '✓', className: 'bg-green-100 text-green-800' },
  { id: 'declined', label: 'Declined', icon: '✕', className: 'bg-red-100 text-red-800' },
];

function ConsentFilterTabs({ activeFilter, onFilterChange, counts }: FilterTabsProps) {
  return (
    <div className="flex gap-2 mb-4">
      {filterTabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onFilterChange(tab.id)}
          className={cn(
            'px-4 py-2 rounded-lg font-medium transition-colors',
            tab.className,
            activeFilter === tab.id ? 'ring-2 ring-offset-2' : 'opacity-70 hover:opacity-100'
          )}
        >
          {tab.icon && <span className="mr-1">{tab.icon}</span>}
          {tab.label}
          <span className="ml-2 text-sm">({counts[tab.id] || 0})</span>
        </button>
      ))}
    </div>
  );
}
```

### URL Integration
```typescript
function PatientsScreen() {
  const [searchParams, setSearchParams] = useSearchParams();
  const consentFilter = searchParams.get('consent') as ConsentStatus | 'all' || 'all';

  const { data: counts } = useQuery({
    queryKey: ['patient-consent-counts'],
    queryFn: () => window.api.patient.getConsentCounts(),
  });

  const { data: patients } = useQuery({
    queryKey: ['patients', page, sortBy, sortDir, consentFilter],
    queryFn: () => window.api.patient.list({
      limit: 25,
      offset: page * 25,
      sortBy,
      sortDir,
      consentStatus: consentFilter === 'all' ? undefined : consentFilter,
    }),
  });

  const handleFilterChange = (filter: ConsentStatus | 'all') => {
    setSearchParams({ consent: filter });
  };

  return (
    <div>
      <ConsentFilterTabs
        activeFilter={consentFilter}
        onFilterChange={handleFilterChange}
        counts={counts}
      />
      <PatientTable patients={patients} />
    </div>
  );
}
```

### IPC Handler Updates
```typescript
// Get consent counts
ipcMain.handle('patient:getConsentCounts', async (event) => {
  await validateSession(event);

  const counts = await db.select({
    status: patients.consentStatus,
    count: sql`count(*)`,
  })
  .from(patients)
  .where(isNull(patients.deletedAt))
  .groupBy(patients.consentStatus);

  const total = counts.reduce((sum, c) => sum + Number(c.count), 0);

  return {
    all: total,
    ...Object.fromEntries(counts.map(c => [c.status, Number(c.count)])),
  };
});

// Updated list with filter
ipcMain.handle('patient:list', async (event, params) => {
  const { consentStatus, ...otherParams } = params;

  let query = db.select().from(patients)
    .where(isNull(patients.deletedAt));

  if (consentStatus) {
    query = query.where(eq(patients.consentStatus, consentStatus));
  }

  // ... rest of query
});
```

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - All tabs render with counts
  - Clicking tab updates filter
  - Patient list filters correctly
  - URL updates on filter change
  - Filter restores from URL
  - Active tab shows highlight

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
