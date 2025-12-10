"""Database connection and session management for Patient Explorer."""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Default database path in project data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "patients.db"))

# Ensure data directory exists
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# Create SQLite engine with settings for Streamlit
# check_same_thread=False is required for Streamlit's multi-threaded execution
engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    """Get a new database session.

    Usage:
        session = get_session()
        try:
            # do work
            session.commit()
        finally:
            session.close()
    """
    return SessionLocal()


def init_db():
    """Create all tables if they don't exist."""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    return True
