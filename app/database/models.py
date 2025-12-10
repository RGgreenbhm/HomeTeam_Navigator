"""SQLAlchemy models for Patient Explorer."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class UserRole(enum.Enum):
    """User role levels."""
    ADMIN = "admin"          # Full access, can manage users
    PROVIDER = "provider"    # Full clinical access
    STAFF = "staff"          # Limited access (no PHI export)
    READONLY = "readonly"    # View only, no edits


class ConsentStatus(enum.Enum):
    """Consent status values."""
    PENDING = "pending"
    INVITATION_SENT = "invitation_sent"
    PORTAL_VISITED = "portal_visited"
    CONSENTED = "consented"
    DECLINED = "declined"
    NO_RESPONSE = "no_response"
    PARTIAL = "partial"  # Some elections made but not all


class APCMStatus(enum.Enum):
    """APCM enrollment status values."""
    ACTIVE = "active"
    REMOVED = "removed"
    HOLD = "hold"
    PENDING = "pending"
    NOT_ENROLLED = "not_enrolled"


class APCMLevel(enum.Enum):
    """APCM billing level (corresponds to G-codes)."""
    LEVEL_1 = "G0556"  # One DX
    LEVEL_2 = "G0557"  # 2+ DX
    LEVEL_3 = "G0558"  # QMB (2+ DX)


class Patient(Base):
    """Patient record from the Excel patient list."""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mrn = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(String(20))  # Stored as string from Excel
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))

    # Spruce matching info
    spruce_matched = Column(Boolean, default=False)
    spruce_id = Column(String(100))
    spruce_match_method = Column(String(50))  # 'phone', 'name', 'email'

    # Preferred name (parsed from "First Name" column, e.g., 'Patricia "Pat"' -> 'Pat')
    preferred_name = Column(String(100))

    # APCM (Advanced Primary Care Management) fields
    apcm_enrolled = Column(Boolean, default=False)
    apcm_signup_date = Column(DateTime)
    apcm_level = Column(Enum(APCMLevel))  # G0556, G0557, or G0558
    apcm_icd_codes = Column(Text)  # Comma-separated ICD codes for billing
    apcm_status = Column(Enum(APCMStatus), default=APCMStatus.NOT_ENROLLED)
    apcm_status_notes = Column(Text)  # Comments from spreadsheet
    apcm_insurance = Column(String(100))
    apcm_copay = Column(String(50))

    # APCM Consent Elections (for transition)
    apcm_continue_with_hometeam = Column(Boolean)  # Patient elects to continue APCM
    apcm_revoke_southview_billing = Column(Boolean)  # Patient authorizes billing revocation
    apcm_election_date = Column(DateTime)

    # Consent portal tracking
    consent_token = Column(String(100), unique=True)  # Unique link token
    consent_token_expires = Column(DateTime)
    consent_portal_visited = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    consent = relationship("Consent", back_populates="patient", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="patient")
    notes = relationship("PatientNote", back_populates="patient", order_by="PatientNote.created_at.desc()")

    def __repr__(self):
        return f"<Patient {self.mrn}: {self.last_name}, {self.first_name}>"


class Consent(Base):
    """Consent tracking for patient records retention."""
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, nullable=False)

    # Consent status
    status = Column(
        Enum(ConsentStatus),
        default=ConsentStatus.PENDING,
        nullable=False
    )

    # Contact tracking
    outreach_attempts = Column(Integer, default=0)
    last_outreach_date = Column(DateTime)
    outreach_method = Column(String(50))  # 'spruce_message', 'phone', 'mail'

    # Response tracking
    response_date = Column(DateTime)
    response_method = Column(String(50))  # How they responded
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="consent")

    def __repr__(self):
        return f"<Consent patient_id={self.patient_id} status={self.status.value}>"


class AuditLog(Base):
    """HIPAA-compliant audit log for all data access and changes."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    # Action details
    action = Column(String(50), nullable=False)  # 'view', 'create', 'update', 'delete', 'export'
    entity_type = Column(String(50), nullable=False)  # 'patient', 'consent', etc.
    entity_id = Column(Integer)

    # User info (for future multi-user support)
    user_id = Column(String(100))
    user_name = Column(String(100))

    # Details
    details = Column(Text)  # JSON string with specifics
    ip_address = Column(String(50))

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type} at {self.timestamp}>"


