"""ElevenLabs text-to-speech service implementation."""

import logging
import subprocess
import tempfile
from pathlib import Path

from elevenlabs import ElevenLabs

from src.models.audio_models import AudioSegment, ElevenLabsConfig, TTSRequest
from src.services.audio import ElevenLabsTTSError, TTSValidationError

logger = logging.getLogger(__name__)

# Default ElevenLabs model
_DEFAULT_MODEL = "eleven_monolingual_v1"


def _mp3_bytes_to_wav(mp3_bytes: bytes) -> bytes:
    """Convert MP3 bytes to WAV bytes using ffmpeg."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mp3_path = Path(tmpdir) / "input.mp3"
        wav_path = Path(tmpdir) / "output.wav"
        mp3_path.write_bytes(mp3_bytes)
        try:
            subprocess.run(
                ["ffmpeg", "-i", str(mp3_path), "-y", str(wav_path)],
                check=True,
                capture_output=True,
            )
            return wav_path.read_bytes()
        except subprocess.CalledProcessError as e:
            raise ElevenLabsTTSError(
                f"Failed to convert MP3 to WAV: {e.stderr.decode(errors='replace')}"
            ) from e


class ElevenLabsTTSService:
    """ElevenLabs cloud text-to-speech service."""

    def __init__(self, config: ElevenLabsConfig) -> None:
        self.config = config
        self._client = ElevenLabs(api_key=config.api_key)

    @property
    def provider_name(self) -> str:
        return "ElevenLabs"

    def convert_to_speech(self, request: TTSRequest) -> AudioSegment:
        """Convert text to speech via ElevenLabs API.

        Args:
            request: TTS request — voice_name is used as the ElevenLabs voice_id.

        Returns:
            AudioSegment with WAV audio bytes.

        Raises:
            TTSValidationError: Invalid request parameters.
            ElevenLabsTTSError: API or conversion failure.
        """
        if not (1 <= len(request.text) <= 5000):
            raise TTSValidationError(
                f"Text length {len(request.text)} outside valid range 1-5000"
            )

        logger.debug(
            "Generating ElevenLabs audio for %d chars with voice %s",
            len(request.text),
            request.voice_name,
        )

        try:
            audio_generator = self._client.text_to_speech.convert(
                text=request.text,
                voice_id=request.voice_name,
                model_id=_DEFAULT_MODEL,
            )
            mp3_bytes = b"".join(audio_generator)
        except Exception as e:
            raise ElevenLabsTTSError(f"ElevenLabs API error: {e}") from e

        wav_bytes = _mp3_bytes_to_wav(mp3_bytes)

        voice_gender = (
            "male"
            if request.voice_name == self.config.male_voice_id
            else "female"
        )

        return AudioSegment(
            item_number=1,  # Updated by caller
            audio_bytes=wav_bytes,
            voice_name=request.voice_name,
            voice_gender=voice_gender,
        )
