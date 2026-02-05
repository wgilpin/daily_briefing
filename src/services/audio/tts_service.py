"""ElevenLabs text-to-speech service implementation."""

import logging
from elevenlabs import ElevenLabs, VoiceSettings as ElevenLabsVoiceSettings

from src.models.audio_models import AudioConfig, TTSRequest, AudioSegment
from src.services.audio import (
    TTSAPIError,
    TTSTimeoutError,
    TTSRateLimitError,
    TTSValidationError,
)

logger = logging.getLogger(__name__)


class ElevenLabsTTSService:
    """ElevenLabs text-to-speech service implementation."""

    def __init__(self, api_key: str, config: AudioConfig):
        """
        Initialize service with API credentials and configuration.

        Args:
            api_key: ElevenLabs API key
            config: Audio configuration
        """
        self.api_key = api_key
        self.config = config
        self._client = ElevenLabs(api_key=api_key)

    def convert_to_speech(self, request: TTSRequest) -> AudioSegment:
        """
        Convert text to speech using ElevenLabs API.

        Args:
            request: TTS request with text and voice configuration

        Returns:
            AudioSegment with generated audio bytes

        Raises:
            TTSAPIError: API call failed
            TTSTimeoutError: API call timed out
            TTSRateLimitError: Rate limit exceeded
            TTSValidationError: Invalid request parameters
        """
        try:
            # Convert our VoiceSettings to ElevenLabs VoiceSettings
            voice_settings = ElevenLabsVoiceSettings(
                stability=request.voice_settings.stability,
                similarity_boost=request.voice_settings.similarity_boost,
            )

            # Call ElevenLabs API
            audio_generator = self._client.text_to_speech.convert(
                text=request.text,
                voice_id=request.voice_id,
                model_id=request.model_id,
                voice_settings=voice_settings,
            )

            # Collect audio bytes from generator
            audio_bytes = b"".join(audio_generator)

            # Determine voice gender based on voice_id
            voice_gender = (
                "male"
                if request.voice_id == self.config.male_voice_id
                else "female"
            )

            return AudioSegment(
                item_number=1,  # Will be updated by caller
                audio_bytes=audio_bytes,
                voice_id=request.voice_id,
                voice_gender=voice_gender,
            )

        except TimeoutError as e:
            logger.error(f"TTS API timeout: {e}")
            raise TTSTimeoutError(f"API call timed out: {e}") from e

        except Exception as e:
            # Check for rate limit (HTTP 429)
            if hasattr(e, "status_code") and e.status_code == 429:
                logger.warning(f"TTS rate limit exceeded: {e}")
                raise TTSRateLimitError(f"Rate limit exceeded: {e}") from e

            # Check for validation errors
            if isinstance(e, ValueError):
                logger.error(f"TTS validation error: {e}")
                raise TTSValidationError(f"Invalid request parameters: {e}") from e

            logger.error(f"TTS API error: {e}")
            raise TTSAPIError(f"API call failed: {e}") from e

    def health_check(self) -> bool:
        """
        Check if TTS service is available.

        Returns:
            True if service is operational, False otherwise
        """
        try:
            # Try to fetch voices to verify API connectivity
            voices = self._client.voices.get_all()
            return len(voices.voices) > 0
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
