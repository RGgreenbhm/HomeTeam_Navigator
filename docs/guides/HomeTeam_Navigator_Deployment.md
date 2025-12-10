# HomeTeam_Navigator Deployment Guide

Deploy Patient Explorer as **HomeTeam_Navigator** for Home Team Medical Services (hometeammed.com).

---

## Overview

| Attribute | Green Clinic (Source) | Home Team (Target) |
|-----------|----------------------|-------------------|
| **Repo Name** | Patient_Explorer | HomeTeam_Navigator |
| **GitHub** | RGgreenbhm/Patient_Explorer | RGgreenbhm/HomeTeam_Navigator |
| **Domain** | greenclinicteam.com | hometeammed.com |
| **Local Path** | `D:\Projects\Patient_Explorer` | `D:\Projects\HomeTeam_Navigator` |
| **Storage Account** | stgreenclinicworkspace | sthometeamworkspace |
| **Inbound Email** | - | info@hometeammed.com |

---

## Pre-Deployment Checklist

### 1. GitHub Setup
- [ ] Create new repo: `RGgreenbhm/HomeTeam_Navigator`
- [ ] **IMPORTANT**: Add Claude Code access to new repo
  - Go to GitHub Settings → Integrations → Claude Code
  - Grant access to `HomeTeam_Navigator` repository
- [ ] Set repo to Private (contains HIPAA-related code patterns)

### 2. Azure Resources (hometeammed.com tenant)
- [ ] Create Storage Account: `sthometeamworkspace`
  - Region: East US 2 (HIPAA compliant)
  - Replication: GRS (geo-redundant)
  - Enable encryption at rest
- [ ] Create Blob Container: `workspace-sync`
- [ ] Configure RBAC: Storage Blob Data Contributor for users
- [ ] Verify BAA coverage under Home Team's Microsoft agreement

### 3. Spruce Health (if separate account)
- [ ] Obtain Home Team Spruce API token
- [ ] Obtain Home Team Spruce Access ID
- [ ] Note: May use same Spruce account if shared practice

---

## Deployment Steps

### Step 1: Clone Without PHI

Run from PowerShell on your device:

```powershell
# Navigate to Projects folder
cd D:\Projects

# Clone Green Clinic repo (shallow, no history)
git clone --depth 1 https://github.com/RGgreenbhm/Patient_Explorer.git HomeTeam_Navigator

# Enter new directory
cd HomeTeam_Navigator

# Remove git history (start fresh)
Remove-Item -Recurse -Force .git

# Remove ALL PHI and sensitive data
Remove-Item -Recurse -Force data\*
Remove-Item -Force .env -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force logs\* -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backup_* -ErrorAction SilentlyContinue

# Remove Green Clinic specific sync logs (keep structure)
Remove-Item -Recurse -Force "..Workspace\History\SyncLogs\*" -ErrorAction SilentlyContinue

# Initialize fresh git repo
git init
git remote add origin https://github.com/RGgreenbhm/HomeTeam_Navigator.git
```

### Step 2: Update Configuration Files

#### A. Update `.gitignore-sync.json`

```json
{
  "version": "1.0",
  "storage_account": "sthometeamworkspace",
  "container": "workspace-sync",
  "tenant": "hometeammed.com",
  "sync_paths": [
    {
      "local": "data/",
      "remote": "data/",
      "pattern": "**/*",
      "description": "Patient data files (PHI)"
    },
    {
      "local": ".env",
      "remote": "config/.env",
      "description": "Environment credentials"
    },
    {
      "local": "logs/",
      "remote": "logs/",
      "pattern": "*.log",
      "description": "Application logs"
    }
  ],
  "cross_reference": {
    "enabled": true,
    "source_org": "Green Clinic",
    "source_identifier_field": "green_clinic_mrn",
    "notes": "Patients transferring from Green Clinic may have cross-reference MRN"
  }
}
```

#### B. Create `.env` for Home Team

```env
# HomeTeam_Navigator Environment Configuration
# Domain: hometeammed.com

# Spruce Health API (Home Team account)
SPRUCE_API_TOKEN=<home_team_spruce_token>
SPRUCE_ACCESS_ID=<home_team_access_id>

# Azure Storage (Home Team workspace)
AZURE_STORAGE_ACCOUNT=sthometeamworkspace
AZURE_TENANT_ID=<hometeammed_tenant_id>

# Microsoft 365 (Home Team tenant)
MS_CLIENT_ID=<home_team_client_id>
MS_TENANT_ID=<hometeammed_tenant_id>

# Inbound Data Sources
INBOUND_EMAIL=info@hometeammed.com
INBOUND_EMAIL_MONITOR=true

# Cross-Reference Settings (for Green Clinic transfers)
CROSS_REF_ENABLED=true
CROSS_REF_SOURCE_ORG=Green Clinic
CROSS_REF_IDENTIFIER=green_clinic_mrn

# Paths
PATIENT_DATA_PATH=data/
LOG_FILE=logs/hometeam_navigator.log
```

