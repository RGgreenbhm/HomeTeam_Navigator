# Story E3-S2: Create Patient Detail View with Tabs

## Status
Draft

## Story
**As a** clinical user,
**I want** to see a patient's complete information in a tabbed view,
**so that** I can access all their data in one place.

## Acceptance Criteria
1. Header displays patient name, MRN, DOB, age
2. Tabs include: Timeline, Care Plans, Consents, Notes
3. Default tab is Timeline (most recent activity)
4. Edit button opens patient edit form
5. Breadcrumb navigation back to patient list
6. Status badges show consent and APCM status

## Tasks / Subtasks
- [ ] Create patient detail screen (AC: 1, 2)
  - [ ] Create src/renderer/screens/PatientDetailScreen.tsx
  - [ ] Build header with demographics
  - [ ] Implement tab navigation
- [ ] Implement header section (AC: 1, 6)
  - [ ] Display: "Doe, John" (large text)
  - [ ] Display: "MRN: 12345 • DOB: 05/15/1960 (64y)"
  - [ ] Show consent status badge
  - [ ] Show APCM status badge
- [ ] Create tab components (AC: 2, 3)
  - [ ] TimelineTab (default)
  - [ ] CarePlansTab
  - [ ] ConsentsTab
  - [ ] NotesTab
  - [ ] Use URL params for tab state
- [ ] Add edit functionality (AC: 4)
  - [ ] Edit button in header
  - [ ] Opens PatientEditModal
  - [ ] Refreshes data on save
- [ ] Add breadcrumb nav (AC: 5)
  - [ ] "← Back to Patients" link
  - [ ] Uses react-router navigation
- [ ] Fetch patient data
  - [ ] patient:get IPC handler
  - [ ] React Query with patient ID
  - [ ] Handle not found state

## Dev Notes

### Patient Detail Layout (from Frontend Spec §4.5)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Patients                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Doe, John                              [✓ APCM] [✓ Consent]                │
│  MRN: 12345 • DOB: 05/15/1960 (64y)    [Generate Care Plan] [Edit]          │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Timeline] [Care Plans] [Consents] [Notes]                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  (Tab content renders here)                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Age Calculation
```typescript
function calculateAge(dob: string): number {
  const birth = new Date(dob);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  return age;
}
```

### Tab Navigation with URL
```typescript
// Route: /patients/:id/:tab?
const { id, tab = 'timeline' } = useParams();
const navigate = useNavigate();

const tabs = [
  { id: 'timeline', label: 'Timeline' },
  { id: 'careplans', label: 'Care Plans' },
  { id: 'consents', label: 'Consents' },
  { id: 'notes', label: 'Notes' },
];

const handleTabChange = (tabId: string) => {
  navigate(`/patients/${id}/${tabId}`);
};
```

### Status Badge Component
```typescript
<Badge variant={patient.consentStatus === 'signed' ? 'success' : 'warning'}>
  {patient.consentStatus === 'signed' ? '✓ Consent' : '⏳ Pending'}
</Badge>
```

## Testing
- **Location**: `src/renderer/screens/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Header renders patient info
  - Tabs switch content
  - Edit button opens modal
  - Back link navigates correctly
  - Age calculates correctly
  - Not found shows 404 state

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
