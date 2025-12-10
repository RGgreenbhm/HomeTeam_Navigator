# Workspace Synchronization Protocol

Synchronize the current workspace across GitHub and Azure Storage with HIPAA-compliant audit logging.

## Overview

This command performs a comprehensive workspace sync:
1. **Code** → GitHub repository (public/shared files)
2. **PHI/Data** → Azure Blob Storage (HIPAA-compliant, encrypted)
3. **Device-specific files** → Azure Blob Storage (user-specific folder)
4. **Audit logs** → Local SyncLogs folder (for HIPAA compliance)

---

## Phase 1: Pre-Sync Information Gathering

### Step 1: Identify Current User

Check for workspace user environment variable:
```powershell
$env:WORKSPACE_USER
```

If not set, prompt user to identify themselves:
- **RG** = Robert Green
- **PR** = Pat Rutledge
- **PS** = Pavel Savine

Set for session:
```powershell
$env:WORKSPACE_USER = "RG"  # or PR, PS
```

### Step 2: Gather Sync Targets

Collect and display sync target information:

**GitHub:**
```bash
git remote get-url origin
git branch --show-current
```

**Azure Storage:**
- Storage Account: `stgreenclinicworkspace`
- Container: `workspace-sync`
- Tenant: `greenclinicteam.com` (Green Clinic)
- User Folder: `[INITIALS]-VScode-workspace-syncs/` (e.g., `RG-VScode-workspace-syncs/`)

### Step 3: Display Pre-Sync Summary

Present to user BEFORE proceeding:

```
╔══════════════════════════════════════════════════════════════╗
║              WORKSPACE SYNC - PRE-FLIGHT CHECK               ║
╠══════════════════════════════════════════════════════════════╣
║ ACTIVE USER: [First Last] ([INITIALS])                       ║
║ DEVICE: [Computer Name]                                      ║
║ TIMESTAMP: [YYYY-MM-DD HH:MM:SS]                             ║
╠══════════════════════════════════════════════════════════════╣
║ GITHUB TARGET:                                               ║
║   Repository: RGgreenbhm/Patient_Explorer                    ║
║   Branch: main                                               ║
║   Status: [X ahead / Y behind]                               ║
╠══════════════════════════════════════════════════════════════╣
║ AZURE STORAGE TARGET:                                        ║
║   Account: stgreenclinicworkspace                            ║
║   Tenant: greenclinicteam.com                                ║
║   Container: workspace-sync                                  ║
║   User Folder: [INITIALS]-VScode-workspace-syncs/            ║
╠══════════════════════════════════════════════════════════════╣
║ FILES TO SYNC:                                               ║
║   To GitHub: [count] files (code, docs, configs)             ║
║   To Azure: [count] files (PHI, credentials, device-specific)║
╚══════════════════════════════════════════════════════════════╝
```

### Step 4: Browser Authentication Reminder

**IMPORTANT: Display this warning:**

```
⚠️  AUTHENTICATION REMINDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before proceeding, please verify:

1. Open Microsoft Edge or Internet Explorer
2. Navigate to: https://portal.azure.com
3. Ensure you are logged in as: [expected account]
   - For RG: rgreen@greenclinicteam.com
   - For PR: prutledge@greenclinicteam.com
   - For PS: psavine@greenclinicteam.com

This ensures the authentication popup will use the correct account.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask user: **"Is your browser logged into the correct Microsoft account? (yes/no)"**

If no, wait for user to confirm before proceeding.

---

## Phase 2: Generate Audit Log (HIPAA Compliance)

**BEFORE any sync operations**, create an audit log file:

### Audit Log Location
```
..Workspace/History/SyncLogs/YYYY-MM-DD_HHMMSS_[FirstName]_[LastName]_sync.md
```

Example: `2025-12-10_143052_Robert_Green_sync.md`

### Audit Log Content

```markdown
# Workspace Sync Audit Log

## Session Information
- **Timestamp**: [YYYY-MM-DD HH:MM:SS]
- **User**: [Full Name] ([Initials])
- **Device**: [Computer Name]
- **Device ID**: [Unique identifier or hostname]
- **IP Address**: [If available]
- **Session ID**: [Generated UUID]

## Sync Targets
### GitHub
- Repository: [repo URL]
- Branch: [branch name]
- Local Commit: [hash]
- Remote Commit: [hash]
- Status: [ahead/behind count]

### Azure Storage
- Account: stgreenclinicworkspace
- Tenant: greenclinicteam.com
- Container: workspace-sync
- User Folder: [INITIALS]-VScode-workspace-syncs/

## Pre-Sync State
### Local Files (PHI/Sensitive)
| File | Size | Last Modified | SHA256 Hash |
|------|------|---------------|-------------|
| [file] | [size] | [date] | [hash] |

### Git Status
- Uncommitted changes: [Yes/No]
- Untracked files: [count]
- Modified files: [list]

## Actions Requested
- [ ] GitHub Pull
- [ ] GitHub Push
- [ ] Azure Pull
- [ ] Azure Push

## Sync Results
[To be filled after sync completes]

## Compliance Notes
- PHI files encrypted at rest (AES-256)
- PHI files encrypted in transit (TLS 1.2+)
- Access authenticated via Azure AD
- Audit log preserved for compliance review

---
*Generated by Patient_Explorer Workspace Sync*
*HIPAA Compliance Audit Trail*
```

---

## Phase 3: Check/Create Azure User Folder

Before syncing to Azure, verify user-specific folder exists:

```python
# Check if user folder exists
# Container: workspace-sync
# Path: [INITIALS]-VScode-workspace-syncs/

