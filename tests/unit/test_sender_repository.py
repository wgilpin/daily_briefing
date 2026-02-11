"""Unit tests for Repository sender and newsletter_config methods.

Tests CRUD operations for the senders table and key/value newsletter_config table.
All tests mock get_connection so no real DB is needed.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from src.db.repository import Repository
from src.models.newsletter_models import SenderRecord


def _make_conn_mock(cursor_mock):
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = cursor_mock
    return mock_conn


# =============================================================================
# T003 — Sender CRUD methods
# =============================================================================


class TestGetAllSenders:
    def test_returns_empty_list_when_no_rows(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_all_senders()
        assert result == []

    def test_returns_sender_records(self):
        repo = Repository()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            ("a@example.com", "Alice", "", True, now),
            ("b@example.com", None, "custom prompt", False, now),
        ]
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_all_senders()
        assert len(result) == 2
        assert isinstance(result[0], SenderRecord)
        assert result[0].email == "a@example.com"
        assert result[0].display_name == "Alice"
        assert result[1].enabled is False


class TestGetSender:
    def test_returns_none_when_not_found(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_sender("missing@example.com")
        assert result is None

    def test_returns_sender_record_when_found(self):
        repo = Repository()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        cursor = MagicMock()
        cursor.fetchone.return_value = ("a@example.com", "Alice", "", True, now)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_sender("a@example.com")
        assert isinstance(result, SenderRecord)
        assert result.email == "a@example.com"
        assert result.display_name == "Alice"


class TestAddSender:
    def test_executes_insert(self):
        repo = Repository()
        cursor = MagicMock()
        sender = SenderRecord(email="new@example.com", display_name="New", parsing_prompt="", enabled=True)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            repo.add_sender(sender)
        cursor.execute.assert_called_once()
        sql = cursor.execute.call_args[0][0]
        assert "INSERT INTO senders" in sql or "insert into senders" in sql.lower()

    def test_commits_after_insert(self):
        repo = Repository()
        cursor = MagicMock()
        sender = SenderRecord(email="new@example.com")
        mock_conn = _make_conn_mock(cursor)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = mock_conn
            repo.add_sender(sender)
        mock_conn.commit.assert_called_once()


class TestUpdateSender:
    def test_executes_update(self):
        repo = Repository()
        cursor = MagicMock()
        sender = SenderRecord(email="a@example.com", display_name="Updated", parsing_prompt="x", enabled=False)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            repo.update_sender(sender)
        cursor.execute.assert_called_once()
        sql = cursor.execute.call_args[0][0].lower()
        assert "update senders" in sql


class TestUpdateSenderDisplayName:
    def test_executes_update_for_display_name(self):
        repo = Repository()
        cursor = MagicMock()
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            repo.update_sender_display_name("a@example.com", "New Name")
        cursor.execute.assert_called_once()
        sql = cursor.execute.call_args[0][0].lower()
        assert "update senders" in sql
        assert "display_name" in sql

    def test_accepts_none_display_name(self):
        repo = Repository()
        cursor = MagicMock()
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            repo.update_sender_display_name("a@example.com", None)
        cursor.execute.assert_called_once()


class TestDeleteSender:
    def test_executes_delete(self):
        repo = Repository()
        cursor = MagicMock()
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            repo.delete_sender("a@example.com")
        cursor.execute.assert_called_once()
        sql = cursor.execute.call_args[0][0].lower()
        assert "delete from senders" in sql

    def test_commits_after_delete(self):
        repo = Repository()
        cursor = MagicMock()
        mock_conn = _make_conn_mock(cursor)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = mock_conn
            repo.delete_sender("a@example.com")
        mock_conn.commit.assert_called_once()


class TestSenderExists:
    def test_returns_true_when_found(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchone.return_value = (1,)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            assert repo.sender_exists("a@example.com") is True

    def test_returns_false_when_not_found(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            assert repo.sender_exists("missing@example.com") is False


# =============================================================================
# T004 — Newsletter config methods
# =============================================================================


class TestGetNewsletterConfig:
    def test_returns_newsletter_config_values(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            ("consolidation_prompt", "some prompt"),
            ("retention_limit", "100"),
            ("days_lookback", "30"),
            ("max_workers", "10"),
            ("default_parsing_prompt", "parse this"),
            ("default_consolidation_prompt", "consolidate this"),
            ("models", '{"parsing": "gemini-2.0-flash", "consolidation": "gemini-2.0-flash"}'),
            ("excluded_topics", '["topic1", "topic2"]'),
        ]
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_newsletter_config()
        assert result["retention_limit"] == 100
        assert result["days_lookback"] == 30
        assert result["max_workers"] == 10
        assert result["excluded_topics"] == ["topic1", "topic2"]
        assert result["models"] == {"parsing": "gemini-2.0-flash", "consolidation": "gemini-2.0-flash"}
        assert result["consolidation_prompt"] == "some prompt"

    def test_returns_empty_dict_when_no_config(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_newsletter_config()
        assert isinstance(result, dict)


class TestGetConfigValue:
    def test_returns_value_when_found(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchone.return_value = ("hello",)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_config_value("consolidation_prompt")
        assert result == "hello"

    def test_returns_none_when_not_found(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            result = repo.get_config_value("nonexistent_key")
        assert result is None


class TestSetConfigValue:
    def test_executes_upsert(self):
        repo = Repository()
        cursor = MagicMock()
        mock_conn = _make_conn_mock(cursor)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = mock_conn
            repo.set_config_value("retention_limit", "100")
        cursor.execute.assert_called_once()
        sql = cursor.execute.call_args[0][0].lower()
        assert "newsletter_config" in sql
        mock_conn.commit.assert_called_once()


class TestSetConfigValues:
    def test_upserts_all_values(self):
        repo = Repository()
        cursor = MagicMock()
        mock_conn = _make_conn_mock(cursor)
        values = {"retention_limit": "100", "days_lookback": "30"}
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = mock_conn
            repo.set_config_values(values)
        assert cursor.execute.call_count == 2
        mock_conn.commit.assert_called_once()


class TestConfigKeyExists:
    def test_returns_true_when_found(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchone.return_value = (1,)
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            assert repo.config_key_exists("retention_limit") is True

    def test_returns_false_when_not_found(self):
        repo = Repository()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        with patch("src.db.repository.get_connection") as mc:
            mc.return_value.__enter__.return_value = _make_conn_mock(cursor)
            assert repo.config_key_exists("nonexistent") is False
