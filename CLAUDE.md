# CLAUDE.md - AI Assistant Guide for HomeTeam_Navigator

This document provides guidance for AI assistants (like Claude) working on the HomeTeam_Navigator codebase.

## Home Team Medical Services Context

**Organization**: Home Team Medical Services
**Domain**: hometeammed.com
**Inbound Email**: info@hometeammed.com (monitor for patient record transfer requests)

### Cross-Reference Capability

This deployment supports cross-referencing patients from **Green Clinic** transfers:
- Field: `green_clinic_mrn` - Original MRN from Green Clinic
- Enables tracking patients who transferred from Dr. Green's practice
- Search by either Home Team MRN or Green Clinic MRN

## HIPAA Compliance for AI Services

### Claude Code (Anthropic Direct) - NO BAA
**Anthropic does NOT have a BAA for Claude Code.** Therefore:

#### DO NOT
- Display individual patient names, MRNs, phone numbers, or emails in terminal output
- Read patient data files (Excel, CSV with PHI) directly
- Log or echo PHI in any command output
- Ask users to paste patient data into chat

#### DO
- Show only aggregate statistics (counts, percentages)
- Write detailed results to local files (CSV) that user reviews offline
- Process PHI in local Python scripts without displaying it
- Keep all PHI processing on the user's encrypted device

All CLI commands in this project are designed to output **aggregate statistics only**.

### Azure Foundry Claude - COVERED UNDER BAA ✅
**Claude models on Azure Foundry ARE covered under the Microsoft HIPAA BAA.**

As of November 2025, Claude Sonnet 4.5, Opus, and Haiku are available through Azure Foundry and inherit Azure's HIPAA compliance when:
- Deployed in HIPAA-compliant regions (e.g., East US2)
- Accessed via Azure API endpoints (not Anthropic direct)
- Used with proper encryption, access controls, and logging

**Use Cases Enabled by Azure Claude:**
- AI-assisted consent form processing
- Patient communication parsing (Spruce message analysis)
- Care plan generation assistance
- Conflict resolution suggestions

See: `docs/Research_Reports/2025-11-30_Azure-Claude-HIPAA-BAA-Compatible.md`

---

## Project Overview

**HomeTeam_Navigator** is a HIPAA-compliant patient tracking and outreach tool for Home Team Medical Services.

- **Current Status**: Phase 0 - Patient Outreach Tool (Python CLI)
- **Purpose**: Track patients, manage outreach, and cross-reference Green Clinic transfers
- **Platform**: Windows 11 + BitLocker, Python virtual environment
- **Storage**: Local files + SharePoint/Azure (under HIPAA BAA)
- **Created**: December 2025 (cloned from Patient_Explorer)
- **Source**: Derived from Green Clinic's Patient_Explorer project

## Project Structure

```
HomeTeam_Navigator/
├── phase0/                     # Python consent outreach tool
│   ├── __init__.py
│   ├── __main__.py            # Entry point for `python -m phase0`
│   ├── main.py                # CLI commands (typer/rich)
│   ├── models.py              # Pydantic data models
│   ├── excel_loader.py        # Excel patient import
│   ├── spruce/                # Spruce Health API client
│   │   ├── __init__.py
│   │   └── client.py
│   └── sharepoint/            # SharePoint integration
│       ├── __init__.py
│       └── client.py
├── ..Workspace/                # Workspace management (sorted first alphabetically)
│   ├── Focus/                 # Current session focus documents
│   │   ├── YYYY-MM-DD_SessionPlanner.md    # Today's session planner
│   │   ├── YYYY-MM-DD_StatusUpdates.md     # Today's status update
│   │   └── YYYY-MM-DD_WorkspaceOverview.md # Today's workspace overview
│   ├── History/               # Historical records & archives
│   │   ├── BriefingSummaries/ # Archived briefs by year/month
│   │   │   └── YYYY/          # Year folder (e.g., 2025/)
│   │   │       └── MM-MonthName/ # Month folder (e.g., 12-December/)
│   │   ├── ClaudeCodeChats/   # Preserved raw chat transcripts
│   │   └── SyncLogs/          # Workspace sync audit logs (HIPAA compliance)
│   ├── Reference/             # User's manual reference artifacts
│   │   ├── Research_Notes/    # Research notes and findings
│   │   ├── Templates/         # Reusable templates
│   │   ├── External_Docs/     # External documentation
│   │   ├── Screenshots/       # Visual references
│   │   ├── Code_Snippets/     # Reference code snippets
│   │   ├── Meeting_Notes/     # Meeting and call notes
│   │   └── Vendor_Materials/  # Third-party materials
│   └── Settings/              # Workspace configuration (master)
│       ├── workspace-config.md    # Master configuration file
│       ├── reconciliation-rules.md # Config sync rules
│       └── RG-ws-config/      # Device setup & environment config
├── .claude/                    # Claude Code configuration
│   └── commands/              # Custom slash commands
│       └── workspace-brief.md # Generate daily briefs
├── data/                       # Patient data (gitignored)
├── docs/                       # Architecture & planning docs
├── archive/                    # Previous Electron attempt
├── .venv/                      # Python virtual environment
├── .env                        # API credentials (gitignored)
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
├── CLAUDE.md                   # This file
└── LESSONS-LEARNED.md          # Development history
```

