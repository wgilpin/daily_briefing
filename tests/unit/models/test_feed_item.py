"""Unit tests for FeedItem model audio properties.

Tests has_audio and audio_path computed fields.
Per constitution: TDD required - write tests first, ensure they FAIL before implementation.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestFeedItemAudioProperties:
    """Tests for audio-related computed properties on FeedItem."""

    @pytest.fixture
    def sample_feed_item_data(self):
        """Create sample FeedItem data."""
        return {
            'id': 'newsletter:1a4f6b0976cc66ba',
            'source_type': 'newsletter',
            'source_id': '1a4f6b0976cc66ba',
            'title': 'Test Newsletter Item',
            'date': datetime(2026, 2, 6, 12, 0, 0),
            'summary': 'Test summary',
            'link': 'https://example.com/article',
            'metadata': {'sender': 'test@example.com'},
            'fetched_at': datetime(2026, 2, 6, 12, 0, 0),
        }

    # T019: has_audio computed property
    def test_has_audio_returns_true_when_file_exists(self, sample_feed_item_data):
        """Test has_audio returns True when audio file exists."""
        from src.models.feed_item import FeedItem

        item = FeedItem(**sample_feed_item_data)

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True

            # This will FAIL until has_audio is implemented
            assert item.has_audio is True

    def test_has_audio_returns_false_when_file_missing(self, sample_feed_item_data):
        """Test has_audio returns False when audio file doesn't exist."""
        from src.models.feed_item import FeedItem

        item = FeedItem(**sample_feed_item_data)

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            # This will FAIL until has_audio is implemented
            assert item.has_audio is False

    # T020: audio_path computed property
    def test_audio_path_returns_url_when_audio_exists(self, sample_feed_item_data):
        """Test audio_path returns URL when audio file exists."""
        from src.models.feed_item import FeedItem

        item = FeedItem(**sample_feed_item_data)

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True

            # This will FAIL until audio_path is implemented
            expected_path = f"/audio/{item.source_id}"
            assert item.audio_path == expected_path

    def test_audio_path_returns_none_when_no_audio(self, sample_feed_item_data):
        """Test audio_path returns None when audio file doesn't exist."""
        from src.models.feed_item import FeedItem

        item = FeedItem(**sample_feed_item_data)

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False

            # This will FAIL until audio_path is implemented
            assert item.audio_path is None

    def test_has_audio_uses_source_id_for_filename(self, sample_feed_item_data):
        """Test has_audio uses source_id (hash) for audio filename."""
        from src.models.feed_item import FeedItem

        item = FeedItem(**sample_feed_item_data)

        # Create a mock Path instance
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True

        # Patch Path constructor to return our mock
        with patch('src.models.feed_item.Path', return_value=mock_path_instance) as mock_path_class:
            # Access property to trigger file check
            _ = item.has_audio

            # Verify Path was called with the correct filename
            mock_path_class.assert_called_once_with('data/audio_cache/1a4f6b0976cc66ba.wav')
            # Verify exists() was called
            mock_path_instance.exists.assert_called_once()
