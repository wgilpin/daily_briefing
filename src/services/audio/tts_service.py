"""Kokoro text-to-speech service and provider factory."""

import io
import logging

from src.models.audio_models import AudioConfig, AudioSegment, ElevenLabsConfig, TTSRequest
from src.services.audio import (
    TTSError,
    TTSGenerationError,
    TTSProvider,
    TTSValidationError,
)

logger = logging.getLogger(__name__)


class KokoroTTSService:
    """Kokoro text-to-speech service implementation (local GPU)."""

    def __init__(self, config: AudioConfig) -> None:
        """Initialize service with configuration.

        Args:
            config: Audio configuration (voice names)

        Raises:
            TTSGenerationError: If Kokoro pipeline cannot be initialised.
        """
        import soundfile as sf  # noqa: F401 – kept here to fail fast if missing
        from kokoro import KPipeline

        self.config = config
        self._sf = sf
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._pipeline = KPipeline(lang_code="b", device=device)
            logger.info("Kokoro TTS pipeline initialized (British English, device=%s)", device)
        except OSError as e:
            if "en_core_web_sm" in str(e):
                error_msg = (
                    "Kokoro requires spaCy's 'en_core_web_sm' model.\n"
                    "Install it with: uv run python -c \"import spacy; spacy.cli.download('en_core_web_sm')\"\n"
                    f"Original error: {e}"
                )
                logger.error(error_msg)
                raise TTSGenerationError(error_msg) from e
            logger.error("Failed to initialize Kokoro pipeline: %s", e)
            raise TTSGenerationError(f"Pipeline initialization failed: {e}") from e
        except Exception as e:
            logger.error("Failed to initialize Kokoro pipeline: %s", e)
            raise TTSGenerationError(f"Pipeline initialization failed: {e}") from e

    @property
    def provider_name(self) -> str:
        return "Kokoro"

    def convert_to_speech(self, request: TTSRequest) -> AudioSegment:
        """Convert text to speech using Kokoro TTS.

        Args:
            request: TTS request with text and voice configuration

        Returns:
            AudioSegment with generated WAV audio bytes

        Raises:
            TTSGenerationError: Audio generation failed
            TTSValidationError: Invalid request parameters
        """
        import numpy as np

        try:
            if not (1 <= len(request.text) <= 5000):
                raise TTSValidationError(
                    f"Text length {len(request.text)} outside valid range 1-5000"
                )

            logger.debug(
                "Generating audio for %d characters with voice %s",
                len(request.text),
                request.voice_name,
            )
            generator = self._pipeline(request.text, voice=request.voice_name)

            audio_chunks = []
            for _graphemes, _phonemes, audio in generator:
                audio_chunks.append(audio)

            if not audio_chunks:
                raise TTSGenerationError("No audio generated from pipeline")

            full_audio = np.concatenate(audio_chunks)

            wav_buffer = io.BytesIO()
            self._sf.write(wav_buffer, full_audio, 24000, format="WAV")
            audio_bytes = wav_buffer.getvalue()

            voice_gender = (
                "male" if request.voice_name == self.config.male_voice else "female"
            )

            return AudioSegment(
                item_number=1,  # Updated by caller
                audio_bytes=audio_bytes,
                voice_name=request.voice_name,
                voice_gender=voice_gender,
            )

        except TTSValidationError:
            raise
        except Exception as e:
            logger.error("TTS generation error: %s", e, exc_info=True)
            raise TTSGenerationError(f"Audio generation failed: {e}") from e


def get_tts_provider(config: AudioConfig) -> TTSProvider:
    """Return the best available TTS provider.

    Tries Kokoro first (local, free). Falls back to ElevenLabs if Kokoro is
    not installed or fails to initialise.

    Args:
        config: AudioConfig (used for Kokoro voice names).

    Returns:
        A TTSProvider instance ready for use.

    Raises:
        TTSError: If neither Kokoro nor ElevenLabs is available.
    """
    try:
        import kokoro  # noqa: F401
        provider: TTSProvider = KokoroTTSService(config)
        logger.info("TTS provider: %s", provider.provider_name)
        return provider
    except (ImportError, TTSGenerationError) as kokoro_error:
        logger.warning(
            "Kokoro unavailable (%s), falling back to ElevenLabs", kokoro_error
        )

    try:
        from src.services.audio.elevenlabs_service import ElevenLabsTTSService

        el_config = ElevenLabsConfig.from_env()
        provider = ElevenLabsTTSService(config=el_config)
        logger.info("TTS provider: %s", provider.provider_name)
        return provider
    except ValueError as e:
        raise TTSError(
            f"No TTS provider available: Kokoro not installed, {e}"
        ) from e
