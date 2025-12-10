# Desktop Shortcut Setup for Claude Code CLI

**Purpose:** Create a desktop shortcut that launches Claude Code CLI directly in the Patient_Explorer project directory.

---

## Quick Setup (Ask Claude)

On any device with this repo cloned, ask Claude:

> "Create a desktop shortcut for Claude Code CLI using the instructions in `docs/guides/desktop-shortcut-setup.md`"

Claude will run the setup scripts and verify the shortcut works.

---

## Manual Setup Steps

### Prerequisites

- Claude Code CLI installed (`claude --version` should work)
- Patient_Explorer repo cloned to `D:\Projects\Patient_Explorer\`
- Python environment set up (for icon conversion)

### Step 1: Create the Icon

```powershell
# Create icon storage folder
New-Item -ItemType Directory -Path "$env:LOCALAPPDATA\ClaudeCode" -Force

# Convert PNG to ICO (run from project directory)
cd D:\Projects\Patient_Explorer
.venv\Scripts\python.exe -c "from PIL import Image; img = Image.open(r'D:\Projects\Patient_Explorer\..Workspace\Reference\Brand_Media\claude-code-icon.png'); img.save(r'$env:LOCALAPPDATA\ClaudeCode\claude-code-icon.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)])"
```

Or use the provided script:
```powershell
powershell -ExecutionPolicy Bypass -File "D:\Projects\Patient_Explorer\scripts\convert-icon.ps1"
```

### Step 2: Create the Batch File

Create `%USERPROFILE%\Desktop\Pt_Exp-CLI.bat` with this content:

```batch
@echo off
title Claude Code - Patient Explorer
cd /d D:\Projects\Patient_Explorer
claude
```

### Step 3: Create the Shortcut

Run the provided script:
```powershell
powershell -ExecutionPolicy Bypass -File "D:\Projects\Patient_Explorer\scripts\create-shortcut.ps1"
```

Or manually:
1. Right-click Desktop → New → Shortcut
2. Location: `%USERPROFILE%\Desktop\Pt_Exp-CLI.bat`
3. Name: `Pt_Exp-CLI`
4. Right-click shortcut → Properties → Change Icon
5. Browse to: `%LOCALAPPDATA%\ClaudeCode\claude-code-icon.ico`

### Step 4: Verify

Double-click the shortcut. You should see:
- Terminal opens with title "Claude Code - Patient Explorer"
- Working directory is `D:\Projects\Patient_Explorer`
- Claude Code CLI starts with project context (CLAUDE.md loaded)

---

## Files Reference

| File | Location | Purpose |
|------|----------|---------|
| `Pt_Exp-CLI.bat` | Desktop | Batch file that launches Claude |
| `Pt_Exp-CLI.lnk` | Desktop | Shortcut with custom icon |
| `claude-code-icon.ico` | `%LOCALAPPDATA%\ClaudeCode\` | Custom icon file |
| `claude-code-icon.png` | `..Workspace/Reference/Brand_Media/` | Source icon image |
| `create-shortcut.ps1` | `scripts/` | PowerShell script to create shortcut |
| `convert-icon.ps1` | `scripts/` | PowerShell script to convert icon |

---

## Troubleshooting

### Icon shows as grayscale
- Use Pillow (Python) to convert PNG to ICO, not .NET
- Run `ie4uinit.exe -show` to refresh icon cache
- Or: Stop/restart Explorer process

### "claude" not recognized
- Ensure Claude Code CLI is installed: `npm install -g @anthropic-ai/claude-code`
- Or check if installed at: `%USERPROFILE%\.local\bin\claude.exe`
- Restart terminal after installation

### Wrong project directory
- Verify `D:\Projects\Patient_Explorer\` exists on this device
- If different path, update the .bat file and `create-shortcut.ps1`

---

## For Claude (Automated Setup)

When asked to create this shortcut on a new device, run these commands in order:

```powershell
# 1. Verify project path exists
Test-Path "D:\Projects\Patient_Explorer\CLAUDE.md"

# 2. Create icon folder
New-Item -ItemType Directory -Path "$env:LOCALAPPDATA\ClaudeCode" -Force

# 3. Convert icon (requires Python + Pillow)
cd D:\Projects\Patient_Explorer
.\.venv\Scripts\python.exe -c "from PIL import Image; img = Image.open(r'D:\Projects\Patient_Explorer\..Workspace\Reference\Brand_Media\claude-code-icon.png'); img.save(f'{__import__(\"os\").environ[\"LOCALAPPDATA\"]}\\ClaudeCode\\claude-code-icon.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)])"

# 4. Create batch file
@"
@echo off
title Claude Code - Patient Explorer
cd /d D:\Projects\Patient_Explorer
claude
"@ | Out-File -FilePath "$env:USERPROFILE\Desktop\Pt_Exp-CLI.bat" -Encoding ASCII

# 5. Create shortcut
powershell -ExecutionPolicy Bypass -File "D:\Projects\Patient_Explorer\scripts\create-shortcut.ps1"

# 6. Verify shortcut exists
Test-Path "$env:USERPROFILE\Desktop\Pt_Exp-CLI.lnk"
```

---

*Last Updated: 2025-12-10*