## Quick Reference

### Development Commands

```bash
# Activate virtual environment (required before all commands)
.venv\Scripts\activate

# Test Spruce API connection
python -m phase0 test-spruce

# Validate patient Excel file (aggregate stats only)
python -m phase0 load-patients data/patients.xlsx

# Match patients to Spruce contacts (results to CSV)
python -m phase0 match-spruce data/patients.xlsx

# Initialize SharePoint consent list
python -m phase0 init-sharepoint

# Import patients to SharePoint tracking
python -m phase0 import-to-sharepoint data/patients.xlsx

# Show consent tracking statistics
python -m phase0 status
```

### Available CLI Commands

| Command | Description | Output |
|---------|-------------|--------|
| `test-spruce` | Test Spruce API connection | Connection status, contact count |
| `load-patients <file>` | Validate Excel patient list | Column info, row counts |
| `match-spruce <file>` | Match patients to Spruce | Aggregate stats → CSV file |
| `init-sharepoint` | Create SharePoint consent list | Setup confirmation |
| `import-to-sharepoint <file>` | Import patients to SharePoint | Import stats |
| `status` | Show consent statistics | Aggregate counts |
| `init-sync` | Create Azure sync manifest | `.gitignore-sync.json` |
| `sync-push -i` | Push data to Azure | Upload status |
| `sync-pull -i` | Pull data from Azure | Download status |
| `sync-status -i` | Check sync status | Local vs remote comparison |

## Azure Workspace Sync

Securely sync gitignored PHI data between devices using Azure Blob Storage.

### Commands
```bash
# Initialize sync manifest (one-time)
python -m phase0 init-sync

# Push local data to Azure (before switching devices)
python -m phase0 sync-push --interactive

# Pull data from Azure (on new device after git clone)
python -m phase0 sync-pull --interactive

# Check sync status
python -m phase0 sync-status --interactive
```

### What Gets Synced
- `data/` - Patient databases and Excel files (PHI)
- `.env` - API credentials and secrets
- `logs/` - Application logs

### Security Guarantees
| Protection | Implementation |
|------------|----------------|
| **At Rest (Azure)** | AES-256 encryption (Microsoft-managed keys) |
| **In Transit** | TLS 1.2+ (HTTPS only) |
| **At Rest (Local)** | BitLocker required |
| **Authentication** | Azure AD (Microsoft account) |
| **Authorization** | RBAC - Storage Blob Data Contributor role |

### New Device Setup
```bash
# 1. Clone repo
git clone https://github.com/RGgreenbhm/Patient_Explorer.git
cd Patient_Explorer

# 2. Setup Python environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Pull PHI data from Azure (opens browser for auth)
python -m phase0 sync-pull --interactive

# 4. Verify
python -m phase0 sync-status --interactive
```

## HIPAA Architecture

### Business Associate Agreements (BAAs)

| Service | BAA Status | Usage |
|---------|------------|-------|
| **Spruce Health** | ✅ BAA in place | Patient contact lookup |
| **Microsoft 365** | ✅ BAA in place | SharePoint consent tracking |
| **Azure Blob Storage** | ✅ BAA in place | PHI workspace sync |
| **Anthropic (Claude)** | ❌ No BAA | Code assistance only, no PHI |

### Data Flow

```
Patient Excel (local) → Python CLI → Results CSV (local)
                             ↓
                      Spruce API (BAA)
                             ↓
                    SharePoint List (BAA)
```

### Security Layers

1. **BitLocker** - Full-disk encryption on Windows 11
2. **Local Processing** - PHI never leaves encrypted device during matching
3. **BAA-Covered APIs** - Only sync to Spruce/SharePoint (both under BAA)
4. **Aggregate Output** - CLI shows counts only, details to files

