# Lessons Learned - Patient Explorer Development

## Electron Attempt (November 2025)

### What Was Attempted
We attempted to build Patient_Explorer as an Electron + React + TypeScript desktop application with:
- **Electron 28.x LTS** as the desktop framework
- **React 18** for the UI
- **TypeScript 5.3+** for type safety
- **SQLite + SQLCipher** for encrypted local database
- **Drizzle ORM** for type-safe queries
- **electron-vite** for build tooling

### Technical Blockers Encountered

#### 1. Windows Defender File Locking
**Problem:** Windows Defender's real-time scanning locked `.asar` files (Electron's archive format) during npm install, preventing clean reinstalls.

**Symptoms:**
```
EBUSY: resource busy or locked, rename '...\node_modules\electron\dist\resources\default_app.asar'
```

**Root Cause:** Defender scans large binary packages like Electron (~150MB Chromium distribution) and holds file handles open.

**Solution (Partially Applied):**
- Add `node_modules` to Windows Defender exclusion paths
- Run: `Add-MpPreference -ExclusionPath "V:\Projects\Patient_Explorer\Patient_Explorer\node_modules"`
- Requires admin privileges
- Must be done BEFORE npm install, not after

#### 2. Electron Module Resolution Issue
**Problem:** When running Electron via electron-vite, `require('electron')` returned a **string path** to electron.exe instead of the Electron API.

**Symptoms:**
```
TypeError: Cannot read properties of undefined (reading 'disableHardwareAcceleration')
```

**Root Cause:** Node.js module resolution found `node_modules/electron/index.js` (which exports the executable path) before Electron's internal module interceptor could provide the API.

**Attempted Fixes (All Failed):**
1. `vite-plugin-electron` - same error
2. `esbuild` with `external: ['electron']` - same error
3. `electron-vite` with various configurations - same error
4. Running electron.exe directly with scripts - same error

**Suspected Root Cause:** Possible Windows-specific issue with Electron 28.x, or conflict with the shell environment (Git Bash via Claude Code).

#### 3. PowerShell Escaping Issues
**Problem:** PowerShell commands with `$_` or `$variable` in script blocks failed when executed through the Claude Code shell environment.

**Symptoms:**
```
'/c/Users/Rober/.claude/shell-snapshots/...' is not recognized as a cmdlet
```

**Root Cause:** The shell wrapper was expanding `$_` as a bash variable before passing to PowerShell.

**Workaround:** Use simpler PowerShell commands without Where-Object, or use `cmd /c` for basic operations.

### Architecture Decisions Made (Still Valid)

These decisions from the architecture phase remain valid for future implementation:

1. **Offline-First Design:** Local database as source of truth, sync to cloud
2. **Hub-and-Spoke Sync:** CouchDB on-premises server for multi-device sync
3. **7-Layer Security:** BitLocker → SQLCipher → TLS → App → Session → Audit
4. **HIPAA Compliance:** All PHI encrypted at rest and in transit
5. **Per-Patient Versioning:** Conflict resolution at patient record level

### Files Archived
The following files were moved to `archive/electron-attempt/`:
- `electron/` - Electron main process files
- `src/` - React components and TypeScript source
- `dist/`, `dist-electron/`, `out/` - Build outputs
- `scripts/` - Build scripts
- `package.json` - Node.js dependencies
- `tsconfig.json`, `tsconfig.node.json` - TypeScript config
- `vite.config.ts`, `vitest.config.ts` - Vite/Vitest config
- `electron.vite.config.ts` - electron-vite config
- `electron-builder.yml` - Electron packaging config
- `tailwind.config.js`, `postcss.config.js` - CSS tooling
- `.eslintrc.cjs`, `.prettierrc` - Linting/formatting
- `index.html` - Vite entry point
- `RESUME-AFTER-REBOOT.md` - Debug notes

### Recommendations for Future Electron Attempts

1. **Start Fresh on Clean Windows Install** - Avoid accumulated tool conflicts
2. **Add Defender Exclusion First** - Before running npm install
3. **Use Electron Forge Instead of electron-vite** - More mature tooling
4. **Test on WSL2** - Avoid Windows-specific file locking issues
5. **Consider Electron 27.x** - If 28.x issues persist, try earlier version
6. **Use Official Electron Quick Start** - Validate basic setup before adding complexity

---

## Phase 0 Pivot (December 2025)

### Strategic Decision
Given the Electron blockers and the December 31, 2025 deadline for Allscripts access termination, we pivoted to a simpler Phase 0 approach:

### Phase 0: Consent Outreach Tool
**Stack:** Python + SharePoint
- Python scripts for Excel/Spruce matching
- SharePoint Lists for consent tracking
- No Electron complexity
- HIPAA-compliant (BitLocker + SharePoint under BAA)

### Benefits of This Approach
1. **Faster to implement** - No complex desktop app setup
2. **Consent-first** - Establishes legal foundation before PHI collection
3. **Uses existing infrastructure** - SharePoint already under HIPAA BAA
4. **Simpler debugging** - Python environment is more predictable

### Phase 1 (Deferred)
Care Plan and Chart building features deferred until:
1. Phase 0 consent collection is operational
2. Electron issues are resolved (or alternative desktop framework chosen)
3. December 31 deadline pressure is relieved

---

*Last Updated: November 30, 2025*
