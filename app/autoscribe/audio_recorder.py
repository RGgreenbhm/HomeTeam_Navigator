"""Audio Recording Module for AutoScribe.

Provides audio capture with device selection, segment management,
and composite file creation for medical visit transcription.
"""

import os
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import json
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Represents a recorded audio segment."""
    id: str
    file_path: Path
    duration_seconds: float
    start_time: datetime
    sample_rate: int = 44100
    channels: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "file_path": str(self.file_path),
            "duration_seconds": self.duration_seconds,
            "start_time": self.start_time.isoformat(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
        }


@dataclass
class AudioDevice:
    """Represents an audio input/output device."""
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_default: bool = False


class AudioRecorder:
    """Manages audio recording with device selection and segment management.

    Features:
    - Device enumeration (microphones and speakers)
    - Segment-based recording (pause creates new segment)
    - 60-minute maximum total duration
    - Local temp storage with session cleanup
    - Composite audio generation
    """

    MAX_DURATION_SECONDS = 60 * 60  # 60 minutes
    DEFAULT_SAMPLE_RATE = 44100
    DEFAULT_CHANNELS = 1  # Mono for speech

    def __init__(self, temp_dir: Optional[Path] = None):
        """Initialize the audio recorder.

        Args:
            temp_dir: Directory for temporary audio files.
                     Defaults to system temp directory.
        """
        if temp_dir is None:
            temp_dir = Path(tempfile.gettempdir()) / "autoscribe_audio"

        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.segments: List[AudioSegment] = []
        self.is_recording: bool = False
        self.current_device_index: Optional[int] = None
        self._recording_data: List = []
        self._recording_start: Optional[datetime] = None

        # Check if sounddevice is available
        self._sd_available = self._check_sounddevice()

    def _check_sounddevice(self) -> bool:
        """Check if sounddevice is available."""
        try:
            import sounddevice
            return True
        except ImportError:
            logger.warning("sounddevice not installed - audio recording disabled")
            return False

    def get_input_devices(self) -> List[AudioDevice]:
        """Get available audio input devices (microphones).

        Returns:
            List of available input devices
        """
        if not self._sd_available:
            return [AudioDevice(
                index=0,
                name="System Default (sounddevice not installed)",
                max_input_channels=1,
                max_output_channels=0,
                default_sample_rate=44100,
                is_default=True,
            )]

        try:
            import sounddevice as sd

            devices = []
            default_input = sd.default.device[0]

            for i, device in enumerate(sd.query_devices()):
                if device['max_input_channels'] > 0:
                    devices.append(AudioDevice(
                        index=i,
                        name=device['name'],
                        max_input_channels=device['max_input_channels'],
                        max_output_channels=device['max_output_channels'],
                        default_sample_rate=device['default_samplerate'],
                        is_default=(i == default_input),
                    ))

            return devices

        except Exception as e:
            logger.error(f"Failed to enumerate input devices: {e}")
            return []

    def get_output_devices(self) -> List[AudioDevice]:
        """Get available audio output devices (speakers).

        Returns:
            List of available output devices
        """
        if not self._sd_available:
            return [AudioDevice(
                index=0,
                name="System Default (sounddevice not installed)",
                max_input_channels=0,
                max_output_channels=2,
                default_sample_rate=44100,
                is_default=True,
            )]

        try:
            import sounddevice as sd

            devices = []
            default_output = sd.default.device[1]

            for i, device in enumerate(sd.query_devices()):
                if device['max_output_channels'] > 0:
                    devices.append(AudioDevice(
                        index=i,
                        name=device['name'],
                        max_input_channels=device['max_input_channels'],
                        max_output_channels=device['max_output_channels'],
                        default_sample_rate=device['default_samplerate'],
                        is_default=(i == default_output),
                    ))

            return devices

        except Exception as e:
            logger.error(f"Failed to enumerate output devices: {e}")
            return []

    def get_total_duration(self) -> float:
        """Get total duration of all recorded segments.

        Returns:
            Total duration in seconds
        """
        return sum(s.duration_seconds for s in self.segments)

    def can_record_more(self) -> bool:
        """Check if more recording time is available.

        Returns:
            True if under the 60-minute limit
        """
        return self.get_total_duration() < self.MAX_DURATION_SECONDS

    def start_recording(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
    ) -> bool:
        """Start recording audio.

        Args:
            device_index: Input device index (None for default)
            sample_rate: Sample rate in Hz
            channels: Number of channels (1 for mono, 2 for stereo)

        Returns:
            True if recording started successfully
        """
        if self.is_recording:
            logger.warning("Already recording")
            return False

        if not self.can_record_more():
            logger.warning("Maximum recording duration reached")
            return False

        if not self._sd_available:
            logger.error("sounddevice not available")
            return False

        try:
            import sounddevice as sd
            import numpy as np

            self.current_device_index = device_index
            self._recording_data = []
            self._recording_start = datetime.now()
            self.is_recording = True

            # Callback to capture audio data
            def callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                self._recording_data.append(indata.copy())

            # Start the stream
            self._stream = sd.InputStream(
                device=device_index,
                samplerate=sample_rate,
                channels=channels,
                callback=callback,
            )
            self._stream.start()

            logger.info(f"Recording started on device {device_index}")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[AudioSegment]:
        """Stop recording and save the segment.

        Returns:
            The recorded AudioSegment, or None if recording failed
        """
        if not self.is_recording:
            logger.warning("Not currently recording")
            return None

        try:
            import sounddevice as sd
            import numpy as np

            # Stop the stream
            if hasattr(self, '_stream'):
                self._stream.stop()
                self._stream.close()

            self.is_recording = False

            # Combine recorded data
            if not self._recording_data:
                logger.warning("No audio data recorded")
                return None

            audio_data = np.concatenate(self._recording_data, axis=0)
            duration = len(audio_data) / self.DEFAULT_SAMPLE_RATE

            # Save to file
            segment_id = f"seg_{uuid.uuid4().hex[:8]}"
            file_path = self.temp_dir / f"{segment_id}.wav"

            try:
                import soundfile as sf
                sf.write(str(file_path), audio_data, self.DEFAULT_SAMPLE_RATE)
            except ImportError:
                # Fallback to wave module
                import wave
                with wave.open(str(file_path), 'wb') as wf:
                    wf.setnchannels(self.DEFAULT_CHANNELS)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.DEFAULT_SAMPLE_RATE)
                    wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

            # Create segment record
            segment = AudioSegment(
                id=segment_id,
                file_path=file_path,
                duration_seconds=duration,
                start_time=self._recording_start,
                sample_rate=self.DEFAULT_SAMPLE_RATE,
                channels=self.DEFAULT_CHANNELS,
            )

            self.segments.append(segment)
            logger.info(f"Saved segment {segment_id}: {duration:.1f}s")

            return segment

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            self.is_recording = False
            return None

    def delete_segment(self, segment_id: str) -> bool:
        """Delete a recorded segment.

        Args:
            segment_id: ID of segment to delete

        Returns:
            True if segment was deleted
        """
        for i, segment in enumerate(self.segments):
            if segment.id == segment_id:
                # Delete file
                try:
                    segment.file_path.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Could not delete file: {e}")

                # Remove from list
                self.segments.pop(i)
                logger.info(f"Deleted segment {segment_id}")
                return True

        return False

    def create_composite(self, output_path: Optional[Path] = None) -> Optional[Path]:
        """Create a composite audio file from all segments.

        Args:
            output_path: Output file path (defaults to temp directory)

        Returns:
            Path to composite file, or None if failed
        """
        if not self.segments:
            logger.warning("No segments to combine")
            return None

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.temp_dir / f"composite_{timestamp}.wav"

        try:
            from pydub import AudioSegment as PydubSegment

            combined = PydubSegment.empty()

            for segment in self.segments:
                audio = PydubSegment.from_wav(str(segment.file_path))
                combined += audio

            combined.export(str(output_path), format="wav")
            logger.info(f"Created composite: {output_path}")

            return output_path

        except ImportError:
            logger.warning("pydub not available, falling back to manual concat")

            try:
                import numpy as np
                import soundfile as sf

                all_data = []
                for segment in self.segments:
                    data, sr = sf.read(str(segment.file_path))
                    all_data.append(data)

                combined = np.concatenate(all_data)
                sf.write(str(output_path), combined, self.DEFAULT_SAMPLE_RATE)

                return output_path

            except Exception as e:
                logger.error(f"Failed to create composite: {e}")
                return None

    def cleanup(self) -> None:
        """Clean up all temporary audio files."""
        for segment in self.segments:
            try:
                segment.file_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not delete {segment.file_path}: {e}")

        self.segments.clear()

        # Clean up temp directory if empty
        try:
            if self.temp_dir.exists() and not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
        except Exception:
            pass

        logger.info("Cleaned up audio files")

    def get_segments_info(self) -> List[Dict[str, Any]]:
        """Get info about all recorded segments.

        Returns:
            List of segment info dictionaries
        """
        return [s.to_dict() for s in self.segments]


# Singleton instance
_audio_recorder: Optional[AudioRecorder] = None


def get_audio_recorder() -> AudioRecorder:
    """Get the singleton AudioRecorder instance."""
    global _audio_recorder
    if _audio_recorder is None:
        _audio_recorder = AudioRecorder()
    return _audio_recorder