class PatientNote(Base):
    """Local patient notes (alternative to OneNote integration)."""
    __tablename__ = "patient_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Note content
    title = Column(String(255))
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, outreach, clinical, admin

    # Metadata
    created_by = Column(String(100))  # Username who created
    updated_by = Column(String(100))  # Username who last updated
    is_pinned = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="notes")

    def __repr__(self):
        return f"<PatientNote {self.id} for patient {self.patient_id}>"


class CarePlan(Base):
    """APCM Care Plan for a patient."""
    __tablename__ = "care_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # APCM Enrollment Info
    enrollment_date = Column(DateTime)
    enrollment_status = Column(String(50), default="active")  # active, pending, un-enrolled
    consent_location = Column(Text)  # Where consent documentation is stored

    # Care Team
    primary_care_provider = Column(String(100))  # LaChandra Watts, CRNP | Lindsay Bearden, CRNP
    primary_care_nurse = Column(String(100))  # Jenny Linard, RN
    support_team_leader = Column(String(100), default="Robert Green, MD")
    support_team_staff = Column(String(100))
    community_director = Column(String(100))
    population_health_manager = Column(String(100))
    office_coordinator = Column(String(100))

    # APCM Assessments
    functional_status = Column(String(50))  # ambulatory, non-ambulatory
    assistive_devices = Column(Text)  # none or list
    cognitive_status = Column(String(50))  # normal, impaired
    medication_management = Column(String(50))  # self, caregiver, staff managed
    environmental_concerns = Column(Text)
    prognosis = Column(Text)
    treatment_goals = Column(Text)
    code_status = Column(String(50))  # FULL CODE, DNR, Need to clarify

    # Medical Power of Attorney
    mpoa_name = Column(String(100))
    mpoa_relation = Column(String(100))
    mpoa_phone = Column(String(50))

    # Version tracking
    version = Column(Integer, default=1)
    last_reviewed_date = Column(DateTime)
    last_reviewed_by = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))

    # Relationships
    patient = relationship("Patient", backref="care_plans")
    problems = relationship("CarePlanProblem", back_populates="care_plan", cascade="all, delete-orphan")
    medications = relationship("CarePlanMedication", back_populates="care_plan", cascade="all, delete-orphan")
    allergies = relationship("CarePlanAllergy", back_populates="care_plan", cascade="all, delete-orphan")
    contacts = relationship("CarePlanContact", back_populates="care_plan", cascade="all, delete-orphan")
    immunizations = relationship("CarePlanImmunization", back_populates="care_plan", cascade="all, delete-orphan")
    standing_orders = relationship("CarePlanStandingOrder", back_populates="care_plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CarePlan {self.id} for patient {self.patient_id}>"


class CarePlanProblem(Base):
    """Active or historical medical problem in care plan."""
    __tablename__ = "care_plan_problems"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)

    # Problem identification
    diagnosis_name = Column(String(255), nullable=False)
    icd_code = Column(String(20))
    is_active = Column(Boolean, default=True)
    onset_date = Column(DateTime)

    # Care plan sections (from template)
    story = Column(Text)  # Clinical narrative
    timeline = Column(Text)  # Dated entries: MM/DD/YYYY: event
    impression = Column(Text)  # Current assessment
    management_reminders = Column(Text)  # Key reminders
    protocol = Column(Text)  # Checklist items with checkboxes
    patient_goals = Column(Text)  # Patient-specific goals
    care_team_tasks = Column(Text)  # Tasks for care team

    # Sorting
    sort_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    care_plan = relationship("CarePlan", back_populates="problems")

    def __repr__(self):
        return f"<CarePlanProblem {self.diagnosis_name} ({self.icd_code})>"


