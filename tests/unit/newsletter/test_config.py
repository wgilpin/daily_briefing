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
    """Test config loading and saving functions."""

    def test_load_config(self, tmp_path):
        """Config loads from file correctly."""
        config_file = tmp_path / "senders.json"
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["datasette"]
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        loaded_config = load_config(config_file)
        assert loaded_config.excluded_topics == ["datasette"]
        assert loaded_config.retention_limit == 100

    def test_save_config(self, tmp_path):
        """Config saves to file atomically."""
        config_file = tmp_path / "senders.json"
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

        save_config(config, config_file)

        # Verify file was created and contains correct data
        assert config_file.exists()
        saved_data = json.loads(config_file.read_text(encoding="utf-8"))
        assert saved_data["excluded_topics"] == ["datasette", "SQL"]
        assert saved_data["retention_limit"] == 100

    def test_save_config_atomic(self, tmp_path):
        """Config save is atomic (uses temp file)."""
        config_file = tmp_path / "senders.json"
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

        save_config(config, config_file)

        # Verify no .tmp file left behind
        temp_files = list(tmp_path.glob("*.tmp"))
        assert len(temp_files) == 0
