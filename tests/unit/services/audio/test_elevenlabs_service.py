"""Unit tests for ElevenLabs TTS service."""

import pytest
from src.services.audio.elevenlabs_service import ElevenLabsTTSService, _mp3_bytes_to_wav
from src.models.audio_models import ElevenLabsConfig, TTSRequest, AudioSegment


@pytest.fixture
def elevenlabs_config() -> ElevenLabsConfig:
    return ElevenLabsConfig(
        api_key="test-api-key",
        male_voice_id="voice-male-id",
        female_voice_id="voice-female-id",
    )


@pytest.fixture
def sample_mp3_bytes() -> bytes:
    # Minimal MP3-ish bytes
    return b"\xff\xfb\x90\x00" + b"\x00" * 100


def test_elevenlabs_service_provider_name(elevenlabs_config: ElevenLabsConfig) -> None:
    """ElevenLabsTTSService.provider_name returns 'ElevenLabs'."""
    service = ElevenLabsTTSService(config=elevenlabs_config)
    assert service.provider_name == "ElevenLabs"


def test_elevenlabs_convert_to_speech_returns_audio_segment(
    mocker, elevenlabs_config: ElevenLabsConfig, sample_mp3_bytes: bytes
) -> None:
    """T010: convert_to_speech() calls ElevenLabs API and returns AudioSegment with WAV bytes."""
    fake_wav = b"RIFF" + b"\x00" * 44

    # Mock the ElevenLabs client
    mock_client = mocker.MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([sample_mp3_bytes])
    mocker.patch(
        "src.services.audio.elevenlabs_service.ElevenLabs",
        return_value=mock_client,
    )
    # Mock ffmpeg mp3->wav conversion
    mocker.patch(
        "src.services.audio.elevenlabs_service._mp3_bytes_to_wav",
        return_value=fake_wav,
    )

    service = ElevenLabsTTSService(config=elevenlabs_config)
    request = TTSRequest(text="Hello world", voice_name="voice-male-id")

    result = service.convert_to_speech(request)

    assert isinstance(result, AudioSegment)
    assert result.audio_bytes == fake_wav
    assert result.audio_bytes.startswith(b"RIFF")
    assert result.voice_name == "voice-male-id"
    assert result.voice_gender == "male"
    mock_client.text_to_speech.convert.assert_called_once_with(
        text="Hello world",
        voice_id="voice-male-id",
        model_id="eleven_monolingual_v1",
    )


def test_elevenlabs_convert_female_voice(
    mocker, elevenlabs_config: ElevenLabsConfig, sample_mp3_bytes: bytes
) -> None:
    """convert_to_speech() sets voice_gender=female for female voice_id."""
    fake_wav = b"RIFF" + b"\x00" * 44
    mock_client = mocker.MagicMock()
    mock_client.text_to_speech.convert.return_value = iter([sample_mp3_bytes])
    mocker.patch("src.services.audio.elevenlabs_service.ElevenLabs", return_value=mock_client)
    mocker.patch("src.services.audio.elevenlabs_service._mp3_bytes_to_wav", return_value=fake_wav)

    service = ElevenLabsTTSService(config=elevenlabs_config)
    request = TTSRequest(text="Hello world", voice_name="voice-female-id")
    result = service.convert_to_speech(request)

    assert result.voice_gender == "female"


def test_elevenlabs_config_from_env_raises_without_api_key(monkeypatch) -> None:
    """T018: ElevenLabsConfig.from_env() raises ValueError when ELEVENLABS_API_KEY missing."""
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
        ElevenLabsConfig.from_env()


def test_elevenlabs_config_from_env_loads_key(monkeypatch) -> None:
    """ElevenLabsConfig.from_env() loads key from environment."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "my-secret-key")
    config = ElevenLabsConfig.from_env()
    assert config.api_key == "my-secret-key"
