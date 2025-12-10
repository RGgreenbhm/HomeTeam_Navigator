# Patient Explorer

**HIPAA-compliant patient consent tracking and outreach tool** for managing patient data during EMR transitions.

## Current Status: Phase 0 - Consent Outreach

A Python-based CLI tool for:
- Matching patient lists against Spruce Health contacts
- Tracking consent for record retention
- Preparing for Phase 1 (Care Plan & Chart building)

## Quick Start

```bash
# Activate virtual environment
.venv\Scripts\activate

# Test Spruce API connection
python -m phase0 test-spruce

# Load patient data (aggregate stats only - no PHI displayed)
python -m phase0 load-patients data/patients.xlsx

# Match patients to Spruce contacts
python -m phase0 match-spruce data/patients.xlsx
```

## HIPAA Compliance

This tool is designed for HIPAA-compliant workflows:

| Protection | Implementation |
|------------|----------------|
| **No PHI in terminal** | All commands show aggregate statistics only |
| **Results to files** | Patient-level data written to local CSV files |
| **Encrypted storage** | Windows 11 + BitLocker required |
| **BAA coverage** | Spruce Health + Microsoft 365 under BAA |

**Important**: Never paste patient data into Claude Code chat. Run commands and review CSV outputs locally.

## Project Structure

```
Patient_Explorer/
├── phase0/                     # Python consent outreach tool
│   ├── main.py                # CLI commands
│   ├── models.py              # Data models
│   ├── excel_loader.py        # Excel patient import
│   ├── spruce/                # Spruce Health API client
│   └── sharepoint/            # SharePoint integration
├── ..Workspace/                # Workspace management (sorted first alphabetically)
│   ├── Focus/                 # Today's session documents
│   ├── History/               # Archived documents & chat logs
│   ├── Reference/             # Manual reference artifacts
│   └── Settings/              # Master configuration
│       └── RG-ws-config/      # Device setup & environment config
├── data/                       # Patient data (gitignored)
├── docs/                       # Architecture & planning docs
├── archive/                    # Previous Electron attempt
├── .venv/                      # Python virtual environment
├── .env                        # API credentials (gitignored)
└── requirements.txt            # Python dependencies
```

### Workspace Management Folders

| Folder | Purpose |
|--------|---------|
| `..Workspace/Focus/` | Current day's SessionPlanner, StatusUpdates, WorkspaceOverview |
| `..Workspace/History/` | Archived briefs, chat transcripts, git status logs |
| `..Workspace/Reference/` | Your manual reference docs (not auto-managed) |
| `..Workspace/Settings/` | Master configuration - synced to CLAUDE.md |
| `..Workspace/Settings/RG-ws-config/` | Device setup & environment configuration |

## Commands

### Patient Management
| Command | Description |
|---------|-------------|
| `test-spruce` | Test Spruce API connection |
| `load-patients <file>` | Validate Excel patient list |
| `match-spruce <file>` | Match patients to Spruce contacts |
| `init-sharepoint` | Set up SharePoint consent list |
| `import-to-sharepoint <file>` | Import patients to SharePoint |
| `status` | Show consent tracking statistics |

### Azure Workspace Sync
| Command | Description |
|---------|-------------|
| `init-sync` | Create sync manifest (`.gitignore-sync.json`) |
| `sync-push --interactive` | Upload local data to Azure (before switching devices) |
| `sync-pull --interactive` | Download data from Azure (after cloning on new device) |
| `sync-status --interactive` | Check sync status between local and Azure |

## Azure Workspace Sync

Securely sync gitignored data (PHI, credentials) between devices using Azure Blob Storage.

### Setup (One-Time)
```bash
# Initialize sync manifest
python -m phase0 init-sync

# Push your data to Azure
python -m phase0 sync-push --interactive
```

### Switching to a New Device
```bash
# On your current device - push latest data
python -m phase0 sync-push --interactive

# On the new device - after cloning the repo
git clone https://github.com/RGgreenbhm/Patient_Explorer.git
cd Patient_Explorer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m phase0 sync-pull --interactive
```

### What Gets Synced
| Synced to Azure | NOT Synced |
|-----------------|------------|
| `data/` (patient databases) | `.venv/` (recreate with pip) |
| `.env` (credentials) | `__pycache__/` (auto-generated) |
| `logs/*.log` | IDE settings |

### Security
- **Encryption at rest**: AES-256 (Microsoft-managed keys)
- **Encryption in transit**: TLS 1.2+
- **Authentication**: Azure AD (your Microsoft account)
- **Authorization**: RBAC - only designated team members

## Requirements

- Windows 11 with BitLocker enabled
- Python 3.10+
- Spruce Health account with API access
- Microsoft 365 with SharePoint (under HIPAA BAA)
- Azure account with Storage Blob Data Contributor role (for workspace sync)

## Documentation

- [CLAUDE.md](CLAUDE.md) - AI assistant guidance
- [LESSONS-LEARNED.md](LESSONS-LEARNED.md) - Development history
- [docs/architecture.md](docs/architecture.md) - System architecture
- [docs/prd.md](docs/prd.md) - Product requirements

### Configuration

- [..Workspace/Settings/workspace-config.md](..Workspace/Settings/workspace-config.md) - Master configuration
- [..Workspace/Settings/reconciliation-rules.md](..Workspace/Settings/reconciliation-rules.md) - Config sync rules
- [..Workspace/Settings/RG-ws-config/](..Workspace/Settings/RG-ws-config/) - Device setup files

---

**Owner**: Robert Green, MD
**Organization**: Green Clinic / Home Team Medical Services
**Last Updated**: December 8, 2025
