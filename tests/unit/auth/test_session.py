"""Unit tests for session management module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.auth.session import (
    create_session,
    validate_session,
    cleanup_expired_sessions,
    delete_session,
)


def test_create_session_generates_valid_session():
    """Test that create_session generates a valid session ID and stores it."""
    mock_conn = MagicMock()
    user_id = 123
    ip_address = "192.168.1.1"
    user_agent = "Mozilla/5.0"

    session_id = create_session(mock_conn, user_id, ip_address, user_agent)

    assert isinstance(session_id, str)
    assert len(session_id) > 20  # Should be cryptographically secure
    mock_conn.cursor.assert_called_once()


def test_validate_session_returns_user_id_for_valid_session():
    """Test that validate_session returns user_id for valid, non-expired session."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock a valid session
    future_time = datetime.utcnow() + timedelta(days=1)
    mock_cursor.fetchone.return_value = (123, future_time)

    user_id = validate_session(mock_conn, "valid_session_id")

    assert user_id == 123
    mock_cursor.execute.assert_called()


def test_validate_session_returns_none_for_expired_session():
    """Test that validate_session returns None for expired session."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock an expired session
    past_time = datetime.utcnow() - timedelta(days=1)
    mock_cursor.fetchone.return_value = (123, past_time)

    user_id = validate_session(mock_conn, "expired_session_id")

    assert user_id is None


def test_validate_session_returns_none_for_nonexistent_session():
    """Test that validate_session returns None for non-existent session."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock no session found
    mock_cursor.fetchone.return_value = None

    user_id = validate_session(mock_conn, "nonexistent_session_id")

    assert user_id is None


def test_cleanup_expired_sessions_deletes_old_sessions():
    """Test that cleanup_expired_sessions removes expired sessions."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    cleanup_expired_sessions(mock_conn)

    # Should execute DELETE query
    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called_once()


def test_delete_session_removes_session():
    """Test that delete_session removes a specific session."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    delete_session(mock_conn, "session_to_delete")

    # Should execute DELETE query for specific session
    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called_once()
