"""Unit tests for TTS service."""

import sys
import types
import pytest
from unittest.mock import Mock, patch
from src.services.audio.tts_service import KokoroTTSService, get_tts_provider
from src.models.audio_models import AudioConfig, ElevenLabsConfig, TTSRequest
from src.services.audio import TTSProvider


import types


def _make_kokoro_modules(mocker, pipeline_mock):
    """Inject dummy kokoro, soundfile, and torch into sys.modules for testing."""
    dummy_kokoro = types.ModuleType("kokoro")
    dummy_kokoro.KPipeline = mocker.Mock(return_value=pipeline_mock)  # type: ignore[attr-defined]
    dummy_soundfile = types.ModuleType("soundfile")
    dummy_soundfile.write = mocker.Mock()  # type: ignore[attr-defined]
    dummy_torch = types.ModuleType("torch")
    dummy_torch.cuda = types.SimpleNamespace(is_available=lambda: False)  # type: ignore[attr-defined]
    return dummy_kokoro, dummy_soundfile, dummy_torch


@pytest.fixture
def mock_kokoro_pipeline(mocker):
    """Mock Kokoro pipeline instance."""
    mock = mocker.Mock()
    # Fake audio data — soundfile.write is also mocked, so dtype doesn't matter
    audio_data = [0.0] * 24000
    mock.return_value = [(["test"], ["test"], audio_data)]
    return mock


@pytest.fixture
def audio_config():
    """Create test audio configuration."""
    return AudioConfig(
        male_voice="bm_george",
        female_voice="bf_emma",
    )


def _make_kokoro_service(mocker, audio_config, pipeline_mock):
    """Helper: create KokoroTTSService with mocked kokoro/soundfile/torch modules."""
    dummy_kokoro, dummy_soundfile, dummy_torch = _make_kokoro_modules(mocker, pipeline_mock)
    fake_wav = b"RIFF" + b"\x00" * 44

    def fake_sf_write(buf, data, samplerate, format):
        buf.write(fake_wav)

    dummy_soundfile.write = fake_sf_write

    # Dummy numpy: concatenate just joins lists; that's enough for our mock
    dummy_numpy = types.ModuleType("numpy")
    dummy_numpy.concatenate = lambda chunks: chunks[0] if len(chunks) == 1 else sum(chunks, [])  # type: ignore[attr-defined]

    # Keep patches active for the lifetime of the test (not just during __init__)
    mocker.patch.dict(
        sys.modules,
        {"kokoro": dummy_kokoro, "soundfile": dummy_soundfile, "numpy": dummy_numpy, "torch": dummy_torch},
    )
    service = KokoroTTSService(config=audio_config)
    return service, dummy_soundfile, fake_wav


def test_convert_to_speech_success(mocker, mock_kokoro_pipeline, audio_config):
    """Test successful TTS conversion."""
    service, _, fake_wav = _make_kokoro_service(mocker, audio_config, mock_kokoro_pipeline)

    request = TTSRequest(
        text="Test content for speech conversion",
        voice_name="bm_george",
    )

    result = service.convert_to_speech(request)

    assert result.voice_name == "bm_george"
    assert len(result.audio_bytes) > 0
    assert result.audio_bytes.startswith(b"RIFF")
    mock_kokoro_pipeline.assert_called_once_with(
        "Test content for speech conversion", voice="bm_george"
    )


def test_convert_to_speech_male_voice(mocker, mock_kokoro_pipeline, audio_config):
    """Test TTS with male voice."""
    service, _, _ = _make_kokoro_service(mocker, audio_config, mock_kokoro_pipeline)

    request = TTSRequest(text="Male voice test", voice_name="bm_george")
    result = service.convert_to_speech(request)

    assert result.voice_gender == "male"
    assert result.voice_name == "bm_george"


def test_convert_to_speech_female_voice(mocker, mock_kokoro_pipeline, audio_config):
    """Test TTS with female voice."""
    service, _, _ = _make_kokoro_service(mocker, audio_config, mock_kokoro_pipeline)

    request = TTSRequest(text="Female voice test", voice_name="bf_emma")
    result = service.convert_to_speech(request)

    assert result.voice_gender == "female"
    assert result.voice_name == "bf_emma"