#### C. Update `CLAUDE.md` Header

Replace organization references:

```markdown
# CLAUDE.md - AI Assistant Guide for HomeTeam_Navigator

## Project Overview

**HomeTeam_Navigator** is a HIPAA-compliant patient management and care coordination tool for Home Team Medical Services.

- **Organization**: Home Team Medical Services
- **Domain**: hometeammed.com
- **Admin**: Robert Green, MD (rgreen@hometeammed.com)
- **Inbound Email**: info@hometeammed.com

## Cross-Reference with Green Clinic

Patients transferring from Green Clinic (greenclinicteam.com) may have:
- `green_clinic_mrn` field linking to their original MRN
- Consent documentation for record transfer
- Records received via info@hometeammed.com

When processing inbound patient data, check for Green Clinic cross-reference.
```

#### D. Update `workspace-sync.md` Azure Settings

```markdown
**Azure Storage:**
- Storage Account: `sthometeamworkspace`
- Container: `workspace-sync`
- Tenant: `hometeammed.com` (Home Team Medical)
```

### Step 3: Create Empty Data Structure

```powershell
# Create data folder structure (empty, ready for Home Team patients)
New-Item -ItemType Directory -Path "data" -Force
New-Item -ItemType File -Path "data\.gitkeep" -Force

# Create logs folder
New-Item -ItemType Directory -Path "logs" -Force
New-Item -ItemType File -Path "logs\.gitkeep" -Force
```

### Step 4: Initial Commit and Push

```powershell
# Stage all files
git add -A

# Initial commit
git commit -m "Initial HomeTeam_Navigator deployment from Patient_Explorer

- Cloned app structure from Green Clinic Patient_Explorer
- Removed all PHI and patient data
- Configured for hometeammed.com domain
- Added cross-reference support for Green Clinic transfers
- Inbound email: info@hometeammed.com

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

# Push to new repo
git push -u origin main
```

### Step 5: Setup Python Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

### Step 6: Initialize Azure Sync

```powershell
# Initialize sync manifest (will use new storage account)
python -m phase0 init-sync

# Test connection (will prompt for Azure login)
python -m phase0 sync-status --interactive
```

---

## Cross-Reference Schema

For patients transferring from Green Clinic, add these fields to patient records:

```json
{
  "patient_id": "HT-001234",
  "mrn": "HT001234",
  "cross_reference": {
    "source_organization": "Green Clinic",
    "source_mrn": "GC-005678",
    "transfer_date": "2025-01-15",
    "consent_obtained": true,
    "consent_date": "2025-01-10",
    "records_received_via": "info@hometeammed.com",
    "records_received_date": "2025-01-12"
  }
}
```

---

## Inbound Email Monitoring (info@hometeammed.com)

### Expected Inbound Data

| Source | Content | Action |
|--------|---------|--------|
| Green Clinic | Patient records (consented transfers) | Import to HomeTeam_Navigator |
| Referrals | New patient referrals | Create new patient record |
| Labs/Imaging | Results for existing patients | Attach to patient record |

### Future Enhancement

Consider implementing:
- Email parsing for automatic patient matching
- Attachment extraction and categorization
- Audit trail for received records

---

## Post-Deployment Verification

- [ ] Claude Code can access `HomeTeam_Navigator` repo
- [ ] `streamlit run app/main.py` launches without errors
- [ ] Azure sync connects to `sthometeamworkspace`
- [ ] Empty patient list displays correctly
- [ ] Can create test patient record
- [ ] Cross-reference fields available in patient schema

---

## Reminder: Claude Code Access

**IMPORTANT**: After creating the GitHub repo, grant Claude Code access:

1. Go to: https://github.com/settings/installations
2. Find Claude Code integration
3. Click "Configure"
4. Under "Repository access", add `HomeTeam_Navigator`
5. Save changes

Without this, Claude Code sessions in the new workspace won't be able to read/write files.

---

*Created: 2025-12-10*
*Source: Patient_Explorer deployment guide*
