"""APCM patient data loader from Excel."""

import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def parse_preferred_name(first_name: str) -> Tuple[str, Optional[str]]:
    """Parse first name and preferred name from format like 'Patricia "Pat"'.

    Returns:
        Tuple of (first_name, preferred_name)
    """
    if not first_name or pd.isna(first_name):
        return ("", None)

    first_name = str(first_name).strip()

    # Look for quoted nickname: "Pat", 'Pat', or (Pat)
    patterns = [
        r'^(.+?)\s*"([^"]+)"',      # Patricia "Pat"
        r"^(.+?)\s*'([^']+)'",      # Patricia 'Pat'
        r'^(.+?)\s*\(([^)]+)\)',    # Patricia (Pat)
    ]

    for pattern in patterns:
        match = re.match(pattern, first_name)
        if match:
            return (match.group(1).strip(), match.group(2).strip())

    return (first_name, None)


def determine_apcm_level(row: pd.Series) -> Tuple[Optional[str], Optional[str]]:
    """Determine APCM level and ICD codes from Level 1/2/3 columns.

    Returns:
        Tuple of (level_code, icd_codes)
        level_code is 'G0556', 'G0557', or 'G0558'
    """
    # Column indices based on header row
    level_cols = {
        'Level 1 (One DX) (G0556)': 'G0556',
        'Level 2 (2 + DX) (G0557)': 'G0557',
        'QMB (2 + DX) (G0558)': 'G0558',
    }

    for col_name, level_code in level_cols.items():
        if col_name in row.index:
            value = row[col_name]
            if pd.notna(value) and str(value).strip():
                # The value contains ICD codes
                return (level_code, str(value).strip())

    return (None, None)


def load_apcm_patients(excel_path: str) -> Dict[str, List[Dict]]:
    """Load APCM patient data from Excel file.

    Args:
        excel_path: Path to the APCM Excel file

    Returns:
        Dict with 'active' and 'removed' patient lists
    """
    result = {'active': [], 'removed': []}

    xls = pd.ExcelFile(excel_path)

    # Load active patients from "2025" sheet (header on row 2)
    if '2025' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='2025', header=2)

        for _, row in df.iterrows():
            mrn = row.get('Patient #')
            if pd.isna(mrn):
                continue

            first_name_raw = row.get('First Name', '')
            first_name, preferred_name = parse_preferred_name(first_name_raw)

            level_code, icd_codes = determine_apcm_level(row)

            # Parse signup date
            signup_date = row.get('Date Signed Up')
            if pd.notna(signup_date):
                if isinstance(signup_date, datetime):
                    signup_date = signup_date
                else:
                    try:
                        signup_date = pd.to_datetime(signup_date)
                    except:
                        signup_date = None
            else:
                signup_date = None

            patient = {
                'mrn': str(int(mrn)) if pd.notna(mrn) else None,
                'last_name': str(row.get('Last Name', '')).strip() if pd.notna(row.get('Last Name')) else '',
                'first_name': first_name,
                'preferred_name': preferred_name,
                'signup_date': signup_date,
                'level_code': level_code,
                'icd_codes': icd_codes,
                'status': 'active',
                'status_notes': str(row.get('Comments', '')).strip() if pd.notna(row.get('Comments')) else None,
                'insurance': str(row.get('Insurance', '')).strip() if pd.notna(row.get('Insurance')) else None,
                'copay': str(row.get('Copay', '')).strip() if pd.notna(row.get('Copay')) else None,
                'apcm_status_text': str(row.get('APCM Status', '')).strip() if pd.notna(row.get('APCM Status')) else None,
            }

            if patient['mrn']:
                result['active'].append(patient)

    # Load removed patients from "REMOVED" sheet (header on row 0)
    if 'REMOVED' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='REMOVED', header=0)

        for _, row in df.iterrows():
            mrn = row.get('Patient #')
            if pd.isna(mrn):
                continue

            first_name_raw = row.get('First Name', '')
            first_name, preferred_name = parse_preferred_name(first_name_raw)

            level_code, icd_codes = determine_apcm_level(row)

            # Parse signup date
            signup_date = row.get('Date Signed Up')
            if pd.notna(signup_date):
                if isinstance(signup_date, datetime):
                    signup_date = signup_date
                else:
                    try:
                        signup_date = pd.to_datetime(signup_date)
                    except:
                        signup_date = None
            else:
                signup_date = None

            # Collect removal notes from various columns
            notes_parts = []
            for col in df.columns:
                if col not in ['Patient #', 'Last Name', 'First Name', 'Date Signed Up',
                              'Level 1 (One DX) (G0556)', 'Level 2 (2 + DX) (G0557)',
                              'QMB (2 + DX) (G0558)']:
                    val = row.get(col)
                    if pd.notna(val) and str(val).strip() and str(val).strip() not in ['G0556', 'G0557', 'G0558']:
                        notes_parts.append(str(val).strip())

            patient = {
                'mrn': str(int(mrn)) if pd.notna(mrn) else None,
                'last_name': str(row.get('Last Name', '')).strip() if pd.notna(row.get('Last Name')) else '',
                'first_name': first_name,
                'preferred_name': preferred_name,
                'signup_date': signup_date,
                'level_code': level_code,
                'icd_codes': icd_codes,
                'status': 'removed',
                'status_notes': '; '.join(notes_parts) if notes_parts else None,
                'insurance': None,
                'copay': None,
                'apcm_status_text': None,
            }

            if patient['mrn']:
                result['removed'].append(patient)

    return result


def get_apcm_summary(excel_path: str) -> Dict:
    """Get summary statistics from APCM file without loading full data.

    Returns:
        Dict with counts and level breakdowns
    """
    data = load_apcm_patients(excel_path)

    active = data['active']
    removed = data['removed']

    level_counts = {'G0556': 0, 'G0557': 0, 'G0558': 0}
    for p in active:
        if p['level_code'] in level_counts:
            level_counts[p['level_code']] += 1

    return {
        'active_count': len(active),
        'removed_count': len(removed),
        'total': len(active) + len(removed),
        'level_1_count': level_counts['G0556'],
        'level_2_count': level_counts['G0557'],
        'level_3_count': level_counts['G0558'],
    }


if __name__ == "__main__":
    # Test the loader
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "data/2025-11-30_Green_APCM.xlsx"

    summary = get_apcm_summary(path)
    print(f"APCM Summary:")
    print(f"  Active patients: {summary['active_count']}")
    print(f"  Removed patients: {summary['removed_count']}")
    print(f"  Level 1 (G0556): {summary['level_1_count']}")
    print(f"  Level 2 (G0557): {summary['level_2_count']}")
    print(f"  Level 3 (G0558): {summary['level_3_count']}")
