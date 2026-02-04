"""Unit tests for repository email tracking methods.

Tests email processing tracking in PostgreSQL.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.db.repository import Repository


class TestIsEmailProcessed:
    """Test checking if email is already processed."""

    def test_returns_true_when_email_exists(self):
        """Should return True when email found in processed_emails."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            result = repo.is_email_processed("test_message_id")

        assert result is True
        mock_cursor.execute.assert_called_once()
        assert "SELECT 1 FROM processed_emails" in mock_cursor.execute.call_args[0][0]
        assert "message_id" in mock_cursor.execute.call_args[0][0]

    def test_returns_false_when_email_not_exists(self):
        """Should return False when email not found."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            result = repo.is_email_processed("nonexistent_id")

        assert result is False


class TestGetProcessedMessageIds:
    """Test retrieving set of processed message IDs."""

    def test_returns_all_message_ids_when_no_filter(self):
        """Should return all processed message IDs when no sender filter."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("msg1",),
            ("msg2",),
            ("msg3",)
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            result = repo.get_processed_message_ids()

        assert result == {"msg1", "msg2", "msg3"}
        mock_cursor.execute.assert_called_once()

    def test_filters_by_sender_emails(self):
        """Should filter by sender emails when provided."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("msg1",),
            ("msg2",)
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            result = repo.get_processed_message_ids(
                sender_emails=["sender1@example.com", "sender2@example.com"]
            )

        assert result == {"msg1", "msg2"}
        # Verify WHERE clause includes sender filter
        execute_args = mock_cursor.execute.call_args[0]
        assert "sender_email IN" in execute_args[0] or "sender_email = ANY" in execute_args[0]

    def test_returns_empty_set_when_no_results(self):
        """Should return empty set when no emails processed."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            result = repo.get_processed_message_ids()

        assert result == set()


class TestTrackEmailProcessed:
    """Test recording email as processed."""

    def test_inserts_new_email_record(self):
        """Should insert new record in processed_emails."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            repo.track_email_processed(
                message_id="test_msg",
                sender_email="sender@example.com",
                status="collected",
                subject="Test Subject"
            )

        mock_cursor.execute.assert_called_once()
        execute_args = mock_cursor.execute.call_args[0]
        # Verify INSERT statement
        assert "INSERT INTO processed_emails" in execute_args[0]
        assert "ON CONFLICT" in execute_args[0]
        # Verify parameters passed
        assert "test_msg" in execute_args[1]
        assert "sender@example.com" in execute_args[1]
        assert "collected" in execute_args[1]
        mock_conn.commit.assert_called_once()

    def test_updates_existing_email_on_conflict(self):
        """Should update status on conflict (message_id already exists)."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            repo.track_email_processed(
                message_id="existing_msg",
                sender_email="sender@example.com",
                status="parsed"
            )

        execute_args = mock_cursor.execute.call_args[0]
        # Verify ON CONFLICT clause for upsert
        assert "ON CONFLICT" in execute_args[0]
        assert "DO UPDATE" in execute_args[0]

    def test_handles_optional_subject(self):
        """Should handle None subject gracefully."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            repo.track_email_processed(
                message_id="test_msg",
                sender_email="sender@example.com",
                status="collected",
                subject=None
            )

        execute_args = mock_cursor.execute.call_args[0]
        # Verify None handled in parameters
        assert None in execute_args[1]

    def test_records_error_message_for_failed_status(self):
        """Should record error message when status is 'failed'."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            repo.track_email_processed(
                message_id="test_msg",
                sender_email="sender@example.com",
                status="failed",
                error_message="Parsing failed"
            )

        execute_args = mock_cursor.execute.call_args[0]
        assert "Parsing failed" in execute_args[1]


class TestUpdateEmailStatus:
    """Test updating status of existing processed email."""

    def test_updates_email_status(self):
        """Should update status and processed_at timestamp."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            repo.update_email_status(
                message_id="test_msg",
                status="parsed"
            )

        execute_args = mock_cursor.execute.call_args[0]
        assert "UPDATE processed_emails" in execute_args[0]
        assert "SET status" in execute_args[0]
        assert "WHERE message_id" in execute_args[0]
        mock_conn.commit.assert_called_once()

    def test_updates_error_message_when_provided(self):
        """Should update error_message field when provided."""
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            repo.update_email_status(
                message_id="test_msg",
                status="failed",
                error_message="Connection timeout"
            )

        execute_args = mock_cursor.execute.call_args[0]
        assert "error_message" in execute_args[0]
        assert "Connection timeout" in execute_args[1]

    def test_raises_error_if_message_not_found(self):
        """Should raise ValueError if message_id not found."""
        # This test will FAIL until validation added
        repo = Repository()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0  # No rows affected
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("src.db.repository.get_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            with pytest.raises(ValueError, match="not found"):
                repo.update_email_status(
                    message_id="nonexistent",
                    status="parsed"
                )
