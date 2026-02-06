"""Kokoro text-to-speech service implementation."""

import io
import logging
import soundfile as sf
from kokoro import KPipeline

from src.models.audio_models import AudioConfig, TTSRequest, AudioSegment
from src.services.audio import (
    TTSGenerationError,
    TTSValidationError,
)

logger = logging.getLogger(__name__)


class KokoroTTSService:
    """Kokoro text-to-speech service implementation (local GPU)."""

    def __init__(self, config: AudioConfig):
        """
        Initialize service with configuration.

        Args:
            config: Audio configuration (voice names)
        """
        self.config = config
        # Initialize pipeline once for British English
        try:
            self._pipeline = KPipeline(lang_code='b')
            logger.info("Kokoro TTS pipeline initialized (British English)")
        except Exception as e:
            logger.error(f"Failed to initialize Kokoro pipeline: {e}")
            raise TTSGenerationError(f"Pipeline initialization failed: {e}") from e

    def convert_to_speech(self, request: TTSRequest) -> AudioSegment:
        """
        Convert text to speech using Kokoro TTS.

        Args:
            request: TTS request with text and voice configuration

        Returns:
            AudioSegment with generated WAV audio bytes

        Raises:
            TTSGenerationError: Audio generation failed
            TTSValidationError: Invalid request parameters
        """
        try:
            # Validate text length
            if not (1 <= len(request.text) <= 5000):
                raise TTSValidationError(
                    f"Text length {len(request.text)} outside valid range 1-5000"
                )

            # Call Kokoro pipeline
            logger.debug(f"Generating audio for {len(request.text)} characters with voice {request.voice_name}")
            generator = self._pipeline(request.text, voice=request.voice_name)

            # Collect audio data from generator
            audio_chunks = []
            for graphemes, phonemes, audio in generator:
                audio_chunks.append(audio)

            if not audio_chunks:
                raise TTSGenerationError("No audio generated from pipeline")

            # Concatenate all audio chunks
            import numpy as np
            full_audio = np.concatenate(audio_chunks)

            # Convert numpy audio to WAV bytes in memory
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, full_audio, 24000, format='WAV')
            audio_bytes = wav_buffer.getvalue()

            # Determine voice gender based on voice_name
            voice_gender = (
                "male"
                if request.voice_name == self.config.male_voice
                else "female"
            )

            return AudioSegment(
                item_number=1,  # Will be updated by caller
                audio_bytes=audio_bytes,
                voice_name=request.voice_name,
                voice_gender=voice_gender,
            )

        except TTSValidationError:
            raise
        except Exception as e:
            logger.error(f"TTS generation error: {e}", exc_info=True)
            raise TTSGenerationError(f"Audio generation failed: {e}") from e
