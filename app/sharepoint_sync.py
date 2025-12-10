"""SharePoint File Sync for Patient Explorer.

Provides session-based file synchronization with SharePoint for HIPAA-compliant
data sharing between users.

This module supports TWO sync methods:
1. **File Path Mode**: Uses mapped SharePoint drives (S:\PatientExplorer)
2. **Graph API Mode**: Uses Microsoft Graph API with OAuth (no drive mapping needed)

The module automatically uses Graph API if the user is authenticated with
Microsoft OAuth, otherwise falls back to file path mode.

Usage:
    from sharepoint_sync import (
        download_from_sharepoint,
        upload_to_sharepoint,
        get_sync_status,
        is_sync_enabled,
        # Graph API functions
        list_sharepoint_sites,
        list_site_drives,
        list_drive_folders,
        configure_graph_sync,
    )

    # At session start
    if is_sync_enabled():
        success, message = download_from_sharepoint()

    # At session end
    if is_sync_enabled():
        success, message = upload_to_sharepoint()

    # With Graph API - browse and select SharePoint folder
    sites = list_sharepoint_sites()
    drives = list_site_drives(site_id)
    folders = list_drive_folders(drive_id, folder_path)
    configure_graph_sync(site_id, drive_id, folder_path)
"""

import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
import json

from loguru import logger

# Sync configuration file location
SYNC_CONFIG_FILE = Path(__file__).parent.parent / "data" / "sync_config.json"

# Default paths
DEFAULT_LOCAL_DB = Path(__file__).parent.parent / "data" / "patients.db"


