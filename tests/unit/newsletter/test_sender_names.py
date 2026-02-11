"""Unit tests for sender name display utilities."""

from unittest.mock import patch
from src.newsletter.sender_names import get_sender_display_name
from src.models.newsletter_models import SenderRecord


def test_get_sender_display_name_with_configured_name():
    """Test getting display name from DB."""
    sender = SenderRecord(email="news@alphasignal.ai", display_name="Alphasignal")
    with patch("src.db.repository.Repository.get_sender", return_value=sender):
        result = get_sender_display_name("news@alphasignal.ai")
    assert result == "Alphasignal"


def test_get_sender_display_name_without_display_name():
    """Test sender without display_name field returns None."""
    sender = SenderRecord(email="test@example.com", display_name=None)
    with patch("src.db.repository.Repository.get_sender", return_value=sender):
        result = get_sender_display_name("test@example.com")
    assert result is None


def test_get_sender_display_name_unknown_sender():
    """Test unknown sender returns None."""
    with patch("src.db.repository.Repository.get_sender", return_value=None):
        result = get_sender_display_name("unknown@example.com")
    assert result is None


def test_get_sender_display_name_empty_email():
    """Test empty email returns None."""
    result = get_sender_display_name("")
    assert result is None


def test_get_sender_display_name_none_email():
    """Test None email returns None."""
    result = get_sender_display_name(None)
    assert result is None


def test_get_sender_display_name_config_error():
    """Test DB error returns None."""
    with patch("src.db.repository.Repository.get_sender", side_effect=Exception("DB error")):
        result = get_sender_display_name("test@example.com")
    assert result is None


def test_get_sender_display_name_multiple_senders():
    """Test multiple senders with different configurations."""
    def _mock_get_sender(email):
        data = {
            "news@alphasignal.ai": SenderRecord(email="news@alphasignal.ai", display_name="Alphasignal"),
            "dan@tldrnewsletter.com": SenderRecord(email="dan@tldrnewsletter.com", display_name="TLDR"),
            "publishing@email.mckinsey.com": SenderRecord(email="publishing@email.mckinsey.com", display_name="McKinsey"),
        }
        return data.get(email)

    with patch("src.db.repository.Repository.get_sender", side_effect=_mock_get_sender):
        assert get_sender_display_name("news@alphasignal.ai") == "Alphasignal"
        assert get_sender_display_name("dan@tldrnewsletter.com") == "TLDR"
        assert get_sender_display_name("publishing@email.mckinsey.com") == "McKinsey"
