"""Audio generation services for newsletter text-to-speech conversion."""

from typing import Protocol

from src.models.audio_models import AudioSegment, TTSRequest


# Custom exception classes for audio generation


class TTSError(Exception):
    """Base exception for TTS operations."""

    pass


class TTSGenerationError(TTSError):
    """Audio generation failed (local processing error)."""

    pass


class TTSValidationError(TTSError):
    """Invalid request parameters."""

    pass


class ElevenLabsTTSError(TTSError):
    """ElevenLabs API error."""

    pass


class TTSProvider(Protocol):
    """Protocol for TTS provider implementations."""

    def convert_to_speech(self, request: TTSRequest) -> AudioSegment:
        """Convert text to speech and return an AudioSegment."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable provider name for logging and UI display."""
        ...
