"""Unit tests for newsletter config.py DB-backed load/save functions.

T009: load_senders_config and save_senders_config call Repository, not file I/O.
T018: load_config and save_config call Repository, not file I/O.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.newsletter_models import SenderRecord


class TestLoadSendersConfig:
    """load_senders_config() should call Repository.get_all_senders()."""

    def test_calls_repository_get_all_senders(self):
        from src.newsletter.config import load_senders_config

        sender = SenderRecord(email="a@example.com", display_name="Alice", parsing_prompt="", enabled=True)
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_all_senders.return_value = [sender]
            result = load_senders_config()

        MockRepo.return_value.get_all_senders.assert_called_once()
        assert "a@example.com" in result
        assert result["a@example.com"].display_name == "Alice"

    def test_returns_empty_dict_when_no_senders(self):
        from src.newsletter.config import load_senders_config

        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_all_senders.return_value = []
            result = load_senders_config()

        assert result == {}

    def test_does_not_open_files(self):
        from src.newsletter.config import load_senders_config

        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_all_senders.return_value = []
            with patch("builtins.open") as mock_open:
                load_senders_config()
                mock_open.assert_not_called()


class TestSaveSendersConfig:
    """save_senders_config() should call Repository methods, not file I/O."""

    def test_calls_add_sender_for_new_sender(self):
        from src.newsletter.config import save_senders_config

        sender = SenderRecord(email="new@example.com", enabled=True)
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.sender_exists.return_value = False
            save_senders_config({"new@example.com": sender})

        MockRepo.return_value.add_sender.assert_called_once()
        MockRepo.return_value.update_sender.assert_not_called()

    def test_calls_update_sender_for_existing_sender(self):
        from src.newsletter.config import save_senders_config

        sender = SenderRecord(email="existing@example.com", enabled=True)
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.sender_exists.return_value = True
            save_senders_config({"existing@example.com": sender})

        MockRepo.return_value.update_sender.assert_called_once()
        MockRepo.return_value.add_sender.assert_not_called()

    def test_does_not_open_files(self):
        from src.newsletter.config import save_senders_config

        sender = SenderRecord(email="a@example.com")
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.sender_exists.return_value = False
            with patch("builtins.open") as mock_open:
                save_senders_config({"a@example.com": sender})
                mock_open.assert_not_called()


# =============================================================================
# T018 — load_config / save_config
# =============================================================================


class TestLoadConfig:
    """load_config() should call Repository.get_newsletter_config(), not file I/O."""

    def test_calls_repository_get_newsletter_config(self):
        from src.newsletter.config import load_config

        mock_config = {
            "consolidation_prompt": "cp",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "dpp",
            "default_consolidation_prompt": "dcp",
            "models": {"parsing": "gemini-2.0-flash", "consolidation": "gemini-2.0-flash"},
            "excluded_topics": [],
            "senders": {},
        }
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_newsletter_config.return_value = mock_config
            MockRepo.return_value.get_all_senders.return_value = []
            result = load_config()

        MockRepo.return_value.get_newsletter_config.assert_called_once()
        assert result.retention_limit == 100

    def test_does_not_open_files(self):
        from src.newsletter.config import load_config

        mock_config = {
            "consolidation_prompt": "",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "",
            "default_consolidation_prompt": "",
            "models": {"parsing": "gemini-2.0-flash", "consolidation": "gemini-2.0-flash"},
            "excluded_topics": [],
            "senders": {},
        }
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_newsletter_config.return_value = mock_config
            MockRepo.return_value.get_all_senders.return_value = []
            with patch("builtins.open") as mock_open:
                load_config()
                mock_open.assert_not_called()


class TestSaveConfig:
    """save_config() should call Repository.set_config_values(), not file I/O."""

    def test_calls_set_config_values(self):
        from src.newsletter.config import load_config, save_config

        mock_config = {
            "consolidation_prompt": "cp",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "dpp",
            "default_consolidation_prompt": "dcp",
            "models": {"parsing": "gemini-2.0-flash", "consolidation": "gemini-2.0-flash"},
            "excluded_topics": [],
            "senders": {},
        }
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_newsletter_config.return_value = mock_config
            MockRepo.return_value.get_all_senders.return_value = []
            config = load_config()

        with patch("src.newsletter.config.Repository") as MockRepo:
            save_config(config)
            MockRepo.return_value.set_config_values.assert_called_once()

    def test_does_not_open_files(self):
        from src.newsletter.config import load_config, save_config

        mock_config = {
            "consolidation_prompt": "",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "",
            "default_consolidation_prompt": "",
            "models": {"parsing": "gemini-2.0-flash", "consolidation": "gemini-2.0-flash"},
            "excluded_topics": [],
            "senders": {},
        }
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_newsletter_config.return_value = mock_config
            MockRepo.return_value.get_all_senders.return_value = []
            config = load_config()

        with patch("src.newsletter.config.Repository") as MockRepo:
            with patch("builtins.open") as mock_open:
                save_config(config)
                mock_open.assert_not_called()
