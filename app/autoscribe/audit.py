"""HIPAA Audit Logging for AutoScribe.

Tracks all access and actions for compliance reporting.
Stores in SQLite with 6-year retention requirement.
"""

import os
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import json

from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class AuditEvent(Enum):
    """Types of auditable events."""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    AUDIO_RECORDED = "audio_recorded"
    AUDIO_UPLOADED = "audio_uploaded"
    TRANSCRIPTION_REQUESTED = "transcription_requested"
    NOTE_GENERATED = "note_generated"
    NOTE_EXPORTED = "note_exported"
    NOTE_COPIED = "note_copied"
    PROMPT_CREATED = "prompt_created"
    PROMPT_MODIFIED = "prompt_modified"
    PROMPT_DELETED = "prompt_deleted"
    PROMPT_SELECTED = "prompt_selected"
    AUDIT_REPORT_GENERATED = "audit_report_generated"
    AUDIT_LOG_VIEWED = "audit_log_viewed"


class AuditLogEntry(Base):
    """SQLAlchemy model for audit log entries."""
    __tablename__ = "autoscribe_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    user_email = Column(String(255), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    details = Column(Text, nullable=True)  # JSON string
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "event_type": self.event_type,
            "details": json.loads(self.details) if self.details else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
        }


@dataclass
class AuditSummary:
    """Summary of audit activity for reporting."""
    user_id: str
    user_email: Optional[str]
    date_range_start: datetime
    date_range_end: datetime
    total_events: int
    events_by_type: Dict[str, int]
    sessions_count: int
    notes_generated: int
    audio_recordings: int
    suspicious_flags: List[str]