## Technology Stack (Phase 0)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Runtime** | Python 3.10+ | Script execution |
| **CLI Framework** | Typer + Rich | Command-line interface |
| **Data Models** | Pydantic | Type-safe data validation |
| **Excel Parsing** | pandas + openpyxl | Patient list import |
| **HTTP Client** | httpx | Async API calls |
| **SharePoint** | Office365-REST-Python-Client | Consent list management |
| **Logging** | loguru | File-based logging (no terminal PHI) |
| **Environment** | python-dotenv | Credential management |

## Data Models

### Patient (from Excel)
- `mrn`: Medical Record Number (unique identifier)
- `first_name`, `last_name`: Patient name
- `date_of_birth`: DOB for matching
- `phone`, `email`: Contact information
- `address`: Optional address

### ConsentRecord (SharePoint tracking)
- `mrn`: Links to patient
- `patient_name`: Display name
- `status`: pending | outreach_sent | consented | declined | unreachable
- `method`: spruce | phone | mail | in_person | n/a
- `outreach_date`, `response_date`, `consent_date`: Tracking dates
- `notes`: Free-text notes
- `spruce_matched`: Whether found in Spruce

### SpruceContact (API response)
- `patient_id`: Spruce's internal ID
- `first_name`, `last_name`, `display_name`: Name fields
- `phone`, `email`: Contact info
- `created_at`: Account creation date

## Environment Setup

### Prerequisites

**Required:**
- Windows 11 Pro/Enterprise with BitLocker enabled
- Python 3.10+
- Git
- VS Code with Claude Code extension

**API Access:**
- Spruce Health account with API token
- Microsoft 365 with SharePoint (under HIPAA BAA)

### Initial Setup

```bash
# Clone/navigate to project
cd Patient_Explorer

# Create virtual environment (one-time)
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env
# Edit .env with your API credentials
```

### Environment Variables (.env)

```env
# Spruce Health API
SPRUCE_API_TOKEN=your_base64_token
SPRUCE_ACCESS_ID=your_access_id

# SharePoint (optional - for consent tracking)
SHAREPOINT_SITE_URL=https://tenant.sharepoint.com/sites/PatientConsent
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_client_secret

# Paths
PATIENT_EXCEL_PATH=data/patients.xlsx
LOG_FILE=logs/phase0.log
```

## Tenant Context

### Home Team Medical Services (This Deployment)
- **Tenant**: hometeammed.com
- **BAA**: HIPAA BAA with Microsoft in place
- **Admin**: Robert Green, MD
- **Inbound Email**: info@hometeammed.com

### Cross-Reference: Green Clinic
- **Related Tenant**: southviewteam.com
- **Related Project**: Patient_Explorer
- **Purpose**: Track patients transferring from Dr. Green's Green Clinic practice
- **Cross-Reference Field**: `green_clinic_mrn`

## Workflow

### Patient Consent Outreach (Phase 0)

1. **Load Patient List**
   - Export patient list from EMR to Excel
   - Place in `data/` directory (gitignored)
   - Run `python -m phase0 load-patients data/patients.xlsx`

2. **Match to Spruce**
   - Run `python -m phase0 match-spruce data/patients.xlsx`
   - Review `data/match_results.csv` locally
   - Identify patients already in Spruce Health

3. **Track Consent in SharePoint**
   - Initialize list: `python -m phase0 init-sharepoint`
   - Import patients: `python -m phase0 import-to-sharepoint data/patients.xlsx`
   - Update consent status through SharePoint UI or CLI

4. **Monitor Progress**
   - Run `python -m phase0 status` for aggregate statistics
   - Review SharePoint list for detailed tracking

## Important Notes for AI Assistants

### Working with PHI-Adjacent Code

When modifying CLI commands:
1. **Never print individual patient data** to terminal
2. **Always use aggregate statistics** for user feedback
3. **Write detailed results to files** that user reviews offline
4. **Suppress logging to file only** - no PHI in stdout/stderr

### Code Patterns to Follow

```python
# GOOD: Aggregate output
console.print(f"Matched: {matched_count} of {total_count} patients")

# BAD: Individual PHI
console.print(f"Found: {patient.first_name} {patient.last_name}")

# GOOD: Results to file
df.to_csv("data/results.csv", index=False)
console.print(f"Results written to data/results.csv")

# BAD: PHI in table display
table.add_row(patient.mrn, patient.name, patient.phone)
```

