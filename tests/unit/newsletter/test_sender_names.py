"""Unit tests for sender name display utilities."""

from unittest.mock import patch
from src.newsletter.sender_names import get_sender_display_name


def test_get_sender_display_name_with_configured_name():
    """Test getting display name from configuration."""
    mock_config = {
        "senders": {
            "news@alphasignal.ai": {
                "enabled": True,
                "display_name": "Alphasignal"
            }
        }
    }

    with patch("src.newsletter.sender_names.load_config", return_value=mock_config):
        result = get_sender_display_name("news@alphasignal.ai")
        assert result == "Alphasignal"


def test_get_sender_display_name_without_display_name():
    """Test sender without display_name field returns None."""
    mock_config = {
        "senders": {
            "test@example.com": {
                "enabled": True
                # No display_name field
            }
        }
    }

    with patch("src.newsletter.sender_names.load_config", return_value=mock_config):
        result = get_sender_display_name("test@example.com")
        assert result is None


def test_get_sender_display_name_unknown_sender():
    """Test unknown sender returns None."""
    mock_config = {
        "senders": {}
    }

    with patch("src.newsletter.sender_names.load_config", return_value=mock_config):
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
    """Test configuration load error returns None."""
    with patch("src.newsletter.sender_names.load_config", side_effect=Exception("Config error")):
        result = get_sender_display_name("test@example.com")
        assert result is None


def test_get_sender_display_name_multiple_senders():
    """Test multiple senders with different configurations."""
    mock_config = {
        "senders": {
            "news@alphasignal.ai": {
                "enabled": True,
                "display_name": "Alphasignal"
            },
            "dan@tldrnewsletter.com": {
                "enabled": True,
                "display_name": "TLDR"
            },
            "publishing@email.mckinsey.com": {
                "enabled": True,
                "display_name": "McKinsey"
            }
        }
    }

    with patch("src.newsletter.sender_names.load_config", return_value=mock_config):
        assert get_sender_display_name("news@alphasignal.ai") == "Alphasignal"
        assert get_sender_display_name("dan@tldrnewsletter.com") == "TLDR"
        assert get_sender_display_name("publishing@email.mckinsey.com") == "McKinsey"