def test_kokoro_service_has_provider_name(mocker, mock_kokoro_pipeline, audio_config):
    """Test KokoroTTSService.provider_name returns 'Kokoro'."""
    service, _, _ = _make_kokoro_service(mocker, audio_config, mock_kokoro_pipeline)
    assert service.provider_name == "Kokoro"


# --- Factory tests (T008, T009) ---

def test_get_tts_provider_returns_kokoro_when_available(mocker, audio_config):
    """T008: Factory returns KokoroTTSService when kokoro is importable."""
    import sys
    import types

    # Ensure a dummy kokoro module is present so `import kokoro` succeeds
    dummy_kokoro = types.ModuleType("kokoro")
    dummy_soundfile = types.ModuleType("soundfile")
    dummy_torch = types.ModuleType("torch")
    dummy_torch.cuda = types.SimpleNamespace(is_available=lambda: False)  # type: ignore[attr-defined]
    mock_pipeline = mocker.Mock(return_value=[])
    dummy_kokoro.KPipeline = mock_pipeline  # type: ignore[attr-defined]

    mocker.patch.dict(sys.modules, {"kokoro": dummy_kokoro, "soundfile": dummy_soundfile, "torch": dummy_torch})
    provider = get_tts_provider(audio_config)

    assert isinstance(provider, KokoroTTSService)
    assert provider.provider_name == "Kokoro"


def test_get_tts_provider_falls_back_to_elevenlabs_when_kokoro_missing(mocker, audio_config):
    """T009: Factory returns ElevenLabsTTSService when kokoro raises ImportError."""
    from src.services.audio.elevenlabs_service import ElevenLabsTTSService

    # Simulate kokoro not being installed
    mocker.patch.dict(sys.modules, {"kokoro": None})
    mocker.patch(
        "src.models.audio_models.ElevenLabsConfig.from_env",
        return_value=ElevenLabsConfig(
            api_key="test-key",
            male_voice_id="voice-m",
            female_voice_id="voice-f",
        ),
    )
    # Mock ElevenLabs client so no real HTTP
    mocker.patch("src.services.audio.elevenlabs_service.ElevenLabs")

    provider = get_tts_provider(audio_config)

    assert isinstance(provider, ElevenLabsTTSService)
    assert provider.provider_name == "ElevenLabs"


# --- Phase 4 tests (T017, T019a) ---

def test_get_tts_provider_falls_back_when_kokoro_init_fails(mocker, audio_config):
    """T017: Factory falls back to ElevenLabs when KPipeline raises an exception."""
    import types
    from src.services.audio.elevenlabs_service import ElevenLabsTTSService

    # kokoro importable but KPipeline raises (simulates broken espeak-ng)
    dummy_kokoro = types.ModuleType("kokoro")
    dummy_kokoro.KPipeline = mocker.Mock(side_effect=RuntimeError("espeak-ng not found"))  # type: ignore[attr-defined]
    dummy_soundfile = types.ModuleType("soundfile")

    mocker.patch.dict(sys.modules, {"kokoro": dummy_kokoro, "soundfile": dummy_soundfile})
    mocker.patch(
        "src.models.audio_models.ElevenLabsConfig.from_env",
        return_value=ElevenLabsConfig(
            api_key="test-key",
            male_voice_id="voice-m",
            female_voice_id="voice-f",
        ),
    )
    mocker.patch("src.services.audio.elevenlabs_service.ElevenLabs")

    provider = get_tts_provider(audio_config)

    assert isinstance(provider, ElevenLabsTTSService)
    assert provider.provider_name == "ElevenLabs"


def test_get_tts_provider_raises_when_no_provider_available(mocker, audio_config):
    """T019a: Factory raises TTSError when neither Kokoro nor ElevenLabs is available."""
    from src.services.audio import TTSError

    mocker.patch.dict(sys.modules, {"kokoro": None})
    mocker.patch(
        "src.models.audio_models.ElevenLabsConfig.from_env",
        side_effect=ValueError("ELEVENLABS_API_KEY environment variable is not set"),
    )

    with pytest.raises(TTSError, match="No TTS provider available"):
        get_tts_provider(audio_config)