# If not exists, create it
# Example: RG-VScode-workspace-syncs/
```

**Folder naming convention:**
| User | Folder Name |
|------|-------------|
| Robert Green | `RG-VScode-workspace-syncs/` |
| Pat Rutledge | `PR-VScode-workspace-syncs/` |
| Pavel Savine | `PS-VScode-workspace-syncs/` |

Display to user for confirmation:
```
Azure sync target folder: RG-VScode-workspace-syncs/
Is this correct? (yes/change)
```

---

## Phase 4: Execute Sync Operations

### Order of Operations

1. **PULL FIRST** (always get latest before pushing)
   - Git pull from GitHub
   - Azure pull from user folder

2. **Merge Conflicts**
   - Prefer NEWEST file when conflicts occur
   - Log conflict resolution in audit log

3. **PUSH SECOND** (after merging)
   - Git commit and push to GitHub
   - Azure push to user folder

### File Categories

**To GitHub (code, non-PHI):**
- `*.py`, `*.md`, `*.json`, `*.yaml`
- `app/`, `phase0/`, `docs/`, `scripts/`
- `.claude/commands/`
- Configuration files (non-sensitive)

**To Azure (PHI, sensitive, device-specific):**
- `data/` - Patient databases, Excel files
- `.env` - API credentials
- `logs/` - Application logs
- Device-specific VS Code settings (marked as device-specific)

### Device-Specific File Handling

Files marked as device-specific in `.gitignore-sync.json`:
```json
{
  "device_specific": [
    ".vscode/settings.local.json",
    "logs/device-*.log"
  ]
}
```

These sync to Azure under:
```
[INITIALS]-VScode-workspace-syncs/devices/[DEVICE_NAME]/
```

---

## Phase 5: Post-Sync Verification

### Update Audit Log

Append to the audit log file:

```markdown
## Sync Results

### GitHub Sync
- Pull: [success/failed] - [details]
- Push: [success/failed] - [details]
- Final commit: [hash]

### Azure Sync
- Pull: [success/failed] - [X files downloaded]
- Push: [success/failed] - [X files uploaded]
- Conflicts resolved: [count] (newest kept)

### Files Transferred
| Direction | File | Action | Notes |
|-----------|------|--------|-------|
| Azure→Local | data/patients.db | Downloaded | Newer version |
| Local→Azure | .env | Uploaded | No conflict |

## Completion
- **End Timestamp**: [YYYY-MM-DD HH:MM:SS]
- **Duration**: [X minutes]
- **Status**: SUCCESS / PARTIAL / FAILED
- **Errors**: [if any]

## Verification Checksums
| File | Pre-Sync Hash | Post-Sync Hash | Match |
|------|---------------|----------------|-------|
```

### Display Final Summary

```
╔══════════════════════════════════════════════════════════════╗
║              WORKSPACE SYNC COMPLETE                         ║
╠══════════════════════════════════════════════════════════════╣
║ User: [Name] | Device: [Name] | Duration: [X min]            ║
╠══════════════════════════════════════════════════════════════╣
║ GitHub:  ✅ Synced (commit: abc1234)                         ║
║ Azure:   ✅ Synced (folder: RG-VScode-workspace-syncs/)      ║
╠══════════════════════════════════════════════════════════════╣
║ Audit Log: ..Workspace/History/SyncLogs/                     ║
║   └─ 2025-12-10_143052_Robert_Green_sync.md                  ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Error Handling

### Git Conflicts
- List conflicted files
- Auto-resolve by keeping newest (log decision)
- If unable to auto-resolve, pause and ask user

### Azure Auth Failure
1. Remind user to check browser login
2. Suggest: `az login --tenant greenclinicteam.com`
3. Retry with `--interactive` flag

### Missing User Folder
- Create `[INITIALS]-VScode-workspace-syncs/` automatically
- Log creation in audit file

---

## Environment Variables

Set these for smoother operation:

```powershell
# User identification
$env:WORKSPACE_USER = "RG"  # RG, PR, or PS
$env:WORKSPACE_USER_FULL = "Robert Green"

# Can be set in system environment or .env file
```

---

## Related Commands

- `/workspace-brief` - Generate daily focus documents
- `/save-chat` - Save chat transcript before compaction
- `/setup-desktop-shortcut` - Create desktop shortcut for CLI

---

## Files Reference

| Component | Location | Sync Target |
|-----------|----------|-------------|
| Code | `app/`, `phase0/`, `docs/` | GitHub |
| PHI Data | `data/` | Azure (user folder) |
| Credentials | `.env` | Azure (user folder) |
| Logs | `logs/` | Azure (user folder) |
| Audit Logs | `..Workspace/History/SyncLogs/` | GitHub (no PHI) |
| Sync Manifest | `.gitignore-sync.json` | GitHub |

---

## HIPAA Compliance Notes

1. **Audit Trail**: Every sync creates a timestamped log file
2. **User Attribution**: Logs identify who performed the sync
3. **Data Integrity**: SHA256 hashes verify file integrity
4. **Encryption**: Azure storage uses AES-256 at rest, TLS 1.2+ in transit
5. **Access Control**: Azure AD authentication required
6. **Retention**: SyncLogs preserved for compliance auditing
7. **Traceability**: Session IDs link related operations

Future: Automated reports from SyncLogs for internal auditing.

---

*Last Updated: 2025-12-10*
