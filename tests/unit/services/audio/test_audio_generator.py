"""Unit tests for audio generator."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from src.services.audio.audio_generator import (
    generate_audio_for_newsletter,
    concatenate_audio_segments,
)
from src.models.audio_models import AudioSegment, NewsletterItem


@pytest.fixture
def sample_markdown(tmp_path):
    """Create a sample newsletter markdown file."""
    markdown_path = tmp_path / "test_digest.md"
    content = """
# Newsletter Digest

## Technology

### First Item
*Date: 2026-02-05*
First item content here.
[Read More](https://example.com/1)

### Second Item
*Date: 2026-02-05*
Second item content here.
[Read More](https://example.com/2)
"""
    markdown_path.write_text(content)
    return markdown_path


@pytest.fixture
def mock_tts_service(mocker):
    """Mock TTS service."""
    mock = mocker.Mock()
    mock.provider_name = "MockTTS"
    # Return fake WAV audio segments
    mock.convert_to_speech.side_effect = lambda req: AudioSegment(
        item_number=1,
        audio_bytes=b"RIFF" + b"\x00" * 50,  # WAV format starts with RIFF
        voice_name=req.voice_name,
        voice_gender="male" if "george" in req.voice_name else "female",
    )
    return mock


def test_generate_audio_for_newsletter_success(
    sample_markdown, mock_tts_service, mocker
):
    """Test successful audio generation for newsletter."""
    # Mock the TTS service initialization
    mocker.patch(
        "src.services.audio.audio_generator.get_tts_provider",
        return_value=mock_tts_service,
    )

    result = generate_audio_for_newsletter(sample_markdown)

    assert result.success is True
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.output_path.suffix == ".mp3"
    assert result.total_items == 2
    assert result.items_processed == 2
    assert result.success_rate == 100.0


def test_generate_audio_alternating_voices(sample_markdown, mocker, tmp_path):
    """Test that voices alternate between male and female."""
    voice_names_used = []

    def mock_convert(request):
        voice_names_used.append(request.voice_name)
        return AudioSegment(
            item_number=len(voice_names_used),
            audio_bytes=b"RIFF" + b"\x00" * 50,
            voice_name=request.voice_name,
            voice_gender="male" if len(voice_names_used) % 2 == 1 else "female",
        )

    mock_tts = Mock()
    mock_tts.provider_name = "MockTTS"
    mock_tts.convert_to_speech.side_effect = mock_convert

    mocker.patch(
        "src.services.audio.audio_generator.get_tts_provider", return_value=mock_tts
    )
    # Use temp cache directory to avoid cache hits
    mocker.patch("src.services.audio.audio_generator.CACHE_DIR", tmp_path / "cache")

    result = generate_audio_for_newsletter(sample_markdown)

    assert len(voice_names_used) == 2
    # Odd items should use male voice, even items should use female voice
    # Default: bm_george and bf_emma from AudioConfig
    assert voice_names_used[0] != voice_names_used[1]  # Should alternate


def test_generate_audio_concatenation():
    """Test audio segment concatenation."""
    segments = [
        AudioSegment(
            item_number=1,
            audio_bytes=b"RIFF" + b"\x11" * 10,
            voice_name="bm_george",
            voice_gender="male",
        ),
        AudioSegment(
            item_number=2,
            audio_bytes=b"RIFF" + b"\x22" * 10,
            voice_name="bf_emma",
            voice_gender="female",
        ),
    ]

    result = concatenate_audio_segments(segments)

    assert isinstance(result, bytes)
    assert len(result) == len(segments[0].audio_bytes) + len(segments[1].audio_bytes)
    # Check that both segments' data is present
    assert segments[0].audio_bytes in result or result.startswith(
        segments[0].audio_bytes
    )


def test_generate_audio_file_output(sample_markdown, mock_tts_service, mocker):
    """Test that MP3 file is created with correct name."""
    mocker.patch(
        "src.services.audio.audio_generator.get_tts_provider",
        return_value=mock_tts_service,
    )

    result = generate_audio_for_newsletter(sample_markdown)

    expected_audio_path = sample_markdown.with_suffix(".mp3")
    assert result.output_path == expected_audio_path
    assert expected_audio_path.exists()
    assert expected_audio_path.stat().st_size > 0


def test_generate_audio_populates_provider_used(sample_markdown, mocker):
    """T011: generate_audio_for_newsletter() populates provider_used from provider."""
    mock_provider = mocker.Mock()
    mock_provider.provider_name = "ElevenLabs"
    mock_provider.convert_to_speech.side_effect = lambda req: AudioSegment(
        item_number=1,
        audio_bytes=b"RIFF" + b"\x00" * 50,
        voice_name=req.voice_name,
        voice_gender="male",
    )
    mocker.patch(
        "src.services.audio.audio_generator.get_tts_provider",
        return_value=mock_provider,
    )
    mocker.patch("src.services.audio.audio_generator.CACHE_DIR", mocker.MagicMock())
    mocker.patch("src.services.audio.audio_generator.get_cached_audio", return_value=None)
    mocker.patch("src.services.audio.audio_generator.cache_audio")

    result = generate_audio_for_newsletter(sample_markdown)

    assert result.provider_used == "ElevenLabs"
