"""
Azure Blob Storage sync for portable workspace replication.

Enables secure sync of gitignored data (PHI, credentials) between devices
while maintaining HIPAA compliance (encryption at rest + in transit).

Usage:
    python -m phase0 init-sync      # Create sync manifest
    python -m phase0 sync-push      # Upload to Azure
    python -m phase0 sync-pull      # Download from Azure
    python -m phase0 sync-status    # Check sync state
"""

import json
import hashlib
from pathlib import Path
from typing import Optional

from azure.identity import (
    DefaultAzureCredential,
    InteractiveBrowserCredential,
    AzureCliCredential,
    ChainedTokenCredential,
)
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from loguru import logger


class WorkspaceSync:
    """Sync gitignored data to/from Azure Blob Storage."""

    def __init__(self, config_path: Optional[Path] = None, interactive: bool = False):
        """
        Initialize workspace sync client.

        Args:
            config_path: Path to sync manifest (defaults to .gitignore-sync.json)
            interactive: If True, immediately use interactive browser auth
        """
        if config_path is None:
            config_path = Path(".gitignore-sync.json")

        self.config = self._load_config(config_path)
        self.credential = self._get_credential(interactive)
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
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)

    def _get_credential(self, interactive: bool = False):
        """
        Get Azure credential with smart fallback.

        Credential chain:
        1. If interactive=True, go straight to browser login
        2. Try DefaultAzureCredential (includes az login, env vars, managed identity)
        3. Fall back to interactive browser login
        """
        if interactive:
            logger.info("Using interactive browser authentication...")
            return InteractiveBrowserCredential(
                tenant_id="common"  # Allows any Azure AD tenant
            )

        # Try default credential chain first
        logger.debug("Attempting DefaultAzureCredential...")
        return DefaultAzureCredential(
            exclude_interactive_browser_credential=False,
            exclude_shared_token_cache_credential=False,
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

        Args:
            force: If True, upload all files regardless of hash match

        Returns:
            Dict with uploaded, skipped, and errors lists
        """
        results = {"uploaded": [], "skipped": [], "errors": []}

        for sync_item in self.config.get("sync_paths", []):
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
                    (f, f"{remote_prefix}{f.relative_to(local_path).as_posix()}")
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
                            remote_hash = props.metadata.get("sha256", "") if props.metadata else ""
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

        Args:
            force: If True, download all files regardless of hash match

        Returns:
            Dict with downloaded, skipped, and errors lists
        """
        results = {"downloaded": [], "skipped": [], "errors": []}

        for sync_item in self.config.get("sync_paths", []):
            local_path = Path(sync_item["local"])
            remote_prefix = sync_item["remote"]

            # List blobs with this prefix
            try:
                blobs = list(self.container.list_blobs(
                    name_starts_with=remote_prefix,
                    include=["metadata"]
                ))
            except Exception as e:
                results["errors"].append({"path": remote_prefix, "error": str(e)})
                continue

            for blob in blobs:
                try:
                    # Calculate local path
                    relative = blob.name[len(remote_prefix):]
                    if not relative:  # Single file case
                        local_file = local_path
                    elif local_path.suffix:  # Single file mapping
                        local_file = local_path
                    else:  # Directory mapping
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
        """
        Compare local and remote state.

        Returns:
            Dict with local_only, remote_only, modified, and synced lists
        """
        status = {"local_only": [], "remote_only": [], "modified": [], "synced": []}

        # Build sets of local and remote files with hashes
        local_files = {}
        remote_files = {}

        for sync_item in self.config.get("sync_paths", []):
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
                            key = f"{remote_prefix}{f.relative_to(local_path).as_posix()}"
                            local_files[key] = self._file_hash(f)

            # Remote files
            try:
                for blob in self.container.list_blobs(
                    name_starts_with=remote_prefix,
                    include=["metadata"]
                ):
                    remote_files[blob.name] = blob.metadata.get("sha256", "") if blob.metadata else ""
            except Exception as e:
                logger.warning(f"Failed to list remote files for {remote_prefix}: {e}")

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


def create_default_manifest(storage_account: str = "stgreenclinicworkspace") -> dict:
    """
    Create a default sync manifest.

    Args:
        storage_account: Azure storage account name

    Returns:
        Manifest dictionary
    """
    return {
        "version": "1.0",
        "storage_account": storage_account,
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
            "node_modules/",
            "*.tmp",
            "~$*"  # Office temp files
        ],
        "require_device_encryption": True,
        "require_azure_ad_auth": True
    }
