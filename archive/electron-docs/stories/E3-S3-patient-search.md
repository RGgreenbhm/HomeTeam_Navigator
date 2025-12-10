# Story E3-S3: Add Patient Search with Instant Results

## Status
Draft

## Story
**As a** clinical user,
**I want** to search for patients by name, MRN, or DOB,
**so that** I can quickly find the patient I'm looking for.

## Acceptance Criteria
1. Search by name matches first name, last name, or full name
2. Search by MRN matches exact MRN number
3. Search by DOB matches date format (mm/dd/yyyy)
4. Results update as user types (debounced 150ms)
5. Search response time is under 500ms (NFR4)
6. Empty results show "No patients found" with suggestion

## Tasks / Subtasks
- [ ] Create search input component (AC: 1, 2, 3)
  - [ ] Create src/renderer/components/PatientSearch.tsx
  - [ ] Add search icon prefix
  - [ ] Support clear button
- [ ] Implement search IPC handler (AC: 1, 2, 3, 5)
  - [ ] Add patient:search handler
  - [ ] Search lastName, firstName, mrn
  - [ ] Parse DOB searches (convert to YYYY-MM-DD)
  - [ ] Optimize with indexes
- [ ] Add debouncing (AC: 4)
  - [ ] 150ms debounce after typing stops
  - [ ] Cancel pending requests on new input
  - [ ] Use useDeferredValue or custom debounce
- [ ] Display results (AC: 4)
  - [ ] Show results in dropdown as typing
  - [ ] Highlight matching text
  - [ ] Show patient info: Name, MRN, DOB
- [ ] Handle empty state (AC: 6)
  - [ ] "No patients found for 'query'"
  - [ ] "Try searching by MRN or full name"
- [ ] Add keyboard navigation
  - [ ] Arrow up/down to navigate results
  - [ ] Enter to select
  - [ ] Escape to close

## Dev Notes

### Search IPC Handler (NFR4: < 500ms)
```typescript
ipcMain.handle('patient:search', async (event, { query, limit = 10 }) => {
  const session = await validateSession(event);

  // Normalize query
  const searchTerm = query.trim().toLowerCase();

  // Check if DOB search (contains /)
  const isDobSearch = /\d{1,2}\/\d{1,2}\/\d{2,4}/.test(query);
  if (isDobSearch) {
    const isoDate = convertToISODate(query); // mm/dd/yyyy → YYYY-MM-DD
    return db.select().from(patients)
      .where(eq(patients.dateOfBirth, isoDate))
      .limit(limit);
  }

  // Name/MRN search using LIKE with index
  const results = await db.select().from(patients)
    .where(
      or(
        like(patients.lastName, `%${searchTerm}%`),
        like(patients.firstName, `%${searchTerm}%`),
        eq(patients.mrn, searchTerm),
      )
    )
    .where(isNull(patients.deletedAt))
    .limit(limit);

  return results;
});
```

### Search Component
```typescript
function PatientSearch({ onSelect }: { onSelect: (patient: Patient) => void }) {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);

  const { data: results, isLoading } = useQuery({
    queryKey: ['patient-search', deferredQuery],
    queryFn: () => window.api.patient.search({ query: deferredQuery }),
    enabled: deferredQuery.length >= 2,
  });

  // ...
}
```

### Highlight Matching Text
```typescript
function HighlightMatch({ text, query }: { text: string; query: string }) {
  const parts = text.split(new RegExp(`(${query})`, 'gi'));
  return (
    <span>
      {parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={i} className="bg-yellow-200">{part}</mark>
        ) : (
          part
        )
      )}
    </span>
  );
}
```

### Performance Requirements
- NFR4: Search response < 500ms
- Database indexes on lastName, firstName, mrn
- Limit results to 10 for dropdown

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Search by last name returns matches
  - Search by MRN returns exact match
  - DOB search parses correctly
  - Debounce prevents excessive queries
  - Empty state renders suggestion
  - Keyboard navigation works

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
