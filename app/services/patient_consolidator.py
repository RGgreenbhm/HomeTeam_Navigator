"""Patient Consolidator Service for Patient Explorer V1.0.

Consolidates patient data from multiple sources into a single JSON master file:
1. Main patient Excel file (demographics, contact info)
2. APCM Excel file (enrollment data, ICD codes)
3. Spruce Health API (contact matching, tags)

Outputs: patients_master.json per the PatientMasterRecord schema.

HIPAA Note: This runs locally. Output file contains PHI and must be
stored only in HIPAA-compliant locations (encrypted local, Azure Blob with BAA).
"""

import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()


class PatientConsolidator:
    """Consolidates patient data from Excel files and Spruce API into JSON.

    Usage:
        consolidator = PatientConsolidator()
        consolidator.load_main_patient_list("data/patients.xls")
        consolidator.load_apcm_data("data/apcm.xlsx")
        consolidator.fetch_spruce_contacts()
        consolidator.run_matching()
        consolidator.export_json("data/patients_master.json")
    """

    def __init__(self):
        """Initialize the consolidator."""
        self.patients: Dict[str, Dict[str, Any]] = {}  # Keyed by MRN
        self.apcm_data: Dict[str, Dict[str, Any]] = {}  # Keyed by MRN
        self.spruce_contacts: List[Any] = []
        self.spruce_phone_index: Dict[str, Any] = {}
        self.spruce_name_index: Dict[Tuple[str, str], List[Any]] = {}
        self.spruce_tags: Dict[str, str] = {}  # tag_name -> tag_id

        self.stats = {
            "patients_loaded": 0,
            "apcm_loaded": 0,
            "spruce_contacts": 0,
            "matched_by_phone": 0,
            "matched_by_name_dob": 0,
            "matched_by_email": 0,
            "unmatched": 0,
            "errors": [],
        }

    # =========================================================================
    # Excel Loading
    # =========================================================================

    def load_main_patient_list(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> int:
        """Load patients from main Excel file.

        Supports flexible column mapping via aliases.

        Args:
            file_path: Path to Excel file
            progress_callback: Optional callback(message, current, total)

        Returns:
            Number of patients loaded
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Patient file not found: {file_path}")

        if progress_callback:
            progress_callback("Loading patient Excel file...", 0, 100)

        # Load Excel
        df = pd.read_excel(path)
        logger.info(f"Loaded {len(df)} rows from {path.name}")
        logger.debug(f"Columns: {list(df.columns)}")

        # Map columns
        column_map = self._map_columns(df)
        logger.info(f"Column mapping: {column_map}")

        # Process rows
        total = len(df)
        for idx, row in df.iterrows():
            if progress_callback and idx % 100 == 0:
                progress_callback(f"Processing row {idx}/{total}", int(idx/total*100), 100)

            try:
                patient = self._extract_patient_from_row(row, column_map)
                if patient and patient.get("mrn"):
                    self.patients[patient["mrn"]] = patient
            except Exception as e:
                self.stats["errors"].append(f"Row {idx+2}: {str(e)}")

        self.stats["patients_loaded"] = len(self.patients)
        logger.info(f"Loaded {len(self.patients)} patients")

        if progress_callback:
            progress_callback(f"Loaded {len(self.patients)} patients", 100, 100)

        return len(self.patients)

    def load_apcm_data(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> int:
        """Load APCM enrollment data from Excel.

        Args:
            file_path: Path to APCM Excel file
            progress_callback: Optional callback(message, current, total)

        Returns:
            Number of APCM records loaded
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"APCM file not found: {file_path}")

        if progress_callback:
            progress_callback("Loading APCM Excel file...", 0, 100)

        # Use existing APCM loader
        from app.apcm_loader import load_apcm_patients

        data = load_apcm_patients(str(path))

        # Merge active and removed into lookup by MRN
        for patient in data["active"]:
            if patient.get("mrn"):
                self.apcm_data[patient["mrn"]] = {
                    **patient,
                    "enrolled": True,
                }

        for patient in data["removed"]:
            if patient.get("mrn"):
                self.apcm_data[patient["mrn"]] = {
                    **patient,
                    "enrolled": False,
                }

        self.stats["apcm_loaded"] = len(self.apcm_data)
        logger.info(f"Loaded {len(self.apcm_data)} APCM records")

        if progress_callback:
            progress_callback(f"Loaded {len(self.apcm_data)} APCM records", 100, 100)

        return len(self.apcm_data)

    # =========================================================================
    # Spruce Integration
    # =========================================================================

    def fetch_spruce_contacts(
        self,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> int:
        """Fetch all contacts from Spruce Health API and build indexes.

        Args:
            progress_callback: Optional callback(message, current, total)

        Returns:
            Number of contacts fetched
        """
        if progress_callback:
            progress_callback("Connecting to Spruce API...", 0, 100)

        from phase0.spruce import SpruceClient

        client = SpruceClient()
        if not client.test_connection():
            raise ConnectionError("Failed to connect to Spruce API")

        if progress_callback:
            progress_callback("Fetching contacts...", 20, 100)

        self.spruce_contacts = client.get_contacts()

        # Build indexes
        if progress_callback:
            progress_callback("Building search indexes...", 80, 100)

        for contact in self.spruce_contacts:
            # Phone index
            if contact.phone:
                normalized = self._normalize_phone(contact.phone)
                if normalized:
                    self.spruce_phone_index[normalized] = contact

            # Name index
            if contact.first_name and contact.last_name:
                key = (
                    contact.last_name.lower().strip(),
                    contact.first_name.lower().strip()
                )
                if key not in self.spruce_name_index:
                    self.spruce_name_index[key] = []
                self.spruce_name_index[key].append(contact)

        self.stats["spruce_contacts"] = len(self.spruce_contacts)
        logger.info(f"Fetched {len(self.spruce_contacts)} Spruce contacts")

        if progress_callback:
            progress_callback(f"Fetched {len(self.spruce_contacts)} contacts", 100, 100)

        return len(self.spruce_contacts)

    def fetch_spruce_tags(self) -> Dict[str, str]:
        """Fetch all contact tags from Spruce and build name->id lookup.

        Returns:
            Dict mapping tag name to tag ID
        """
        from phase0.spruce import SpruceClient

        client = SpruceClient()
        tags = client.list_contact_tags()

        self.spruce_tags = {}
        for tag in tags:
            name = tag.get("name", "")
            tag_id = tag.get("id", "")
            if name and tag_id:
                self.spruce_tags[name.lower()] = tag_id

        logger.info(f"Fetched {len(self.spruce_tags)} Spruce tags")
        return self.spruce_tags

    # =========================================================================
    # Matching
    # =========================================================================

    def run_matching(
        self,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, int]:
        """Match patients to Spruce contacts.

        Matching priority:
        1. Phone number (highest confidence)
        2. Name + DOB (secondary)
        3. Email (tertiary)

        Args:
            progress_callback: Optional callback(message, current, total)

        Returns:
            Dict with match statistics
        """
        if progress_callback:
            progress_callback("Running patient matching...", 0, 100)

        total = len(self.patients)
        matched_phone = 0
        matched_name_dob = 0
        matched_email = 0
        unmatched = 0

        for idx, (mrn, patient) in enumerate(self.patients.items()):
            if progress_callback and idx % 50 == 0:
                progress_callback(f"Matching {idx}/{total}", int(idx/total*100), 100)

            contact, method, confidence = self._match_patient(patient)

            if contact:
                # Store match info
                patient["_spruce_contact"] = contact
                patient["_match_method"] = method
                patient["_match_confidence"] = confidence

                if method == "phone":
                    matched_phone += 1
                elif method == "name_dob":
                    matched_name_dob += 1
                elif method == "email":
                    matched_email += 1
            else:
                unmatched += 1

        self.stats["matched_by_phone"] = matched_phone
        self.stats["matched_by_name_dob"] = matched_name_dob
        self.stats["matched_by_email"] = matched_email
        self.stats["unmatched"] = unmatched

        total_matched = matched_phone + matched_name_dob + matched_email
        logger.info(f"Matching complete: {total_matched}/{total} matched "
                   f"(phone={matched_phone}, name_dob={matched_name_dob}, email={matched_email})")

        if progress_callback:
            progress_callback(f"Matched {total_matched}/{total} patients", 100, 100)

        return {
            "total": total,
            "matched": total_matched,
            "matched_by_phone": matched_phone,
            "matched_by_name_dob": matched_name_dob,
            "matched_by_email": matched_email,
            "unmatched": unmatched,
        }

    def _match_patient(
        self,
        patient: Dict[str, Any]
    ) -> Tuple[Optional[Any], Optional[str], float]:
        """Match a single patient to Spruce contact.

        Returns:
            Tuple of (contact, method, confidence) or (None, None, 0.0)
        """
        # Try phone match first (highest confidence)
        if patient.get("phone"):
            normalized = self._normalize_phone(patient["phone"])
            if normalized and normalized in self.spruce_phone_index:
                return (self.spruce_phone_index[normalized], "phone", 0.95)

        # Try name + DOB match
        if patient.get("first_name") and patient.get("last_name"):
            key = (
                patient["last_name"].lower().strip(),
                patient["first_name"].lower().strip()
            )
            if key in self.spruce_name_index:
                candidates = self.spruce_name_index[key]

                # If patient has DOB, try to match
                patient_dob = patient.get("date_of_birth")
                if patient_dob and len(candidates) > 1:
                    for c in candidates:
                        if c.date_of_birth == patient_dob:
                            return (c, "name_dob", 0.85)

                # Return first name match if no DOB or single candidate
                return (candidates[0], "name_dob", 0.70)

        # Try email match (lowest priority)
        if patient.get("email"):
            email = patient["email"].lower().strip()
            for contact in self.spruce_contacts:
                if contact.email and contact.email.lower().strip() == email:
                    return (contact, "email", 0.60)

        return (None, None, 0.0)

    # =========================================================================
    # JSON Export
    # =========================================================================

    def export_json(
        self,
        output_path: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> str:
        """Export consolidated patient data to JSON.

        Generates patients_master.json per the PatientMasterRecord schema.

        Args:
            output_path: Path for output JSON file
            progress_callback: Optional callback(message, current, total)

        Returns:
            Path to generated file
        """
        if progress_callback:
            progress_callback("Building JSON records...", 0, 100)

        records = []
        total = len(self.patients)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        for idx, (mrn, patient) in enumerate(self.patients.items()):
            if progress_callback and idx % 100 == 0:
                progress_callback(f"Processing {idx}/{total}", int(idx/total*100), 100)

            record = self._build_patient_record(patient, now)
            records.append(record)

        # Sort by last name, first name
        records.sort(key=lambda r: (
            r.get("demographics", {}).get("last_name", "").lower(),
            r.get("demographics", {}).get("first_name", "").lower()
        ))

        # Write JSON
        if progress_callback:
            progress_callback("Writing JSON file...", 95, 100)

        output_data = {
            "schema_version": "1.0.0",
            "generated_at": now,
            "generated_by": "patient_consolidator",
            "record_count": len(records),
            "statistics": self.stats,
            "patients": records,
        }

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Exported {len(records)} patients to {path}")

        if progress_callback:
            progress_callback(f"Exported {len(records)} patients", 100, 100)

        return str(path)

    def _build_patient_record(
        self,
        patient: Dict[str, Any],
        timestamp: str
    ) -> Dict[str, Any]:
        """Build a single patient record per the JSON schema.

        Args:
            patient: Patient dict with optional _spruce_contact
            timestamp: ISO timestamp for metadata

        Returns:
            Patient record dict per schema
        """
        mrn = patient.get("mrn", "")
        apcm = self.apcm_data.get(mrn, {})
        spruce_contact = patient.get("_spruce_contact")
        match_method = patient.get("_match_method")
        match_confidence = patient.get("_match_confidence", 0.0)

        # Build record
        record = {
            "id": str(uuid.uuid4()),
            "demographics": {
                "first_name": patient.get("first_name", ""),
                "last_name": patient.get("last_name", ""),
                "middle_name": patient.get("middle_name"),
                "date_of_birth": self._format_date(patient.get("date_of_birth")),
                "mrn": mrn,
                "phone_home": self._normalize_phone(patient.get("phone")),
                "email": patient.get("email"),
                "address": {
                    "line1": patient.get("address"),
                    "city": patient.get("city"),
                    "state": patient.get("state"),
                    "zip": patient.get("zip_code"),
                } if patient.get("address") else None,
            },
            "identifiers": {
                "spruce_id": spruce_contact.spruce_id if spruce_contact else None,
                "allscripts_mrn": mrn,
            },
            "insurance": {
                "primary": {
                    "provider": patient.get("insurer_name"),
                    "member_id": patient.get("insurer_id"),
                } if patient.get("insurer_name") else None,
            },
            "apcm": self._build_apcm_section(apcm),
            "consent": {
                "status": "pending",
            },
            "tags": self._build_tags_section(patient, apcm, spruce_contact),
            "clinical": {
                "problems": [],
                "medications": [],
                "allergies": [],
            },
            "encounters": [],
            "scheduling": {
                "last_visit_date": self._format_date(patient.get("last_visit_date")),
            },
            "screenshots": [],
            "communications": [],
            "metadata": {
                "created_at": timestamp,
                "updated_at": timestamp,
                "version": 1,
                "data_sources": self._get_data_sources(patient, apcm, spruce_contact),
                "spruce_match_confidence": match_confidence if spruce_contact else None,
                "spruce_match_method": match_method,
                "active": True,
            },
        }

        # Clean up None values in nested objects
        record = self._clean_record(record)

        return record

    def _build_apcm_section(self, apcm: Dict[str, Any]) -> Dict[str, Any]:
        """Build APCM section from APCM data."""
        if not apcm:
            return {"enrolled": False}

        return {
            "enrolled": apcm.get("enrolled", False),
            "enrolled_date": self._format_date(apcm.get("signup_date")),
            "level": apcm.get("level_code"),
            "icd_codes": apcm.get("icd_codes", "").split(", ") if apcm.get("icd_codes") else None,
            "status": "active" if apcm.get("status") == "active" else "removed" if apcm.get("status") == "removed" else "pending",
            "notes": apcm.get("status_notes"),
        }

    def _build_tags_section(
        self,
        patient: Dict[str, Any],
        apcm: Dict[str, Any],
        spruce_contact: Any
    ) -> Dict[str, Any]:
        """Build tags section with standardized Spruce tags."""
        tags = {
            "team": [],
            "status": [],
            "communication": [],
            "custom": [],
        }

        # Add APCM status tag if enrolled
        if apcm and apcm.get("enrolled"):
            tags["status"].append("apcm")

        # Default to consent_pending
        tags["status"].append("consent_pending")

        return tags

    def _get_data_sources(
        self,
        patient: Dict[str, Any],
        apcm: Dict[str, Any],
        spruce_contact: Any
    ) -> List[str]:
        """Get list of data sources that contributed to this record."""
        sources = ["excel_patient_list"]
        if apcm:
            sources.append("excel_apcm")
        if spruce_contact:
            sources.append("spruce_api")
        return sources

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Map DataFrame columns to standard field names."""
        aliases = {
            "mrn": ["mrn", "patient id", "patientid", "id", "medical record",
                   "chart number", "account #", "acct #", "acct", "patient #"],
            "first_name": ["first name", "firstname", "first", "fname"],
            "last_name": ["last name", "lastname", "last", "lname"],
            "middle_name": ["middle name", "middlename", "middle", "mname"],
            "patient_name": ["patient name", "patientname", "name", "full name", "fullname"],
            "date_of_birth": ["dob", "date of birth", "birthdate", "birth date", "birthday"],
            "phone": ["phone", "telephone", "phone number", "mobile", "cell",
                     "cell phone", "home phone"],
            "email": ["email", "e-mail", "email address"],
            "address": ["address", "street", "street address"],
            "city": ["city"],
            "state": ["state", "st"],
            "zip_code": ["zip", "zipcode", "zip code", "postal code"],
            "insurer_id": ["insurer id", "insurance id", "payer id"],
            "insurer_name": ["insurer", "insurer name", "insurance", "payer"],
            "last_visit_date": ["last visit", "last dos", "last date of service",
                               "dos", "date of service"],
        }

        column_map = {}
        df_columns = {c.lower().strip().replace("_", " "): c for c in df.columns}

        for field, field_aliases in aliases.items():
            for alias in field_aliases:
                if alias in df_columns:
                    column_map[field] = df_columns[alias]
                    break

        return column_map

    def _extract_patient_from_row(
        self,
        row: pd.Series,
        column_map: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Extract patient dict from DataFrame row."""
        patient = {}

        for field, col in column_map.items():
            value = row.get(col)

            if field in ("date_of_birth", "last_visit_date"):
                value = self._parse_date(value)
            elif field == "phone":
                value = self._clean_phone(value)
            elif pd.isna(value):
                value = None
            else:
                value = str(value).strip() if value else None

            patient[field] = value

        # Handle combined patient_name field
        if "patient_name" in patient and patient["patient_name"]:
            full_name = patient.pop("patient_name")
            if "," in full_name:
                parts = full_name.split(",", 1)
                patient["last_name"] = parts[0].strip()
                if len(parts) > 1:
                    first_parts = parts[1].strip().split()
                    patient["first_name"] = first_parts[0] if first_parts else ""
            else:
                parts = full_name.split()
                if len(parts) >= 2:
                    patient["first_name"] = parts[0]
                    patient["last_name"] = parts[-1]
                elif len(parts) == 1:
                    patient["last_name"] = parts[0]

        return patient if patient.get("mrn") else None

    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone to 10 digits."""
        if not phone:
            return None
        digits = "".join(c for c in str(phone) if c.isdigit())
        if len(digits) >= 10:
            # Take first 10 digits (Excel sometimes has extra)
            return digits[:10]
        return digits if digits else None

    def _clean_phone(self, phone: Optional[str]) -> Optional[str]:
        """Clean phone number, keeping formatted if possible."""
        if not phone or pd.isna(phone):
            return None
        digits = "".join(c for c in str(phone) if c.isdigit())
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return digits if digits else None

    def _parse_date(self, value) -> Optional[date]:
        """Parse various date formats."""
        if pd.isna(value) or value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(value.strip(), fmt).date()
                except ValueError:
                    continue
        return None

    def _format_date(self, value) -> Optional[str]:
        """Format date as ISO string."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return None

    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Remove None values and empty objects from record."""
        if isinstance(record, dict):
            cleaned = {}
            for k, v in record.items():
                cleaned_v = self._clean_record(v)
                # Keep the key if value is not None/empty
                if cleaned_v is not None:
                    if isinstance(cleaned_v, dict) and not cleaned_v:
                        continue  # Skip empty dicts
                    if isinstance(cleaned_v, list) and not cleaned_v:
                        continue  # Skip empty lists
                    cleaned[k] = cleaned_v
            return cleaned
        elif isinstance(record, list):
            return [self._clean_record(item) for item in record if item is not None]
        return record

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            **self.stats,
            "total_patients": len(self.patients),
            "total_apcm": len(self.apcm_data),
            "match_rate": (
                (self.stats["matched_by_phone"] +
                 self.stats["matched_by_name_dob"] +
                 self.stats["matched_by_email"]) / len(self.patients) * 100
                if self.patients else 0
            ),
        }


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Run patient consolidation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Consolidate patient data to JSON")
    parser.add_argument("--patients", "-p", help="Path to patient Excel file")
    parser.add_argument("--apcm", "-a", help="Path to APCM Excel file")
    parser.add_argument("--output", "-o", default="data/patients_master.json",
                       help="Output JSON file path")
    parser.add_argument("--skip-spruce", action="store_true",
                       help="Skip Spruce API matching")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    consolidator = PatientConsolidator()

    # Find files if not specified
    data_dir = Path("data")

    patient_file = args.patients
    if not patient_file:
        files = list(data_dir.glob("*patient*list*.xls*"))
        if files:
            patient_file = str(files[0])
        else:
            print("Error: No patient file found. Use --patients to specify.")
            return 1

    apcm_file = args.apcm
    if not apcm_file:
        files = list(data_dir.glob("*APCM*.xlsx"))
        if files:
            apcm_file = str(files[0])

    # Run consolidation
    print(f"Loading patients from: {patient_file}")
    consolidator.load_main_patient_list(patient_file)

    if apcm_file:
        print(f"Loading APCM data from: {apcm_file}")
        consolidator.load_apcm_data(apcm_file)

    if not args.skip_spruce:
        print("Fetching Spruce contacts...")
        try:
            consolidator.fetch_spruce_contacts()
            print("Running patient matching...")
            consolidator.run_matching()
        except Exception as e:
            print(f"Warning: Spruce matching failed: {e}")

    print(f"Exporting to: {args.output}")
    consolidator.export_json(args.output)

    # Print summary
    summary = consolidator.get_summary()
    print("\n--- Summary ---")
    print(f"Patients loaded: {summary['patients_loaded']}")
    print(f"APCM records: {summary['apcm_loaded']}")
    print(f"Spruce contacts: {summary['spruce_contacts']}")
    print(f"Matched by phone: {summary['matched_by_phone']}")
    print(f"Matched by name/DOB: {summary['matched_by_name_dob']}")
    print(f"Matched by email: {summary['matched_by_email']}")
    print(f"Unmatched: {summary['unmatched']}")
    print(f"Match rate: {summary['match_rate']:.1f}%")

    if summary['errors']:
        print(f"\nErrors ({len(summary['errors'])}):")
        for err in summary['errors'][:5]:
            print(f"  - {err}")
        if len(summary['errors']) > 5:
            print(f"  ... and {len(summary['errors']) - 5} more")

    return 0


if __name__ == "__main__":
    sys.exit(main())
