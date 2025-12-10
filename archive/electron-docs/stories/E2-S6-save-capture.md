# Story E2-S6: Store Captures with Original Image and Extracted Text

## Status
Draft

## Story
**As a** clinical user,
**I want** to save my capture with both the image and extracted text,
**so that** I can review the original screenshot later.

## Acceptance Criteria
1. Both original image and OCR text are saved to database
2. Capture is linked to selected patient
3. Capture includes metadata: source EMR, capture type, notes
4. Save shows success toast with patient name
5. "Save & New" clears form for next capture
6. Database stores image efficiently (compressed, optimized)

## Tasks / Subtasks
- [ ] Create captures table schema (AC: 1, 6)
  - [ ] Create src/main/db/schema/capture.ts
  - [ ] Store image as file path (not inline blob)
  - [ ] Store OCR text as text column
  - [ ] Add indexes for patientId
- [ ] Implement image storage (AC: 1, 6)
  - [ ] Create src/main/services/image-storage.ts
  - [ ] Save images to app data folder
  - [ ] Use consistent naming: {captureId}.png
  - [ ] Compress PNG images (pngquant or sharp)
- [ ] Create save IPC handler (AC: 1, 2, 3)
  - [ ] Add capture:create handler
  - [ ] Accept image, text, patient, metadata
  - [ ] Store image file, then database record
  - [ ] Return created capture ID
- [ ] Build save form UI (AC: 2, 3)
  - [ ] Patient selector (combobox)
  - [ ] Source EMR dropdown (Allscripts, Athena, OneNote)
  - [ ] Capture type dropdown (Worksheet, Labs, Notes)
  - [ ] Notes textarea
- [ ] Implement save flow (AC: 4, 5)
  - [ ] Validate patient is selected
  - [ ] Call capture:create IPC
  - [ ] Show success toast: "Saved to Doe, John"
  - [ ] "Save & New": Clear form, focus paste zone
  - [ ] "Save": Navigate to patient timeline

## Dev Notes

### Capture Schema (from Architecture §4.2)
```typescript
export const captures = sqliteTable('captures', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  patientId: text('patient_id').notNull().references(() => patients.id),
  captureType: text('capture_type', {
    enum: ['screenshot', 'text', 'file', 'ocr_result']
  }).notNull(),
  sourceEmr: text('source_emr', {
    enum: ['allscripts', 'athena', 'onenote', 'spruce', 'other']
  }),
  imagePath: text('image_path'),       // File path, not blob
  ocrText: text('ocr_text'),
  ocrConfidence: real('ocr_confidence'),
  notes: text('notes'),
  tags: text('tags'),                   // JSON array
  version: integer('version').notNull().default(1),
  createdAt: text('created_at').notNull().$defaultFn(() => new Date().toISOString()),
  createdBy: text('created_by').notNull(),
});
```

### Image Storage Service
```typescript
// src/main/services/image-storage.ts
import { app } from 'electron';
import path from 'path';
import sharp from 'sharp';

const CAPTURES_DIR = path.join(app.getPath('userData'), 'captures');

export async function saveImage(captureId: string, imageData: string): Promise<string> {
  const buffer = Buffer.from(imageData.replace(/^data:image\/\w+;base64,/, ''), 'base64');

  // Compress and save as PNG
  const filePath = path.join(CAPTURES_DIR, `${captureId}.png`);
  await sharp(buffer)
    .png({ quality: 80, compressionLevel: 9 })
    .toFile(filePath);

  return filePath;
}
```

### IPC Handler
```typescript
ipcMain.handle('capture:create', async (event, data: NewCaptureInput) => {
  const session = await validateSession(event);
  const captureId = createId();

  // Save image file first
  const imagePath = await saveImage(captureId, data.imageData);

  // Create database record
  const capture = await db.insert(captures).values({
    id: captureId,
    patientId: data.patientId,
    captureType: data.captureType,
    sourceEmr: data.sourceEmr,
    imagePath,
    ocrText: data.ocrText,
    ocrConfidence: data.ocrConfidence,
    notes: data.notes,
    createdBy: session.userId,
  }).returning();

  // Audit log
  await auditLog({ action: 'CREATE', entityType: 'capture', entityId: captureId, userId: session.userId });

  return capture[0];
});
```

### Save Form Validation
```typescript
const schema = z.object({
  patientId: z.string().min(1, 'Please select a patient'),
  captureType: z.enum(['screenshot', 'text', 'file']),
  sourceEmr: z.enum(['allscripts', 'athena', 'onenote', 'spruce', 'other']).optional(),
  notes: z.string().optional(),
});
```

### Dependencies
- sharp: ^0.33.x (image processing)
- zod: ^3.x (validation)

## Testing
- **Location**: `src/main/services/__tests__/` and `src/renderer/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Image saved to correct path
  - Database record created with all fields
  - Validation rejects missing patient
  - Success toast shows correct name
  - Form clears on "Save & New"

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