def _get_config() -> Dict[str, Any]:
    """Load sync configuration from file."""
    if SYNC_CONFIG_FILE.exists():
        try:
            with open(SYNC_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading sync config: {e}")
    return {}


def _save_config(config: Dict[str, Any]) -> bool:
    """Save sync configuration to file."""
    try:
        SYNC_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SYNC_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving sync config: {e}")
        return False


def _get_file_hash(file_path: Path) -> Optional[str]:
    """Calculate MD5 hash of a file for integrity checking."""
    if not file_path.exists():
        return None
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return None


def is_sync_enabled() -> bool:
    """Check if SharePoint sync is enabled.

    Returns:
        True if sync is configured and enabled
    """
    config = _get_config()
    if not config.get("enabled", False):
        return False

    sharepoint_path = config.get("sharepoint_path")
    if not sharepoint_path:
        return False

    # Check if the path exists
    return Path(sharepoint_path).exists()


def get_sharepoint_path() -> Optional[str]:
    """Get the configured SharePoint path.

    Returns:
        SharePoint path string or None if not configured
    """
    config = _get_config()
    return config.get("sharepoint_path")


def set_sharepoint_path(path: str) -> Tuple[bool, str]:
    """Set and validate the SharePoint sync path.

    Args:
        path: Path to SharePoint folder (can be mapped drive like S:\\PatientExplorer)

    Returns:
        Tuple of (success, message)
    """
    sharepoint_path = Path(path)

    # Validate path exists
    if not sharepoint_path.exists():
        return False, f"Path does not exist: {path}"

    # Check if it's a directory
    if not sharepoint_path.is_dir():
        return False, f"Path is not a directory: {path}"

    # Try to write a test file to verify access
    test_file = sharepoint_path / ".patient_explorer_test"
    try:
        test_file.write_text("test")
        test_file.unlink()
    except PermissionError:
        return False, f"No write permission to: {path}"
    except Exception as e:
        return False, f"Error testing write access: {e}"

    # Save configuration
    config = _get_config()
    config["sharepoint_path"] = str(sharepoint_path)
    config["enabled"] = True
    config["configured_at"] = datetime.now().isoformat()

    if _save_config(config):
        logger.info(f"SharePoint sync path configured: {path}")
        return True, f"SharePoint sync configured: {path}"
    else:
        return False, "Failed to save configuration"


def enable_sync(enabled: bool = True) -> bool:
    """Enable or disable SharePoint sync.

    Args:
        enabled: True to enable, False to disable

    Returns:
        True if successful
    """
    config = _get_config()
    config["enabled"] = enabled
    return _save_config(config)


def get_sync_status() -> Dict[str, Any]:
    """Get current sync status and history.

    Returns:
        Dictionary with sync status information:
        - enabled: bool
        - sharepoint_path: str or None
        - last_download: datetime string or None
        - last_upload: datetime string or None
        - last_download_user: str or None
        - last_upload_user: str or None
        - local_hash: str or None
        - remote_hash: str or None
        - in_sync: bool
    """
    config = _get_config()

    status = {
        "enabled": config.get("enabled", False),
        "sharepoint_path": config.get("sharepoint_path"),
        "last_download": config.get("last_download"),
        "last_upload": config.get("last_upload"),
        "last_download_user": config.get("last_download_user"),
        "last_upload_user": config.get("last_upload_user"),
        "local_hash": None,
        "remote_hash": None,
        "in_sync": False,
        "local_exists": False,
        "remote_exists": False,
    }

    # Check local database
    local_db = DEFAULT_LOCAL_DB
    if local_db.exists():
        status["local_exists"] = True
        status["local_hash"] = _get_file_hash(local_db)
        status["local_size"] = local_db.stat().st_size
        status["local_modified"] = datetime.fromtimestamp(
            local_db.stat().st_mtime
        ).isoformat()

    # Check remote database
    sharepoint_path = config.get("sharepoint_path")
    if sharepoint_path:
        remote_db = Path(sharepoint_path) / "patients.db"
        if remote_db.exists():
            status["remote_exists"] = True
            status["remote_hash"] = _get_file_hash(remote_db)
            status["remote_size"] = remote_db.stat().st_size
            status["remote_modified"] = datetime.fromtimestamp(
                remote_db.stat().st_mtime
            ).isoformat()

    # Check if in sync
    if status["local_hash"] and status["remote_hash"]:
        status["in_sync"] = status["local_hash"] == status["remote_hash"]

    return status


def download_from_sharepoint(
    username: Optional[str] = None,
    backup_local: bool = True,
) -> Tuple[bool, str]:
    """Download database from SharePoint to local.

    Args:
        username: Username performing the download (for audit)
        backup_local: If True, backup existing local file before overwriting

    Returns:
        Tuple of (success, message)
    """
    config = _get_config()

    if not config.get("enabled", False):
        return False, "SharePoint sync is not enabled"

    sharepoint_path = config.get("sharepoint_path")
    if not sharepoint_path:
        return False, "SharePoint path not configured"

    remote_db = Path(sharepoint_path) / "patients.db"
    local_db = DEFAULT_LOCAL_DB

    # Check if remote file exists
    if not remote_db.exists():
        return False, f"Remote database not found: {remote_db}"

    try:
        # Backup local file if it exists
        if backup_local and local_db.exists():
            backup_path = local_db.with_suffix(
                f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            shutil.copy2(local_db, backup_path)
            logger.info(f"Backed up local database to: {backup_path}")

        # Copy from SharePoint
        shutil.copy2(remote_db, local_db)

        # Update config with download timestamp
        config["last_download"] = datetime.now().isoformat()
        config["last_download_user"] = username or "unknown"
        config["last_download_hash"] = _get_file_hash(local_db)
        _save_config(config)

        file_size = local_db.stat().st_size / 1024  # KB
        logger.info(f"Downloaded database from SharePoint ({file_size:.1f} KB)")

        return True, f"Downloaded database from SharePoint ({file_size:.1f} KB)"

    except PermissionError:
        return False, "Permission denied accessing SharePoint folder"
    except Exception as e:
        logger.error(f"Error downloading from SharePoint: {e}")
        return False, f"Download failed: {str(e)}"


def upload_to_sharepoint(
    username: Optional[str] = None,
    backup_remote: bool = True,
) -> Tuple[bool, str]:
    """Upload local database to SharePoint.

    Args:
        username: Username performing the upload (for audit)
        backup_remote: If True, backup existing remote file before overwriting

    Returns:
        Tuple of (success, message)
    """
    config = _get_config()

    if not config.get("enabled", False):
        return False, "SharePoint sync is not enabled"

    sharepoint_path = config.get("sharepoint_path")
    if not sharepoint_path:
        return False, "SharePoint path not configured"

    local_db = DEFAULT_LOCAL_DB
    remote_db = Path(sharepoint_path) / "patients.db"

    # Check if local file exists
    if not local_db.exists():
        return False, f"Local database not found: {local_db}"

    try:
        # Backup remote file if it exists
        if backup_remote and remote_db.exists():
            backup_path = remote_db.with_suffix(
                f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            shutil.copy2(remote_db, backup_path)
            logger.info(f"Backed up remote database to: {backup_path}")

        # Ensure SharePoint directory exists
        Path(sharepoint_path).mkdir(parents=True, exist_ok=True)

        # Copy to SharePoint
        shutil.copy2(local_db, remote_db)

        # Update config with upload timestamp
        config["last_upload"] = datetime.now().isoformat()
        config["last_upload_user"] = username or "unknown"
        config["last_upload_hash"] = _get_file_hash(local_db)
        _save_config(config)

        file_size = local_db.stat().st_size / 1024  # KB
        logger.info(f"Uploaded database to SharePoint ({file_size:.1f} KB)")

        return True, f"Uploaded database to SharePoint ({file_size:.1f} KB)"

    except PermissionError:
        return False, "Permission denied accessing SharePoint folder"
    except Exception as e:
        logger.error(f"Error uploading to SharePoint: {e}")
        return False, f"Upload failed: {str(e)}"


def get_sync_conflicts() -> Optional[Dict[str, Any]]:
    """Check for potential sync conflicts.

    Returns:
        Dictionary with conflict information, or None if no conflicts
    """
    status = get_sync_status()

    if not status["local_exists"] or not status["remote_exists"]:
        return None

    if status["in_sync"]:
        return None

    # Files differ - potential conflict
    return {
        "local_modified": status.get("local_modified"),
        "remote_modified": status.get("remote_modified"),
        "local_size": status.get("local_size"),
        "remote_size": status.get("remote_size"),
        "last_upload": status.get("last_upload"),
        "last_upload_user": status.get("last_upload_user"),
        "message": "Local and remote databases differ. Choose which version to keep.",
    }


def cleanup_old_backups(keep_count: int = 5) -> int:
    """Remove old backup files, keeping the most recent ones.

    Args:
        keep_count: Number of backups to keep

    Returns:
        Number of files deleted
    """
    deleted = 0

    # Clean local backups
    local_dir = DEFAULT_LOCAL_DB.parent
    local_backups = sorted(
        local_dir.glob("patients.backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for backup in local_backups[keep_count:]:
        try:
            backup.unlink()
            deleted += 1
            logger.info(f"Deleted old backup: {backup}")
        except Exception as e:
            logger.warning(f"Could not delete backup {backup}: {e}")

    # Clean remote backups if configured
    config = _get_config()
    sharepoint_path = config.get("sharepoint_path")
    if sharepoint_path:
        remote_dir = Path(sharepoint_path)
        remote_backups = sorted(
            remote_dir.glob("patients.backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for backup in remote_backups[keep_count:]:
            try:
                backup.unlink()
                deleted += 1
                logger.info(f"Deleted old remote backup: {backup}")
            except Exception as e:
                logger.warning(f"Could not delete remote backup {backup}: {e}")

    return deleted


# =============================================================================
# Graph API Sync Functions
# =============================================================================

def _get_graph_client():
    """Get the delegated Graph client if user is authenticated.

    Returns:
        DelegatedGraphClient or None
    """
    try:
        from ms_oauth import get_user_graph_client, is_user_authenticated

        if is_user_authenticated():
            return get_user_graph_client()
    except ImportError:
        pass
    return None


def is_graph_sync_available() -> bool:
    """Check if Graph API sync is available (user authenticated with MS).

    Returns:
        True if user is authenticated with Microsoft
    """
    try:
        from ms_oauth import is_user_authenticated
        return is_user_authenticated()
    except ImportError:
        return False


def get_sync_mode() -> str:
    """Get the current sync mode.

    Returns:
        'graph' if using Graph API, 'file_path' if using mapped drives, 'none' if not configured
    """
    config = _get_config()

    # Check if Graph sync is configured
    if config.get("graph_sync") and is_graph_sync_available():
        return "graph"

    # Check if file path sync is configured
    if config.get("sharepoint_path"):
        return "file_path"

    return "none"


def list_sharepoint_sites() -> List[Dict[str, Any]]:
    """List SharePoint sites the user has access to.

    Requires Microsoft OAuth authentication.

    Returns:
        List of site dicts with id, name, webUrl
    """
    client = _get_graph_client()
    if not client:
        return []

    try:
        sites = client.list_sites()
        return [
            {
                "id": site.get("id"),
                "name": site.get("displayName") or site.get("name"),
                "webUrl": site.get("webUrl"),
            }
            for site in sites
        ]
    except Exception as e:
        logger.error(f"Error listing SharePoint sites: {e}")
        return []


def list_site_drives(site_id: str) -> List[Dict[str, Any]]:
    """List document libraries (drives) in a SharePoint site.

    Args:
        site_id: SharePoint site ID

    Returns:
        List of drive dicts with id, name, webUrl
    """
    client = _get_graph_client()
    if not client:
        return []

    try:
        drives = client.list_site_drives(site_id)
        return [
            {
                "id": drive.get("id"),
                "name": drive.get("name"),
                "webUrl": drive.get("webUrl"),
                "driveType": drive.get("driveType"),
            }
            for drive in drives
        ]
    except Exception as e:
        logger.error(f"Error listing drives: {e}")
        return []


def list_drive_folders(
    drive_id: str,
    folder_path: str = "root",
) -> List[Dict[str, Any]]:
    """List folders in a SharePoint drive.

    Args:
        drive_id: Drive ID
        folder_path: Folder path (default "root" for top level)

    Returns:
        List of folder dicts with id, name, path
    """
    client = _get_graph_client()
    if not client:
        return []

    try:
        items = client.list_drive_items(drive_id, folder_path)
        folders = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "path": item.get("parentReference", {}).get("path", "") + "/" + item.get("name"),
                "isFolder": "folder" in item,
                "size": item.get("size", 0),
            }
            for item in items
            if "folder" in item  # Only folders
        ]
        return folders
    except Exception as e:
        logger.error(f"Error listing folders: {e}")
        return []


def list_drive_items(
    drive_id: str,
    folder_path: str = "root",
) -> List[Dict[str, Any]]:
    """List all items (files and folders) in a SharePoint drive folder.

    Args:
        drive_id: Drive ID
        folder_path: Folder path (default "root" for top level)

    Returns:
        List of item dicts
    """
    client = _get_graph_client()
    if not client:
        return []

    try:
        items = client.list_drive_items(drive_id, folder_path)
        return [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "isFolder": "folder" in item,
                "size": item.get("size", 0),
                "lastModified": item.get("lastModifiedDateTime"),
            }
            for item in items
        ]
    except Exception as e:
        logger.error(f"Error listing items: {e}")
        return []


def configure_graph_sync(
    site_id: str,
    drive_id: str,
    folder_path: str,
    site_name: str = "",
    drive_name: str = "",
) -> Tuple[bool, str]:
    """Configure SharePoint sync using Graph API.

    Args:
        site_id: SharePoint site ID
        drive_id: Document library (drive) ID
        folder_path: Folder path within the drive (e.g., "PatientExplorer")
        site_name: Display name of the site
        drive_name: Display name of the drive

    Returns:
        Tuple of (success, message)
    """
    config = _get_config()

    config["graph_sync"] = {
        "site_id": site_id,
        "drive_id": drive_id,
        "folder_path": folder_path,
        "site_name": site_name,
        "drive_name": drive_name,
        "configured_at": datetime.now().isoformat(),
    }
    config["enabled"] = True
    config["sync_mode"] = "graph"

    if _save_config(config):
        logger.info(f"Graph sync configured: {site_name}/{drive_name}/{folder_path}")
        return True, f"Configured sync to: {site_name} / {drive_name} / {folder_path}"
    else:
        return False, "Failed to save configuration"


def get_graph_sync_config() -> Optional[Dict[str, Any]]:
    """Get the Graph API sync configuration.

    Returns:
        Graph sync config dict or None if not configured
    """
    config = _get_config()
    return config.get("graph_sync")


def download_from_sharepoint_graph(
    username: Optional[str] = None,
    backup_local: bool = True,
) -> Tuple[bool, str]:
    """Download database from SharePoint using Graph API.

    Args:
        username: Username performing the download (for audit)
        backup_local: If True, backup existing local file before overwriting

    Returns:
        Tuple of (success, message)
    """
    client = _get_graph_client()
    if not client:
        return False, "Not authenticated with Microsoft. Please sign in first."

    config = _get_config()
    graph_config = config.get("graph_sync")

    if not graph_config:
        return False, "Graph sync not configured. Please select a SharePoint folder."

    drive_id = graph_config.get("drive_id")
    folder_path = graph_config.get("folder_path", "")
    file_path = f"{folder_path}/patients.db" if folder_path else "patients.db"

    local_db = DEFAULT_LOCAL_DB

    try:
        # Backup local file if it exists
        if backup_local and local_db.exists():
            backup_path = local_db.with_suffix(
                f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            shutil.copy2(local_db, backup_path)
            logger.info(f"Backed up local database to: {backup_path}")

        # Download from SharePoint
        content = client.download_file(drive_id, file_path)

        # Ensure local directory exists
        local_db.parent.mkdir(parents=True, exist_ok=True)

        # Write to local file
        with open(local_db, "wb") as f:
            f.write(content)

        # Update config with download timestamp
        config["last_download"] = datetime.now().isoformat()
        config["last_download_user"] = username or "unknown"
        config["last_download_hash"] = _get_file_hash(local_db)
        _save_config(config)

        file_size = len(content) / 1024  # KB
        logger.info(f"Downloaded database via Graph API ({file_size:.1f} KB)")

        return True, f"Downloaded database from SharePoint ({file_size:.1f} KB)"

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "itemNotFound" in error_msg:
            return False, f"Database file not found on SharePoint at: {file_path}"
        logger.error(f"Error downloading via Graph API: {e}")
        return False, f"Download failed: {error_msg}"


def upload_to_sharepoint_graph(
    username: Optional[str] = None,
) -> Tuple[bool, str]:
    """Upload local database to SharePoint using Graph API.

    Args:
        username: Username performing the upload (for audit)

    Returns:
        Tuple of (success, message)
    """
    client = _get_graph_client()
    if not client:
        return False, "Not authenticated with Microsoft. Please sign in first."

    config = _get_config()
    graph_config = config.get("graph_sync")

    if not graph_config:
        return False, "Graph sync not configured. Please select a SharePoint folder."

    drive_id = graph_config.get("drive_id")
    folder_path = graph_config.get("folder_path", "")

    local_db = DEFAULT_LOCAL_DB

    if not local_db.exists():
        return False, f"Local database not found: {local_db}"

    try:
        # Read local file
        with open(local_db, "rb") as f:
            content = f.read()

        # Upload to SharePoint
        client.upload_file(drive_id, folder_path, "patients.db", content)

        # Update config with upload timestamp
        config["last_upload"] = datetime.now().isoformat()
        config["last_upload_user"] = username or "unknown"
        config["last_upload_hash"] = _get_file_hash(local_db)
        _save_config(config)

        file_size = len(content) / 1024  # KB
        logger.info(f"Uploaded database via Graph API ({file_size:.1f} KB)")

        return True, f"Uploaded database to SharePoint ({file_size:.1f} KB)"

    except Exception as e:
        logger.error(f"Error uploading via Graph API: {e}")
        return False, f"Upload failed: {str(e)}"


# =============================================================================
# Unified Sync Functions (auto-select mode)
# =============================================================================

def download_from_sharepoint_auto(
    username: Optional[str] = None,
    backup_local: bool = True,
) -> Tuple[bool, str]:
    """Download database from SharePoint (auto-selects sync mode).

    Uses Graph API if available and configured, otherwise falls back to file path.

    Args:
        username: Username performing the download (for audit)
        backup_local: If True, backup existing local file before overwriting

    Returns:
        Tuple of (success, message)
    """
    mode = get_sync_mode()

    if mode == "graph":
        return download_from_sharepoint_graph(username, backup_local)
    elif mode == "file_path":
        return download_from_sharepoint(username, backup_local)
    else:
        return False, "SharePoint sync not configured"


def upload_to_sharepoint_auto(
    username: Optional[str] = None,
    backup_remote: bool = True,
) -> Tuple[bool, str]:
    """Upload database to SharePoint (auto-selects sync mode).

    Uses Graph API if available and configured, otherwise falls back to file path.

    Args:
        username: Username performing the upload (for audit)
        backup_remote: If True, backup existing remote file before overwriting (file path mode only)

    Returns:
        Tuple of (success, message)
    """
    mode = get_sync_mode()

    if mode == "graph":
        return upload_to_sharepoint_graph(username)
    elif mode == "file_path":
        return upload_to_sharepoint(username, backup_remote)
    else:
        return False, "SharePoint sync not configured"


def get_sync_status_extended() -> Dict[str, Any]:
    """Get extended sync status including Graph API info.

    Returns:
        Dictionary with sync status information including mode and Graph config
    """
    status = get_sync_status()

    # Add mode info
    status["sync_mode"] = get_sync_mode()
    status["graph_available"] = is_graph_sync_available()

    # Add Graph config if available
    graph_config = get_graph_sync_config()
    if graph_config:
        status["graph_config"] = {
            "site_name": graph_config.get("site_name"),
            "drive_name": graph_config.get("drive_name"),
            "folder_path": graph_config.get("folder_path"),
        }

    return status
