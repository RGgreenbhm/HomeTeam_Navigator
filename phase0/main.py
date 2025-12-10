"""
Phase 0: Patient Consent Outreach Tool - CLI Entry Point

Usage:
    python -m phase0 load-patients data/patients.xlsx
    python -m phase0 match-spruce
    python -m phase0 init-sharepoint
    python -m phase0 status
"""

import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.table import Table

from . import __version__
from .excel_loader import load_patients_from_excel, preview_excel
from .models import ConsentRecord, ConsentStatus
from .spruce import SpruceClient
from .sharepoint import SharePointClient

# Load environment variables
load_dotenv()

# Configure logging - HIPAA safe: only errors to stderr, details to file
logger.remove()
# Only show warnings/errors to terminal (no PHI in error messages)
logger.add(sys.stderr, level="WARNING", format="{level}: {message}")

# Detailed logs go to file only (never displayed in terminal)
log_file = os.getenv("LOG_FILE", "logs/phase0.log")
if log_file:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger.add(log_file, rotation="10 MB", retention="30 days", level="DEBUG")

# CLI app
app = typer.Typer(
    name="phase0",
    help="Patient Consent Outreach Tool - Phase 0",
    add_completion=False,
)
console = Console()


@app.command()
def version():
    """Show version information."""
    console.print(f"Phase 0 Consent Tool v{__version__}")


@app.command("load-patients")
def load_patients(
    file_path: str = typer.Argument(..., help="Path to Excel file"),
    show_columns: bool = typer.Option(False, "--columns", "-c", help="Show column names only"),
):
    """Load and validate patients from Excel file (no PHI displayed)."""
    path = Path(file_path)

    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    if show_columns:
        # Safe: only show column headers, not data
        console.print(f"\n[bold]Columns in {path.name}[/bold]\n")
        df = preview_excel(path, rows=0)
        for i, col in enumerate(df.columns, 1):
            console.print(f"  {i}. {col}")
        console.print(f"\n[dim]Use these column names to verify mapping[/dim]")

    else:
        try:
            patients = load_patients_from_excel(path)
            console.print(f"\n[green]Successfully loaded {len(patients)} patients[/green]\n")

            # Aggregate statistics only - no PHI
            table = Table(title="Patient Data Summary (no PHI displayed)")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", justify="right")
            table.add_column("Percentage", justify="right")

            total = len(patients)
            with_phone = sum(1 for p in patients if p.phone)
            with_email = sum(1 for p in patients if p.email)
            apcm_eligible = sum(1 for p in patients if p.apcm_eligible)

            table.add_row("Total patients", str(total), "100%")
            table.add_row("With phone", str(with_phone), f"{with_phone/total*100:.1f}%")
            table.add_row("With email", str(with_email), f"{with_email/total*100:.1f}%")
            table.add_row("APCM eligible", str(apcm_eligible), f"{apcm_eligible/total*100:.1f}%")

            console.print(table)
            console.print("\n[dim]PHI is processed locally only - not displayed here[/dim]")

        except Exception as e:
            console.print(f"[red]Error loading patients: {e}[/red]")
            raise typer.Exit(1)


@app.command("init-sharepoint")
def init_sharepoint():
    """Initialize SharePoint consent tracking list."""
    console.print("\n[bold]Initializing SharePoint...[/bold]\n")

    try:
        client = SharePointClient()
        if client.create_consent_list():
            console.print("[green]SharePoint list created successfully![/green]")
        else:
            console.print("[yellow]SharePoint list creation failed or already exists[/yellow]")

    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print("\n[dim]Make sure these environment variables are set:")
        console.print("  SHAREPOINT_SITE_URL")
        console.print("  SHAREPOINT_CLIENT_ID")
        console.print("  SHAREPOINT_CLIENT_SECRET[/dim]")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("test-spruce")
