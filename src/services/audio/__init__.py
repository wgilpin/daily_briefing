"""Audio generation services for newsletter text-to-speech conversion."""

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
