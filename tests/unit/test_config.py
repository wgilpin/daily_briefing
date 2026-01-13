"""Unit tests for newsletter configuration functions."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.utils.config import load_config, save_config


class TestLoadConfig:
    """Tests for load_config() function."""

    def test_load_config_with_valid_file(self):
        """Test loading configuration from valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "senders.json"
            config_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {
                    "newsletter@example.com": {
                        "parsing_prompt": "Extract articles from this newsletter...",
                        "enabled": True,
                        "created_at": "2024-12-30T10:00:00Z",
                    }
                },
                "consolidation_prompt": "Create a consolidated newsletter...",
                "retention_limit": 100,
            }
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            result = load_config(str(config_path))

            # Config should include the original data plus default_parsing_prompt
            assert "models" in result
            assert result["models"] == config_data["models"]
            assert "senders" in result
            assert result["senders"] == config_data["senders"]
            assert "consolidation_prompt" in result
            assert result["consolidation_prompt"] == config_data["consolidation_prompt"]
            assert "retention_limit" in result
            assert result["retention_limit"] == config_data["retention_limit"]
            # default_parsing_prompt should be added if missing
            assert "default_parsing_prompt" in result

    def test_load_config_with_missing_file_raises_error(self):
        """Test loading configuration when file doesn't exist raises error (no defaults for models)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"

            # Should raise ValueError because config file is required
            with pytest.raises(ValueError, match="Configuration file not found"):
                load_config(str(config_path))

    def test_load_config_with_partial_data_applies_defaults(self):
        """Test loading configuration with partial data applies defaults for missing keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "senders.json"
            config_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {
                    "newsletter@example.com": {
                        "parsing_prompt": "Extract articles...",
                        "enabled": True,
                    }
                }
            }
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            result = load_config(str(config_path))

            assert "models" in result
            assert "senders" in result
            assert "consolidation_prompt" in result
            assert result["consolidation_prompt"] == ""  # default
            assert "retention_limit" in result
            assert result["retention_limit"] == 100  # default
            assert "default_parsing_prompt" in result  # default

    def test_load_config_with_invalid_json_raises_error(self):
        """Test loading configuration with invalid JSON raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "invalid.json"
            with open(config_path, "w") as f:
                f.write("{ invalid json }")

            with pytest.raises(json.JSONDecodeError):
                load_config(str(config_path))


class TestSaveConfig:
    """Tests for save_config() function."""

    def test_save_config_creates_file(self):
        """Test saving configuration creates file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "senders.json"
            config_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {
                    "newsletter@example.com": {
                        "parsing_prompt": "Extract articles...",
                        "enabled": True,
                        "created_at": "2024-12-30T10:00:00Z",
                    }
                },
                "consolidation_prompt": "Create consolidated newsletter...",
                "retention_limit": 100,
            }

            save_config(str(config_path), config_data)

            assert config_path.exists()
            with open(config_path) as f:
                saved_data = json.load(f)
            assert saved_data == config_data

    def test_save_config_overwrites_existing_file(self):
        """Test saving configuration overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "senders.json"
            # Create initial file
            initial_data = {
                "models": {
                    "parsing": "gemini-2.0-flash-exp",
                    "consolidation": "gemini-2.0-flash-exp",
                },
                "senders": {}
            }
            with open(config_path, "w") as f:
                json.dump(initial_data, f)

            # Overwrite with new data
            new_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {
                    "new@example.com": {
                        "parsing_prompt": "New prompt",
                        "enabled": True,
                    }
                }
            }
            save_config(str(config_path), new_data)

            with open(config_path) as f:
                saved_data = json.load(f)
            assert saved_data == new_data

    def test_save_config_creates_directory_if_needed(self):
        """Test saving configuration creates parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "senders.json"
            config_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {}
            }

            save_config(str(config_path), config_data)

            assert config_path.exists()
            with open(config_path) as f:
                saved_data = json.load(f)
            assert saved_data == config_data

    def test_save_config_formats_json_pretty(self):
        """Test saving configuration formats JSON with indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "senders.json"
            config_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {
                    "test@example.com": {"parsing_prompt": "Test", "enabled": True}
                }
            }

            save_config(str(config_path), config_data)

            with open(config_path) as f:
                content = f.read()
            # Check that JSON is pretty-printed (has newlines and indentation)
            assert "\n" in content
            assert "  " in content  # indentation

    def test_save_config_with_new_sender(self):
        """Test saving configuration with a new sender."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "senders.json"
            config_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {
                    "new@example.com": {
                        "parsing_prompt": "New prompt",
                        "enabled": True,
                    }
                },
                "consolidation_prompt": "Test prompt",
                "retention_limit": 100,
                "default_parsing_prompt": "Default prompt",
            }

            save_config(str(config_path), config_data)

            with open(config_path) as f:
                saved_data = json.load(f)
            assert saved_data == config_data

    def test_save_config_with_updated_consolidation_prompt(self):
        """Test saving configuration with updated consolidation prompt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "senders.json"
            config_data = {
                "models": {
                    "parsing": "gemini-2.5-flash",
                    "consolidation": "gemini-2.5-flash",
                },
                "senders": {},
                "consolidation_prompt": "New consolidation prompt",
                "retention_limit": 100,
                "default_parsing_prompt": "Default prompt",
            }

            save_config(str(config_path), config_data)

            with open(config_path) as f:
                saved_data = json.load(f)
            assert saved_data == config_data
