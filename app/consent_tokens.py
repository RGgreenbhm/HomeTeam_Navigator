"""Consent token generator for Patient Explorer.

Generates unique, secure tokens for patient consent form links.
Tokens are:
- URL-safe (base62 encoding)
- Time-limited (configurable expiration)
- Unique per patient
- Auditable

Microsoft Forms URL pattern:
https://forms.microsoft.com/r/YOUR_FORM_ID?token={patient_token}
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple

from database import get_session
from database.models import Patient, Consent, ConsentStatus


# Token configuration
TOKEN_LENGTH = 16  # 16 chars of base62 = 62^16 possibilities
TOKEN_EXPIRATION_DAYS = 30  # Tokens valid for 30 days


def generate_token() -> str:
    """Generate a URL-safe random token.

    Uses base62 (alphanumeric) to avoid URL encoding issues.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(TOKEN_LENGTH))


def create_patient_token(
    patient_id: int,
    expiration_days: int = TOKEN_EXPIRATION_DAYS
) -> Tuple[str, datetime]:
    """Create a consent token for a patient.

    Args:
        patient_id: Database ID of the patient
        expiration_days: Days until token expires

    Returns:
        Tuple of (token, expiration_datetime)
    """
    session = get_session()
    try:
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError(f"Patient ID {patient_id} not found")

        # Generate unique token (retry if collision)
        for _ in range(10):
            token = generate_token()
            existing = session.query(Patient).filter(
                Patient.consent_token == token
            ).first()
            if not existing:
                break
        else:
            raise RuntimeError("Failed to generate unique token after 10 attempts")

        # Set expiration
        expires = datetime.utcnow() + timedelta(days=expiration_days)

        # Update patient record
        patient.consent_token = token
        patient.consent_token_expires = expires

        # Update consent status to invitation_sent if pending
        if patient.consent and patient.consent.status == ConsentStatus.PENDING:
            patient.consent.status = ConsentStatus.INVITATION_SENT
            patient.consent.last_outreach_date = datetime.utcnow()
            patient.consent.outreach_method = "consent_token"
            patient.consent.outreach_attempts = (patient.consent.outreach_attempts or 0) + 1

        session.commit()
        return token, expires

    finally:
        session.close()


def regenerate_patient_token(patient_id: int) -> Tuple[str, datetime]:
    """Regenerate a consent token for a patient (replaces existing).

    Args:
        patient_id: Database ID of the patient

    Returns:
        Tuple of (new_token, new_expiration_datetime)
    """
    return create_patient_token(patient_id)


def create_single_token(
    patient_id: int,
    expiration_days: int = TOKEN_EXPIRATION_DAYS
) -> dict:
    """Create a single consent token for a patient (used by Single Invite UI).

    Args:
        patient_id: Database ID of the patient
        expiration_days: Days until token expires

    Returns:
        Dict with {"token": str, "expires": datetime, "error": str|None}
    """
    try:
        token, expires = create_patient_token(patient_id, expiration_days)
        return {"token": token, "expires": expires, "error": None}
    except Exception as e:
        return {"token": None, "expires": None, "error": str(e)}


def batch_create_tokens(
    patient_ids: list,
    expiration_days: int = TOKEN_EXPIRATION_DAYS
) -> dict:
    """Create tokens for multiple patients at once.

    Args:
        patient_ids: List of patient database IDs
        expiration_days: Days until tokens expire

    Returns:
        Dict with {patient_id: {"token": str, "expires": datetime, "error": str|None}}
    """
    results = {}

    session = get_session()
    try:
        expires = datetime.utcnow() + timedelta(days=expiration_days)

        for patient_id in patient_ids:
            try:
                patient = session.query(Patient).filter(Patient.id == patient_id).first()
                if not patient:
                    results[patient_id] = {"token": None, "expires": None, "error": "Patient not found"}
                    continue

                # Generate unique token
                for _ in range(10):
                    token = generate_token()
                    existing = session.query(Patient).filter(
                        Patient.consent_token == token
                    ).first()
                    if not existing:
                        break
                else:
                    results[patient_id] = {"token": None, "expires": None, "error": "Token generation failed"}
                    continue

                # Update patient
                patient.consent_token = token
                patient.consent_token_expires = expires

                # Update consent status
                if patient.consent and patient.consent.status == ConsentStatus.PENDING:
                    patient.consent.status = ConsentStatus.INVITATION_SENT
                    patient.consent.last_outreach_date = datetime.utcnow()
                    patient.consent.outreach_method = "consent_token"
                    patient.consent.outreach_attempts = (patient.consent.outreach_attempts or 0) + 1

                results[patient_id] = {"token": token, "expires": expires, "error": None}

            except Exception as e:
                results[patient_id] = {"token": None, "expires": None, "error": str(e)}

        session.commit()

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

    return results


