# Workspace Setup Guide

**Master installation guide for setting up agent teams and workspace management in a new environment.**

> **Note on "RG-" prefix**: Files and folders prefixed with "RG-" indicate Robert Green's personal configuration preferences (his initials). When sharing these templates, others can create their own versions with their initials (e.g., "JD-workspace-setup.md") to track their customizations separately.

---

## Quick Start

To set up a new workspace with all agent teams:

```powershell
# 1. Copy the entire ..Workspace folder to your new workspace
Copy-Item -Path "..Workspace" -Destination "C:\YourNewWorkspace\" -Recurse

# 2. Run the setup (see Installation Steps below)
```

---

## Available Agent Teams

### Team: Workspace Management (`team-ws`)

**Purpose:** Session management, document generation, workspace hygiene

| Agent | Command | Description |
|-------|---------|-------------|
| Workspace Manager | `/agent-ws-manager` | Session startup, archives, settings sync |

**Additional Commands:**
- `/workspace-brief` - Generate daily focus documents
- `/save-chat` - Preserve chat and compact
- `/export-pdf` - Export markdown to PDF
- `/research-topic` - Research a topic with report and PDF output

**Location:** `..Workspace/Settings/teams/team-ws/`

---

### Team: BMAD Methodology (`team-bmad`)

**Purpose:** Full product development methodology with specialized agents

| Agent | Icon | Specialty |
|-------|------|-----------|
| BMAD Master | 🧙 | Orchestrates all agents |
| Analyst | 🔍 | Research, brainstorming |
| PM (John) | 📋 | PRDs, product strategy |
| Product Owner | ✅ | Validation, sharding |
| Architect (Winston) | 🏗️ | System design |
| UX Expert | 🎨 | UI/UX specs |
| Scrum Master | 📊 | Sprints, stories |
| QA (Quinn) | 🧪 | Testing, quality gates |
| Developer | 💻 | Implementation |

**Command:** `/agent-bmad-master` (accesses all agents through Team Consultation)

**Location:** `..Workspace/Settings/teams/team-bmad/`

**Contents:**
- 10 agent profiles
- 23 executable tasks
- 13 document templates
- 6 quality checklists
- 6 development workflows
- 6 knowledge base resources

---

## Installation Steps

### Step 1: Create Required Folders

```powershell
# In your new workspace root, create these folders:
New-Item -ItemType Directory -Path ".claude\commands" -Force
New-Item -ItemType Directory -Path ".bmad-core" -Force
New-Item -ItemType Directory -Path "..Workspace\Focus" -Force
New-Item -ItemType Directory -Path "..Workspace\History\BriefingSummaries" -Force
New-Item -ItemType Directory -Path "..Workspace\History\ClaudeCodeChats" -Force
New-Item -ItemType Directory -Path "..Workspace\History\GitStatus" -Force
New-Item -ItemType Directory -Path "..Workspace\Reference" -Force
New-Item -ItemType Directory -Path "..Workspace\Settings\RG-ws-config" -Force
```

### Step 2: Install Team WS (Workspace Management)

```powershell
# Copy slash commands
Copy-Item "..Workspace\Settings\teams\team-ws\commands\*" ".claude\commands\" -Force

# The agent profile stays in ..Workspace/Settings/teams/team-ws/
```

### Step 3: Install Team BMAD

```powershell
# Copy BMAD core to workspace root
Copy-Item "..Workspace\Settings\teams\team-bmad\*" ".bmad-core\" -Recurse -Force

# Copy slash command
Copy-Item "..Workspace\Settings\teams\team-bmad\commands\agent-bmad-master.md" ".claude\commands\" -Force
```

### Step 4: Verify Installation

```powershell
# Check slash commands exist
Get-ChildItem ".claude\commands"

# Expected output:
# agent-bmad-master.md
# agent-ws-manager.md
# save-chat.md
# workspace-brief.md

# Check BMAD core exists
Get-ChildItem ".bmad-core"

# Expected folders: agents, tasks, templates, checklists, workflows, data
```

### Step 5: Initialize Workspace

