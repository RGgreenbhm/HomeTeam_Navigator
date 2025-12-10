"""Cost Tracking Module for AutoScribe.

Tracks API usage and costs for Azure OpenAI services.
Provides reporting by user, time period, and model type.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine, func
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class ModelType(Enum):
    """Types of AI models used."""
    SUMMARIZE = "summarize"       # gpt-4.1
    TRANSCRIBE = "transcribe"     # gpt-4o-transcribe
    TRANSCRIBE_MINI = "transcribe_mini"  # gpt-4o-mini-transcribe
    TTS = "tts"                   # gpt-4o-mini-tts
    SPEECH_TO_TEXT = "speech_to_text"  # Azure Speech Services


# Pricing per model (as of Dec 2025)
# Source: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
# Azure Speech: https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/
MODEL_PRICING = {
    # GPT-4.1 (summarization)
    "gpt-4.1": {
        "input_per_1m_tokens": 2.00,   # $2.00 per 1M input tokens
        "output_per_1m_tokens": 8.00,  # $8.00 per 1M output tokens
    },
    # GPT-4o Transcribe (high accuracy)
    "gpt-4o-transcribe": {
        "per_minute_audio": 0.006,     # $0.006 per minute of audio
        "input_per_1m_tokens": 2.50,
        "output_per_1m_tokens": 10.00,
    },
    # GPT-4o Mini Transcribe (cost-effective)
    "gpt-4o-mini-transcribe": {
        "per_minute_audio": 0.003,     # $0.003 per minute of audio
        "input_per_1m_tokens": 1.25,
        "output_per_1m_tokens": 5.00,
    },
    # GPT-4o Mini TTS
    "gpt-4o-mini-tts": {
        "per_1m_characters": 15.00,    # $15 per 1M characters
    },
    # Azure Speech Services (Speech-to-Text Standard)
    "azure-speech-to-text": {
        "per_minute_audio": 0.016,     # $0.016 per minute (~$1/hour)
    },
}


class UsageRecord(Base):
    """SQLAlchemy model for usage tracking."""
    __tablename__ = "autoscribe_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    user_email = Column(String(255), nullable=True)
    is_admin = Column(Integer, default=0)  # 1 if admin user

    # Model info
    model_type = Column(String(50), nullable=False, index=True)  # summarize, transcribe, tts
    model_name = Column(String(100), nullable=False)  # actual deployment name

    # Usage metrics
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    audio_seconds = Column(Float, default=0)  # for transcription
    characters = Column(Integer, default=0)   # for TTS

    # Cost (calculated at time of usage)
    cost_usd = Column(Float, nullable=False, default=0)

    # Context
    session_id = Column(String(100), nullable=True)
    operation = Column(String(100), nullable=True)  # e.g., "generate_sbar", "transcribe_audio"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "is_admin": bool(self.is_admin),
            "model_type": self.model_type,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "audio_seconds": self.audio_seconds,
            "characters": self.characters,
            "cost_usd": self.cost_usd,
            "session_id": self.session_id,
            "operation": self.operation,
        }


@dataclass
class UsageSummary:
    """Summary of usage for reporting."""
    period_start: datetime
    period_end: datetime
    total_cost: float
    total_requests: int
    by_model: Dict[str, Dict[str, Any]]
    by_user: Dict[str, Dict[str, Any]]
    admin_cost: float
    user_cost: float


class CostTracker:
    """Tracks and reports on AI usage costs.

    Features:
    - Log each API call with token counts and costs
    - Calculate costs based on current pricing
    - Generate reports by day/week/month
    - Break down by user vs admin
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the cost tracker.

        Args:
            db_path: Path to SQLite database. Defaults to app data directory.
        """
        if db_path is None:
            from pathlib import Path
            app_dir = Path(__file__).parent.parent
            db_path = str(app_dir / "autoscribe_costs.db")

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        logger.info(f"Cost tracker initialized with database: {db_path}")

    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        audio_seconds: float = 0,
        characters: int = 0,
    ) -> float:
        """Calculate cost for a usage record.

        Args:
            model_name: Name of the model deployment
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            audio_seconds: Duration of audio in seconds (for transcription)
            characters: Number of characters (for TTS)

        Returns:
            Cost in USD
        """
        pricing = MODEL_PRICING.get(model_name, {})
        cost = 0.0

        # Token-based cost
        if input_tokens > 0 and "input_per_1m_tokens" in pricing:
            cost += (input_tokens / 1_000_000) * pricing["input_per_1m_tokens"]

        if output_tokens > 0 and "output_per_1m_tokens" in pricing:
            cost += (output_tokens / 1_000_000) * pricing["output_per_1m_tokens"]

        # Audio-based cost (per minute)
        if audio_seconds > 0 and "per_minute_audio" in pricing:
            cost += (audio_seconds / 60) * pricing["per_minute_audio"]

        # Character-based cost (for TTS)
        if characters > 0 and "per_1m_characters" in pricing:
            cost += (characters / 1_000_000) * pricing["per_1m_characters"]

        return round(cost, 6)

    def log_usage(
        self,
        user_id: str,
        model_type: ModelType,
        model_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        audio_seconds: float = 0,
        characters: int = 0,
        user_email: Optional[str] = None,
        is_admin: bool = False,
        session_id: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> UsageRecord:
        """Log a usage record.

        Args:
            user_id: ID of the user
            model_type: Type of model (summarize, transcribe, tts)
            model_name: Actual deployment name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            audio_seconds: Duration of audio (for transcription)
            characters: Number of characters (for TTS)
            user_email: User's email
            is_admin: Whether user is admin
            session_id: Session identifier
            operation: Description of operation

        Returns:
            Created UsageRecord
        """
        # Calculate cost
        cost = self.calculate_cost(
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            audio_seconds=audio_seconds,
            characters=characters,
        )

        session = self.Session()
        try:
            record = UsageRecord(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                user_email=user_email,
                is_admin=1 if is_admin else 0,
                model_type=model_type.value,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                audio_seconds=audio_seconds,
                characters=characters,
                cost_usd=cost,
                session_id=session_id,
                operation=operation,
            )
            session.add(record)
            session.commit()

            logger.debug(
                f"Logged usage: {model_type.value} by {user_id}, "
                f"cost=${cost:.6f}"
            )
            return record

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log usage: {e}")
            raise
        finally:
            session.close()

    def get_summary(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> UsageSummary:
        """Get usage summary for a date range.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            UsageSummary with aggregated data
        """
        session = self.Session()
        try:
            # Get all records in range
            records = session.query(UsageRecord).filter(
                UsageRecord.timestamp >= start_date,
                UsageRecord.timestamp <= end_date,
            ).all()

            # Aggregate by model
            by_model: Dict[str, Dict[str, Any]] = {}
            by_user: Dict[str, Dict[str, Any]] = {}
            admin_cost = 0.0
            user_cost = 0.0

            for record in records:
                # By model
                if record.model_type not in by_model:
                    by_model[record.model_type] = {
                        "requests": 0,
                        "cost": 0.0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "audio_seconds": 0,
                    }
                by_model[record.model_type]["requests"] += 1
                by_model[record.model_type]["cost"] += record.cost_usd
                by_model[record.model_type]["input_tokens"] += record.input_tokens
                by_model[record.model_type]["output_tokens"] += record.output_tokens
                by_model[record.model_type]["audio_seconds"] += record.audio_seconds

                # By user
                user_key = record.user_email or record.user_id
                if user_key not in by_user:
                    by_user[user_key] = {
                        "requests": 0,
                        "cost": 0.0,
                        "is_admin": bool(record.is_admin),
                    }
                by_user[user_key]["requests"] += 1
                by_user[user_key]["cost"] += record.cost_usd

                # Admin vs user
                if record.is_admin:
                    admin_cost += record.cost_usd
                else:
                    user_cost += record.cost_usd

            return UsageSummary(
                period_start=start_date,
                period_end=end_date,
                total_cost=sum(r.cost_usd for r in records),
                total_requests=len(records),
                by_model=by_model,
                by_user=by_user,
                admin_cost=admin_cost,
                user_cost=user_cost,
            )

        finally:
            session.close()

    def get_daily_costs(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily cost breakdown.

        Args:
            days: Number of days to look back

        Returns:
            List of daily cost records
        """
        session = self.Session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Query with date grouping
            results = session.query(
                func.date(UsageRecord.timestamp).label("date"),
                func.sum(UsageRecord.cost_usd).label("total_cost"),
                func.count(UsageRecord.id).label("requests"),
                func.sum(UsageRecord.input_tokens).label("input_tokens"),
                func.sum(UsageRecord.output_tokens).label("output_tokens"),
            ).filter(
                UsageRecord.timestamp >= start_date
            ).group_by(
                func.date(UsageRecord.timestamp)
            ).order_by(
                func.date(UsageRecord.timestamp)
            ).all()

            return [
                {
                    "date": str(r.date),
                    "total_cost": r.total_cost or 0,
                    "requests": r.requests or 0,
                    "input_tokens": r.input_tokens or 0,
                    "output_tokens": r.output_tokens or 0,
                }
                for r in results
            ]

        finally:
            session.close()

    def get_user_breakdown(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Get cost breakdown by user.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            List of user cost records
        """
        session = self.Session()
        try:
            results = session.query(
                UsageRecord.user_id,
                UsageRecord.user_email,
                UsageRecord.is_admin,
                func.sum(UsageRecord.cost_usd).label("total_cost"),
                func.count(UsageRecord.id).label("requests"),
            ).filter(
                UsageRecord.timestamp >= start_date,
                UsageRecord.timestamp <= end_date,
            ).group_by(
                UsageRecord.user_id,
                UsageRecord.user_email,
                UsageRecord.is_admin,
            ).order_by(
                func.sum(UsageRecord.cost_usd).desc()
            ).all()

            return [
                {
                    "user_id": r.user_id,
                    "user_email": r.user_email,
                    "is_admin": bool(r.is_admin),
                    "total_cost": r.total_cost or 0,
                    "requests": r.requests or 0,
                }
                for r in results
            ]

        finally:
            session.close()


# Singleton instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the singleton CostTracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