### When Reviewing Excel/CSV Files

- **Do not** read patient data files directly
- **Do** help with code that processes them
- **Do** suggest column mapping and validation logic
- **Do not** display sample rows or patient-identifiable data

---

## Workspace Focus & History System

### Overview

This workspace maintains session planning documents to track progress, guide focus, and preserve historical context.

### Folder Structure

```
..Workspace/                           # Workspace management (sorted first alphabetically)
├── Focus/                            # Current day's documents live here
│   ├── YYYY-MM-DD_SessionPlanner.md  # Today's session planner (interactive)
│   ├── YYYY-MM-DD_StatusUpdates.md   # Today's status update
│   └── YYYY-MM-DD_WorkspaceOverview.md # Today's workspace overview
├── History/                          # Historical records & archives
│   ├── BriefingSummaries/            # Archived session documents
│   │   └── YYYY/                     # Archive by year (e.g., 2025/)
│   │       └── MM-MonthName/         # Archive by month (e.g., 12-December/)
│   ├── ClaudeCodeChats/              # Preserved raw chat transcripts
│   └── SyncLogs/                     # Workspace sync audit logs (HIPAA compliance)
├── Reference/                        # User's manual reference artifacts (not auto-managed)
│   ├── Research_Notes/               # Research notes and findings
│   ├── Templates/                    # Reusable templates
│   ├── External_Docs/                # External documentation
│   ├── Screenshots/                  # Visual references
│   ├── Code_Snippets/                # Reference code snippets
│   ├── Meeting_Notes/                # Meeting and call notes
│   └── Vendor_Materials/             # Third-party materials
└── Settings/                         # Master configuration (synced to CLAUDE.md & README.md)
    ├── workspace-config.md           # Master configuration file
    ├── reconciliation-rules.md       # Config sync rules
    └── RG-ws-config/                 # Device setup & environment config
```

### Session Startup Checklist

**IMPORTANT: At the start of each new Claude Code session, perform these checks in order:**

#### Step 0: Settings Reconciliation
- Read `..Workspace/Settings/workspace-config.md` (master configuration)
- Compare key settings with `CLAUDE.md` and `README.md`
- If discrepancies found, report to user and offer to sync
- See `..Workspace/Settings/reconciliation-rules.md` for detailed process

#### Step 1: Document Generation Check
Check if today's documents exist in `..Workspace/Focus/`. If not, generate them using the `/workspace-brief` command or by following these procedures:

#### 1. Status Update (`YYYY-MM-DD_StatusUpdates.md`)

Generate a status update that summarizes:
- **Last 24 Hours**: What work appears to have been accomplished based on file modifications, git commits, and document changes
- **Last Week**: Summary of progress over the past 7 days
- **Key Metrics**: Files changed, commits made, documents created/updated

Save to: `..Workspace/Focus/YYYY-MM-DD_StatusUpdates.md`

#### 2. Workspace Overview (`YYYY-MM-DD_WorkspaceOverview.md`)

Generate an executive-level summary including:
- **Workspace Contents**: What information and resources the workspace contains
- **Current Goals**: What the workspace goals appear to be at present
- **Active Areas**: Which areas or topics are currently active (based on recent changes)
- **Top 3 Focus Areas**: Suggestions for areas most ripe for additional development

Save to: `..Workspace/Focus/YYYY-MM-DD_WorkspaceOverview.md`

#### 3. Session Planner (`YYYY-MM-DD_SessionPlanner.md`)

Generate an interactive session planning document with these sections:

**Section 1: Session Scratch Notes**
- Empty text area for user to capture stream-of-consciousness thoughts at session start
- Helps user focus and provides context not already in workspace files

**Section 2: Proposed Focus Areas**
- Top 3 focus areas from the Workspace Overview
- Actionable checklists for each area
- Priority ordering based on dependencies and impact

**Section 3: Outstanding User To-Dos**
- Review last 5 SessionPlanner files for uncompleted user tasks
- Carry forward items that still need attention
- Table format: Item | Source Session | Status

**Section 4: Current Session Intentions**
- Area for user to enter specific goals for THIS session
- Separate area for topics to discuss now but reserve for future sessions
- Distinguishes immediate work from future planning

**Section 5: Session Follow-Up Log**
- Append notes throughout session about next steps
- **For User (Before Next Session)**: Tasks requiring user action
- **For Agent (Next Session Prep)**: Tasks for AI to prepare
- **Cloud Agent Delegation**: Tasks suitable for autonomous execution post-session (Claude Code background tasks, GitHub Copilot, etc.)

