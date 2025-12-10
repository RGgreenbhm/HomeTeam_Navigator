# Story E3-S6: Import Patients from Excel File

## Status
Draft

## Story
**As a** clinical admin,
**I want** to import patients from an Excel file,
**so that** I can quickly populate the database with existing patient lists.

## Acceptance Criteria
1. User can upload .xlsx or .csv file
2. Column mapping UI allows matching file columns to patient fields
3. Preview shows first 10 rows before import
4. Duplicate MRNs are detected and reported
5. Import summary shows success/error counts
6. Failed rows can be exported for correction

## Tasks / Subtasks
- [ ] Create import upload screen (AC: 1)
  - [ ] Create src/renderer/screens/PatientImportScreen.tsx
  - [ ] File picker for .xlsx and .csv
  - [ ] Drag-and-drop support
- [ ] Parse Excel/CSV files (AC: 2)
  - [ ] Use xlsx library for Excel parsing
  - [ ] Use papaparse for CSV parsing
  - [ ] Extract headers and rows
- [ ] Build column mapping UI (AC: 2)
  - [ ] Dropdown for each patient field
  - [ ] Auto-detect common column names
  - [ ] Required fields marked
- [ ] Show import preview (AC: 3)
  - [ ] Display first 10 rows with mapped data
  - [ ] Highlight validation errors inline
  - [ ] Show total row count
- [ ] Detect duplicates (AC: 4)
  - [ ] Check MRN against existing patients
  - [ ] Check for duplicates within file
  - [ ] Options: Skip, Update, Create Duplicate Warning
- [ ] Implement bulk import (AC: 5, 6)
  - [ ] patient:bulkImport IPC handler
  - [ ] Transaction for atomicity
  - [ ] Return success/error counts
  - [ ] Export failed rows to CSV

## Dev Notes

### Import Workflow
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Import Patients                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: Upload File                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │            📁 Drop Excel or CSV file here                           │   │
│  │                    or click to browse                               │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Step 2: Map Columns                                                        │
│  ┌──────────────────┬───────────────────────────────────────────────────┐  │
│  │ Patient Field    │ File Column                                       │  │
│  ├──────────────────┼───────────────────────────────────────────────────┤  │
│  │ First Name *     │ [First Name        ▼]                             │  │
│  │ Last Name *      │ [Last Name         ▼]                             │  │
│  │ MRN *            │ [Patient ID        ▼]                             │  │
│  │ Date of Birth *  │ [DOB               ▼]                             │  │
│  │ Phone            │ [Phone Number      ▼]                             │  │
│  │ Email            │ [-- Skip --        ▼]                             │  │
│  └──────────────────┴───────────────────────────────────────────────────┘  │
│                                                                             │
│  Step 3: Preview                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Row │ First Name │ Last Name │ MRN    │ DOB        │ Status        │   │
│  ├─────┼────────────┼───────────┼────────┼────────────┼───────────────┤   │
│  │ 1   │ John       │ Doe       │ 12345  │ 1960-05-15 │ ✓ Valid       │   │
│  │ 2   │ Jane       │ Smith     │ 12346  │ 1958-03-22 │ ✓ Valid       │   │
│  │ 3   │            │ Jones     │ 12347  │ 1955-01-10 │ ⚠ Missing FN  │   │
│  │ 4   │ Bob        │ Wilson    │ 12345  │ 1970-08-05 │ ⚠ Duplicate   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  Showing 4 of 1,384 rows                                                    │
│                                                                             │
│  Duplicate Handling: ◉ Skip duplicates  ○ Update existing  ○ Import all    │
│                                                                             │
│                            [Cancel]  [Import 1,382 Patients]                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Import IPC Handler
```typescript
ipcMain.handle('patient:bulkImport', async (event, { patients, duplicateMode }) => {
  const session = await validateSession(event);

  // Get existing MRNs
  const existingMrns = new Set(
    (await db.select({ mrn: patients.mrn }).from(patients)).map(p => p.mrn)
  );

  const results = { imported: 0, skipped: 0, updated: 0, errors: [] as string[] };

  await db.transaction(async (tx) => {
    for (const row of patients) {
      try {
        const isDuplicate = existingMrns.has(row.mrn);

        if (isDuplicate) {
          if (duplicateMode === 'skip') {
            results.skipped++;
            continue;
          } else if (duplicateMode === 'update') {
            await tx.update(patients)
              .set({ ...row, updatedAt: new Date().toISOString() })
              .where(eq(patients.mrn, row.mrn));
            results.updated++;
            continue;
          }
        }

        await tx.insert(patients).values({
          ...row,
          createdBy: session.userId,
          createdAt: new Date().toISOString(),
        });
        results.imported++;
      } catch (error) {
        results.errors.push(`Row ${row.mrn}: ${error.message}`);
      }
    }
  });

  await auditLog({
    action: 'BULK_IMPORT',
    entityType: 'patient',
    details: results,
  });

  return results;
});
```

### Column Auto-Detection
```typescript
const fieldMappings: Record<string, string[]> = {
  firstName: ['first name', 'firstname', 'first', 'given name', 'fname'],
  lastName: ['last name', 'lastname', 'last', 'family name', 'surname', 'lname'],
  mrn: ['mrn', 'patient id', 'patientid', 'id', 'medical record', 'chart number'],
  dateOfBirth: ['dob', 'date of birth', 'birthdate', 'birth date', 'birthday'],
  phone: ['phone', 'telephone', 'phone number', 'mobile', 'cell'],
  email: ['email', 'e-mail', 'email address'],
};

function autoDetectColumn(header: string): string | null {
  const normalized = header.toLowerCase().trim();
  for (const [field, aliases] of Object.entries(fieldMappings)) {
    if (aliases.includes(normalized)) return field;
  }
  return null;
}
```

### Dependencies
- **xlsx**: ^0.18.x for Excel parsing
- **papaparse**: ^5.4.x for CSV parsing

## Testing
- **Location**: `src/renderer/screens/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - File upload accepts xlsx and csv
  - Column mapping detects common headers
  - Preview shows correct row count
  - Duplicate detection flags conflicts
  - Bulk import creates correct records
  - Failed rows are exported correctly

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
