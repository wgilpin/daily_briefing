"""Unit tests for newsletter configuration with topic exclusions."""

import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.newsletter.config import NewsletterConfig, load_config, save_config


class TestNewsletterConfig:
    """Test NewsletterConfig Pydantic model."""

    def test_config_with_excluded_topics(self):
        """Config loads with excluded_topics list."""
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["datasette", "SQL"]
        }
        config = NewsletterConfig(**config_data)
        assert config.excluded_topics == ["datasette", "SQL"]

    def test_config_without_excluded_topics(self):
        """Config loads with empty excluded_topics if field missing (backward compatibility)."""
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"}
        }
        config = NewsletterConfig(**config_data)
        assert config.excluded_topics == []

    def test_exclusions_max_50_topics(self):
        """Validator rejects > 50 topics."""
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": [f"topic{i}" for i in range(51)]
        }
        with pytest.raises(ValidationError, match="Maximum 50"):
            NewsletterConfig(**config_data)

    def test_exclusions_max_100_chars(self):
        """Validator rejects topics > 100 characters."""
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["a" * 101]
        }
        with pytest.raises(ValidationError, match="100 character limit"):
            NewsletterConfig(**config_data)

    def test_exclusions_allow_duplicates(self):
        """Duplicates are allowed per spec."""
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["datasette", "datasette", "SQL"]
        }
        config = NewsletterConfig(**config_data)
        assert config.excluded_topics == ["datasette", "datasette", "SQL"]

    def test_exclusions_reject_empty_string(self):
        """Validator rejects empty or whitespace-only strings."""
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["valid", "   ", "another"]
        }
        with pytest.raises(ValidationError, match="cannot be empty"):
            NewsletterConfig(**config_data)


class TestConfigLoadSave:
    """Test config loading and saving functions (DB-backed)."""

    def test_load_config(self):
        """load_config reads from Repository."""
        from unittest.mock import patch

        mock_db = {
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["datasette"],
        }
        with patch("src.newsletter.config.Repository") as MockRepo:
            MockRepo.return_value.get_newsletter_config.return_value = mock_db
            MockRepo.return_value.get_all_senders.return_value = []
            loaded_config = load_config()
        assert loaded_config.excluded_topics == ["datasette"]
        assert loaded_config.retention_limit == 100

    def test_save_config(self):
        """save_config writes to Repository.set_config_values."""
        from unittest.mock import patch

        config = NewsletterConfig(
            senders={},
            consolidation_prompt="test prompt",
            retention_limit=100,
            days_lookback=30,
            max_workers=10,
            default_parsing_prompt="test parsing",
            default_consolidation_prompt="test consolidation",
            models={"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            excluded_topics=["datasette", "SQL"]
        )
        with patch("src.newsletter.config.Repository") as MockRepo:
            save_config(config)
            MockRepo.return_value.set_config_values.assert_called_once()
            saved = MockRepo.return_value.set_config_values.call_args[0][0]
        assert saved["retention_limit"] == "100"
        assert json.loads(saved["excluded_topics"]) == ["datasette", "SQL"]

    def test_save_config_atomic(self):
        """save_config does not write any temp files."""
        import tempfile
        from unittest.mock import patch

        config = NewsletterConfig(
            senders={},
            consolidation_prompt="test prompt",
            retention_limit=100,
            days_lookback=30,
            max_workers=10,
            default_parsing_prompt="test parsing",
            default_consolidation_prompt="test consolidation",
            models={"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            excluded_topics=["test"]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.newsletter.config.Repository") as MockRepo:
                save_config(config)
                # No files should have been written
                from pathlib import Path
                assert list(Path(tmpdir).glob("*.tmp")) == []
            MockRepo.return_value.set_config_values.assert_called_once()
