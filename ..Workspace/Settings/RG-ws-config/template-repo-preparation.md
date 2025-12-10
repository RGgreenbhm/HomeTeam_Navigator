# Workspace Template Repository Preparation Guide

**Instructions for creating a reusable workspace template from the Patient_Explorer repository.**

> **Status:** Draft - Not yet executed. Review and approve before proceeding.

---

## Overview

This guide describes how to create a clean, reusable GitHub template repository from the current Patient_Explorer workspace configuration. The template will include all workspace management features while removing project-specific content.

---

## Phase 1: Create Template Clone

### Step 1.1: Clone to New Location

```bash
# Clone the repo to a new directory
git clone https://github.com/RGgreenbhm/Patient_Explorer.git workspace-template
cd workspace-template

# Remove the git history (start fresh)
rm -rf .git
git init
```

### Step 1.2: Rename Root Folder

Rename from `Patient_Explorer` to a generic name like `workspace-template` or `claude-workspace-starter`.

---

## Phase 2: Files to KEEP (Template Core)

### Workspace Management Structure
```
✅ KEEP:
..Workspace/
├── Focus/                    # Keep folder, clear contents
├── History/
│   ├── BriefingSummaries/   # Keep folder structure, clear contents
│   ├── ClaudeCodeChats/     # Keep folder, clear contents
│   └── GitStatus/           # Keep folder, clear contents
├── Reference/               # Keep folder structure with READMEs only
│   ├── Code_Snippets/README.md
│   ├── External_Docs/README.md
│   ├── Meeting_Notes/README.md
│   ├── Research_Notes/      # Clear contents
│   ├── Screenshots/README.md
│   ├── Templates/README.md
│   └── Vendor_Materials/README.md
└── Settings/
    ├── workspace-config.md          # MODIFY for generic use
    ├── reconciliation-rules.md      # Keep
    ├── bmad-reference.md            # Keep
    ├── teams/                       # Keep entire folder
    └── RG-ws-config/
        ├── RG-workspace-setup.md    # Keep (or rename to generic)
        ├── first-time-setup-checklist.md  # Keep
        └── template-repo-preparation.md   # Keep this file
```

### Claude Code Configuration
```
✅ KEEP:
.claude/
└── commands/
    ├── agent-bmad-master.md      # Keep
    ├── agent-ws-manager.md       # Keep
    ├── workspace-brief.md        # Keep
    ├── save-chat.md              # Keep
    └── export-pdf.md             # Keep
```

### BMAD Core
```
✅ KEEP:
.bmad-core/                       # Keep entire folder
```

### Export Ready
```
✅ KEEP:
Export_Ready/
└── pdf-style.css                 # Keep
```

### Root Files
```
✅ KEEP (but modify):
├── CLAUDE.md                     # Modify - make generic
├── README.md                     # Modify - template documentation
└── .gitignore                    # Keep
```

---

## Phase 3: Files to REMOVE (Project-Specific)

### Project Code & Data
```
❌ REMOVE:
├── phase0/                       # Project-specific Python code
├── app/                          # Project-specific Streamlit app
├── data/                         # Patient data (should be gitignored anyway)
├── docs/                         # Project-specific documentation
├── archive/                      # Old project attempts
├── .venv/                        # Virtual environment
├── .env                          # Credentials (should be gitignored)
├── requirements.txt              # Project-specific dependencies
└── LESSONS-LEARNED.md            # Project-specific history
```

### Project Folders
```
❌ REMOVE:
├── Project_Patient_Explorer_App/ # Project-specific agent folder
```

### Workspace History (Contents Only)
```
❌ CLEAR CONTENTS (keep folders):
..Workspace/Focus/*.md                           # Clear all dated files
..Workspace/History/BriefingSummaries/**/*.md    # Clear all
..Workspace/History/ClaudeCodeChats/*            # Clear all
..Workspace/History/GitStatus/*                  # Clear all
..Workspace/Reference/Research_Notes/*           # Clear project research
..Workspace/Reference/Brand_Media/               # Remove project branding
..Workspace/Reference/Reference_Files/           # Remove project reference data
..Workspace/Reference/ideas/                     # Remove project ideas
Export_Ready/*.pdf                               # Clear generated PDFs
```

### Project-Specific Slash Commands
```
❌ REMOVE:
.claude/commands/agent-patient-explorer-app.md   # Project-specific agent
.claude/commands/bmad-project-agent-template.md  # If exists, evaluate
```

---

## Phase 4: Modify Files for Generic Use

### 4.1: CLAUDE.md Modifications

**Remove:**
- All Patient_Explorer specific content
- HIPAA compliance sections (or make optional/example)
- Green Clinic / Home Team references
- Spruce Health, SharePoint integrations
- phase0/ command references
- Contact/Ownership section specifics

