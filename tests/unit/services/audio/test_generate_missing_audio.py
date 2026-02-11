"""Unit tests for generate_missing_audio module."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.models.feed_item import FeedItem


@pytest.fixture
def mock_feed_items():
    """Create mock feed items for testing."""
    return [
        FeedItem(
            id="newsletter:abc123",
            source_type="newsletter",
            source_id="abc123",
            title="Test Article from Alphasignal",
            date=datetime(2026, 2, 7, tzinfo=timezone.utc),
            summary="This is a test summary.",
            link="https://example.com/article",
            metadata={"sender": "news@alphasignal.ai"},
            fetched_at=datetime(2026, 2, 7, tzinfo=timezone.utc),
        ),
        FeedItem(
            id="newsletter:def456",
            source_type="newsletter",
            source_id="def456",
            title="Another Test Article",
            date=datetime(2026, 2, 7, tzinfo=timezone.utc),
            summary="Another summary.",
            link="https://example.com/article2",
            metadata={"sender": "dan@tldrnewsletter.com"},
            fetched_at=datetime(2026, 2, 7, tzinfo=timezone.utc),
        ),
        FeedItem(
            id="zotero:xyz789",
            source_type="zotero",
            source_id="xyz789",
            title="Research Paper",
            date=datetime(2026, 2, 7, tzinfo=timezone.utc),
            summary="Research summary.",
            link="https://example.com/paper",
            metadata={},  # No sender for Zotero items
            fetched_at=datetime(2026, 2, 7, tzinfo=timezone.utc),
        ),
    ]


def test_audio_text_generation_with_sender():
    """Test that audio text includes sender attribution when configured."""
    from src.newsletter.sender_names import get_sender_display_name

    # Simulate the logic in generate_missing_audio.py
    item_title = "Perplexity Elevates AI Research"
    item_summary = "Perplexity has enhanced its Deep Research system."
    sender_email = "news@alphasignal.ai"

    from src.models.newsletter_models import SenderRecord

    with patch("src.db.repository.Repository.get_sender",
               return_value=SenderRecord(email=sender_email, display_name="Alphasignal")):
        sender_name = get_sender_display_name(sender_email)

        if sender_name:
            text = f"{sender_name} reports that {item_title}. {item_summary}"
        else:
            text = f"{item_title}. {item_summary}"

        assert "Alphasignal reports that" in text
        assert item_title in text
        assert item_summary in text


def test_audio_text_generation_without_sender():
    """Test that audio text works without sender attribution (Zotero items)."""
    item_title = "Research Paper Title"
    item_summary = "Research paper summary."
    sender_email = ""  # No sender for Zotero items

    from src.newsletter.sender_names import get_sender_display_name

    sender_name = get_sender_display_name(sender_email) if sender_email else None

    if sender_name:
        text = f"{sender_name} reports that {item_title}. {item_summary}"
    else:
        text = f"{item_title}. {item_summary}"

    assert text == "Research Paper Title. Research paper summary."
    assert "reports that" not in text


def test_audio_text_generation_sender_not_configured():
    """Test fallback when sender email has no display_name configured."""
    from src.newsletter.sender_names import get_sender_display_name

    item_title = "Test Article"
    item_summary = "Test summary."
    sender_email = "unknown@example.com"

    from src.models.newsletter_models import SenderRecord

    with patch("src.db.repository.Repository.get_sender",
               return_value=SenderRecord(email=sender_email, display_name=None)):
        sender_name = get_sender_display_name(sender_email)

        if sender_name:
            text = f"{sender_name} reports that {item_title}. {item_summary}"
        else:
            text = f"{item_title}. {item_summary}"

        # Should fallback to no attribution
        assert text == "Test Article. Test summary."
        assert "reports that" not in text