Save to: `..Workspace/Focus/YYYY-MM-DD_SessionPlanner.md`

### Archive Sweep Rule

**When generating new documents, archive older ones:**

1. Check if folder `..Workspace/History/BriefingSummaries/YYYY/` exists (current year). If not, create it.
2. Check if folder `..Workspace/History/BriefingSummaries/YYYY/MM-MonthName/` exists (e.g., `12-December`). If not, create it.
3. Move all SessionPlanner, StatusUpdates, and WorkspaceOverview files with dates **older than today** from `..Workspace/Focus/` to the appropriate archive folder based on their file date.

This keeps only the current day's documents visible while automatically archiving historical documents for reference.

### Chat Preservation Rule

**CRITICAL: Before ANY chat compaction (manual or auto-triggered), preserve the raw chat data:**

#### Manual Preservation
Use `/save-chat` command to manually save and compact. This will:
1. Generate one-line topic summary
2. Save full transcript with metadata
3. Proceed with compaction

#### Auto-Compaction Preservation
When auto-compaction is triggered (context window filling), Claude MUST:
1. **Detect the trigger** - Recognize when compaction is about to occur
2. **Preserve FIRST** - Save complete transcript BEFORE compaction executes
3. **Generate summary** - Create kebab-case topic summary (max 50 chars)
4. **Save with timestamp** - Format: `YYYY-MM-DD_HHmm_<topic-summary>.md`
5. **Include metadata**:
   - Date/time
   - Trigger reason (manual or auto)
   - Key topics discussed
   - Files modified during session
6. **Then compact** - Only after preservation is complete

#### File Location & Format
- **Location**: `..Workspace/History/ClaudeCodeChats/`
- **Filename**: `YYYY-MM-DD_HHmm_<topic-summary>.md`
- **Example**: `2025-12-01_2315_workspace-briefing-system-setup.md`

See `..Workspace/Settings/workspace-config.md` for detailed format specification.

### Workspace Sync Audit Logging Rule

**When `/workspace-sync` is executed, create a HIPAA-compliant audit log:**

Trigger conditions:
- User runs `/workspace-sync` command
- Manual sync operations (git push/pull, Azure sync)

Generate an audit log file in `..Workspace/History/SyncLogs/YYYY-MM-DD_HHMMSS_[FirstName]_[LastName]_sync.md` containing:
- **Session Info**: Timestamp, user, device, session ID
- **Sync Targets**: GitHub repo/branch, Azure storage account/container/user folder
- **Pre-Sync State**: File hashes, git status, uncommitted changes
- **Actions Performed**: Pull/push operations for both GitHub and Azure
- **Sync Results**: Success/failure status, files transferred, conflicts resolved
- **Compliance Notes**: Encryption status, authentication method

**User Identification:**
- RG = Robert Green (rgreen@greenclinicteam.com)
- PR = Pat Rutledge (prutledge@greenclinicteam.com)
- PS = Pavel Savine (psavine@greenclinicteam.com)

**Azure User Folders:**
Each user syncs to their own folder: `[INITIALS]-VScode-workspace-syncs/`

See `/workspace-sync` command for full protocol details.

### Changelog Generation Rule

**After every `git push` to the GitHub repository, create a changelog summary:**

Trigger: Successful `git push` command execution

Generate a changelog file in `..Workspace/History/SyncLogs/YYYY-MM-DD_HH-MM-SS_changelog.md` containing:
- **Timestamp**: Date and time of push
- **Branch**: Branch name pushed
- **Remote**: Repository URL
- **Commits Pushed**: List of commit hashes and messages included in push
- **Files Changed**: Summary of files added/modified/deleted
- **Summary**: Brief description of the changes

Example filename: `2025-12-03_14-30-45_changelog.md`

### Workspace Setup for New Environments

For setting up new workspaces with this management system, see:
`..Workspace/Settings/RG-ws-config/RG-workspace-setup.md`

This guide includes installation steps, PowerShell scripts, configuration checklists, and document templates.

### Rationale

These time-stamped summary documents enable:
- Historical analysis of how focus changes over time within this workspace
- Quick onboarding for new sessions without re-reading entire codebase
- Consistent progress tracking and accountability
- Strategic alignment on priorities
- Preservation of detailed chat context for future reference
- Clean branch hygiene and collaboration visibility

### Slash Commands

