# Story E2-S2: Add File Upload for Screenshots

## Status
Draft

## Story
**As a** clinical user,
**I want** to upload screenshot files via drag-drop or file picker,
**so that** I can capture saved images from my computer.

## Acceptance Criteria
1. Drag-and-drop images onto drop zone uploads them
2. Click on drop zone opens native file picker
3. Supported formats: PNG, JPG, JPEG, BMP
4. File size limit: 10MB with clear error message if exceeded
5. Multiple files can be queued (stored, processed one at a time)
6. Drop zone shows visual feedback during drag-over

## Tasks / Subtasks
- [ ] Implement drag-drop handler (AC: 1, 6)
  - [ ] Add onDragOver, onDragLeave, onDrop handlers
  - [ ] Show visual feedback (border color, background)
  - [ ] Validate dropped files are images
- [ ] Implement file picker (AC: 2)
  - [ ] Add click handler to open dialog.showOpenDialog
  - [ ] Filter to image file types
  - [ ] Handle single and multi-select
- [ ] Validate file type (AC: 3)
  - [ ] Check MIME type: image/png, image/jpeg, image/bmp
  - [ ] Check file extension as backup
  - [ ] Show error toast for invalid types
- [ ] Validate file size (AC: 4)
  - [ ] Limit: 10MB (10 * 1024 * 1024 bytes)
  - [ ] Show error: "File too large. Maximum size is 10MB"
- [ ] Handle multiple files (AC: 5)
  - [ ] Add files to upload queue
  - [ ] Show queue count indicator
  - [ ] Process first file, hold others in queue
- [ ] Create IPC channel for file read (AC: 1, 2)
  - [ ] Add capture:upload IPC handler
  - [ ] Read file from disk
  - [ ] Return base64 data and metadata

## Dev Notes

### Drag-Drop Visual States (from Frontend Spec §4.2)
```css
/* Default state */
.drop-zone {
  border: 2px dashed theme('colors.neutral.200');
  background: theme('colors.neutral.100');
}

/* Drag-over state */
.drop-zone.dragging {
  border-color: theme('colors.primary.500');
  background: theme('colors.primary.50');
}
```

### IPC Handler for File Upload
```typescript
// Main process
ipcMain.handle('capture:upload', async (_, filePath: string) => {
  const stats = await fs.stat(filePath);

  if (stats.size > 10 * 1024 * 1024) {
    return { success: false, error: 'File too large' };
  }

  const buffer = await fs.readFile(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const mimeType = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.bmp': 'image/bmp',
  }[ext];

  if (!mimeType) {
    return { success: false, error: 'Unsupported format' };
  }

  const base64 = buffer.toString('base64');
  const dataUrl = `data:${mimeType};base64,${base64}`;

  return {
    success: true,
    data: {
      dataUrl,
      fileName: path.basename(filePath),
      size: stats.size,
    },
  };
});
```

### File Picker Dialog
```typescript
// Main process
ipcMain.handle('capture:openFilePicker', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'bmp'] },
    ],
  });

  return result.canceled ? [] : result.filePaths;
});
```

### Queue State
```typescript
interface UploadQueue {
  files: Array<{
    path: string;
    name: string;
    size: number;
    status: 'pending' | 'processing' | 'done' | 'error';
  }>;
  currentIndex: number;
}
```

## Testing
- **Location**: `src/renderer/screens/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Drop zone visual feedback on drag
  - File picker opens on click
  - Large file shows error
  - Invalid format shows error
- **Manual Testing**: Drag multiple files, verify queue

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
