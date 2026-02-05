"""Unit tests for TTS service."""

import pytest
from unittest.mock import Mock
from src.services.audio.tts_service import ElevenLabsTTSService
from src.models.audio_models import AudioConfig, TTSRequest, VoiceSettings


@pytest.fixture
def mock_elevenlabs_client(mocker):
    """Mock ElevenLabs client."""
    mock = mocker.Mock()
    # Mock text_to_speech.convert to return an iterable of audio bytes
    mock.text_to_speech.convert.return_value = [b"\xff\xfb\x90\x00" + b"\x00" * 100]
    return mock


@pytest.fixture
def audio_config():
    """Create test audio configuration."""
    return AudioConfig(
        male_voice_id="test_male_voice",
        female_voice_id="test_female_voice",
        model_id="test_model",
        api_timeout=30,
    )


def test_convert_to_speech_success(mock_elevenlabs_client, audio_config):
    """Test successful TTS conversion."""
    service = ElevenLabsTTSService(api_key="test_key", config=audio_config)
    service._client = mock_elevenlabs_client

    request = TTSRequest(
        text="Test content for speech conversion",
        voice_id="test_voice",
        model_id="test_model",
        voice_settings=VoiceSettings(),
    )

    result = service.convert_to_speech(request)

    expected_bytes = b"".join(mock_elevenlabs_client.text_to_speech.convert.return_value)
    assert result.audio_bytes == expected_bytes
    assert result.voice_id == "test_voice"
    assert len(result.audio_bytes) > 0
    mock_elevenlabs_client.text_to_speech.convert.assert_called_once()


def test_health_check_success(mock_elevenlabs_client, audio_config):
    """Test successful health check."""
    service = ElevenLabsTTSService(api_key="test_key", config=audio_config)
    service._client = mock_elevenlabs_client

    # Mock voices API response
    mock_voices = Mock()
    mock_voices.voices = [Mock(voice_id="test_voice_1")]
    mock_elevenlabs_client.voices.get_all.return_value = mock_voices

    assert service.health_check() is True
    mock_elevenlabs_client.voices.get_all.assert_called_once()
