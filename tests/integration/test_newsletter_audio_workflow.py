"""Integration tests for newsletter audio generation workflow."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.newsletter.storage import save_consolidated_digest


@pytest.fixture
def sample_newsletter_content():
    """Sample newsletter markdown content."""
    return """
# Newsletter Digest - 2026-02-05

## Technology

### First Article
*Date: 2026-02-05*
First article content here.
[Read More](https://example.com/1)

### Second Article
*Date: 2026-02-05*
Second article content here.
[Read More](https://example.com/2)
"""


@pytest.fixture
def mock_audio_result(mocker):
    """Mock successful audio generation result."""
    mock_result = mocker.Mock()
    mock_result.success = True
    mock_result.output_path = Path("test_digest.mp3")
    mock_result.total_items = 2
    mock_result.items_processed = 2
    mock_result.success_rate = 100.0
    mock_result.duration_seconds = 5.0
    return mock_result


def test_save_consolidated_digest_triggers_audio(
    tmp_path, sample_newsletter_content, mock_audio_result, mocker
):
    """Test that saving a newsletter automatically triggers audio generation."""
    # Mock audio generation
    mock_generate = mocker.patch(
        "src.services.audio.audio_generator.generate_audio_for_newsletter",
        return_value=mock_audio_result
    )

    # Save newsletter
    output_dir = str(tmp_path)
    file_path = save_consolidated_digest(sample_newsletter_content, output_dir)

    # Verify markdown was saved
    assert Path(file_path).exists()
    assert Path(file_path).suffix == ".md"

    # Verify audio generation was triggered
    mock_generate.assert_called_once()
    call_args = mock_generate.call_args[0][0]
    assert call_args == Path(file_path)


def test_audio_failure_does_not_block_newsletter(
    tmp_path, sample_newsletter_content, mocker
):
    """Test that audio generation failure doesn't prevent newsletter saving."""
    # Mock audio generation to fail
    mocker.patch(
        "src.services.audio.audio_generator.generate_audio_for_newsletter",
        side_effect=Exception("Generation error")
    )

    # Save newsletter - should succeed despite audio failure
    output_dir = str(tmp_path)
    file_path = save_consolidated_digest(sample_newsletter_content, output_dir)

    # Verify markdown was still saved
    assert Path(file_path).exists()
    assert Path(file_path).suffix == ".md"

    # Verify content is correct
    saved_content = Path(file_path).read_text()
    assert "First Article" in saved_content
    assert "Second Article" in saved_content


def test_multiple_newsletters_each_get_audio(
    tmp_path, sample_newsletter_content, mock_audio_result, mocker
):
    """Test that multiple newsletters each get their own audio file."""
    # Mock audio generation
    mock_generate = mocker.patch(
        "src.services.audio.audio_generator.generate_audio_for_newsletter",
        return_value=mock_audio_result
    )

    output_dir = str(tmp_path)

    # Save first newsletter
    file_path_1 = save_consolidated_digest(sample_newsletter_content, output_dir)

    # Save second newsletter (slightly different content)
    content_2 = sample_newsletter_content.replace("First", "Third")
    file_path_2 = save_consolidated_digest(content_2, output_dir)

    # Verify both markdown files exist
    assert Path(file_path_1).exists()
    assert Path(file_path_2).exists()
    assert file_path_1 != file_path_2

    # Verify audio generation was called twice
    assert mock_generate.call_count == 2
