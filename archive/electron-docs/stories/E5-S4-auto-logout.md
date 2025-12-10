# Story E5-S4: Add Auto-Logout on Inactivity

## Status
Draft

## Story
**As a** clinical admin,
**I want** the application to automatically log out inactive users,
**so that** unattended workstations don't expose patient data.

## Acceptance Criteria
1. Auto-logout triggers after 15 minutes of inactivity (default)
2. Timeout duration configurable in Settings (5-60 minutes)
3. Warning dialog appears 2 minutes before logout
4. User activity resets the timer
5. Logout redirects to login screen
6. Auto-logout event logged to audit trail

## Tasks / Subtasks
- [ ] Implement activity tracking (AC: 1, 4)
  - [ ] Track mouse movement, clicks, keyboard
  - [ ] Debounce activity events
  - [ ] Reset timer on any activity
- [ ] Create countdown timer (AC: 1)
  - [ ] Track elapsed idle time
  - [ ] Trigger logout at threshold
  - [ ] Run in main process
- [ ] Add warning dialog (AC: 3)
  - [ ] Show 2 minutes before logout
  - [ ] Display countdown timer
  - [ ] "Stay Logged In" button
- [ ] Make timeout configurable (AC: 2)
  - [ ] Settings UI with slider/dropdown
  - [ ] Store in user preferences
  - [ ] Range: 5-60 minutes
- [ ] Implement logout flow (AC: 5, 6)
  - [ ] Clear session
  - [ ] Navigate to login screen
  - [ ] Log auto-logout event

## Dev Notes

### Activity Tracker
```typescript
// src/renderer/hooks/useActivityTracker.ts
const ACTIVITY_EVENTS = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'];
const DEBOUNCE_MS = 1000;

export function useActivityTracker(onActivity: () => void) {
  useEffect(() => {
    let debounceTimer: NodeJS.Timeout;

    const handleActivity = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        onActivity();
        window.api.session.recordActivity();
      }, DEBOUNCE_MS);
    };

    ACTIVITY_EVENTS.forEach((event) => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    return () => {
      ACTIVITY_EVENTS.forEach((event) => {
        document.removeEventListener(event, handleActivity);
      });
      clearTimeout(debounceTimer);
    };
  }, [onActivity]);
}
```

### Inactivity Service (Main Process)
```typescript
// src/main/services/auth/inactivityService.ts
const DEFAULT_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes
const WARNING_BEFORE_MS = 2 * 60 * 1000;   // 2 minutes

interface InactivityConfig {
  timeoutMs: number;
  lastActivity: number;
  warningShown: boolean;
  timer: NodeJS.Timeout | null;
}

const config: InactivityConfig = {
  timeoutMs: DEFAULT_TIMEOUT_MS,
  lastActivity: Date.now(),
  warningShown: false,
  timer: null,
};

export function recordActivity(): void {
  config.lastActivity = Date.now();
  config.warningShown = false;
}

export function setTimeoutDuration(minutes: number): void {
  config.timeoutMs = Math.min(Math.max(minutes, 5), 60) * 60 * 1000;
}

export function startInactivityMonitor(
  onWarning: (remainingMs: number) => void,
  onTimeout: () => void
): void {
  if (config.timer) {
    clearInterval(config.timer);
  }

  config.timer = setInterval(() => {
    const idleTime = Date.now() - config.lastActivity;
    const remainingTime = config.timeoutMs - idleTime;

    // Trigger logout
    if (remainingTime <= 0) {
      onTimeout();
      return;
    }

    // Show warning
    if (remainingTime <= WARNING_BEFORE_MS && !config.warningShown) {
      config.warningShown = true;
      onWarning(remainingTime);
    }
  }, 10_000); // Check every 10 seconds
}

export function stopInactivityMonitor(): void {
  if (config.timer) {
    clearInterval(config.timer);
    config.timer = null;
  }
}
```

### Warning Dialog
```typescript
// src/renderer/components/InactivityWarning.tsx
function InactivityWarning({ remainingMs, onStayLoggedIn }: InactivityWarningProps) {
  const [countdown, setCountdown] = useState(Math.ceil(remainingMs / 1000));

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const minutes = Math.floor(countdown / 60);
  const seconds = countdown % 60;

  return (
    <Modal open onClose={onStayLoggedIn}>
      <div className="p-6 text-center max-w-sm">
        <ClockIcon className="w-12 h-12 mx-auto text-yellow-500 mb-4" />

        <h2 className="text-xl font-semibold mb-2">Session Expiring</h2>

        <p className="text-gray-600 mb-4">
          You will be logged out in
        </p>

        <div className="text-4xl font-mono font-bold text-red-600 mb-6">
          {minutes}:{seconds.toString().padStart(2, '0')}
        </div>

        <button
          onClick={onStayLoggedIn}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          Stay Logged In
        </button>
      </div>
    </Modal>
  );
}
```

### Settings UI
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Session Settings                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Auto-Logout Timeout                                                        │
│                                                                             │
│  Log out after inactivity:                                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ○ 5 minutes   ○ 10 minutes   ● 15 minutes   ○ 30 minutes          │   │
│  │  ○ 45 minutes  ○ 60 minutes                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ℹ️ A warning will appear 2 minutes before automatic logout.               │
│                                                                             │
│                                                    [Save Changes]           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### IPC Handlers
```typescript
ipcMain.handle('session:recordActivity', async (event) => {
  const session = await validateSession(event);
  if (session) {
    recordActivity();
  }
});

ipcMain.handle('session:setTimeoutDuration', async (event, { minutes }) => {
  const session = await validateSession(event);
  if (session?.role === 'admin') {
    setTimeoutDuration(minutes);
    return { success: true };
  }
  return { success: false, error: 'Admin required' };
});

// Called when timeout triggers
function handleAutoLogout(session: Session) {
  destroySession(session.token);

  auditLog({
    action: 'AUTO_LOGOUT',
    userId: session.userId,
    details: { reason: 'inactivity' },
  });

  // Notify renderer to show login screen
  BrowserWindow.getAllWindows().forEach((win) => {
    win.webContents.send('session:expired');
  });
}
```

## Testing
- **Location**: `src/main/services/auth/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - Activity resets timer
  - Warning shows at correct time
  - Logout triggers at timeout
  - Setting timeout works
  - Timeout persists across restarts
  - Audit log created on auto-logout

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
