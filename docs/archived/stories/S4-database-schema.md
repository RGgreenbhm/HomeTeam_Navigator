# Story S4: SQLite Database Schema with SQLAlchemy

## Status
Draft

## Story
**As a** developer,
**I want** a SQLite database with proper schema for patients and consent,
**so that** data persists locally between sessions.

## Acceptance Criteria
1. SQLAlchemy models for Patient, Consent, AuditLog
2. Database file created in data/patients.db
3. Automatic table creation on first run
4. Migration support for schema changes
5. Connection pooling for Streamlit sessions

## Tasks / Subtasks
- [ ] Create database connection module (AC: 2, 5)
  - [ ] app/database/connection.py
  - [ ] SQLite connection with check_same_thread=False
  - [ ] Session factory for dependency injection
- [ ] Define SQLAlchemy models (AC: 1)
  - [ ] Patient model with all fields
  - [ ] Consent model with status tracking
  - [ ] AuditLog for HIPAA compliance
- [ ] Initialize database (AC: 3)
  - [ ] Create tables if not exist
  - [ ] Run on app startup
- [ ] Data import from existing CSV (AC: 1)
  - [ ] Load match_results.csv
  - [ ] Create Patient records
  - [ ] Set spruce_matched flag

## Dev Notes

### SQLAlchemy Setup
```python
# app/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/patients.db")

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False}  # Required for Streamlit
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    """Get database session."""
    return SessionLocal()

def init_db():
    """Create tables if they don't exist."""
    from .models import Base
    Base.metadata.create_all(bind=engine)
```

### Model Definitions
See architecture-streamlit.md §4.1 for full model definitions.

### Import from Match Results
```python
def import_from_match_results(csv_path: str):
    """Import patients from CLI match results."""
    import pandas as pd
    from phase0.excel_loader import load_patients_from_excel

    # Load original patient data
    patients = load_patients_from_excel("data/2025-11-30_GreenPatients.xls")

    # Load match results
    matches = pd.read_csv(csv_path)
    match_dict = {row['mrn']: row for _, row in matches.iterrows()}

    session = get_session()
    for patient in patients:
        match = match_dict.get(patient.mrn, {})
        db_patient = Patient(
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            phone=patient.phone,
            email=patient.email,
            address=patient.address,
            city=patient.city,
            state=patient.state,
            zip_code=patient.zip_code,
            spruce_matched=match.get('matched', False),
            spruce_id=match.get('spruce_id', None),
            spruce_match_method=match.get('match_method', None),
        )
        session.add(db_patient)

    session.commit()
```

## Testing
- **Required Tests**:
  - Database file created on init
  - Models create correct tables
  - CRUD operations work
  - Session management handles concurrent access

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story | Claude |
