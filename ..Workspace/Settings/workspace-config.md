# Workspace Configuration

**This is the master configuration file for workspace behavior.**

Changes made here should be reconciled with `CLAUDE.md` and `README.md` during session startup.

---

## Workspace Identity

- **Workspace Name**: Patient_Explorer
- **Owner**: Robert Green, MD
- **Organization**: Green Clinic / Home Team Medical Services
- **Created**: October 2025
- **Purpose**: HIPAA-compliant patient consent tracking and outreach tool

---

## Folder Structure

### Core Project Folders
| Folder | Purpose | Managed By |
|--------|---------|------------|
| `phase0/` | Python consent outreach CLI | Development |
| `app/` | Streamlit web application | Development |
| `docs/` | Project documentation | Development |
| `data/` | Patient data (gitignored) | User |
| `archive/` | Archived code attempts | Development |

### Workspace Management Folders (under `..Workspace/`)
| Folder | Purpose | Managed By |
|--------|---------|------------|
| `..Workspace/Focus/` | Current day's session documents | Automated |
| `..Workspace/History/` | Historical records and archives | Automated |
| `..Workspace/Reference/` | User's manual reference artifacts | User (manual) |
| `..Workspace/Settings/` | Workspace configuration | User + Agents |
| `..Workspace/Settings/RG-ws-config/` | Device setup & environment config | User |

---

## Session Startup Rules

At the start of each new Claude Code session:

### 1. Settings Reconciliation
- Read `..Workspace/Settings/workspace-config.md` (this file)
- Compare with `CLAUDE.md` and `README.md`
- Report any discrepancies to user
- Offer to sync if differences found

### 2. Document Generation Check
- Check if today's documents exist in `..Workspace/Focus/`
- If missing, offer to generate via `/workspace-brief`

### 3. Archive Sweep
- Move older documents from `..Workspace/Focus/` to `..Workspace/History/BriefingSummaries/`

### 4. Git Status Check
- If remote changes detected, generate GitStatus summary

---

## Document Generation Settings

### Status Update
- **Frequency**: Daily (at session start if missing)
- **Lookback**: 24 hours + 7 days
- **Location**: `..Workspace/Focus/YYYY-MM-DD_StatusUpdates.md`

### Workspace Overview
- **Frequency**: Daily (at session start if missing)
- **Content**: Goals, active areas, top 3 focus areas
- **Location**: `..Workspace/Focus/YYYY-MM-DD_WorkspaceOverview.md`

### Session Planner
- **Frequency**: Daily (at session start if missing)
- **Sections**: Scratch notes, focus areas, to-dos, intentions, follow-up log
- **Location**: `..Workspace/Focus/YYYY-MM-DD_SessionPlanner.md`

---

## Archive Settings

### BriefingSummaries Archive
- **Structure**: `YYYY/MM-MonthName/` (e.g., `2025/12-December/`)
- **Trigger**: Documents older than current date
- **Location**: `..Workspace/History/BriefingSummaries/`

### Chat Preservation
- **Manual Trigger**: `/save-chat` command
- **Auto Trigger**: Before any chat compaction (manual or auto)
- **Format**: `YYYY-MM-DD_HHmm_<topic-summary>.md` (with timestamp for multiple per day)
- **Location**: `..Workspace/History/ClaudeCodeChats/`
- **Content**: Full conversation transcript + metadata

### Git Status Tracking
- **Trigger**: Branch changes, remote sync, user request
- **Format**: `YYYY-MM-DD_GitStatus.md`
- **Location**: `..Workspace/History/GitStatus/`

### Changelog Generation
- **Trigger**: After every `git push` to the GitHub repository
- **Format**: `YYYY-MM-DD_HH-MM-SS_changelog.md`
- **Location**: `..Workspace/History/GitStatus/`
- **Content**: Summary of changes pushed to remote, including:
  - Commit hash(es) pushed
  - Commit messages
  - Files added/modified/deleted
  - Branch name
  - Remote repository URL

---

## HIPAA Compliance Settings

### Claude Code (No BAA)
- **DO NOT**: Display individual PHI in terminal
- **DO NOT**: Read patient data files directly
- **DO**: Show aggregate statistics only
- **DO**: Write detailed results to local files

### BAA-Covered Services
- Spruce Health: Patient contact lookup
- Microsoft 365/SharePoint: Consent tracking
- Azure Foundry Claude: AI-assisted PHI processing (if configured)

---

## Custom Slash Commands

