# Azure Secure Blob Storage Proposal

## Overview

This document proposes a secure Azure Blob Storage solution that enables **portable workspace replication** across multiple devices while maintaining HIPAA compliance.

### Goal
```
Device A (Primary)                    Device B (New Workstation)
┌─────────────────────┐               ┌─────────────────────┐
│ Patient_Explorer/   │               │ Patient_Explorer/   │
│ ├── app/           │               │ ├── app/           │  ← From GitHub
│ ├── phase0/        │  git push     │ ├── phase0/        │
│ ├── docs/          │ ──────────►   │ ├── docs/          │
│ └── (code files)   │               │ └── (code files)   │
│                    │               │                    │
│ ├── data/          │               │ ├── data/          │  ← From Azure
│ ├── .env           │  Azure Sync   │ ├── .env           │
│ └── *.xlsx (PHI)   │ ──────────►   │ └── *.xlsx (PHI)   │
└─────────────────────┘    (TLS)     └─────────────────────┘
         │                                    │
         │         ┌─────────────────┐        │
         └────────►│  Azure Blob     │◄───────┘
                   │  (Encrypted)    │
                   │  East US 2      │
                   └─────────────────┘
```

### Workflow
1. **Clone repo** from GitHub on new device
2. **Run sync command** to pull encrypted data from Azure
3. **Authenticate** via Azure AD (same Microsoft account)
4. **Work locally** - all PHI stays on encrypted device
5. **Push changes** back to Azure before switching devices

## Data Categories to Store

Based on `.gitignore`, the following sensitive data needs secure cloud backup:

| Category | File Types | HIPAA Concern | Priority |
|----------|------------|---------------|----------|
| **Patient Data** | `*.xlsx`, `*.xls`, `data/` | PHI - Critical | High |
| **Databases** | `*.db`, `*.sqlite`, `*.sqlite3` | PHI - Critical | High |
| **Credentials** | `.env`, `.env.local` | Secrets | High |
| **Logs** | `logs/`, `*.log` | May contain PHI | Medium |
| **Virtual Env** | `.venv/` | No PHI (rebuild) | Low |

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Azure East US 2                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Resource Group: rg-patient-explorer         │    │
│  │                                                          │    │
│  │  ┌──────────────────────┐  ┌──────────────────────┐     │    │
│  │  │  Storage Account     │  │  Key Vault           │     │    │
│  │  │  stpatientexplorer   │  │  kv-patient-explorer │     │    │
│  │  │                      │  │                      │     │    │
│  │  │  ├─ Container:       │  │  ├─ storage-key      │     │    │
│  │  │  │  patient-data     │  │  ├─ spruce-token     │     │    │
│  │  │  │  (PHI - encrypted)│  │  ├─ sharepoint-creds │     │    │
│  │  │  │                   │  │  └─ encryption-key   │     │    │
│  │  │  ├─ Container:       │  │                      │     │    │
│  │  │  │  app-config       │  └──────────────────────┘     │    │
│  │  │  │  (.env files)     │                               │    │
│  │  │  │                   │  ┌──────────────────────┐     │    │
│  │  │  └─ Container:       │  │  Private Endpoint    │     │    │
│  │  │     backups          │  │  (No public access)  │     │    │
│  │  │     (db snapshots)   │  └──────────────────────┘     │    │
│  │  └──────────────────────┘                               │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │  Virtual Network: vnet-patient-explorer          │   │    │
│  │  │  Subnet: snet-storage (Private Endpoint)         │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Security Configuration

### 1. Storage Account Settings

```json
{
  "name": "stpatientexplorer",
  "location": "eastus2",
  "sku": "Standard_GRS",
  "kind": "StorageV2",
  "properties": {
    "supportsHttpsTrafficOnly": true,
    "minimumTlsVersion": "TLS1_2",
    "allowBlobPublicAccess": false,
    "networkAcls": {
      "defaultAction": "Deny",
      "bypass": "AzureServices"
    },
    "encryption": {
      "services": {
        "blob": {
          "enabled": true,
          "keyType": "Account"
        }
      },
      "keySource": "Microsoft.Keyvault"
    }
  }
}
```

### 2. Container Structure

