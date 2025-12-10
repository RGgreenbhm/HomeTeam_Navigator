# New Device Setup Instructions for Patient_Explorer

**For Claude Code on a new device** - Follow these steps to sync this workspace from GitHub and Azure.

---

## Prerequisites

Before starting, ensure:
- Windows 11 with BitLocker enabled
- Python 3.10+ installed
- Git installed
- VS Code with Claude Code extension
- Azure account with access to `stgreenclinicworkspace` storage account

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/RGgreenbhm/Patient_Explorer.git
cd Patient_Explorer
```

---

## Step 2: Create Python Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4: Pull Data from Azure

This pulls the gitignored files (PHI database, credentials, logs) from Azure Blob Storage:

```bash
python -m phase0 sync-pull --interactive
```

A browser window will open for Microsoft authentication. Log in with your authorized Azure account (rgreen@greenclinicteam.com or rgreen@southviewteam.com).

**Files that will be downloaded:**
- `data/patients.db` - Patient database (PHI)
- `.env` - API credentials and secrets
- `.gitignore-sync.json` - Sync manifest
- `logs/phase0.log` - Application logs

---

## Step 5: Verify Sync Status

```bash
python -m phase0 sync-status --interactive
```

Expected output:
```
Synced: 4 files

All files in sync!
```

---

## Step 6: Test the Application

```bash
python -m phase0 test-spruce
```

If credentials are correct, you should see a successful connection message.

---

## Daily Workflow

### Starting Work on This Device

```bash
# Pull any changes from GitHub
git pull origin main

# Pull any data changes from Azure
python -m phase0 sync-pull --interactive
```

### Ending Work on This Device

```bash
# Push data to Azure (before switching devices)
python -m phase0 sync-push --interactive

# Commit and push code changes to GitHub
git add -A
git commit -m "Your commit message"
git push origin main
```

---

## Troubleshooting

### Authentication Errors

If you get `AuthorizationPermissionMismatch`:
1. Ensure you're using `--interactive` flag
2. Verify your Azure account has `Storage Blob Data Contributor` role on `stgreenclinicworkspace`

### Missing .env File

If `.env` is missing after sync-pull:
1. Check Azure Portal > Storage Account > Containers > workspace-sync > config/
2. Verify the file exists in Azure
3. Try `python -m phase0 sync-pull --force --interactive`

### Azure CLI Alternative

If browser auth doesn't work, you can try Azure CLI:
```bash
az login
python -m phase0 sync-status  # (without --interactive)
```

---

## Azure Resources Reference

| Resource | Value |
|----------|-------|
| Storage Account | `stgreenclinicworkspace` |
| Container | `workspace-sync` |
| Resource Group | `Green_Clinic` |
| Region | East US 2 |
| Subscription | PAYG-RG-Dev |

---

## Security Notes

- All data is encrypted at rest (AES-256) and in transit (TLS 1.2+)
- Only authorized Azure AD users can access the storage
- Never commit `.env` or `data/` to git - they are gitignored
- PHI should only be stored on BitLocker-encrypted devices

---

## Slash Commands Available

Once setup is complete, you can use these Claude Code commands:

| Command | Description |
|---------|-------------|
| `/workspace-sync` | Full sync protocol (git + Azure + environment check) |
| `/workspace-brief` | Generate daily focus documents |
| `/save-chat` | Save chat transcript before compaction |

---

*Last Updated: December 8, 2025*
*Source Device: Primary workstation*
*Azure Storage URL: https://stgreenclinicworkspace.blob.core.windows.net*