| Command | Description | Location |
|---------|-------------|----------|
| `/agent-bmad-master` | Launch BMAD Master Orchestrator for product development | `.claude/commands/agent-bmad-master.md` |
| `/agent-ws-manager` | Launch Workspace Manager for session/document management | `.claude/commands/agent-ws-manager.md` |
| `/agent-patient-explorer-app` | Launch Patient Explorer App Agent | `.claude/commands/agent-patient-explorer-app.md` |
| `/workspace-brief` | Generate daily focus documents | `.claude/commands/workspace-brief.md` |
| `/save-chat` | Save chat transcript and compact | `.claude/commands/save-chat.md` |
| `/export-pdf` | Export markdown file to PDF in Export_Ready folder | `.claude/commands/export-pdf.md` |
| `/research-topic` | Research a topic and save report to docs/research with PDF | `.claude/commands/research-topic.md` |

## Agent Teams

Agent teams are self-contained packages in `..Workspace/Settings/teams/`:

| Team | Folder | Purpose |
|------|--------|---------|
| Workspace Management | `teams/team-ws/` | Session startup, document management, workspace hygiene |
| BMAD Methodology | `teams/team-bmad/` | Full product development with 9 specialized agents |

Each team contains:
- `team-manifest.yaml` - Team metadata and installation instructions
- Agent profile(s) - `.md` files defining agent personas
- `commands/` - Slash commands to copy to `.claude/commands/`

## Agent Profiles

| Agent | Profile Location | Slash Command |
|-------|-----------------|---------------|
| Workspace Manager | `teams/team-ws/agent-ws-manager-profile.md` | `/agent-ws-manager` |
| BMAD Master | `teams/team-bmad/agents/bmad-master.md` | `/agent-bmad-master` |
| Patient Explorer App Agent | `.claude/commands/agent-patient-explorer-app.md` | `/agent-patient-explorer-app` |

## Project Folder System

### Naming Convention

Project folders follow the pattern `Project_[Name]/` where `[Name]` becomes the agent name:

**Rule:** Extract text after `Project_`, replace underscores with spaces, convert to title case, append "Agent".

| Folder | Agent Name | Command |
|--------|------------|---------|
| `Project_Patient_Explorer_App/` | Patient Explorer App Agent | `/agent-patient-explorer-app` |

### Project Agent Scope

**Read Access:** ✅ Full workspace (for context)
**Write Access:** ⚠️ Assigned `Project_[Name]/` folder only

### Project Folder Structure

```
Project_[Name]/
├── briefs/           # Status briefs (YYYY-MM-DD_*.md)
├── research/         # Research reports
├── architecture/     # ADRs and technical docs
└── README.md         # Project overview
```

### Creating New Project Agents

See `.claude/commands/bmad-project-agent-template.md` for the full template.

## BMAD Reference

Complete BMAD methodology reference is stored at:
`..Workspace/Settings/bmad-reference.md`

## Workspace Setup

For setting up new workspaces with these teams, see:
`..Workspace/Settings/RG-ws-config/RG-workspace-setup.md`

**Note**: The "RG-" prefix indicates Robert Green's personal configuration preferences. Others can create their own versions with their initials to track customizations.

---

## Chat Preservation Rules

### Manual Preservation (`/save-chat`)

When user invokes `/save-chat`:
1. Generate one-line summary of dominant chat topic
2. Create file: `..Workspace/History/ClaudeCodeChats/YYYY-MM-DD_HHmm_<topic-summary>.md`
3. Write full conversation transcript with metadata header
4. Confirm save to user
5. Proceed with chat compaction

### Auto-Compaction Preservation

**CRITICAL: Before ANY chat compaction (including auto-triggered), Claude MUST:**

1. **Detect compaction trigger** - When context window is filling or compaction is about to occur
2. **Preserve first** - Save complete chat transcript BEFORE compaction executes
3. **Generate summary** - Create one-line topic summary based on dominant themes
4. **Save with timestamp** - `YYYY-MM-DD_HHmm_<topic-summary>.md` format
5. **Include metadata**:
   - Session start time (if known)
   - Compaction trigger reason
   - Key topics discussed
   - Files modified during session
6. **Then compact** - Proceed with normal compaction after preservation

### Chat File Format

```markdown
# Chat Transcript: YYYY-MM-DD HH:mm

## Metadata
- **Date**: YYYY-MM-DD
- **Time**: HH:mm
- **Topic**: <one-line-summary>
- **Trigger**: Manual | Auto-compaction
- **Files Modified**: [list of files]

## Conversation

[Full transcript here...]

---
*Preserved: YYYY-MM-DD HH:mm*
```

---

*Last Updated: December 4, 2025*
*Version: 1.8 - Added /research-topic command*
