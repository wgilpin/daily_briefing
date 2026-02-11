"""Unit tests for migrate_senders_if_needed().

T022: Covers all specified scenarios per tasks.md.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestMigrateSendersIfNeeded:

    def test_noop_when_file_absent(self):
        """No DB calls when file does not exist."""
        from src.newsletter.migration import migrate_senders_if_needed

        with patch("src.db.repository.Repository.sender_exists") as mock_exists, \
             patch("src.db.repository.Repository.add_sender") as mock_add, \
             patch("src.db.repository.Repository.set_config_value") as mock_cfg:
            migrate_senders_if_needed(Path("/nonexistent/path/senders.json"))

        mock_exists.assert_not_called()
        mock_add.assert_not_called()
        mock_cfg.assert_not_called()

    def test_inserts_senders_when_not_in_db(self, tmp_path):
        """Senders in file but not in DB are inserted; file renamed to .bak."""
        config = {
            "senders": {
                "a@example.com": {
                    "parsing_prompt": "",
                    "enabled": True,
                    "display_name": "Alice",
                    "created_at": "2026-01-01T00:00:00",
                },
            },
            "retention_limit": 100,
        }
        config_file = tmp_path / "senders.json"
        config_file.write_text(json.dumps(config))

        from src.newsletter.migration import migrate_senders_if_needed

        with patch("src.db.repository.Repository.sender_exists", return_value=False) as mock_exists, \
             patch("src.db.repository.Repository.add_sender") as mock_add, \
             patch("src.db.repository.Repository.config_key_exists", return_value=False), \
             patch("src.db.repository.Repository.set_config_value") as mock_cfg:
            migrate_senders_if_needed(config_file)

        mock_add.assert_called_once()
        added = mock_add.call_args[0][0]
        assert added.email == "a@example.com"
        assert added.display_name == "Alice"

        bak_file = tmp_path / "senders.json.bak"
        assert bak_file.exists()
        assert not config_file.exists()

    def test_skips_senders_already_in_db(self, tmp_path):
        """Senders already in DB are not re-inserted; file still renamed."""
        config = {
            "senders": {
                "existing@example.com": {
                    "parsing_prompt": "",
                    "enabled": True,
                    "created_at": "2026-01-01T00:00:00",
                },
            },
        }
        config_file = tmp_path / "senders.json"
        config_file.write_text(json.dumps(config))

        from src.newsletter.migration import migrate_senders_if_needed

        with patch("src.db.repository.Repository.sender_exists", return_value=True), \
             patch("src.db.repository.Repository.add_sender") as mock_add, \
             patch("src.db.repository.Repository.config_key_exists", return_value=True), \
             patch("src.db.repository.Repository.set_config_value") as mock_cfg:
            migrate_senders_if_needed(config_file)

        mock_add.assert_not_called()
        assert (tmp_path / "senders.json.bak").exists()

    def test_raises_runtime_error_on_malformed_json(self, tmp_path):
        """RuntimeError raised for malformed JSON; file not renamed."""
        config_file = tmp_path / "senders.json"
        config_file.write_text("{ not valid json }")

        from src.newsletter.migration import migrate_senders_if_needed

        with pytest.raises(RuntimeError):
            migrate_senders_if_needed(config_file)

        assert config_file.exists()
        assert not (tmp_path / "senders.json.bak").exists()

    def test_duplicate_email_db_record_kept(self, tmp_path):
        """Duplicate email: DB wins, no insert; file renamed."""
        config = {
            "senders": {
                "dup@example.com": {
                    "parsing_prompt": "file version",
                    "enabled": True,
                    "created_at": "2026-01-01T00:00:00",
                },
            },
        }
        config_file = tmp_path / "senders.json"
        config_file.write_text(json.dumps(config))

        from src.newsletter.migration import migrate_senders_if_needed

        with patch("src.db.repository.Repository.sender_exists", return_value=True) as mock_exists, \
             patch("src.db.repository.Repository.add_sender") as mock_add, \
             patch("src.db.repository.Repository.config_key_exists", return_value=True), \
             patch("src.db.repository.Repository.set_config_value"):
            migrate_senders_if_needed(config_file)

        mock_add.assert_not_called()
        assert (tmp_path / "senders.json.bak").exists()

    def test_global_config_migrated_when_key_absent(self, tmp_path):
        """Global config keys absent from DB are inserted."""
        config = {
            "senders": {},
            "retention_limit": 42,
            "consolidation_prompt": "hello",
        }
        config_file = tmp_path / "senders.json"
        config_file.write_text(json.dumps(config))

        from src.newsletter.migration import migrate_senders_if_needed

        with patch("src.db.repository.Repository.sender_exists", return_value=False), \
             patch("src.db.repository.Repository.add_sender"), \
             patch("src.db.repository.Repository.config_key_exists", return_value=False) as mock_exists, \
             patch("src.db.repository.Repository.set_config_value") as mock_cfg:
            migrate_senders_if_needed(config_file)

        # retention_limit and consolidation_prompt should be set
        keys_set = {call[0][0] for call in mock_cfg.call_args_list}
        assert "retention_limit" in keys_set
        assert "consolidation_prompt" in keys_set

    def test_global_config_skipped_when_key_exists(self, tmp_path):
        """Global config keys already in DB are not overwritten."""
        config = {
            "senders": {},
            "retention_limit": 42,
        }
        config_file = tmp_path / "senders.json"
        config_file.write_text(json.dumps(config))

        from src.newsletter.migration import migrate_senders_if_needed

        with patch("src.db.repository.Repository.sender_exists", return_value=False), \
             patch("src.db.repository.Repository.add_sender"), \
             patch("src.db.repository.Repository.config_key_exists", return_value=True), \
             patch("src.db.repository.Repository.set_config_value") as mock_cfg:
            migrate_senders_if_needed(config_file)

        mock_cfg.assert_not_called()
