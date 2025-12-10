# Story E2-S1: Implement Clipboard Paste Handler for Images

## Status
Draft

## Story
**As a** clinical user,
**I want** to paste screenshots from my clipboard using Ctrl+V,
**so that** I can quickly capture patient data from EMR screens.

## Acceptance Criteria
1. Ctrl+V captures image from system clipboard
2. Pasted image displays in preview area immediately
3. Supported formats: PNG, JPG, BMP
4. Invalid clipboard content shows user-friendly error message
5. Preview shows image dimensions and file size
6. User can paste another image to replace current one

## Tasks / Subtasks
- [ ] Create Capture screen component (AC: 2)
  - [ ] Create src/renderer/screens/CaptureScreen.tsx
  - [ ] Implement empty state with drop zone
  - [ ] Add image preview container
- [ ] Implement clipboard listener (AC: 1, 3)
  - [ ] Add global Ctrl+V keyboard handler
  - [ ] Read image from clipboard using Electron API
  - [ ] Validate image format (PNG, JPG, BMP)
- [ ] Create IPC channel for clipboard (AC: 1)
  - [ ] Add capture:paste IPC handler in main process
  - [ ] Use clipboard.readImage() from Electron
  - [ ] Return image as base64 data URL
- [ ] Display image preview (AC: 2, 5)
  - [ ] Show image in scrollable container
  - [ ] Display dimensions (e.g., "1920 x 1080")
  - [ ] Display file size (e.g., "245 KB")
- [ ] Handle errors (AC: 4)
  - [ ] Show toast: "No image in clipboard"
  - [ ] Show toast: "Unsupported image format"
- [ ] Enable replacement (AC: 6)
  - [ ] New paste replaces existing image
  - [ ] Show confirmation if current image has unsaved edits

## Dev Notes

### Capture Screen Layout (from Frontend Spec §4.2, §4.3)
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│              ┌─────────────────────────────────────┐            │
│              │               📷                    │            │
│              │     PASTE SCREENSHOT HERE           │            │
│              │      (Ctrl+V or drag file)          │            │
│              └─────────────────────────────────────┘            │
│                                                                  │
│  After paste:                                                    │
│  ┌─────────────────────────┐  ┌───────────────────────────────┐ │
│  │   [Screenshot Preview]  │  │  Patient: [Search...]      ▼  │ │
│  │                         │  │  Source:  [Allscripts]     ▼  │ │
│  │   1920 x 1080 • 245 KB  │  │  Type:    [Worksheet]      ▼  │ │
│  │                         │  │                                │ │
│  │  [Zoom] [OCR] [Rotate]  │  │  [Cancel]  [Save & New] [Save]│ │
│  └─────────────────────────┘  └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### IPC Channel (from Architecture §5.2.2)
```typescript
// Main process handler
ipcMain.handle('capture:paste', async () => {
  const image = clipboard.readImage();

  if (image.isEmpty()) {
    return { success: false, error: 'No image in clipboard' };
  }

  const buffer = image.toPNG();
  const base64 = buffer.toString('base64');
  const dataUrl = `data:image/png;base64,${base64}`;

  return {
    success: true,
    data: {
      dataUrl,
      width: image.getSize().width,
      height: image.getSize().height,
      size: buffer.length,
    },
  };
});

// Preload API
capture: {
  paste: () => ipcRenderer.invoke('capture:paste'),
}
```

### Keyboard Shortcut Registration
```typescript
// In CaptureScreen component
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'v') {
      e.preventDefault();
      handlePaste();
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);
```

### State Management
```typescript
interface CaptureState {
  imageData: string | null;
  imageWidth: number;
  imageHeight: number;
  imageSize: number;
  isLoading: boolean;
  error: string | null;
}
```

## Testing
- **Location**: `src/renderer/screens/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Empty state renders drop zone
  - Paste handler calls IPC
  - Image preview displays after paste
  - Error toast on empty clipboard
- **Manual Testing**: Paste screenshots from different apps

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
