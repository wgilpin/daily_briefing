"""Audio generation services for newsletter text-to-speech conversion."""

# Custom exception classes for audio generation


class TTSError(Exception):
    """Base exception for TTS operations."""

    pass


class TTSAPIError(TTSError):
    """API call failed (server error, auth failure)."""

    pass


class TTSTimeoutError(TTSError):
    """API call timed out."""

    pass


class TTSRateLimitError(TTSError):
    """Rate limit exceeded."""

    pass


class TTSValidationError(TTSError):
    """Invalid request parameters."""

    pass