def validate_token(token: str) -> Optional[Patient]:
    """Validate a consent token and return the associated patient.

    Args:
        token: The consent token to validate

    Returns:
        Patient object if valid, None if invalid or expired
    """
    if not token:
        return None

    session = get_session()
    try:
        patient = session.query(Patient).filter(
            Patient.consent_token == token
        ).first()

        if not patient:
            return None

        # Check expiration
        if patient.consent_token_expires and patient.consent_token_expires < datetime.utcnow():
            return None

        return patient

    finally:
        session.close()


def build_form_url(base_url: str, token: str, patient: Patient = None) -> str:
    """Build the full Microsoft Forms URL with token.

    Args:
        base_url: Base Microsoft Forms URL (e.g., https://forms.microsoft.com/r/ABC123)
        token: Patient's consent token
        patient: Optional patient object for additional params

    Returns:
        Full URL with token appended
    """
    # Append token as query parameter
    if "?" in base_url:
        url = f"{base_url}&token={token}"
    else:
        url = f"{base_url}?token={token}"

    return url


def get_outreach_summary() -> dict:
    """Get summary statistics for consent outreach.

    Returns:
        Dict with outreach statistics
    """
    session = get_session()
    try:
        total = session.query(Patient).count()

        with_token = session.query(Patient).filter(
            Patient.consent_token.isnot(None)
        ).count()

        token_expired = session.query(Patient).filter(
            Patient.consent_token.isnot(None),
            Patient.consent_token_expires < datetime.utcnow()
        ).count()

        # Consent status breakdown
        from sqlalchemy import func
        consent_stats = session.query(
            Consent.status, func.count(Consent.id)
        ).group_by(Consent.status).all()

        consent_by_status = {status.value: count for status, count in consent_stats}

        # APCM-specific
        apcm_pending = session.query(Patient).filter(
            Patient.apcm_enrolled == True,
            Patient.apcm_continue_with_hometeam.is_(None)
        ).count()

        apcm_decided = session.query(Patient).filter(
            Patient.apcm_enrolled == True,
            Patient.apcm_continue_with_hometeam.isnot(None)
        ).count()

        return {
            "total_patients": total,
            "with_token": with_token,
            "token_valid": with_token - token_expired,
            "token_expired": token_expired,
            "pending_token": total - with_token,
            "consent_by_status": consent_by_status,
            "apcm_pending_decision": apcm_pending,
            "apcm_decided": apcm_decided,
        }

    finally:
        session.close()


def get_patients_needing_tokens(filter_type: str = "all") -> list:
    """Get list of patients who need consent tokens generated.

    Args:
        filter_type: "all", "apcm_only", "spruce_matched", "no_token"

    Returns:
        List of Patient objects
    """
    session = get_session()
    try:
        query = session.query(Patient)

        if filter_type == "no_token":
            query = query.filter(Patient.consent_token.is_(None))
        elif filter_type == "apcm_only":
            query = query.filter(
                Patient.apcm_enrolled == True,
                Patient.consent_token.is_(None)
            )
        elif filter_type == "spruce_matched":
            query = query.filter(
                Patient.spruce_matched == True,
                Patient.consent_token.is_(None)
            )

        return query.all()

    finally:
        session.close()
