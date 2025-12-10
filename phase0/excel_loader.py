"""
Excel patient data loader.

Loads patient records from Excel files with flexible column mapping.
Supports the column aliases defined in the architecture documentation.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from .models import Patient


# Column name aliases for flexible matching
COLUMN_ALIASES = {
    "mrn": ["mrn", "patient id", "patientid", "id", "medical record", "chart number", "account #", "acct #", "acct"],
    "first_name": ["first name", "firstname", "first", "fname"],
    "last_name": ["last name", "lastname", "last", "lname"],
    "middle_name": ["middle name", "middlename", "middle", "mname"],
    "patient_name": ["patient name", "patientname", "name", "full name", "fullname"],  # Combined name field
    "date_of_birth": ["dob", "date of birth", "birthdate", "birth date", "birthday"],
    "phone": ["phone", "telephone", "phone number", "mobile", "cell", "cell phone", "home phone"],
    "email": ["email", "e-mail", "email address"],
    "address": ["address", "street", "street address"],
    "city": ["city"],
    "state": ["state", "st"],
    "zip_code": ["zip", "zipcode", "zip code", "postal code"],
    "insurer_id": ["insurer id", "insurance id", "payer id"],
    "insurer_name": ["insurer", "insurer name", "insurance", "payer"],
    "last_visit_date": ["last visit", "last dos", "last date of service", "dos", "date of service"],
}


def normalize_column_name(name: str) -> str:
    """Normalize column name for matching."""
    return name.lower().strip().replace("_", " ")


def map_columns(df: pd.DataFrame) -> dict[str, str]:
    """
    Map Excel column names to our field names.

    Returns a dict mapping our field names to actual column names in the DataFrame.
    """
    column_map = {}
    df_columns = {normalize_column_name(c): c for c in df.columns}

    for field_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            normalized = normalize_column_name(alias)
            if normalized in df_columns:
                column_map[field_name] = df_columns[normalized]
                break

    return column_map


def parse_date(value) -> Optional[datetime]:
    """Parse various date formats."""
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def clean_phone(value) -> Optional[str]:
    """Clean phone number to digits only."""
    if pd.isna(value):
        return None
    digits = "".join(c for c in str(value) if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return digits if digits else None


def load_patients_from_excel(file_path: str | Path) -> list[Patient]:
    """
    Load patient records from an Excel file.

    Args:
        file_path: Path to the Excel file (.xlsx or .xls)

    Returns:
        List of Patient objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    logger.info(f"Loading patients from {file_path}")

    # Load Excel file
    df = pd.read_excel(file_path)
    logger.info(f"Found {len(df)} rows in Excel file")
    logger.debug(f"Columns: {list(df.columns)}")

    # Map columns
    column_map = map_columns(df)
    logger.info(f"Mapped columns: {column_map}")

    # Check required columns - need MRN and either (last_name) or (patient_name)
    has_mrn = "mrn" in column_map
    has_name = "last_name" in column_map or "patient_name" in column_map

    if not has_mrn or not has_name:
        missing = []
        if not has_mrn:
            missing.append("mrn")
        if not has_name:
            missing.append("last_name or patient_name")
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

    # Convert rows to Patient objects
    patients = []
    errors = []

    for idx, row in df.iterrows():
        try:
            patient_data = {}

            # Extract mapped fields
            for field_name, excel_col in column_map.items():
                value = row.get(excel_col)

                # Handle special fields
                if field_name == "date_of_birth":
                    value = parse_date(value)
                elif field_name == "last_visit_date":
                    value = parse_date(value)
                elif field_name == "phone":
                    value = clean_phone(value)
                elif pd.isna(value):
                    value = None
                else:
                    value = str(value).strip() if value else None

                patient_data[field_name] = value

            # Handle combined patient_name field -> split into first/last
            if "patient_name" in patient_data and patient_data["patient_name"]:
                full_name = patient_data.pop("patient_name")
                # Common formats: "Last, First" or "First Last"
                if "," in full_name:
                    # "Last, First Middle" format
                    parts = full_name.split(",", 1)
                    patient_data["last_name"] = parts[0].strip()
                    if len(parts) > 1:
                        first_parts = parts[1].strip().split()
                        patient_data["first_name"] = first_parts[0] if first_parts else ""
                else:
                    # "First Last" format
                    parts = full_name.split()
                    if len(parts) >= 2:
                        patient_data["first_name"] = parts[0]
                        patient_data["last_name"] = parts[-1]
                    elif len(parts) == 1:
                        patient_data["last_name"] = parts[0]

            # Create patient
            patient = Patient(**patient_data)
            patients.append(patient)

        except Exception as e:
            errors.append({"row": idx + 2, "error": str(e)})  # +2 for header and 0-index
            logger.warning(f"Error parsing row {idx + 2}: {e}")

    logger.info(f"Successfully loaded {len(patients)} patients")
    if errors:
        logger.warning(f"Encountered {len(errors)} errors during import")

    return patients


def preview_excel(file_path: str | Path, rows: int = 5) -> pd.DataFrame:
    """
    Preview the first few rows of an Excel file.

    Useful for verifying column mapping before full import.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    df = pd.read_excel(file_path, nrows=rows)
    return df