def test_spruce():
    """Test Spruce API connection (no PHI displayed)."""
    console.print("\n[bold]Testing Spruce API connection...[/bold]\n")

    try:
        client = SpruceClient()
        if client.test_connection():
            console.print("[green]Spruce API connection successful![/green]")

            # Count contacts - no PHI displayed
            contacts = client.get_contacts()
            if contacts:
                # Aggregate statistics only
                with_phone = sum(1 for c in contacts if c.phone)
                with_email = sum(1 for c in contacts if c.email)
                with_name = sum(1 for c in contacts if c.full_name)

                table = Table(title="Spruce Contact Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Count", justify="right")

                table.add_row("Total contacts", str(len(contacts)))
                table.add_row("With name", str(with_name))
                table.add_row("With phone", str(with_phone))
                table.add_row("With email", str(with_email))

                console.print(table)
        else:
            console.print("[red]Spruce API connection failed[/red]")

    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print("\n[dim]Make sure SPRUCE_API_TOKEN is set in .env[/dim]")
        raise typer.Exit(1)

    except PermissionError as e:
        console.print(f"[red]Authentication failed: {e}[/red]")
        console.print("[dim]Check that your API token is valid and enabled[/dim]")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def status():
    """Show consent tracking status."""
    console.print("\n[bold]Consent Tracking Status[/bold]\n")

    try:
        client = SharePointClient()
        records = client.get_all_records()

        if not records:
            console.print("[yellow]No consent records found[/yellow]")
            return

        # Count by status
        status_counts = {}
        for status in ConsentStatus:
            count = sum(1 for r in records if r.status == status)
            status_counts[status.value] = count

        table = Table(title=f"Consent Status ({len(records)} total)")
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        for status, count in status_counts.items():
            pct = (count / len(records) * 100) if records else 0
            color = {
                "consented": "green",
                "declined": "red",
                "pending": "yellow",
                "contacted": "blue",
                "no_response": "dim",
            }.get(status, "white")
            table.add_row(
                f"[{color}]{status}[/{color}]",
                str(count),
                f"{pct:.1f}%"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Is SharePoint configured? Run 'init-sharepoint' first.[/dim]")
        raise typer.Exit(1)


@app.command("import-to-sharepoint")
def import_to_sharepoint(
    file_path: str = typer.Argument(..., help="Path to Excel file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without importing"),
):
    """Import patients from Excel to SharePoint consent list (no PHI displayed)."""
    path = Path(file_path)

    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    try:
        patients = load_patients_from_excel(path)
        console.print(f"\n[bold]Loaded {len(patients)} patients from Excel[/bold]\n")

        if dry_run:
            console.print("[yellow]Dry run - validating data, no changes will be made[/yellow]\n")

            # Aggregate validation only - no PHI
            valid = sum(1 for p in patients if p.mrn and p.last_name)
            with_phone = sum(1 for p in patients if p.phone)
            with_email = sum(1 for p in patients if p.email)

            table = Table(title="Validation Summary (no PHI displayed)")
            table.add_column("Check", style="cyan")
            table.add_column("Result", justify="right")

            table.add_row("Total records", str(len(patients)))
            table.add_row("Valid (has MRN + name)", f"[green]{valid}[/green]")
            table.add_row("Invalid (missing required)", f"[red]{len(patients) - valid}[/red]")
            table.add_row("With phone (for SMS outreach)", str(with_phone))
            table.add_row("With email (for DocuSign)", str(with_email))

            console.print(table)
            console.print("\n[dim]Run without --dry-run to import[/dim]")
            return

        # Actually import
        client = SharePointClient()
        success = 0
        failed = 0

        with console.status("Importing to SharePoint..."):
            for patient in patients:
                record = ConsentRecord(
                    mrn=patient.mrn,
                    patient_name=patient.full_name,
                    status=ConsentStatus.PENDING,
                )

                if client.add_consent_record(record):
                    success += 1
                else:
                    failed += 1

        console.print(f"\n[green]Imported {success} records[/green]")
        if failed:
            console.print(f"[red]Failed: {failed} records[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("match-spruce")
def match_spruce(
    file_path: str = typer.Argument(..., help="Path to patient Excel file"),
    output: str = typer.Option("data/match_results.csv", "--output", "-o", help="Output file path"),
):
    """Match patients against Spruce contacts (results written to file, no PHI displayed)."""
    from datetime import datetime
    import csv

    path = Path(file_path)
    output_path = Path(output)

    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load patients
        console.print("\n[bold]Loading patient data...[/bold]")
        patients = load_patients_from_excel(path)
        console.print(f"  Loaded {len(patients)} patients")

        # Load Spruce contacts
        console.print("\n[bold]Fetching Spruce contacts...[/bold]")
        spruce_client = SpruceClient()
        spruce_contacts = spruce_client.get_contacts()
        console.print(f"  Found {len(spruce_contacts)} Spruce contacts")

        # Build lookup indexes for matching
        console.print("\n[bold]Matching patients to Spruce contacts...[/bold]")

        # Index by phone (normalized to first 10 digits)
        # Note: Excel data has 11 digits with trailing extra digit, so use first 10
        phone_index = {}
        for contact in spruce_contacts:
            if contact.phone:
                digits = "".join(c for c in contact.phone if c.isdigit())
                if len(digits) >= 10:
                    digits = digits[:10]  # First 10 digits
                    phone_index[digits] = contact

        # Index by name (lowercase)
        name_index = {}
        for contact in spruce_contacts:
            if contact.full_name:
                key = contact.full_name.lower().strip()
                name_index[key] = contact

        # Match patients
        matched = 0
        unmatched = 0
        results = []

        for patient in patients:
            match_found = False
            match_method = ""
            spruce_id = ""

            # Try phone match first (use first 10 digits)
            if patient.phone:
                digits = "".join(c for c in patient.phone if c.isdigit())
                if len(digits) >= 10:
                    digits = digits[:10]  # First 10 digits
                    if digits in phone_index:
                        match_found = True
                        match_method = "phone"
                        spruce_id = phone_index[digits].spruce_id

            # Try name match if no phone match
            if not match_found and patient.full_name:
                key = patient.full_name.lower().strip()
                if key in name_index:
                    match_found = True
                    match_method = "name"
                    spruce_id = name_index[key].spruce_id

            if match_found:
                matched += 1
            else:
                unmatched += 1

            results.append({
                "mrn": patient.mrn,
                "matched": match_found,
                "match_method": match_method,
                "spruce_id": spruce_id,
            })

        # Write results to CSV (PHI stays in file, not terminal)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["mrn", "matched", "match_method", "spruce_id"])
            writer.writeheader()
            writer.writerows(results)

        # Display aggregate statistics only
        table = Table(title="Matching Results (no PHI displayed)")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        total = len(patients)
        table.add_row("Total patients", str(total), "100%")
        table.add_row("[green]Matched to Spruce[/green]", str(matched), f"{matched/total*100:.1f}%")
        table.add_row("[yellow]Not matched[/yellow]", str(unmatched), f"{unmatched/total*100:.1f}%")

        # Match method breakdown
        phone_matches = sum(1 for r in results if r["match_method"] == "phone")
        name_matches = sum(1 for r in results if r["match_method"] == "name")
        table.add_row("  - by phone", str(phone_matches), "")
        table.add_row("  - by name", str(name_matches), "")

        console.print(table)
        console.print(f"\n[green]Results written to: {output_path}[/green]")
        console.print("[dim]Review the CSV file locally for patient-level details[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("init-sync")
def init_sync(
    storage_account: str = typer.Option(
        "stgreenclinicworkspace",
        "--storage-account", "-s",
        help="Azure storage account name"
    ),
):
    """Initialize sync manifest for Azure workspace backup."""
    from .azure_sync import create_default_manifest
    import json

    manifest_path = Path(".gitignore-sync.json")

    if manifest_path.exists():
        console.print(f"[yellow]Manifest already exists: {manifest_path}[/yellow]")
        if not typer.confirm("Overwrite?"):
            raise typer.Exit(0)

    manifest = create_default_manifest(storage_account)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    console.print(f"[green]Created {manifest_path}[/green]")
    console.print("\nSync paths configured:")
    for item in manifest["sync_paths"]:
        console.print(f"  - {item['local']} -> {item['remote']}")

    console.print("\n[dim]Edit this file to customize, then run:[/dim]")
    console.print("  python -m phase0 sync-push")


@app.command("sync-push")
def sync_push(
    force: bool = typer.Option(False, "--force", "-f", help="Force upload all files"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Use browser login"),
):
    """Push gitignored data to Azure (before switching devices)."""
    from .azure_sync import WorkspaceSync

    console.print("\n[bold]Pushing workspace data to Azure...[/bold]\n")

    try:
        sync = WorkspaceSync(interactive=interactive)
        results = sync.push(force=force)

        console.print(f"[green]Uploaded:[/green] {len(results['uploaded'])} files")
        for f in results['uploaded']:
            console.print(f"  + {f}")

        console.print(f"[dim]Skipped:[/dim] {len(results['skipped'])} files (unchanged)")

        if results['errors']:
            console.print(f"[red]Errors:[/red] {len(results['errors'])} files")
            for err in results['errors']:
                console.print(f"  - {err['file']}: {err['error']}")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("sync-pull")
def sync_pull(
    force: bool = typer.Option(False, "--force", "-f", help="Force download all files"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Use browser login"),
):
    """Pull gitignored data from Azure (after cloning on new device)."""
    from .azure_sync import WorkspaceSync

    console.print("\n[bold]Pulling workspace data from Azure...[/bold]\n")

    try:
        sync = WorkspaceSync(interactive=interactive)
        results = sync.pull(force=force)

        console.print(f"[green]Downloaded:[/green] {len(results['downloaded'])} files")
        for f in results['downloaded']:
            console.print(f"  + {f}")

        console.print(f"[dim]Skipped:[/dim] {len(results['skipped'])} files (unchanged)")

        if results['errors']:
            console.print(f"[red]Errors:[/red] {len(results['errors'])} files")
            for err in results['errors']:
                console.print(f"  - {err.get('blob', err.get('path', 'unknown'))}: {err['error']}")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("sync-status")
def sync_status(
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Use browser login"),
):
    """Show sync status between local and Azure."""
    from .azure_sync import WorkspaceSync

    console.print("\n[bold]Workspace Sync Status[/bold]\n")

    try:
        sync = WorkspaceSync(interactive=interactive)
        status = sync.status()

        if status['synced']:
            console.print(f"[green]Synced:[/green] {len(status['synced'])} files")

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

        # Summary
        total = sum(len(v) for v in status.values())
        if total == 0:
            console.print("[dim]No files configured for sync[/dim]")
        elif not status['local_only'] and not status['remote_only'] and not status['modified']:
            console.print("\n[green]All files in sync![/green]")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
