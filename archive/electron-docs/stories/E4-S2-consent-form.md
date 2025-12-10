# Story E4-S2: Create Consent Tracking Form

## Status
Draft

## Story
**As a** clinical user,
**I want** to record consent status through a dedicated form,
**so that** I can track how and when patients consented.

## Acceptance Criteria
1. Consent form accessible from patient detail view
2. Status selection (Pending, Obtained, Declined)
3. Method selection required when status is Obtained
4. Date picker defaults to today's date
5. Optional witness field for verbal/written consent
6. Notes field for additional context
7. Save updates patient record and creates history entry

## Tasks / Subtasks
- [ ] Create consent form component (AC: 1, 2, 3)
  - [ ] Create src/renderer/components/ConsentForm.tsx
  - [ ] Status radio buttons with color coding
  - [ ] Conditional method dropdown
  - [ ] Form validation
- [ ] Add date and witness fields (AC: 4, 5)
  - [ ] Date picker component
  - [ ] Default to current date
  - [ ] Witness text input (shown for verbal/written)
- [ ] Add notes field (AC: 6)
  - [ ] Textarea for additional context
  - [ ] Character limit indication
- [ ] Implement save functionality (AC: 7)
  - [ ] patient:updateConsent IPC handler
  - [ ] Create consent history entry
  - [ ] Show success notification
  - [ ] Refresh patient detail

## Dev Notes

### Consent Form Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Update Consent Status                                          [X]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Patient: Doe, John (MRN: 12345)                                           │
│                                                                             │
│  Consent Status *                                                           │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                  │
│  │ ⏳ Pending     │ │ ✓ Obtained     │ │ ✕ Declined     │                  │
│  └────────────────┘ └────────────────┘ └────────────────┘                  │
│                                                                             │
│  ─────────────── When status is Obtained ───────────────                   │
│                                                                             │
│  Method *                          Date *                                   │
│  ┌─────────────────────────┐      ┌─────────────────────────┐              │
│  │ Select method...      ▼ │      │ 11/30/2025              │              │
│  └─────────────────────────┘      └─────────────────────────┘              │
│                                                                             │
│  Witness (for verbal/written)                                               │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  Notes                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                                                             │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│  0 / 500 characters                                                         │
│                                                                             │
│                                    [Cancel]  [Save Consent Status]          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Consent Form Component
```typescript
function ConsentForm({ patient, onSave, onCancel }: ConsentFormProps) {
  const [status, setStatus] = useState<ConsentStatus>(patient.consentStatus);
  const [method, setMethod] = useState<ConsentMethod | undefined>(patient.consentMethod);
  const [date, setDate] = useState(patient.consentDate || new Date().toISOString().split('T')[0]);
  const [witness, setWitness] = useState(patient.consentWitness || '');
  const [notes, setNotes] = useState(patient.consentNotes || '');

  const showMethodFields = status === 'obtained';
  const showWitness = method === 'verbal' || method === 'written';

  const handleSubmit = async () => {
    await window.api.patient.updateConsent({
      patientId: patient.id,
      consentStatus: status,
      consentMethod: showMethodFields ? method : undefined,
      consentDate: showMethodFields ? date : undefined,
      consentWitness: showWitness ? witness : undefined,
      consentNotes: notes || undefined,
    });
    onSave();
  };

  return (
    // Form JSX...
  );
}
```

### IPC Handler
```typescript
ipcMain.handle('patient:updateConsent', async (event, consentData) => {
  const session = await validateSession(event);
  const { patientId, ...consentFields } = consentData;

  // Get current consent status for history
  const [current] = await db.select().from(patients)
    .where(eq(patients.id, patientId));

  // Update patient consent fields
  await db.update(patients)
    .set({
      ...consentFields,
      updatedAt: new Date().toISOString(),
    })
    .where(eq(patients.id, patientId));

  // Create consent history entry
  await db.insert(consentHistory).values({
    patientId,
    previousStatus: current.consentStatus,
    newStatus: consentFields.consentStatus,
    method: consentFields.consentMethod,
    changedBy: session.userId,
    changedAt: new Date().toISOString(),
    notes: consentFields.consentNotes,
  });

  await auditLog({
    action: 'UPDATE_CONSENT',
    entityType: 'patient',
    entityId: patientId,
    details: { from: current.consentStatus, to: consentFields.consentStatus },
  });

  return { success: true };
});
```

### Status Button Styling
```typescript
const statusStyles = {
  pending: 'bg-yellow-100 border-yellow-400 text-yellow-800',
  obtained: 'bg-green-100 border-green-400 text-green-800',
  declined: 'bg-red-100 border-red-400 text-red-800',
};
```

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Form renders with current consent status
  - Method dropdown appears when Obtained selected
  - Witness field appears for verbal/written
  - Date defaults to today
  - Save calls IPC handler with correct data
  - History entry is created on save

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
