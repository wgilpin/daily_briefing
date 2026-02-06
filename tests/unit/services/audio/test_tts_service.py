"""Unit tests for TTS service."""

import io
import pytest
import numpy as np
from unittest.mock import Mock
from src.services.audio.tts_service import KokoroTTSService
from src.models.audio_models import AudioConfig, TTSRequest


@pytest.fixture
def mock_kokoro_pipeline(mocker):
    """Mock Kokoro pipeline."""
    mock = mocker.Mock()
    # Mock pipeline to return generator of (graphemes, phonemes, audio) tuples
    # Audio is a numpy array at 24kHz
    audio_data = np.random.rand(24000).astype(np.float32)  # 1 second of audio
    mock.return_value = [(["test"], ["test"], audio_data)]
    return mock


@pytest.fixture
def audio_config():
    """Create test audio configuration."""
    return AudioConfig(
        male_voice="bm_george",
        female_voice="bf_emma",
    )


def test_convert_to_speech_success(mocker, mock_kokoro_pipeline, audio_config):
    """Test successful TTS conversion."""
    # Mock KPipeline class
    mocker.patch('src.services.audio.tts_service.KPipeline', return_value=mock_kokoro_pipeline)

    service = KokoroTTSService(config=audio_config)

    request = TTSRequest(
        text="Test content for speech conversion",
        voice_name="bm_george",
    )

    result = service.convert_to_speech(request)

    assert result.voice_name == "bm_george"
    assert len(result.audio_bytes) > 0
    # Verify it's WAV format (starts with RIFF header)
    assert result.audio_bytes.startswith(b'RIFF')
    mock_kokoro_pipeline.assert_called_once_with("Test content for speech conversion", voice="bm_george")


def test_convert_to_speech_male_voice(mocker, mock_kokoro_pipeline, audio_config):
    """Test TTS with male voice."""
    mocker.patch('src.services.audio.tts_service.KPipeline', return_value=mock_kokoro_pipeline)

    service = KokoroTTSService(config=audio_config)

    request = TTSRequest(
        text="Male voice test",
        voice_name="bm_george",
    )

    result = service.convert_to_speech(request)

    assert result.voice_gender == "male"
    assert result.voice_name == "bm_george"


def test_convert_to_speech_female_voice(mocker, mock_kokoro_pipeline, audio_config):
    """Test TTS with female voice."""
    mocker.patch('src.services.audio.tts_service.KPipeline', return_value=mock_kokoro_pipeline)

    service = KokoroTTSService(config=audio_config)

    request = TTSRequest(
        text="Female voice test",
        voice_name="bf_emma",
    )

    result = service.convert_to_speech(request)

    assert result.voice_gender == "female"
    assert result.voice_name == "bf_emma"
