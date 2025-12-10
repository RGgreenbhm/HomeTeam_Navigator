# Story E3-S5: Tag Captures to Patients

## Status
Draft

## Story
**As a** clinical user,
**I want** to associate captures with specific patients,
**so that** captured data appears in the patient's record.

## Acceptance Criteria
1. Patient selector dropdown appears when saving capture
2. Typeahead search filters patients by name or MRN
3. Selected patient is saved with capture record
4. Capture appears in patient's Captures tab
5. User can create new patient inline if not found
6. Capture displays patient attribution in Capture Workspace

## Tasks / Subtasks
- [ ] Create patient selector component (AC: 1, 2)
  - [ ] Create src/renderer/components/PatientSelector.tsx
  - [ ] Typeahead with debounce (150ms)
  - [ ] Display: "Doe, John (MRN: 12345)"
  - [ ] Clear button to deselect
- [ ] Add data type tagging (AC: 3)
  - [ ] Dropdown for capture type (Timeline, Medication, Lab, Note, etc.)
  - [ ] Required before save
  - [ ] Stored in captureType field
- [ ] Implement save with patient association (AC: 3, 6)
  - [ ] Update capture:save IPC to include patientId
  - [ ] Validate patient exists
  - [ ] Show patient info after save
- [ ] Display captures in patient detail (AC: 4)
  - [ ] Add Captures tab to patient detail
  - [ ] Chronological list of captures
  - [ ] Click to view full capture
- [ ] Add inline patient creation (AC: 5)
  - [ ] "+ Create New Patient" option at bottom of dropdown
  - [ ] Opens mini patient form modal
  - [ ] Auto-selects after creation

## Dev Notes

### Capture Workflow with Patient Tagging
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Capture Workspace                                                          │
├────────────────────┬───────────────────────┬────────────────────────────────┤
│                    │                       │                                │
│  [Drop Zone]       │  OCR Text Preview     │  Patient & Tag                 │
│                    │                       │                                │
│  ┌────────────┐    │  Extracted text...    │  Select Patient *              │
│  │            │    │                       │  ┌──────────────────────────┐  │
│  │  Paste or  │    │                       │  │ 🔍 Search patients...    │  │
│  │  Drop Here │    │                       │  └──────────────────────────┘  │
│  │            │    │                       │                                │
│  └────────────┘    │                       │  Capture Type *                │
│                    │                       │  ┌──────────────────────────┐  │
│                    │                       │  │ Select type...           │  │
│                    │                       │  └──────────────────────────┘  │
│                    │                       │                                │
│                    │                       │  Notes                         │
│                    │                       │  ┌──────────────────────────┐  │
│                    │                       │  │                          │  │
│                    │                       │  └──────────────────────────┘  │
│                    │                       │                                │
│                    │                       │  [Cancel]  [Save Capture]      │
└────────────────────┴───────────────────────┴────────────────────────────────┘
```

### Capture Types (from PRD)
```typescript
const captureTypes = [
  { value: 'timeline', label: 'Timeline / Progress Note' },
  { value: 'medication', label: 'Medication List' },
  { value: 'lab', label: 'Lab Results' },
  { value: 'vital', label: 'Vital Signs' },
  { value: 'problem', label: 'Problem List' },
  { value: 'allergy', label: 'Allergies' },
  { value: 'imaging', label: 'Imaging / Radiology' },
  { value: 'schedule', label: 'Schedule / Appointments' },
  { value: 'consent', label: 'Consent Form' },
  { value: 'other', label: 'Other' },
];
```

### Patient Selector with Typeahead
```typescript
function PatientSelector({ value, onChange }: PatientSelectorProps) {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);
  const [showCreate, setShowCreate] = useState(false);

  const { data: patients } = useQuery({
    queryKey: ['patient-search', deferredQuery],
    queryFn: () => window.api.patient.search({ query: deferredQuery, limit: 10 }),
    enabled: deferredQuery.length >= 2,
  });

  return (
    <Combobox value={value} onChange={onChange}>
      <Combobox.Input
        placeholder="Search patients..."
        onChange={(e) => setQuery(e.target.value)}
      />
      <Combobox.Options>
        {patients?.map((patient) => (
          <Combobox.Option key={patient.id} value={patient}>
            {patient.lastName}, {patient.firstName} (MRN: {patient.mrn})
          </Combobox.Option>
        ))}
        <Combobox.Option value="__create__" onClick={() => setShowCreate(true)}>
          + Create New Patient
        </Combobox.Option>
      </Combobox.Options>
    </Combobox>
  );
}
```

### Captures Tab in Patient Detail
```typescript
function CapturesTab({ patientId }: { patientId: string }) {
  const { data: captures } = useQuery({
    queryKey: ['patient-captures', patientId],
    queryFn: () => window.api.capture.listByPatient({ patientId }),
  });

  return (
    <div className="space-y-4">
      {captures?.map((capture) => (
        <CaptureCard key={capture.id} capture={capture} />
      ))}
    </div>
  );
}
```

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Patient selector renders with search
  - Typeahead filters patients correctly
  - Create new patient option appears
  - Capture saves with patient association
  - Captures tab displays patient's captures
  - Capture type is required for save

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
