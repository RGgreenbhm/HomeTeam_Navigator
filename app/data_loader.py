"""Unified data loader for Patient Explorer.

Loads data from:
1. Patient Excel file (auto-detects files matching *patient*list*.xls*, *patients*.xls*, etc.)
2. Spruce Health API (live matching)
3. APCM Excel file (enrollment data)

And reconciles everything into the SQLite database.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add phase0 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from database import get_session
from database.models import Patient, Consent, ConsentStatus, APCMStatus, APCMLevel


def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number to first 10 digits for matching."""
    if not phone:
        return None
    digits = "".join(c for c in str(phone) if c.isdigit())
    if len(digits) >= 10:
        return digits[:10]  # First 10 digits (Excel data has trailing extra digit)
    return digits if digits else None


def normalize_name(name: str) -> str:
    """Normalize name for matching (lowercase, stripped)."""
    if not name:
        return ""
    return str(name).lower().strip()


def fetch_spruce_contacts() -> Tuple[List, Dict, Dict]:
    """Fetch all contacts from Spruce and build lookup indexes.

    Returns:
        Tuple of (contacts_list, phone_index, name_index)
    """
    from phase0.spruce import SpruceClient

    client = SpruceClient()
    if not client.test_connection():
        raise ConnectionError("Failed to connect to Spruce API")

    contacts = client.get_contacts()

    # Build indexes for fast matching
    phone_index = {}
    name_index = {}

    for contact in contacts:
        # Phone index (normalized to first 10 digits)
        if contact.phone:
            digits = normalize_phone(contact.phone)
            if digits and len(digits) >= 10:
                phone_index[digits] = contact

        # Name index (last_name, first_name normalized)
        if contact.first_name and contact.last_name:
            key = (normalize_name(contact.last_name), normalize_name(contact.first_name))
            if key not in name_index:
                name_index[key] = []
            name_index[key].append(contact)

    return contacts, phone_index, name_index


