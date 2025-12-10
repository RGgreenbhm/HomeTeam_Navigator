"""AutoScribe Module - Medical note creation with audio capture and AI summarization.

This module provides:
- Audio recording with device selection
- Azure Speech Services transcription
- Azure OpenAI GPT-4.1 summarization
- Prompt library management (SBAR, Office Note, Video Note)
- HIPAA audit logging

HIPAA Compliance:
- All audio contains PHI - encrypted at rest (Azure), in transit (TLS)
- Uses Azure services under Microsoft BAA
- Audit logging for all access
"""

__version__ = "0.1.0"

from .prompt_manager import PromptManager, PromptType, get_prompt_manager
from .audit import AuditLogger, AuditEvent, get_audit_logger
from .azure_openai import AzureOpenAIClient, get_azure_openai_client
from .audio_recorder import AudioRecorder, get_audio_recorder
from .azure_speech import AzureSpeechClient, get_azure_speech_client
from .cost_tracking import CostTracker, get_cost_tracker, ModelType, MODEL_PRICING

__all__ = [
    # Prompt Management
    "PromptManager",
    "PromptType",
    "get_prompt_manager",
    # Audit Logging
    "AuditLogger",
    "AuditEvent",
    "get_audit_logger",
    # AI Services
    "AzureOpenAIClient",
    "get_azure_openai_client",
    # Audio Recording
    "AudioRecorder",
    "get_audio_recorder",
    # Speech Transcription
    "AzureSpeechClient",
    "get_azure_speech_client",
    # Cost Tracking
    "CostTracker",
    "get_cost_tracker",
    "ModelType",
    "MODEL_PRICING",
]