1. Start a Claude Code session
2. Run `/agent-ws-manager`
3. Select `startup` to generate initial documents
4. Workspace is ready!

---

## Automated Setup Script

Save this as `setup-workspace.ps1` in your new workspace:

```powershell
# setup-workspace.ps1
# Run from workspace root where ..Workspace folder exists

param(
    [switch]$TeamWS = $true,
    [switch]$TeamBMAD = $true
)

Write-Host "Setting up workspace..." -ForegroundColor Cyan

# Create folder structure
$folders = @(
    ".claude\commands",
    ".bmad-core",
    "..Workspace\Focus",
    "..Workspace\History\BriefingSummaries",
    "..Workspace\History\ClaudeCodeChats",
    "..Workspace\History\GitStatus",
    "..Workspace\Reference",
    "..Workspace\Settings\RG-ws-config"
)

foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        Write-Host "  Created: $folder" -ForegroundColor Green
    }
}

# Install Team WS
if ($TeamWS) {
    Write-Host "Installing Team WS (Workspace Management)..." -ForegroundColor Yellow
    Copy-Item "..Workspace\Settings\teams\team-ws\commands\*" ".claude\commands\" -Force
    Write-Host "  Team WS installed" -ForegroundColor Green
}

# Install Team BMAD
if ($TeamBMAD) {
    Write-Host "Installing Team BMAD..." -ForegroundColor Yellow
    Copy-Item "..Workspace\Settings\teams\team-bmad\*" ".bmad-core\" -Recurse -Force
    Copy-Item "..Workspace\Settings\teams\team-bmad\commands\agent-bmad-master.md" ".claude\commands\" -Force
    Write-Host "  Team BMAD installed" -ForegroundColor Green
}

Write-Host "`nSetup complete!" -ForegroundColor Cyan
Write-Host "Available commands:"
Get-ChildItem ".claude\commands" | ForEach-Object { Write-Host "  /$($_.BaseName)" }
```

**Usage:**
```powershell
# Install both teams (default)
.\setup-workspace.ps1

# Install only Team WS
.\setup-workspace.ps1 -TeamBMAD:$false

# Install only Team BMAD
.\setup-workspace.ps1 -TeamWS:$false
```

---

## Adding New Teams

To create a new agent team:

1. Create folder: `..Workspace/Settings/teams/team-{name}/`
2. Create `team-manifest.yaml` with team metadata
3. Add agent profile(s) as `.md` files
4. Add slash commands in `commands/` subfolder
5. Update this guide with new team info

### Team Manifest Template

```yaml
# team-manifest.yaml
name: "Team Display Name"
short_name: "team-{name}"
version: "1.0"
created: "YYYY-MM-DD"
description: "What this team does"

agents:
  - name: "Agent Name"
    file: "agent-profile.md"
    icon: "🎯"
    slash_command: "/agent-{name}"
    description: "Agent specialty"

slash_commands:
  - source: "commands/agent-{name}.md"
    target: ".claude/commands/agent-{name}.md"

install_notes: |
  Installation instructions here
```

---

## Configuration Checklist

When setting up a new workspace, verify:

### Workspace Structure (under `..Workspace/` parent folder)
- [ ] Created `..Workspace/` main folder (keeps workspace files sorted at top)
- [ ] Created `..Workspace/Focus/` subfolder (current day's documents)
- [ ] Created `..Workspace/History/BriefingSummaries/` subfolder
- [ ] Created `..Workspace/History/ClaudeCodeChats/` subfolder
- [ ] Created `..Workspace/History/GitStatus/` subfolder
- [ ] Created `..Workspace/Reference/` subfolder (user's manual artifacts)
- [ ] Created `..Workspace/Settings/` subfolder (master configuration)
- [ ] Created `..Workspace/Settings/RG-ws-config/` subfolder (device setup & environment)

### Claude Code Commands
- [ ] Created `.claude/commands/` folder
- [ ] Copied `agent-ws-manager.md` slash command
- [ ] Copied `workspace-brief.md` slash command
- [ ] Copied `save-chat.md` slash command

### BMAD Method (Optional)
- [ ] Created `.bmad-core/` folder in workspace root
- [ ] Copied BMAD team resources (agents, tasks, templates, etc.)
- [ ] Copied `agent-bmad-master.md` slash command

### Configuration
- [ ] Copied workspace rules to `CLAUDE.md` (from `..Workspace/Settings/workspace-config.md`)
- [ ] Tested `/agent-ws-manager` command
- [ ] Tested `/workspace-brief` command

---

## Document Templates

### Session Planner Template

```markdown
# Session Planner: YYYY-MM-DD