**Keep/Modify:**
- Workspace Focus & History System section (keep, make paths generic)
- Session Startup Checklist
- Archive Sweep Rule
- Chat Preservation Rule
- Git Status Tracking Rule
- Changelog Generation Rule
- Slash Commands table (update for generic commands only)

**Add:**
- Instructions for customizing CLAUDE.md for new projects
- Placeholder sections marked with `<!-- CUSTOMIZE: ... -->`

### 4.2: workspace-config.md Modifications

**Remove:**
- Patient_Explorer workspace identity
- Project-specific folder references
- HIPAA compliance settings
- Project-specific agent profiles

**Keep/Modify:**
- Workspace management folder structure
- Session startup rules
- Document generation settings
- Archive settings
- Chat preservation rules
- Slash command table (generic only)

### 4.3: README.md Rewrite

Create new README.md with:
- Template description
- Quick start guide
- Customization instructions
- Feature list
- Prerequisites (Node.js, npm, etc.)

---

## Phase 5: Create Placeholder/Example Files

### 5.1: Example CLAUDE.md Section

Create `..Workspace/Settings/RG-ws-config/example-claude-sections.md` with:
- Example project identity section
- Example HIPAA compliance section
- Example custom slash commands

### 5.2: Placeholder Focus Documents

Create placeholder in `..Workspace/Focus/`:
```markdown
# Placeholder

This folder will contain daily session documents:
- YYYY-MM-DD_SessionPlanner.md
- YYYY-MM-DD_StatusUpdates.md
- YYYY-MM-DD_WorkspaceOverview.md

Run `/workspace-brief` to generate these documents.
```

---

## Phase 6: Final Cleanup & Validation

### 6.1: Cleanup Script

```bash
# Run from template root

# Remove project-specific folders
rm -rf phase0 app data docs archive .venv

# Remove project-specific files
rm -f .env requirements.txt LESSONS-LEARNED.md

# Remove project-specific commands
rm -f ".claude/commands/agent-patient-explorer-app.md"

# Remove Project folders
rm -rf Project_Patient_Explorer_App

# Clear workspace history contents
rm -f "..Workspace/Focus/"*.md
rm -rf "..Workspace/History/BriefingSummaries/2025"
rm -f "..Workspace/History/ClaudeCodeChats/"*
rm -f "..Workspace/History/GitStatus/"*

# Clear project-specific reference content
rm -rf "..Workspace/Reference/Brand_Media"
rm -rf "..Workspace/Reference/Reference_Files"
rm -rf "..Workspace/Reference/Research_Notes/"*.md
rm -rf "..Workspace/Reference/ideas"

# Clear generated exports
rm -f "Export_Ready/"*.pdf
```

### 6.2: Validation Checklist

- [ ] No patient data or PHI references
- [ ] No project-specific code
- [ ] No credentials or .env files
- [ ] All placeholder/example content in place
- [ ] CLAUDE.md is generic with customization markers
- [ ] README.md describes template usage
- [ ] workspace-config.md is generic
- [ ] All slash commands work in fresh workspace
- [ ] Folder structure is correct
- [ ] .gitignore is appropriate for template

---

## Phase 7: Publish Template

### 7.1: Initialize Git & Push

```bash
git init
git add .
git commit -m "Initial workspace template"
git remote add origin https://github.com/RGgreenbhm/workspace-template.git
git push -u origin main
```

### 7.2: Enable Template Repository

1. Go to repository Settings on GitHub
2. Check "Template repository" under General settings
3. Add description and topics

### 7.3: Test Template

```bash
# Create new repo from template
gh repo create test-workspace --template RGgreenbhm/workspace-template --private
cd test-workspace

# Verify structure
ls -la
ls -la .claude/commands/
ls -la "..Workspace/"
```

---

## Usage After Template Creation

### For New Projects

```bash
# Option 1: GitHub CLI
gh repo create my-new-project --template RGgreenbhm/workspace-template

# Option 2: GitHub Web UI
# Click "Use this template" button on the template repo page

# Option 3: Manual clone
git clone https://github.com/RGgreenbhm/workspace-template.git my-new-project
cd my-new-project
rm -rf .git
git init
```

### Post-Clone Customization

1. Edit `CLAUDE.md` - Add project-specific sections
2. Edit `..Workspace/Settings/workspace-config.md` - Update identity
3. Run `/workspace-brief` to generate initial documents
4. Create project-specific slash commands as needed

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-04 | Initial draft |

---

*Last Updated: December 4, 2025*
*Status: DRAFT - Awaiting approval to execute*