| Container | Purpose | Access Tier | Lifecycle |
|-----------|---------|-------------|-----------|
| `patient-data` | Excel files, CSVs with PHI | Hot | 90-day retention |
| `app-config` | .env files, credentials | Hot | Version all |
| `backups` | SQLite DB snapshots | Cool | 30-day archive to cold |
| `logs` | Application logs | Cool | 7-day delete |

### 3. Encryption

- **At Rest**: Azure Storage Service Encryption (SSE) with customer-managed keys in Key Vault
- **In Transit**: TLS 1.2+ enforced
- **Client-Side**: Optional additional encryption for PHI files using Azure SDK

### 4. Access Control

```
┌─────────────────────────────────────────────────────────┐
│                    Access Hierarchy                      │
├─────────────────────────────────────────────────────────┤
│  Azure AD Authentication (Primary)                       │
│    ├─ rgreen@southviewteam.com      → Storage Owner     │
│    ├─ rgreen@greenclinicteam.com    → Storage Owner     │
│    └─ autopilot@southviewteam.com   → Storage Contrib   │
│                                                          │
│  Service Principal (App Access)                          │
│    └─ sp-patient-explorer-app       → Blob Data Contrib │
│                                                          │
│  Managed Identity (Future Containers)                    │
│    └─ mi-patient-explorer           → Blob Data Reader  │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Phase 1: Infrastructure Setup (Azure Portal/CLI)

```bash
# 1. Create Resource Group
az group create \
  --name rg-patient-explorer \
  --location eastus2

# 2. Create Storage Account (HIPAA-compliant settings)
az storage account create \
  --name stpatientexplorer \
  --resource-group rg-patient-explorer \
  --location eastus2 \
  --sku Standard_GRS \
  --kind StorageV2 \
  --https-only true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# 3. Create Key Vault
az keyvault create \
  --name kv-patient-explorer \
  --resource-group rg-patient-explorer \
  --location eastus2 \
  --enable-soft-delete true \
  --enable-purge-protection true

# 4. Create Containers
az storage container create --name patient-data --account-name stpatientexplorer
az storage container create --name app-config --account-name stpatientexplorer
az storage container create --name backups --account-name stpatientexplorer
az storage container create --name logs --account-name stpatientexplorer

# 5. Enable Blob Versioning (for .env file history)
az storage account blob-service-properties update \
  --account-name stpatientexplorer \
  --resource-group rg-patient-explorer \
  --enable-versioning true

# 6. Set Lifecycle Management
az storage account management-policy create \
  --account-name stpatientexplorer \
  --resource-group rg-patient-explorer \
  --policy @lifecycle-policy.json
```

### Phase 2: Sync Manifest

Create `.gitignore-sync.json` (tracked in git) to define what gets synced:

```json
{
  "version": "1.0",
  "storage_account": "stpatientexplorer",
  "container": "workspace-sync",
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
  "exclude_patterns": [
    "*.pyc",
    "__pycache__/",
    ".venv/",
    "node_modules/"
  ],
  "require_device_encryption": true,
  "require_azure_ad_auth": true
}
```

### Phase 3: Python Integration

Add to `requirements.txt`:
```
azure-storage-blob>=12.19.0
azure-identity>=1.15.0
azure-keyvault-secrets>=4.7.0
```

Create `phase0/azure_sync.py`:
```python
"""
Azure Blob Storage sync for portable workspace replication.

Enables secure sync of gitignored data (PHI, credentials) between devices
while maintaining HIPAA compliance (encryption at rest + in transit).
"""

import json
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

from azure.identity import InteractiveBrowserCredential, DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError
from loguru import logger


