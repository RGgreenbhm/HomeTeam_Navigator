# Story E4-S3: Display Consent Status in Patient List

## Status
Draft

## Story
**As a** clinical user,
**I want** to see consent status badges in the patient list,
**so that** I can quickly identify patients needing consent follow-up.

## Acceptance Criteria
1. Consent status column displays in patient list table
2. Color-coded badges: Yellow (Pending), Green (Obtained), Red (Declined)
3. Badge includes icon and text label
4. Column is sortable by consent status
5. Hover shows consent date and method if available

## Tasks / Subtasks
- [ ] Create consent badge component (AC: 1, 2, 3)
  - [ ] Create src/renderer/components/ConsentBadge.tsx
  - [ ] Yellow badge with clock icon for Pending
  - [ ] Green badge with checkmark for Obtained
  - [ ] Red badge with X for Declined
- [ ] Add column to patient list (AC: 1, 4)
  - [ ] Add "Consent" column header
  - [ ] Render ConsentBadge in column
  - [ ] Enable sorting by consentStatus
- [ ] Add hover tooltip (AC: 5)
  - [ ] Show consent date formatted
  - [ ] Show consent method
  - [ ] Show "Pending" for no date

## Dev Notes

### Badge Design
```
Pending:   ⏳ Pending    (yellow background, yellow-800 text)
Obtained:  ✓ Obtained   (green background, green-800 text)
Declined:  ✕ Declined   (red background, red-800 text)
```

### ConsentBadge Component
```typescript
const badgeConfig = {
  pending: {
    icon: '⏳',
    label: 'Pending',
    className: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  },
  obtained: {
    icon: '✓',
    label: 'Obtained',
    className: 'bg-green-100 text-green-800 border-green-300',
  },
  declined: {
    icon: '✕',
    label: 'Declined',
    className: 'bg-red-100 text-red-800 border-red-300',
  },
};

function ConsentBadge({ status, date, method }: ConsentBadgeProps) {
  const config = badgeConfig[status];

  const tooltipContent = status === 'obtained' && date
    ? `${formatDate(date)} via ${method || 'unknown'}`
    : status === 'pending'
    ? 'Not yet obtained'
    : 'Patient declined';

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

### Patient List Column Definition
```typescript
const columns = [
  // ... other columns ...
  {
    accessorKey: 'consentStatus',
    header: 'Consent',
    cell: ({ row }) => (
      <ConsentBadge
        status={row.original.consentStatus}
        date={row.original.consentDate}
        method={row.original.consentMethod}
      />
    ),
    sortingFn: (rowA, rowB) => {
      const order = { pending: 0, declined: 1, obtained: 2 };
      return order[rowA.original.consentStatus] - order[rowB.original.consentStatus];
    },
  },
];
```

### Visual Reference
```
┌─────────┬─────────────┬────────────┬──────────────────┬─────────────────┐
│  MRN    │ Name        │ DOB        │ Consent          │ APCM            │
├─────────┼─────────────┼────────────┼──────────────────┼─────────────────┤
│  12345  │ Doe, John   │ 05/15/1960 │ ✓ Obtained       │ ✓ Enrolled      │
│  12346  │ Smith, Jane │ 03/22/1958 │ ⏳ Pending       │ ○ Eligible      │
│  12347  │ Brown, Bob  │ 07/18/1965 │ ✕ Declined       │ — Not Eligible  │
└─────────┴─────────────┴────────────┴──────────────────┴─────────────────┘
```

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Badge renders correct color for each status
  - Icon matches status
  - Tooltip shows date and method for obtained
  - Sorting by consent status works
  - Click badge opens consent form (if applicable)

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
