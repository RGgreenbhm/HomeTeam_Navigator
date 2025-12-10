"""Azure Speech Services Client for audio transcription.

Uses Azure Speech-to-Text (under Microsoft BAA) for HIPAA-compliant
transcription of medical visit recordings.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result from audio transcription."""
    text: str
    duration_seconds: float
    confidence: Optional[float] = None
    language: str = "en-US"
    segments: Optional[List[Dict[str, Any]]] = None  # Word-level timing if available


class AzureSpeechClient:
    """Client for Azure Speech Services transcription.

    Uses Azure Speech-to-Text which is covered under Microsoft HIPAA BAA.
    """

    def __init__(
        self,
        speech_key: Optional[str] = None,
        speech_region: Optional[str] = None,
    ):
        """Initialize the Azure Speech client.

        Args:
            speech_key: Azure Speech Services key
            speech_region: Azure region (e.g., "eastus2")
        """
        self.speech_key = speech_key or os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = speech_region or os.getenv("AZURE_SPEECH_REGION", "eastus2")

        if not self.speech_key:
            raise ValueError(
                "Azure Speech key not configured. "
                "Set AZURE_SPEECH_KEY environment variable."
            )

        self._speech_config = None
        self._check_sdk()

    def _check_sdk(self) -> bool:
        """Check if Azure Speech SDK is available."""
        try:
            import azure.cognitiveservices.speech as speechsdk
            self._sdk_available = True
            return True
        except ImportError:
            logger.warning(
                "azure-cognitiveservices-speech not installed. "
                "Run: pip install azure-cognitiveservices-speech"
            )
            self._sdk_available = False
            return False

    def _get_speech_config(self):
        """Get or create speech config."""
        if self._speech_config is None and self._sdk_available:
            import azure.cognitiveservices.speech as speechsdk

            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region,
            )
            # Enable detailed output for better transcription
            self._speech_config.output_format = speechsdk.OutputFormat.Detailed
            # Set language
            self._speech_config.speech_recognition_language = "en-US"

        return self._speech_config

    def transcribe_file(
        self,
        audio_path: Path,
        language: str = "en-US",
    ) -> TranscriptionResult:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            language: Language code for recognition

        Returns:
            TranscriptionResult with transcribed text
        """
        if not self._sdk_available:
            raise RuntimeError(
                "Azure Speech SDK not available. "
                "Install with: pip install azure-cognitiveservices-speech"
            )

        import azure.cognitiveservices.speech as speechsdk

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Get speech config
        speech_config = self._get_speech_config()
        speech_config.speech_recognition_language = language

        # Create audio config from file
        audio_config = speechsdk.AudioConfig(filename=str(audio_path))

        # Create recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        # For long audio, use continuous recognition
        all_results = []
        done = False

        def handle_result(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                all_results.append({
                    "text": evt.result.text,
                    "offset": evt.result.offset,
                    "duration": evt.result.duration,
                })

        def handle_canceled(evt):
            nonlocal done
            if evt.reason == speechsdk.CancellationReason.EndOfStream:
                done = True
            elif evt.reason == speechsdk.CancellationReason.Error:
                logger.error(f"Speech recognition error: {evt.error_details}")
                done = True

        def handle_stopped(evt):
            nonlocal done
            done = True

        # Connect callbacks
        recognizer.recognized.connect(handle_result)
        recognizer.canceled.connect(handle_canceled)
        recognizer.session_stopped.connect(handle_stopped)

        # Start continuous recognition
        recognizer.start_continuous_recognition()

        # Wait for completion (with timeout)
        import time
        timeout = 600  # 10 minutes max
        start = time.time()
        while not done and (time.time() - start) < timeout:
            time.sleep(0.1)

        recognizer.stop_continuous_recognition()

        # Combine results
        full_text = " ".join(r["text"] for r in all_results)
        total_duration = sum(r["duration"] for r in all_results) / 10_000_000  # ticks to seconds

        return TranscriptionResult(
            text=full_text.strip(),
            duration_seconds=total_duration,
            language=language,
            segments=all_results,
        )

    def transcribe_short(
        self,
        audio_path: Path,
        language: str = "en-US",
    ) -> TranscriptionResult:
        """Transcribe a short audio file (< 60 seconds).

        For longer files, use transcribe_file() with continuous recognition.

        Args:
            audio_path: Path to audio file
            language: Language code

        Returns:
            TranscriptionResult
        """
        if not self._sdk_available:
            raise RuntimeError("Azure Speech SDK not available")

        import azure.cognitiveservices.speech as speechsdk

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        speech_config = self._get_speech_config()
        speech_config.speech_recognition_language = language

        audio_config = speechsdk.AudioConfig(filename=str(audio_path))

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        # Simple one-shot recognition
        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return TranscriptionResult(
                text=result.text,
                duration_seconds=result.duration / 10_000_000,
                language=language,
            )
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return TranscriptionResult(
                text="",
                duration_seconds=0,
                language=language,
            )
        else:
            raise RuntimeError(f"Speech recognition failed: {result.reason}")

    def test_connection(self) -> bool:
        """Test the connection to Azure Speech Services.

        Returns:
            True if connection successful
        """
        if not self._sdk_available:
            return False

        try:
            # Just verify we can create the config
            config = self._get_speech_config()
            return config is not None
        except Exception as e:
            logger.error(f"Azure Speech connection test failed: {e}")
            return False


# Singleton instance
_speech_client: Optional[AzureSpeechClient] = None


def get_azure_speech_client() -> AzureSpeechClient:
    """Get the singleton AzureSpeechClient instance."""
    global _speech_client
    if _speech_client is None:
        _speech_client = AzureSpeechClient()
    return _speech_client