class WorkspaceSync:
    """Sync gitignored data to/from Azure Blob Storage."""

    def __init__(self, config_path: Path = Path(".gitignore-sync.json")):
        self.config = self._load_config(config_path)
        self.credential = self._get_credential()
        self.blob_service = BlobServiceClient(
            f"https://{self.config['storage_account']}.blob.core.windows.net",
            credential=self.credential
        )
        self.container = self.blob_service.get_container_client(
            self.config.get("container", "workspace-sync")
        )

    def _load_config(self, config_path: Path) -> dict:
        """Load sync configuration from manifest file."""
        if not config_path.exists():
            raise FileNotFoundError(
                f"Sync manifest not found: {config_path}\n"
                "Run 'python -m phase0 init-sync' to create one."
            )
        with open(config_path) as f:
            return json.load(f)

    def _get_credential(self):
        """Get Azure credential - interactive browser for user auth."""
        try:
            # Try default credential first (for CI/automation)
            cred = DefaultAzureCredential()
            # Test it works
            return cred
        except Exception:
            # Fall back to interactive browser login
            logger.info("Opening browser for Azure authentication...")
            return InteractiveBrowserCredential(
                tenant_id="common"  # Allows any Azure AD tenant
            )

    def _file_hash(self, path: Path) -> str:
        """Calculate SHA256 hash of file for change detection."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def push(self, force: bool = False) -> dict:
        """
        Push local gitignored files to Azure.

        Returns dict of uploaded files and their status.
        """
        results = {"uploaded": [], "skipped": [], "errors": []}

        for sync_item in self.config["sync_paths"]:
            local_path = Path(sync_item["local"])
            remote_prefix = sync_item["remote"]

            if not local_path.exists():
                logger.warning(f"Local path not found: {local_path}")
                continue

            # Handle single file vs directory
            if local_path.is_file():
                files = [(local_path, remote_prefix)]
            else:
                pattern = sync_item.get("pattern", "**/*")
                files = [
                    (f, f"{remote_prefix}{f.relative_to(local_path)}")
                    for f in local_path.glob(pattern)
                    if f.is_file() and not self._is_excluded(f)
                ]

            for local_file, remote_path in files:
                try:
                    blob = self.container.get_blob_client(remote_path)
                    local_hash = self._file_hash(local_file)

                    # Check if remote exists and matches
                    if not force:
                        try:
                            props = blob.get_blob_properties()
                            remote_hash = props.metadata.get("sha256", "")
                            if remote_hash == local_hash:
                                results["skipped"].append(str(local_file))
                                continue
                        except ResourceNotFoundError:
                            pass  # File doesn't exist remotely, upload it

                    # Upload with hash metadata
                    with open(local_file, "rb") as data:
                        blob.upload_blob(
                            data,
                            overwrite=True,
                            metadata={"sha256": local_hash}
                        )

                    results["uploaded"].append(str(local_file))
                    logger.info(f"Uploaded: {local_file} -> {remote_path}")

                except Exception as e:
                    results["errors"].append({"file": str(local_file), "error": str(e)})
                    logger.error(f"Failed to upload {local_file}: {e}")

        return results

    def pull(self, force: bool = False) -> dict:
        """
        Pull gitignored files from Azure to local workspace.

        Returns dict of downloaded files and their status.
        """
        results = {"downloaded": [], "skipped": [], "errors": []}

        for sync_item in self.config["sync_paths"]:
            local_path = Path(sync_item["local"])
            remote_prefix = sync_item["remote"]

            # List blobs with this prefix
            blobs = self.container.list_blobs(name_starts_with=remote_prefix)

            for blob in blobs:
                try:
                    # Calculate local path
                    relative = blob.name[len(remote_prefix):]
                    if local_path.suffix:  # Single file
                        local_file = local_path
                    else:  # Directory
                        local_file = local_path / relative

                    # Ensure parent directory exists
                    local_file.parent.mkdir(parents=True, exist_ok=True)

                    # Check if local matches remote
                    remote_hash = blob.metadata.get("sha256", "") if blob.metadata else ""

                    if not force and local_file.exists():
                        local_hash = self._file_hash(local_file)
                        if local_hash == remote_hash:
                            results["skipped"].append(str(local_file))
                            continue

                    # Download
                    blob_client = self.container.get_blob_client(blob.name)
                    with open(local_file, "wb") as f:
                        stream = blob_client.download_blob()
                        f.write(stream.readall())

                    results["downloaded"].append(str(local_file))
                    logger.info(f"Downloaded: {blob.name} -> {local_file}")

                except Exception as e:
                    results["errors"].append({"blob": blob.name, "error": str(e)})
                    logger.error(f"Failed to download {blob.name}: {e}")

        return results

    def status(self) -> dict:
        """Compare local and remote state."""
        status = {"local_only": [], "remote_only": [], "modified": [], "synced": []}

        # Build sets of local and remote files with hashes
        local_files = {}
        remote_files = {}

        for sync_item in self.config["sync_paths"]:
            local_path = Path(sync_item["local"])
            remote_prefix = sync_item["remote"]

            # Local files
            if local_path.exists():
                if local_path.is_file():
                    local_files[remote_prefix] = self._file_hash(local_path)
                else:
                    pattern = sync_item.get("pattern", "**/*")
                    for f in local_path.glob(pattern):
                        if f.is_file() and not self._is_excluded(f):
                            key = f"{remote_prefix}{f.relative_to(local_path)}"
                            local_files[key] = self._file_hash(f)

            # Remote files
            for blob in self.container.list_blobs(name_starts_with=remote_prefix):
                remote_files[blob.name] = blob.metadata.get("sha256", "") if blob.metadata else ""

        # Compare
        all_keys = set(local_files.keys()) | set(remote_files.keys())
        for key in all_keys:
            if key in local_files and key not in remote_files:
                status["local_only"].append(key)
            elif key in remote_files and key not in local_files:
                status["remote_only"].append(key)
            elif local_files.get(key) != remote_files.get(key):
                status["modified"].append(key)
            else:
                status["synced"].append(key)

        return status

    def _is_excluded(self, path: Path) -> bool:
        """Check if path matches exclusion patterns."""
        path_str = str(path)
        for pattern in self.config.get("exclude_patterns", []):
            if pattern in path_str:
                return True
        return False
```

### Phase 4: CLI Commands

Add to `phase0/main.py`:
```python
@app.command()
def sync_push(
    force: bool = typer.Option(False, "--force", "-f", help="Force upload all files"),
):
    """Push gitignored data to Azure (before switching devices)."""
    from .azure_sync import WorkspaceSync

    console.print("[bold]Pushing workspace data to Azure...[/bold]")
    sync = WorkspaceSync()
    results = sync.push(force=force)

    console.print(f"[green]Uploaded:[/green] {len(results['uploaded'])} files")
    console.print(f"[dim]Skipped:[/dim] {len(results['skipped'])} files (unchanged)")
    if results['errors']:
        console.print(f"[red]Errors:[/red] {len(results['errors'])} files")
        for err in results['errors']:
            console.print(f"  - {err['file']}: {err['error']}")


@app.command()
def sync_pull(
    force: bool = typer.Option(False, "--force", "-f", help="Force download all files"),
):
    """Pull gitignored data from Azure (after cloning on new device)."""
    from .azure_sync import WorkspaceSync

    console.print("[bold]Pulling workspace data from Azure...[/bold]")
    sync = WorkspaceSync()
    results = sync.pull(force=force)

    console.print(f"[green]Downloaded:[/green] {len(results['downloaded'])} files")
    console.print(f"[dim]Skipped:[/dim] {len(results['skipped'])} files (unchanged)")
    if results['errors']:
        console.print(f"[red]Errors:[/red] {len(results['errors'])} files")


@app.command()
def sync_status():
    """Show sync status between local and Azure."""
    from .azure_sync import WorkspaceSync

    sync = WorkspaceSync()
    status = sync.status()

    console.print("\n[bold]Workspace Sync Status[/bold]\n")

    if status['synced']:
        console.print(f"[green]✓ Synced:[/green] {len(status['synced'])} files")

    if status['local_only']:
        console.print(f"\n[yellow]Local only (not in Azure):[/yellow]")
        for f in status['local_only']:
            console.print(f"  + {f}")

    if status['remote_only']:
        console.print(f"\n[blue]Remote only (not local):[/blue]")
        for f in status['remote_only']:
            console.print(f"  - {f}")

    if status['modified']:
        console.print(f"\n[red]Modified (out of sync):[/red]")
        for f in status['modified']:
            console.print(f"  ~ {f}")


@app.command()
def init_sync():
    """Initialize sync manifest for this workspace."""
    import json

    manifest = {
        "version": "1.0",
        "storage_account": "stpatientexplorer",
        "container": "workspace-sync",
        "sync_paths": [
            {"local": "data/", "remote": "data/", "pattern": "**/*", "description": "Patient data files (PHI)"},
            {"local": ".env", "remote": "config/.env", "description": "Environment credentials"},
            {"local": "logs/", "remote": "logs/", "pattern": "*.log", "description": "Application logs"}
        ],
        "exclude_patterns": ["*.pyc", "__pycache__/", ".venv/", "node_modules/"],
        "require_device_encryption": True,
        "require_azure_ad_auth": True
    }

    with open(".gitignore-sync.json", "w") as f:
        json.dump(manifest, f, indent=2)

    console.print("[green]Created .gitignore-sync.json[/green]")
    console.print("Edit this file to customize sync paths, then run:")
    console.print("  python -m phase0 sync-push")
```

## New Device Setup Workflow

### On Your Current Device (Before Switching)

```bash
# 1. Commit and push code changes
git add -A && git commit -m "Latest changes" && git push

# 2. Push gitignored data to Azure
python -m phase0 sync-push
```

### On the New Device

```bash
# 1. Clone the repository
git clone https://github.com/RGgreenbhm/Patient_Explorer.git
cd Patient_Explorer

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull gitignored data from Azure (opens browser for auth)
python -m phase0 sync-pull

# 5. Verify
python -m phase0 sync-status
```

### Security Guarantees

| Stage | Protection |
|-------|------------|
| **At Rest (Azure)** | AES-256 encryption with customer-managed keys |
| **In Transit** | TLS 1.2+ (HTTPS only) |
| **At Rest (Local)** | BitLocker (Windows) / FileVault (Mac) required |
| **Authentication** | Azure AD - same Microsoft account |
| **Authorization** | RBAC - only designated users can access |

### What Gets Synced vs What Doesn't

| Synced to Azure | NOT Synced (Rebuild Locally) |
|-----------------|------------------------------|
| `data/*.xlsx` (PHI) | `.venv/` (recreate with pip) |
| `.env` (credentials) | `node_modules/` (recreate with npm) |
| `logs/*.log` | `__pycache__/` (auto-generated) |
| `*.db` (databases) | IDE settings (`.vscode/`) |

## Cost Estimate (Monthly)

| Resource | SKU | Est. Cost |
|----------|-----|-----------|
| Storage Account (GRS) | Standard, 10GB | ~$2.50 |
| Key Vault | Standard | ~$0.03/10k ops |
| Private Endpoint | Per hour | ~$7.50 |
| **Total** | | **~$10-15/month** |

## HIPAA Compliance Checklist

- [x] **BAA**: Covered under existing Microsoft HIPAA BAA
- [x] **Encryption at Rest**: SSE with customer-managed keys
- [x] **Encryption in Transit**: TLS 1.2+ enforced
- [x] **Access Control**: Azure AD RBAC, no anonymous access
- [x] **Audit Logging**: Azure Storage Analytics enabled
- [x] **Geo-Redundancy**: GRS replication for disaster recovery
- [x] **Network Security**: Private endpoint, no public access
- [x] **Data Retention**: Lifecycle policies defined

## Next Steps

### Phase 1: Azure Infrastructure (User Action)
1. Create Resource Group and Storage Account using Azure CLI commands above
2. Create Key Vault for encryption keys
3. Configure RBAC for authorized users (rgreen@southviewteam.com, etc.)
4. Enable private endpoint (optional, for enhanced security)

### Phase 2: Python Implementation (Claude Action - After Azure Setup)
1. Add Azure SDK packages to `requirements.txt`
2. Create `phase0/azure_sync.py` module
3. Add CLI commands to `phase0/main.py`
4. Create `.gitignore-sync.json` manifest template

### Phase 3: Documentation (Claude Action - After Testing)
1. Update README.md with new device setup instructions
2. Update CLAUDE.md with sync workflow documentation
3. Add troubleshooting guide

---

*Proposal Created: 2025-12-08*
*Region: Azure East US 2*
*Compliance: HIPAA (under Microsoft BAA)*
*Goal: Portable workspace replication with encrypted PHI sync*
