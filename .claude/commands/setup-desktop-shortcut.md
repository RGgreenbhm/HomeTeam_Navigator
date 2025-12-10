# Setup Desktop Shortcut for Claude Code CLI

Create a desktop shortcut (Pt_Exp-CLI) that launches Claude Code CLI directly in the Patient_Explorer project directory.

## Instructions

When the user asks to set up a desktop shortcut for Claude Code CLI, perform these steps:

### Step 1: Verify Prerequisites

```powershell
# Check Claude CLI is installed
claude --version

# Check project path exists
Test-Path "D:\Projects\Patient_Explorer\CLAUDE.md"

# Check Python environment exists
Test-Path "D:\Projects\Patient_Explorer\.venv\Scripts\python.exe"
```

If any check fails, inform the user what's missing.

### Step 2: Create Icon Directory and Convert Icon

```powershell
# Create icon storage folder
New-Item -ItemType Directory -Path "$env:LOCALAPPDATA\ClaudeCode" -Force

# Run icon conversion script
powershell -ExecutionPolicy Bypass -File "D:\Projects\Patient_Explorer\scripts\convert-icon.ps1"
```

### Step 3: Create Batch File

Create `%USERPROFILE%\Desktop\Pt_Exp-CLI.bat`:

```batch
@echo off
title Claude Code - Patient Explorer
cd /d D:\Projects\Patient_Explorer
claude
```

PowerShell command:
```powershell
@"
@echo off
title Claude Code - Patient Explorer
cd /d D:\Projects\Patient_Explorer
claude
"@ | Out-File -FilePath "$env:USERPROFILE\Desktop\Pt_Exp-CLI.bat" -Encoding ASCII
```

### Step 4: Create Shortcut with Icon

```powershell
powershell -ExecutionPolicy Bypass -File "D:\Projects\Patient_Explorer\scripts\create-shortcut.ps1"
```

### Step 5: Verify Installation

```powershell
# Check files exist
Test-Path "$env:USERPROFILE\Desktop\Pt_Exp-CLI.lnk"
Test-Path "$env:USERPROFILE\Desktop\Pt_Exp-CLI.bat"
Test-Path "$env:LOCALAPPDATA\ClaudeCode\claude-code-icon.ico"
```

### Step 6: Report to User

After successful setup, inform the user:

```
Desktop shortcut created successfully!

Files created:
- Pt_Exp-CLI.lnk (shortcut with Claude icon)
- Pt_Exp-CLI.bat (launcher script)

Double-click "Pt_Exp-CLI" on your Desktop to launch Claude Code CLI
in the Patient_Explorer project directory.
```

## Troubleshooting

### Icon appears grayscale
- The convert-icon.ps1 script uses Python/Pillow which preserves color
- If still grayscale, run: `ie4uinit.exe -show` to refresh icon cache
- Or restart Windows Explorer

### "claude" not recognized
- Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- Or verify it exists at: `%USERPROFILE%\.local\bin\claude.exe`

### Different project path
- If project is not at `D:\Projects\Patient_Explorer\`, update:
  - `scripts\create-shortcut.ps1` (WorkingDirectory line)
  - `scripts\convert-icon.ps1` (ProjectRoot variable)
  - The batch file content

## Reference Files

| File | Purpose |
|------|---------|
| `scripts/create-shortcut.ps1` | Creates Windows shortcut with icon |
| `scripts/convert-icon.ps1` | Converts PNG to ICO with color |
| `..Workspace/Reference/Brand_Media/claude-code-icon.png` | Source icon |
| `docs/guides/desktop-shortcut-setup.md` | Full documentation |