class CarePlanMedication(Base):
    """Medication entry in care plan."""
    __tablename__ = "care_plan_medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)

    # Medication details
    medication_name = Column(String(255), nullable=False)
    generic_name = Column(String(255))
    strength = Column(String(100))
    form = Column(String(100))  # tablet, capsule, solution
    dose = Column(String(100))
    instructions = Column(Text)  # "Take 1 tablet by mouth daily"
    route = Column(String(50))  # oral, topical, injection

    # Prescription details
    quantity = Column(Integer)
    days_supply = Column(Integer)
    refills = Column(Integer)
    prescribed_date = Column(DateTime)
    pharmacy = Column(String(255))
    runs_out_date = Column(DateTime)

    # Status
    is_active = Column(Boolean, default=True)
    is_prn = Column(Boolean, default=False)  # As needed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    care_plan = relationship("CarePlan", back_populates="medications")

    def __repr__(self):
        return f"<CarePlanMedication {self.medication_name}>"


class CarePlanAllergy(Base):
    """Allergy entry in care plan."""
    __tablename__ = "care_plan_allergies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)

    allergen = Column(String(255), nullable=False)
    reaction = Column(Text)
    severity = Column(String(50))  # mild, moderate, severe
    onset_date = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    care_plan = relationship("CarePlan", back_populates="allergies")

    def __repr__(self):
        return f"<CarePlanAllergy {self.allergen}>"


class CarePlanContact(Base):
    """Contact person involved in patient's care."""
    __tablename__ = "care_plan_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)

    # Contact info
    name = Column(String(255), nullable=False)
    relation = Column(String(100))  # spouse, child, caregiver, specialist
    contact_type = Column(String(50))  # family, provider, agency
    phone = Column(String(50))
    email = Column(String(255))

    # For providers
    specialty = Column(String(100))
    organization = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    care_plan = relationship("CarePlan", back_populates="contacts")

    def __repr__(self):
        return f"<CarePlanContact {self.name} ({self.contact_type})>"


class CarePlanImmunization(Base):
    """Immunization/health maintenance entry in care plan."""
    __tablename__ = "care_plan_immunizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)

    # Immunization/screening info
    item_type = Column(String(50))  # vaccine, screening
    name = Column(String(255), nullable=False)  # Influenza, Colonoscopy, etc.
    status = Column(String(50))  # Completed, Declined, Up To Date, Planned, Overdue
    timeline = Column(Text)  # Dated entries
    comments = Column(Text)
    next_due_date = Column(DateTime)
    last_completed_date = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    care_plan = relationship("CarePlan", back_populates="immunizations")

    def __repr__(self):
        return f"<CarePlanImmunization {self.name} ({self.status})>"


class CarePlanStandingOrder(Base):
    """Personalized standing order for care plan."""
    __tablename__ = "care_plan_standing_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=False)

    # Standing order details
    name = Column(String(255), nullable=False)  # e.g., "Urinalysis orders"
    trigger = Column(Text)  # When to activate
    decision_points = Column(Text)  # Decision tree
    actions = Column(Text)  # Steps to take
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    care_plan = relationship("CarePlan", back_populates="standing_orders")

    def __repr__(self):
        return f"<CarePlanStandingOrder {self.name}>"


class User(Base):
    """App user for authentication and access control."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    display_name = Column(String(100), nullable=False)

    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.READONLY, nullable=False)
    is_active = Column(Boolean, default=True)

    # Microsoft Graph association (optional)
    microsoft_user_id = Column(String(100))  # For future delegated auth
    microsoft_email = Column(String(255))

    # Feature permissions (JSON flags)
    can_view_patients = Column(Boolean, default=True)
    can_edit_patients = Column(Boolean, default=False)
    can_view_consents = Column(Boolean, default=True)
    can_edit_consents = Column(Boolean, default=False)
    can_send_messages = Column(Boolean, default=False)  # Spruce
    can_export_data = Column(Boolean, default=False)   # PHI export
    can_view_tasks = Column(Boolean, default=True)      # Planner/Tasks
    can_manage_tasks = Column(Boolean, default=False)
    can_use_ai = Column(Boolean, default=True)          # AI features
    can_use_scanner = Column(Boolean, default=True)     # Document scanner

    # Session tracking
    last_login = Column(DateTime)
    last_activity = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        # Admins have all permissions
        if self.role == UserRole.ADMIN:
            return True

        # Check specific permission attribute
        perm_attr = f"can_{permission}"
        if hasattr(self, perm_attr):
            return getattr(self, perm_attr)

        return False
