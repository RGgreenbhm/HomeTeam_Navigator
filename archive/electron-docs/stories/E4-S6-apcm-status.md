# Story E4-S6: Add APCM Enrollment Status Tracking

## Status
Draft

## Story
**As a** clinical user,
**I want** to track APCM (Advanced Primary Care Management) enrollment status,
**so that** I can manage patient enrollment in the CMS care management program.

## Acceptance Criteria
1. Patient schema includes apcmStatus field (eligible, enrolled, declined, ineligible)
2. APCM enrollment date is tracked
3. Authorization/enrollment number stored
4. APCM status badge displays in patient list
5. APCM status can be updated from patient detail
6. APCM filter tab shows enrolled/eligible patients

## Tasks / Subtasks
- [ ] Update patient schema for APCM (AC: 1, 2, 3)
  - [ ] Add apcmStatus column (text enum)
  - [ ] Add apcmEnrollmentDate column
  - [ ] Add apcmAuthorizationNumber column
  - [ ] Add apcmNotes column
- [ ] Create APCM badge component (AC: 4)
  - [ ] Color-coded by status
  - [ ] Display in patient list
  - [ ] Show enrollment date on hover
- [ ] Add APCM update form (AC: 5)
  - [ ] Status selection
  - [ ] Date and authorization number fields
  - [ ] Notes field
- [ ] Add APCM filter (AC: 6)
  - [ ] APCM Enrolled filter tab
  - [ ] APCM Eligible filter tab

## Dev Notes

### APCM Status Definitions
| Status | Description | Badge Color |
|--------|-------------|-------------|
| `eligible` | Patient meets APCM criteria, not yet enrolled | Blue |
| `enrolled` | Active APCM enrollment | Green |
| `declined` | Patient declined APCM participation | Gray |
| `ineligible` | Does not meet APCM criteria | Gray |

### Schema Updates
```typescript
export const apcmStatusEnum = ['eligible', 'enrolled', 'declined', 'ineligible'] as const;

export const patients = sqliteTable('patients', {
  // ... existing fields ...

  // APCM fields
  apcmStatus: text('apcm_status', { enum: apcmStatusEnum })
    .notNull()
    .default('ineligible'),
  apcmEnrollmentDate: text('apcm_enrollment_date'), // ISO date
  apcmAuthorizationNumber: text('apcm_authorization_number'),
  apcmNotes: text('apcm_notes'),
});
```

### APCM Badge Component
```typescript
const apcmBadgeConfig = {
  eligible: {
    icon: '○',
    label: 'Eligible',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
  },
  enrolled: {
    icon: '✓',
    label: 'Enrolled',
    className: 'bg-green-100 text-green-800 border-green-300',
  },
  declined: {
    icon: '—',
    label: 'Declined',
    className: 'bg-gray-100 text-gray-600 border-gray-300',
  },
  ineligible: {
    icon: '—',
    label: 'Not Eligible',
    className: 'bg-gray-100 text-gray-600 border-gray-300',
  },
};

function ApcmBadge({ status, enrollmentDate, authNumber }: ApcmBadgeProps) {
  const config = apcmBadgeConfig[status];

  const tooltipContent = status === 'enrolled'
    ? `Enrolled ${formatDate(enrollmentDate)} | Auth: ${authNumber}`
    : status === 'eligible'
    ? 'Meets APCM criteria'
    : 'Not enrolled in APCM';

  return (
    <Tooltip content={tooltipContent}>
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${config.className}`}>
        <span className="mr-1">{config.icon}</span>
        {config.label}
      </span>
    </Tooltip>
  );
}
```

### APCM Form
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  APCM Enrollment Status                                         [X]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Patient: Doe, John (MRN: 12345)                                           │
│                                                                             │
│  APCM Status *                                                              │
│  ┌──────────────────┐ ┌──────────────────┐                                 │
│  │ ○ Eligible       │ │ ✓ Enrolled       │                                 │
│  └──────────────────┘ └──────────────────┘                                 │
│  ┌──────────────────┐ ┌──────────────────┐                                 │
│  │ — Declined       │ │ — Not Eligible   │                                 │
│  └──────────────────┘ └──────────────────┘                                 │
│                                                                             │
│  ─────────────── When status is Enrolled ───────────────                   │
│                                                                             │
│  Enrollment Date *                Authorization Number                      │
│  ┌─────────────────────────┐      ┌─────────────────────────┐              │
│  │ 11/30/2025              │      │ APCM-2025-00123         │              │
│  └─────────────────────────┘      └─────────────────────────┘              │
│                                                                             │
│  Notes                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ Patient enrolled during annual wellness visit               │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│                                    [Cancel]  [Save APCM Status]             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### IPC Handler
```typescript
ipcMain.handle('patient:updateApcm', async (event, apcmData) => {
  const session = await validateSession(event);
  const { patientId, ...apcmFields } = apcmData;

  await db.update(patients)
    .set({
      ...apcmFields,
      updatedAt: new Date().toISOString(),
    })
    .where(eq(patients.id, patientId));

  await auditLog({
    action: 'UPDATE_APCM',
    entityType: 'patient',
    entityId: patientId,
    details: apcmFields,
  });

  return { success: true };
});
```

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - APCM badge renders correct status
  - Enrollment fields appear when enrolled selected
  - APCM status saves correctly
  - APCM filter works in patient list
  - Authorization number stored correctly

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
