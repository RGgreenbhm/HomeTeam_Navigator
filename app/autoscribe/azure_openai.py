"""Azure OpenAI GPT-4.1 Client for medical note summarization.

Uses Azure OpenAI service (under Microsoft BAA) for HIPAA-compliant
medical note generation from transcripts.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result from note generation."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    finish_reason: str


class AzureOpenAIClient:
    """Client for Azure OpenAI GPT-4.1 medical summarization.

    Uses Azure OpenAI endpoints which are covered under Microsoft HIPAA BAA.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment_summarize: Optional[str] = None,
        deployment_transcribe: Optional[str] = None,
        deployment_tts: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
    ):
        """Initialize the Azure OpenAI client.

        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: API key for authentication
            deployment_summarize: Deployment name for summarization (e.g., "gpt-4.1")
            deployment_transcribe: Deployment name for transcription (e.g., "gpt-4o-mini-transcribe")
            deployment_tts: Deployment name for text-to-speech (e.g., "gpt-4o-mini-tts")
            api_version: API version to use
        """
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
        self.deployment_summarize = deployment_summarize or os.getenv("AZURE_OPENAI_DEPLOYMENT_SUMMARIZE", "gpt-4.1")
        self.deployment_transcribe = deployment_transcribe or os.getenv("AZURE_OPENAI_DEPLOYMENT_TRANSCRIBE", "gpt-4o-mini-transcribe")
        self.deployment_tts = deployment_tts or os.getenv("AZURE_OPENAI_DEPLOYMENT_TTS", "gpt-4o-mini-tts")
        self.api_version = api_version

        # User context for cost tracking (set via set_user_context)
        self._current_user_id: Optional[str] = None
        self._current_user_email: Optional[str] = None
        self._current_is_admin: bool = False
        self._current_session_id: Optional[str] = None

        if not self.endpoint:
            raise ValueError(
                "Azure OpenAI endpoint not configured. "
                "Set AZURE_OPENAI_ENDPOINT environment variable."
            )
        if not self.api_key:
            raise ValueError(
                "Azure OpenAI API key not configured. "
                "Set AZURE_OPENAI_KEY environment variable."
            )

        self._client = None

    def set_user_context(
        self,
        user_id: str,
        user_email: Optional[str] = None,
        is_admin: bool = False,
        session_id: Optional[str] = None,
    ) -> None:
        """Set user context for cost tracking.

        Args:
            user_id: User ID for tracking
            user_email: User email for reports
            is_admin: Whether user is admin
            session_id: Session identifier
        """
        self._current_user_id = user_id
        self._current_user_email = user_email
        self._current_is_admin = is_admin
        self._current_session_id = session_id

    def _get_client(self):
        """Get or create the OpenAI client."""
        if self._client is None:
            try:
                from openai import AzureOpenAI

                self._client = AzureOpenAI(
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key,
                    api_version=self.api_version,
                )
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Run: pip install openai>=1.0.0"
                )

        return self._client

    def generate_note(
        self,
        transcript: str,
        prompt: str,
        patient_name: Optional[str] = None,
        additional_context: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.3,
    ) -> GenerationResult:
        """Generate a medical note from transcript using the specified prompt.

        Args:
            transcript: The transcribed audio content
            prompt: The prompt template to use for generation
            patient_name: Optional patient name for personalization
            additional_context: Optional additional context (screenshots, etc.)
            max_tokens: Maximum tokens in response
            temperature: Generation temperature (lower = more deterministic)

        Returns:
            GenerationResult with the generated note
        """
        client = self._get_client()

        # Build the system message from prompt
        system_message = prompt

        # Build the user message with transcript and context
        user_parts = []

        if patient_name:
            user_parts.append(f"Patient Name: {patient_name}")

        if additional_context:
            user_parts.append(f"Additional Context:\n{additional_context}")

        user_parts.append(f"Transcript:\n{transcript}")

        user_message = "\n\n".join(user_parts)

        try:
            response = client.chat.completions.create(
                model=self.deployment_summarize,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            choice = response.choices[0]

            result = GenerationResult(
                content=choice.message.content,
                model=response.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                finish_reason=choice.finish_reason,
            )

            # Log cost (if tracker available)
            try:
                from .cost_tracking import get_cost_tracker, ModelType
                tracker = get_cost_tracker()
                tracker.log_usage(
                    user_id=self._current_user_id or "unknown",
                    model_type=ModelType.SUMMARIZE,
                    model_name=self.deployment_summarize,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    user_email=self._current_user_email,
                    is_admin=self._current_is_admin,
                    session_id=self._current_session_id,
                    operation="generate_note",
                )
            except Exception as e:
                logger.warning(f"Failed to log cost: {e}")

            return result

        except Exception as e:
            logger.error(f"Azure OpenAI generation failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Test the connection to Azure OpenAI.

        Returns:
            True if connection successful
        """
        try:
            client = self._get_client()
            # Simple test request
            response = client.chat.completions.create(
                model=self.deployment_summarize,
                messages=[
                    {"role": "user", "content": "Hello, respond with 'OK'."}
                ],
                max_tokens=10,
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {e}")
            return False

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using GPT-4o transcription model.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        # Note: GPT-4o transcription uses the audio endpoint
        # This is a placeholder - actual implementation depends on Azure OpenAI audio API
        raise NotImplementedError(
            "GPT-4o audio transcription not yet implemented. "
            "Use Azure Speech Services or paste transcript manually."
        )

    def close(self) -> None:
        """Close the client connection."""
        self._client = None


# Singleton instance
_openai_client: Optional[AzureOpenAIClient] = None


def get_azure_openai_client() -> AzureOpenAIClient:
    """Get the singleton AzureOpenAIClient instance."""
    global _openai_client
    if _openai_client is None:
        _openai_client = AzureOpenAIClient()
    return _openai_client
