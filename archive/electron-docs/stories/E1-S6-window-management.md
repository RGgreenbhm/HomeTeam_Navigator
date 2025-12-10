# Story E1-S6: Implement Basic Window Management

## Status
Draft

## Story
**As a** clinical user,
**I want** the application to remember my window position and size,
**so that** it opens where I left it each time.

## Acceptance Criteria
1. Window minimize, maximize, and close buttons work correctly
2. Window position is saved when closed
3. Window size is saved when resized
4. Application opens at last saved position/size on restart
5. Default size is 1280x800 if no saved state exists
6. Window has minimum size constraints (800x600)

## Tasks / Subtasks
- [ ] Configure BrowserWindow defaults (AC: 5, 6)
  - [ ] Set default width: 1280, height: 800
  - [ ] Set minWidth: 800, minHeight: 600
  - [ ] Configure frame: true (native window chrome)
- [ ] Implement window state persistence (AC: 2, 3, 4)
  - [ ] Create src/main/window-state.ts
  - [ ] Use electron-store for state persistence
  - [ ] Save position (x, y) on move
  - [ ] Save size (width, height) on resize
- [ ] Handle window events (AC: 1)
  - [ ] Listen to 'close' event for state save
  - [ ] Listen to 'resize' event for size tracking
  - [ ] Listen to 'move' event for position tracking
  - [ ] Debounce saves to avoid excessive writes
- [ ] Restore state on launch (AC: 4)
  - [ ] Load saved state from store
  - [ ] Validate state is within screen bounds
  - [ ] Fall back to defaults if invalid

## Dev Notes

### Window State Store
```typescript
// src/main/window-state.ts
import Store from 'electron-store';

interface WindowState {
  x?: number;
  y?: number;
  width: number;
  height: number;
  isMaximized: boolean;
}

const store = new Store<{ windowState: WindowState }>({
  defaults: {
    windowState: {
      width: 1280,
      height: 800,
      isMaximized: false,
    },
  },
});

export function saveWindowState(win: BrowserWindow): void {
  if (!win.isMaximized()) {
    const bounds = win.getBounds();
    store.set('windowState', {
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
      isMaximized: false,
    });
  } else {
    store.set('windowState.isMaximized', true);
  }
}

export function getWindowState(): WindowState {
  return store.get('windowState');
}
```

### BrowserWindow Configuration
```typescript
const state = getWindowState();

const mainWindow = new BrowserWindow({
  x: state.x,
  y: state.y,
  width: state.width,
  height: state.height,
  minWidth: 800,
  minHeight: 600,
  show: false,  // Show after ready-to-show
  webPreferences: {
    nodeIntegration: false,
    contextIsolation: true,
    sandbox: true,
    preload: path.join(__dirname, 'preload.js'),
  },
});

if (state.isMaximized) {
  mainWindow.maximize();
}
```

### Dependencies
- electron-store: ^8.x (simple persistent storage)

### Event Debouncing
Save operations should be debounced (e.g., 300ms) to avoid excessive disk writes during window drag/resize operations.

## Testing
- **Location**: `src/main/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Default state is returned when no saved state
  - State is saved correctly on window close
  - Invalid position (off-screen) falls back to default
- **Manual Testing**: Resize, move, restart - verify position restored

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