| Command | Description |
|---------|-------------|
| `/agent-bmad-master` | Launch BMAD Master Orchestrator for product development |
| `/agent-ws-manager` | Launch Workspace Manager for session/document management |
| `/agent-patient-explorer-app` | Launch Patient Explorer App Agent |
| `/workspace-brief` | Generate all three daily focus documents |
| `/workspace-sync` | Sync workspace across GitHub, Azure with HIPAA audit logging |
| `/setup-desktop-shortcut` | Create desktop shortcut for Claude Code CLI |
| `/save-chat` | Save chat transcript and compact |

---

## Project Folder System (BMAD Multi-Agent Architecture)

### Overview

The workspace supports specialized **Project_ folders** that contain scoped sub-projects managed by dedicated Project Agents. This enables parallel workstreams with clear boundaries and autonomous agent coordination.

### Folder Naming Convention

```
Project_[ProjectName]/
├── briefs/                    # Project status briefs (YYYY-MM-DD_*.md)
├── research/                  # Research reports specific to project
├── architecture/              # Architecture decisions (ADRs) for project
└── [other project-specific folders]
```

**Examples:**
- `Project_Patient_Explorer_App/` → **Patient Explorer App Agent**
- `Project_Clinical_AI_Framework/` → **Clinical AI Framework Agent**
- `Project_Consent_Campaign/` → **Consent Campaign Agent**

### Project Agent Naming Convention

**Rule:** Extract text after `Project_`, replace underscores with spaces, convert to title case, append "Agent".

| Folder | Agent Name |
|--------|------------|
| `Project_Patient_Explorer_App/` | Patient Explorer App Agent |
| `Project_Data_Migration/` | Data Migration Agent |
| `Project_Clinical_Workflows/` | Clinical Workflows Agent |

### Project Agent Rules

Each Project_ folder has a dedicated **Project Agent** that follows these rules:

#### Scope & Permissions

**Read Access:** ✅ Full workspace
- Can read ANY file in workspace for context
- Reviews CLAUDE.md, README.md, workspace config
- Accesses research, docs, code for understanding

**Write Access:** ⚠️ RESTRICTED to assigned Project_ folder only
- Can ONLY create/modify files within `Project_[ProjectName]/`
- Creates briefs in `briefs/` subfolder
- Creates research reports in `research/` subfolder
- Creates architecture docs in `architecture/` subfolder
- **CANNOT** modify CLAUDE.md, workspace config, or other project folders
- **MUST** escalate to BMAD Master Orchestrator for cross-project changes

#### Core Responsibilities

1. **Project Status Tracking** - Monitor progress, track tasks, identify risks
2. **Brief Generation** - Generate status briefs on demand (`YYYY-MM-DD_ProjectStatusBrief.md`)
3. **Research Coordination** - Generate research reports, coordinate with specialists
4. **Technical Documentation** - Track ADRs and technical decisions

### Integration with BMAD Ecosystem

**Project Agents report to:**
- BMAD Master Orchestrator (for cross-project coordination)
- User (for decisions and approvals)

**Project Agents can request help from:**
- BMAD Analyst, Architect, Developer, QA, UX Designer

### Current Project Agents

| Command | Agent | Project Folder |
|---------|-------|----------------|
| `/agent-patient-explorer-app` | Patient Explorer App Agent | `Project_Patient_Explorer_App/` |

---

## Phase 1 (Future): Care Plan Builder

Phase 1 will add a desktop application for:
- Screenshot capture from EMR systems
- OCR processing with Azure Cognitive Services
- Patient chart building and search
- Care plan report generation

Technology decisions made:
- Electron + React + TypeScript
- SQLite with SQLCipher encryption
- CouchDB for multi-device sync

**Note**: Phase 1 was paused due to Electron/Windows Defender conflicts. See [LESSONS-LEARNED.md](LESSONS-LEARNED.md) for details.

## Legal Context

The consent outreach (Phase 0) supports legal requirements for:
- Patient notification of practice transition
- Consent for continued record retention
- Documentation for potential legal proceedings

Consult with legal counsel (Susan Doughton referenced in project history) for specific requirements.

## Contact / Ownership

- **Organization**: Home Team Medical Services
- **Admin/Owner**: Robert Green, MD
- **Microsoft Tenant**: hometeammed.com
- **Inbound Email**: info@hometeammed.com
- **Development Environment**: VS Code + Claude Code
- **Related Project**: Patient_Explorer (Green Clinic)

---

*Last Updated: December 10, 2025 (v1.0 - Initial HomeTeam_Navigator deployment)*
