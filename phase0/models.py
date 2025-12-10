"""
Pydantic models for Phase 0 consent tracking.

These models define the data structures for:
- Patient records (from Excel)
- Consent status tracking
- Spruce contact matching
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class ConsentStatus(str, Enum):
    """Consent status for patient record retention."""
    PENDING = "pending"           # Not yet contacted
    CONTACTED = "contacted"       # Outreach sent, awaiting response
    CONSENTED = "consented"       # Patient agreed to record retention
    DECLINED = "declined"         # Patient declined
    NO_RESPONSE = "no_response"   # No response after cutoff period


class ConsentMethod(str, Enum):
    """Method by which consent was obtained."""
    VERBAL = "verbal"
    WRITTEN = "written"
    TEXT = "text"           # SMS via Spruce
    ELECTRONIC = "electronic"  # DocuSign
    NOT_APPLICABLE = "n/a"


class Patient(BaseModel):
    """Patient record from Excel import."""

    # Identifiers
    mrn: str = Field(..., description="Medical Record Number")
    first_name: str = Field(..., description="Patient first name")
    last_name: str = Field(..., description="Patient last name")
    middle_name: Optional[str] = Field(None, description="Patient middle name")

    # Demographics
    date_of_birth: Optional[date] = Field(None, description="Date of birth")

    # Contact info
    phone: Optional[str] = Field(None, description="Primary phone number")
    email: Optional[str] = Field(None, description="Email address")

    # Address
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None)
    state: Optional[str] = Field(None)
    zip_code: Optional[str] = Field(None)

    # Insurance
    insurer_id: Optional[str] = Field(None)
    insurer_name: Optional[str] = Field(None)

    # Clinical
    last_visit_date: Optional[date] = Field(None, description="Last date of service")
    apcm_eligible: bool = Field(False, description="Eligible for APCM billing")
    apcm_enrolled: bool = Field(False, description="Currently enrolled in APCM")

    @property
    def full_name(self) -> str:
        """Return full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)


class ConsentRecord(BaseModel):
    """Consent tracking record."""

    # Link to patient
    mrn: str = Field(..., description="Patient MRN")
    patient_name: str = Field(..., description="Patient full name for display")

    # Consent status
    status: ConsentStatus = Field(ConsentStatus.PENDING)
    method: ConsentMethod = Field(ConsentMethod.NOT_APPLICABLE)

    # Tracking
    outreach_date: Optional[datetime] = Field(None, description="When outreach was sent")
    response_date: Optional[datetime] = Field(None, description="When patient responded")
    consent_date: Optional[date] = Field(None, description="Date consent was granted")

    # Details
    notes: Optional[str] = Field(None, description="Free-text notes")
    witnessed_by: Optional[str] = Field(None, description="Witness name if applicable")

    # Spruce matching
    spruce_patient_id: Optional[str] = Field(None, description="Matched Spruce patient ID")
    spruce_matched: bool = Field(False, description="Whether patient was found in Spruce")

    # Audit
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None)


class SpruceContact(BaseModel):
    """Contact record from Spruce Health API."""

    spruce_id: str = Field(..., description="Spruce patient/contact ID")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None

    # Matching helpers
    @property
    def full_name(self) -> str:
        """Return full name."""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else ""


class MatchResult(BaseModel):
    """Result of matching a patient to Spruce contact."""

    patient: Patient
    spruce_contact: Optional[SpruceContact] = None
    match_confidence: float = Field(0.0, ge=0.0, le=1.0)
    match_method: Optional[str] = Field(None, description="How match was determined")

    @property
    def is_matched(self) -> bool:
        """Check if patient was matched."""
        return self.spruce_contact is not None and self.match_confidence > 0.5
