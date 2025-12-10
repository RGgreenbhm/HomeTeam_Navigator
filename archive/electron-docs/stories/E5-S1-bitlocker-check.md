# Story E5-S1: Implement BitLocker Status Check on Startup

## Status
Draft

## Story
**As a** clinical admin,
**I want** the application to verify BitLocker encryption is enabled,
**so that** patient data remains protected if the device is lost or stolen.

## Acceptance Criteria
1. Application checks BitLocker status on Windows C: drive at startup
2. If enabled, startup continues normally
3. If disabled, warning modal displays with explanation
4. User can acknowledge warning and continue (not blocking)
5. BitLocker status logged to audit log
6. Status indicator shown in Settings screen

## Tasks / Subtasks
- [ ] Implement BitLocker check (AC: 1)
  - [ ] Use PowerShell/WMI to query encryption status
  - [ ] Check specifically C: drive
  - [ ] Handle query failures gracefully
- [ ] Create warning modal (AC: 2, 3, 4)
  - [ ] Create src/renderer/components/BitLockerWarning.tsx
  - [ ] Explain HIPAA encryption requirement
  - [ ] "I Understand" button to continue
  - [ ] "Learn More" link to help docs
- [ ] Log BitLocker status (AC: 5)
  - [ ] Log at app startup
  - [ ] Include encryption status and volume
  - [ ] Flag as SECURITY event type
- [ ] Add status indicator (AC: 6)
  - [ ] Show in Settings > Security section
  - [ ] Green checkmark if enabled
  - [ ] Red warning if disabled

## Dev Notes

### BitLocker Check Implementation
```typescript
// src/main/services/security/bitlocker.ts
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface BitLockerStatus {
  enabled: boolean;
  protectionStatus: 'On' | 'Off' | 'Unknown';
  encryptionPercentage: number;
  volumeStatus: string;
}

export async function checkBitLockerStatus(): Promise<BitLockerStatus> {
  if (process.platform !== 'win32') {
    return { enabled: false, protectionStatus: 'Unknown', encryptionPercentage: 0, volumeStatus: 'Non-Windows' };
  }

  try {
    // PowerShell command to get BitLocker status
    const { stdout } = await execAsync(
      'powershell -Command "Get-BitLockerVolume -MountPoint C: | Select-Object ProtectionStatus, VolumeStatus, EncryptionPercentage | ConvertTo-Json"'
    );

    const result = JSON.parse(stdout);

    return {
      enabled: result.ProtectionStatus === 1, // 1 = On, 0 = Off
      protectionStatus: result.ProtectionStatus === 1 ? 'On' : 'Off',
      encryptionPercentage: result.EncryptionPercentage || 0,
      volumeStatus: result.VolumeStatus || 'Unknown',
    };
  } catch (error) {
    // Fallback to WMI if PowerShell fails
    try {
      const { stdout } = await execAsync(
        'wmic /namespace:\\\\root\\cimv2\\Security\\MicrosoftVolumeEncryption path Win32_EncryptableVolume where DriveLetter="C:" get ProtectionStatus /value'
      );

      const match = stdout.match(/ProtectionStatus=(\d)/);
      const status = match ? parseInt(match[1]) : 0;

      return {
        enabled: status === 1,
        protectionStatus: status === 1 ? 'On' : 'Off',
        encryptionPercentage: status === 1 ? 100 : 0,
        volumeStatus: 'WMI Query',
      };
    } catch {
      return {
        enabled: false,
        protectionStatus: 'Unknown',
        encryptionPercentage: 0,
        volumeStatus: 'Query Failed',
      };
    }
  }
}
```

### IPC Handler
```typescript
ipcMain.handle('security:getBitLockerStatus', async (event) => {
  const status = await checkBitLockerStatus();

  await auditLog({
    action: 'SECURITY_CHECK',
    entityType: 'system',
    details: {
      check: 'BitLocker',
      ...status,
    },
  });

  return status;
});
```

### Warning Modal
```typescript
function BitLockerWarning({ onAcknowledge }: { onAcknowledge: () => void }) {
  return (
    <Modal open onClose={() => {}}>
      <div className="p-6 max-w-md">
        <div className="flex items-center gap-3 text-yellow-600 mb-4">
          <ShieldAlertIcon className="w-8 h-8" />
          <h2 className="text-xl font-semibold">Encryption Warning</h2>
        </div>

        <div className="space-y-3 text-gray-600 mb-6">
          <p>
            <strong>BitLocker encryption is not enabled</strong> on this device.
          </p>
          <p>
            HIPAA requires encryption for devices storing Protected Health Information (PHI).
            If this device is lost or stolen, patient data could be accessed.
          </p>
          <p>
            Contact your IT administrator to enable BitLocker drive encryption.
          </p>
        </div>

        <div className="flex justify-between">
          <a
            href="https://support.microsoft.com/windows/bitlocker"
            target="_blank"
            className="text-blue-600 hover:underline"
          >
            Learn More
          </a>
          <button
            onClick={onAcknowledge}
            className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
          >
            I Understand, Continue
          </button>
        </div>
      </div>
    </Modal>
  );
}
```

### Startup Integration
```typescript
// src/renderer/App.tsx
function App() {
  const [showBitLockerWarning, setShowBitLockerWarning] = useState(false);
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    async function checkSecurity() {
      const status = await window.api.security.getBitLockerStatus();

      if (!status.enabled) {
        setShowBitLockerWarning(true);
      } else {
        setAppReady(true);
      }
    }

    checkSecurity();
  }, []);

  if (showBitLockerWarning) {
    return (
      <BitLockerWarning
        onAcknowledge={() => {
          setShowBitLockerWarning(false);
          setAppReady(true);
        }}
      />
    );
  }

  if (!appReady) {
    return <SplashScreen />;
  }

  return <MainApp />;
}
```

### Settings Display
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Security Status                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BitLocker Encryption                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✓ Enabled                                              C: Drive    │   │
│  │  Protection Status: On                                              │   │
│  │  Encryption: 100% complete                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Database Encryption                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ✓ SQLCipher AES-256 Enabled                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Testing
- **Location**: `src/main/services/security/__tests__/`
- **Framework**: Vitest
- **Required Tests**:
  - BitLocker check returns status object
  - Warning modal displays when disabled
  - Acknowledge button allows continuing
  - Status logged to audit log
  - Settings displays correct status

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