def match_patient_to_spruce(patient, phone_index: Dict, name_index: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
    """Match a patient to Spruce contacts.

    Returns:
        Tuple of (matched, spruce_id, match_method)
    """
    # Try phone match first (most reliable)
    if patient.phone:
        patient_phone = normalize_phone(patient.phone)
        if patient_phone in phone_index:
            contact = phone_index[patient_phone]
            return (True, contact.spruce_id, "phone")

    # Try name match
    if patient.first_name and patient.last_name:
        key = (normalize_name(patient.last_name), normalize_name(patient.first_name))
        if key in name_index:
            contact = name_index[key][0]  # Take first match
            return (True, contact.spruce_id, "name")

    return (False, None, None)


def import_all_data(progress_callback=None) -> Dict[str, int]:
    """Import all patient data from Excel and match with Spruce.

    Args:
        progress_callback: Optional function to call with progress updates
                          Signature: callback(step: str, current: int, total: int)

    Returns:
        Dict with counts: patients_imported, spruce_matched, apcm_imported, errors
    """
    from phase0.excel_loader import load_patients_from_excel
    from apcm_loader import load_apcm_patients

    results = {
        "patients_imported": 0,
        "patients_updated": 0,
        "spruce_matched": 0,
        "spruce_total": 0,
        "apcm_imported": 0,
        "apcm_updated": 0,
        "errors": 0,
    }

    data_dir = Path(__file__).parent.parent / "data"
    imports_dir = data_dir / "imports"

    # Step 1: Load Spruce contacts
    if progress_callback:
        progress_callback("Connecting to Spruce API...", 0, 100)

    try:
        spruce_contacts, phone_index, name_index = fetch_spruce_contacts()
        results["spruce_total"] = len(spruce_contacts)
    except Exception as e:
        # Continue without Spruce matching if API fails
        spruce_contacts, phone_index, name_index = [], {}, {}
        results["errors"] += 1

    if progress_callback:
        progress_callback(f"Loaded {len(spruce_contacts)} Spruce contacts", 10, 100)

    # Step 2: Load patients from Excel (check both data/ and data/imports/)
    # Look for patient Excel files with flexible naming patterns
    # Supports: "GreenPatients.xlsx", "dr green patient list.xls", etc.
    patient_patterns = ["*patient*list*.xls*", "*GreenPatients*.xls*", "*patients*.xls*"]
    excel_files = []
    for pattern in patient_patterns:
        excel_files.extend(data_dir.glob(pattern))
        if imports_dir.exists():
            excel_files.extend(imports_dir.glob(pattern))
        if excel_files:
            break
    # Remove duplicates while preserving order
    excel_files = list(dict.fromkeys(excel_files))
    if not excel_files:
        raise FileNotFoundError(
            "No patient Excel file found in data/ or data/imports/. "
            "Looking for files matching: *patient*list*.xls*, *GreenPatients*.xls*, or *patients*.xls*"
        )

    if progress_callback:
        progress_callback("Loading patient Excel file...", 15, 100)

    patients = load_patients_from_excel(str(excel_files[0]))

    if progress_callback:
        progress_callback(f"Loaded {len(patients)} patients from Excel", 25, 100)

    # Step 3: Load APCM data (check both data/ and data/imports/)
    apcm_files = list(data_dir.glob("*APCM*.xlsx")) + list(data_dir.glob("*APCM*.xls"))
    if not apcm_files and imports_dir.exists():
        apcm_files = list(imports_dir.glob("*APCM*.xlsx")) + list(imports_dir.glob("*APCM*.xls"))
    apcm_data = {"active": [], "removed": []}
    apcm_by_mrn = {}

    if apcm_files:
        if progress_callback:
            progress_callback("Loading APCM Excel file...", 30, 100)

        apcm_data = load_apcm_patients(str(apcm_files[0]))

        # Build MRN lookup
        for p in apcm_data["active"] + apcm_data["removed"]:
            if p["mrn"]:
                apcm_by_mrn[p["mrn"]] = p

    if progress_callback:
        progress_callback(f"Loaded {len(apcm_data['active'])} active APCM patients", 35, 100)

    # Step 4: Import/update patients in database
    session = get_session()
    total_patients = len(patients)

    try:
        for i, p in enumerate(patients):
            if progress_callback and i % 50 == 0:
                pct = 35 + int((i / total_patients) * 55)
                progress_callback(f"Processing patient {i+1}/{total_patients}...", pct, 100)

            # Match with Spruce
            matched, spruce_id, match_method = match_patient_to_spruce(p, phone_index, name_index)
            if matched:
                results["spruce_matched"] += 1

            # Get APCM data if available
            apcm_info = apcm_by_mrn.get(p.mrn, {})

            # Determine APCM level enum
            level_enum = None
            if apcm_info.get("level_code") == "G0556":
                level_enum = APCMLevel.LEVEL_1
            elif apcm_info.get("level_code") == "G0557":
                level_enum = APCMLevel.LEVEL_2
            elif apcm_info.get("level_code") == "G0558":
                level_enum = APCMLevel.LEVEL_3

            # Determine APCM status
            apcm_status = APCMStatus.NOT_ENROLLED
            if apcm_info:
                if apcm_info.get("status") == "active":
                    apcm_status = APCMStatus.ACTIVE
                    results["apcm_imported"] += 1
                elif apcm_info.get("status") == "removed":
                    apcm_status = APCMStatus.REMOVED

            # Check if patient exists
            existing = session.query(Patient).filter(Patient.mrn == p.mrn).first()

            if existing:
                # Update existing patient
                existing.spruce_matched = matched
                existing.spruce_id = spruce_id
                existing.spruce_match_method = match_method

                # Update APCM fields
                if apcm_info:
                    existing.apcm_enrolled = (apcm_info.get("status") == "active")
                    existing.apcm_signup_date = apcm_info.get("signup_date")
                    existing.apcm_level = level_enum
                    existing.apcm_icd_codes = apcm_info.get("icd_codes")
                    existing.apcm_status = apcm_status
                    existing.apcm_status_notes = apcm_info.get("status_notes")
                    existing.apcm_insurance = apcm_info.get("insurance")
                    existing.apcm_copay = apcm_info.get("copay")
                    if apcm_info.get("preferred_name") and not existing.preferred_name:
                        existing.preferred_name = apcm_info.get("preferred_name")
                    results["apcm_updated"] += 1

                results["patients_updated"] += 1
            else:
                # Create new patient
                db_patient = Patient(
                    mrn=p.mrn,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    date_of_birth=str(p.date_of_birth) if p.date_of_birth else None,
                    phone=p.phone,
                    email=p.email,
                    address=p.address,
                    city=p.city,
                    state=p.state,
                    zip_code=p.zip_code,
                    spruce_matched=matched,
                    spruce_id=spruce_id,
                    spruce_match_method=match_method,
                    # APCM fields
                    preferred_name=apcm_info.get("preferred_name"),
                    apcm_enrolled=(apcm_info.get("status") == "active") if apcm_info else False,
                    apcm_signup_date=apcm_info.get("signup_date"),
                    apcm_level=level_enum,
                    apcm_icd_codes=apcm_info.get("icd_codes"),
                    apcm_status=apcm_status,
                    apcm_status_notes=apcm_info.get("status_notes"),
                    apcm_insurance=apcm_info.get("insurance"),
                    apcm_copay=apcm_info.get("copay"),
                )
                session.add(db_patient)

                # Create pending consent record
                consent = Consent(patient=db_patient, status=ConsentStatus.PENDING)
                session.add(consent)

                results["patients_imported"] += 1

        session.commit()

        if progress_callback:
            progress_callback("Import complete!", 100, 100)

    except Exception as e:
        session.rollback()
        results["errors"] += 1
        raise e
    finally:
        session.close()

    return results


def get_import_summary() -> Dict:
    """Get summary of current database state."""
    session = get_session()
    try:
        total = session.query(Patient).count()
        spruce_matched = session.query(Patient).filter(Patient.spruce_matched == True).count()
        apcm_active = session.query(Patient).filter(Patient.apcm_status == APCMStatus.ACTIVE).count()
        apcm_removed = session.query(Patient).filter(Patient.apcm_status == APCMStatus.REMOVED).count()

        pending_consent = session.query(Consent).filter(Consent.status == ConsentStatus.PENDING).count()
        consented = session.query(Consent).filter(Consent.status == ConsentStatus.CONSENTED).count()

        return {
            "total_patients": total,
            "spruce_matched": spruce_matched,
            "spruce_unmatched": total - spruce_matched,
            "apcm_active": apcm_active,
            "apcm_removed": apcm_removed,
            "pending_consent": pending_consent,
            "consented": consented,
        }
    finally:
        session.close()