---

## 1. Session Scratch Notes

*Capture your thoughts at session start. What's on your mind?*

[Enter your thoughts here...]

---

## 2. Proposed Focus Areas

### Focus Area 1: [Title]
**Priority**: [CRITICAL/HIGH/MEDIUM]
- [ ] Task 1
- [ ] Task 2

### Focus Area 2: [Title]
**Priority**: [CRITICAL/HIGH/MEDIUM]
- [ ] Task 1
- [ ] Task 2

---

## 3. Outstanding User To-Dos

| Item | Source Session | Status |
|------|---------------|--------|
| | | |

---

## 4. Current Session Intentions

### What I Want to Accomplish THIS Session
[Enter goals for this session...]

### Items to Discuss Now, But Reserve for Future Sessions
[Topics to mention but save for later...]

---

## 5. Session Follow-Up Log

### For User (Before Next Session)
| Task | Priority | Notes |
|------|----------|-------|
| | | |

### For Agent (Next Session Prep)
| Task | Priority | Notes |
|------|----------|-------|
| | | |

---

*Generated: YYYY-MM-DD*
```

### Chat Transcript Template

```markdown
# Chat Transcript: YYYY-MM-DD HH:mm

## Metadata
- **Date**: YYYY-MM-DD
- **Time**: HH:mm
- **Topic**: <one-line-summary>
- **Trigger**: Manual | Auto-compaction
- **Files Modified**: [list of files]

---

## Conversation

[Full transcript here...]

---
*Preserved: YYYY-MM-DD HH:mm*
```

---

## Troubleshooting

### Commands Not Available

If slash commands don't appear:
1. Verify files exist in `.claude/commands/`
2. Restart Claude Code session
3. Check file permissions

### BMAD Master Can't Find Resources

If `/agent-bmad-master` fails to load resources:
1. Verify `.bmad-core/` folder exists in workspace root
2. Check that all subfolders (agents, tasks, templates, etc.) were copied
3. Run installation step 3 again

### Workspace Documents Not Generating

If `/workspace-brief` fails:
1. Verify `..Workspace/Focus/` folder exists
2. Verify `..Workspace/History/` folder structure exists
3. Check write permissions

---

## PDF Export Setup

The `/export-pdf` command converts markdown files to PDF with full GitHub-style rendering including color emojis.

### Prerequisites

```bash
# Install Node.js (if not already installed)
# Then install md-to-pdf globally
npm install -g md-to-pdf
```

### How It Works

md-to-pdf uses Puppeteer (headless Chrome) to render markdown exactly like a browser, which means:
- ✅ Full color emoji support
- ✅ Modern CSS rendering
- ✅ GitHub-flavored markdown
- ✅ Excellent font rendering

### Usage

```
/export-pdf path/to/file.md
```

Output goes to `Export_Ready/{filename}.pdf`

### Custom Styling

Add YAML frontmatter to any markdown file for custom PDF options:

```yaml
---
pdf_options:
  format: Letter
  margin: 25mm
  printBackground: true
---
```

### Files

| File | Purpose |
|------|---------|
| `.claude/commands/export-pdf.md` | Slash command definition |
| `Export_Ready/pdf-style.css` | Optional custom CSS stylesheet |
| `Export_Ready/` | Output folder for generated PDFs |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.3 | 2025-12-04 | Added /research-topic command |
| 1.2 | 2025-12-04 | Added PDF Export setup with md-to-pdf |
| 1.1 | 2025-12-03 | Consolidated ExportReady content, added templates and checklist |
| 1.0 | 2025-12-03 | Initial release with team-ws and team-bmad |

---

*Last Updated: December 4, 2025*