class AuditLogger:
    """HIPAA-compliant audit logger for AutoScribe.

    Logs all user actions and access to audio/transcripts for compliance.
    Provides reporting capabilities for audit reviews.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the audit logger.

        Args:
            db_path: Path to SQLite database. Defaults to app data directory.
        """
        if db_path is None:
            # Use the main app database or a separate audit database
            from pathlib import Path
            app_dir = Path(__file__).parent.parent
            db_path = str(app_dir / "autoscribe_audit.db")

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        logger.info(f"Audit logger initialized with database: {db_path}")

    def log(
        self,
        user_id: str,
        event_type: AuditEvent,
        details: Optional[Dict[str, Any]] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """Log an audit event.

        Args:
            user_id: ID of the user performing the action
            event_type: Type of event being logged
            details: Additional details about the event
            user_email: User's email address
            ip_address: Client IP address
            user_agent: Client user agent string
            session_id: Session identifier

        Returns:
            ID of the created log entry
        """
        session = self.Session()
        try:
            entry = AuditLogEntry(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                user_email=user_email,
                event_type=event_type.value,
                details=json.dumps(details) if details else None,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
            )
            session.add(entry)
            session.commit()

            logger.debug(f"Audit log: {event_type.value} by {user_id}")
            return entry.id

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log audit event: {e}")
            raise
        finally:
            session.close()

    def log_session_start(
        self,
        user_id: str,
        user_email: Optional[str] = None,
        session_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Log a session start event."""
        return self.log(
            user_id=user_id,
            event_type=AuditEvent.SESSION_START,
            details={"device_info": device_info} if device_info else None,
            user_email=user_email,
            session_id=session_id,
        )

    def log_session_end(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> int:
        """Log a session end event."""
        return self.log(
            user_id=user_id,
            event_type=AuditEvent.SESSION_END,
            details={"duration_seconds": duration_seconds} if duration_seconds else None,
            session_id=session_id,
        )

    def log_audio_recorded(
        self,
        user_id: str,
        duration_seconds: float,
        segment_count: int,
        session_id: Optional[str] = None,
    ) -> int:
        """Log an audio recording event."""
        return self.log(
            user_id=user_id,
            event_type=AuditEvent.AUDIO_RECORDED,
            details={
                "duration_seconds": duration_seconds,
                "segment_count": segment_count,
            },
            session_id=session_id,
        )

    def log_audio_uploaded(
        self,
        user_id: str,
        blob_url: str,
        file_size_bytes: int,
        session_id: Optional[str] = None,
    ) -> int:
        """Log an audio upload event."""
        return self.log(
            user_id=user_id,
            event_type=AuditEvent.AUDIO_UPLOADED,
            details={
                "blob_url": blob_url,
                "file_size_bytes": file_size_bytes,
            },
            session_id=session_id,
        )

    def log_note_generated(
        self,
        user_id: str,
        prompt_type: str,
        token_count: Optional[int] = None,
        patient_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """Log a note generation event."""
        details = {"prompt_type": prompt_type}
        if token_count:
            details["token_count"] = token_count
        if patient_id:
            details["patient_id"] = patient_id

        return self.log(
            user_id=user_id,
            event_type=AuditEvent.NOTE_GENERATED,
            details=details,
            session_id=session_id,
        )

    def log_note_exported(
        self,
        user_id: str,
        export_type: str,
        patient_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """Log a note export event."""
        details = {"export_type": export_type}
        if patient_id:
            details["patient_id"] = patient_id

        return self.log(
            user_id=user_id,
            event_type=AuditEvent.NOTE_EXPORTED,
            details=details,
            session_id=session_id,
        )

    def get_user_events(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEvent]] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Get audit events for a specific user.

        Args:
            user_id: User ID to query
            start_date: Start of date range
            end_date: End of date range
            event_types: Filter by event types
            limit: Maximum number of results

        Returns:
            List of audit log entries as dictionaries
        """
        session = self.Session()
        try:
            query = session.query(AuditLogEntry).filter(
                AuditLogEntry.user_id == user_id
            )

            if start_date:
                query = query.filter(AuditLogEntry.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLogEntry.timestamp <= end_date)
            if event_types:
                event_values = [e.value for e in event_types]
                query = query.filter(AuditLogEntry.event_type.in_(event_values))

            query = query.order_by(AuditLogEntry.timestamp.desc()).limit(limit)

            return [entry.to_dict() for entry in query.all()]

        finally:
            session.close()

    def get_all_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEvent]] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Get all audit events within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            event_types: Filter by event types
            limit: Maximum number of results

        Returns:
            List of audit log entries as dictionaries
        """
        session = self.Session()
        try:
            query = session.query(AuditLogEntry)

            if start_date:
                query = query.filter(AuditLogEntry.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLogEntry.timestamp <= end_date)
            if event_types:
                event_values = [e.value for e in event_types]
                query = query.filter(AuditLogEntry.event_type.in_(event_values))

            query = query.order_by(AuditLogEntry.timestamp.desc()).limit(limit)

            return [entry.to_dict() for entry in query.all()]

        finally:
            session.close()

    def generate_user_summary(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> AuditSummary:
        """Generate an audit summary for a user.

        Args:
            user_id: User ID to summarize
            start_date: Start of date range
            end_date: End of date range

        Returns:
            AuditSummary with aggregated statistics
        """
        session = self.Session()
        try:
            # Get all events in range
            events = session.query(AuditLogEntry).filter(
                AuditLogEntry.user_id == user_id,
                AuditLogEntry.timestamp >= start_date,
                AuditLogEntry.timestamp <= end_date,
            ).all()

            # Aggregate statistics
            events_by_type: Dict[str, int] = {}
            sessions = set()
            notes_generated = 0
            audio_recordings = 0
            user_email = None

            for event in events:
                # Count by type
                events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1

                # Track sessions
                if event.session_id:
                    sessions.add(event.session_id)

                # Count specific events
                if event.event_type == AuditEvent.NOTE_GENERATED.value:
                    notes_generated += 1
                elif event.event_type == AuditEvent.AUDIO_RECORDED.value:
                    audio_recordings += 1

                # Get user email
                if event.user_email and not user_email:
                    user_email = event.user_email

            # Check for suspicious patterns
            suspicious_flags = self._detect_suspicious_patterns(events)

            return AuditSummary(
                user_id=user_id,
                user_email=user_email,
                date_range_start=start_date,
                date_range_end=end_date,
                total_events=len(events),
                events_by_type=events_by_type,
                sessions_count=len(sessions),
                notes_generated=notes_generated,
                audio_recordings=audio_recordings,
                suspicious_flags=suspicious_flags,
            )

        finally:
            session.close()

    def _detect_suspicious_patterns(self, events: List[AuditLogEntry]) -> List[str]:
        """Detect suspicious patterns in audit events.

        Args:
            events: List of audit log entries to analyze

        Returns:
            List of suspicious pattern descriptions
        """
        flags = []

        # Check for unusual hours (before 6am or after 10pm)
        unusual_hour_events = [
            e for e in events
            if e.timestamp and (e.timestamp.hour < 6 or e.timestamp.hour > 22)
        ]
        if len(unusual_hour_events) > 5:
            flags.append(f"Unusual hours access: {len(unusual_hour_events)} events outside 6am-10pm")

        # Check for bulk exports
        export_events = [e for e in events if e.event_type == AuditEvent.NOTE_EXPORTED.value]
        if len(export_events) > 50:
            flags.append(f"High export volume: {len(export_events)} exports")

        # Check for rapid activity (many events in short time)
        if len(events) > 2:
            sorted_events = sorted(events, key=lambda e: e.timestamp)
            for i in range(len(sorted_events) - 10):
                time_span = (sorted_events[i + 10].timestamp - sorted_events[i].timestamp).total_seconds()
                if time_span < 60:  # More than 10 events per minute
                    flags.append("Rapid activity detected: >10 events per minute")
                    break

        return flags

    def cleanup_old_entries(self, retention_years: int = 6) -> int:
        """Remove audit entries older than retention period.

        Args:
            retention_years: Number of years to retain (HIPAA requires 6)

        Returns:
            Number of entries deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_years * 365)

        session = self.Session()
        try:
            deleted = session.query(AuditLogEntry).filter(
                AuditLogEntry.timestamp < cutoff_date
            ).delete()
            session.commit()

            logger.info(f"Cleaned up {deleted} audit entries older than {retention_years} years")
            return deleted

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to cleanup old entries: {e}")
            raise
        finally:
            session.close()


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
