# Story E3-S4: Implement Patient Create/Edit Forms

## Status
Draft

## Story
**As a** clinical user,
**I want** to create and edit patient records with validation,
**so that** I can maintain accurate patient demographics.

## Acceptance Criteria
1. Create new patient form with all required fields
2. Edit existing patient form pre-populates current data
3. Form validates required fields before save
4. MRN uniqueness is enforced
5. DOB validation ensures valid date format
6. Success message confirms save operation

## Tasks / Subtasks
- [ ] Create patient form component (AC: 1, 2)
  - [ ] Create src/renderer/components/PatientForm.tsx
  - [ ] Build reusable form for create/edit modes
  - [ ] Pre-populate fields in edit mode
- [ ] Implement form validation (AC: 3, 4, 5)
  - [ ] Required field validation (firstName, lastName, mrn, dateOfBirth)
  - [ ] MRN format validation (alphanumeric)
  - [ ] DOB date format validation
  - [ ] Phone number format validation (optional)
- [ ] Add MRN uniqueness check (AC: 4)
  - [ ] Check on blur before submit
  - [ ] Exclude current patient in edit mode
  - [ ] Show inline error if duplicate
- [ ] Implement save functionality (AC: 6)
  - [ ] patient:create IPC handler
  - [ ] patient:update IPC handler
  - [ ] Show success toast on save
  - [ ] Close modal and refresh list
- [ ] Add cancel/discard handling
  - [ ] Confirm if unsaved changes
  - [ ] Discard button resets form

## Dev Notes

### Patient Form Layout
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Add New Patient                                              [X]           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  First Name *              Last Name *                                      │
│  ┌───────────────────┐     ┌───────────────────┐                           │
│  │                   │     │                   │                           │
│  └───────────────────┘     └───────────────────┘                           │
│                                                                             │
│  MRN *                     Date of Birth *                                  │
│  ┌───────────────────┐     ┌───────────────────┐                           │
│  │                   │     │ mm/dd/yyyy        │                           │
│  └───────────────────┘     └───────────────────┘                           │
│                                                                             │
│  Phone                     Email                                            │
│  ┌───────────────────┐     ┌───────────────────┐                           │
│  │ (___) ___-____    │     │                   │                           │
│  └───────────────────┘     └───────────────────┘                           │
│                                                                             │
│  Address                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                               [Cancel]  [Save Patient]                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### IPC Handlers
```typescript
// Create patient
ipcMain.handle('patient:create', async (event, patientData: PatientInput) => {
  const session = await validateSession(event);

  // Validate MRN uniqueness
  const existing = await db.select().from(patients)
    .where(eq(patients.mrn, patientData.mrn))
    .limit(1);
  if (existing.length > 0) {
    throw new Error('MRN already exists');
  }

  const [patient] = await db.insert(patients).values({
    ...patientData,
    createdBy: session.userId,
    createdAt: new Date().toISOString(),
  }).returning();

  await auditLog({ action: 'CREATE', entityType: 'patient', entityId: patient.id });
  return patient;
});

// Update patient
ipcMain.handle('patient:update', async (event, { id, ...updates }) => {
  const session = await validateSession(event);

  const [patient] = await db.update(patients)
    .set({ ...updates, updatedAt: new Date().toISOString() })
    .where(eq(patients.id, id))
    .returning();

  await auditLog({ action: 'UPDATE', entityType: 'patient', entityId: id });
  return patient;
});
```

### Form Validation Schema
```typescript
const patientSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  mrn: z.string().min(1, 'MRN is required').regex(/^[A-Za-z0-9]+$/, 'MRN must be alphanumeric'),
  dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format'),
  phone: z.string().optional(),
  email: z.string().email().optional().or(z.literal('')),
  address: z.string().optional(),
});
```

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Form renders with empty fields in create mode
  - Form pre-populates in edit mode
  - Validation errors display for empty required fields
  - MRN duplicate error displays
  - Successful save calls IPC handler
  - Cancel discards changes

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
