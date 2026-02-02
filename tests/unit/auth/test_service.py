"""Unit tests for authentication service module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from src.auth.service import (
    create_user,
    authenticate_user,
    get_user_by_id,
    get_user_by_email,
    update_last_login,
)


def test_create_user_with_password_hashes_password():
    """Test that create_user hashes the password before storing."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (123,)

    with patch("src.auth.service.hash_password") as mock_hash:
        mock_hash.return_value = "hashed_password"

        user_id = create_user(mock_conn, "test@example.com", "SecurePass123", "Test User")

        assert user_id == 123
        mock_hash.assert_called_once_with("SecurePass123")
        mock_cursor.execute.assert_called()


def test_create_user_with_google_id_no_password():
    """Test that create_user can create user with Google ID and no password."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (456,)

    user_id = create_user(
        mock_conn, "google@example.com", None, "Google User", google_id="google123"
    )

    assert user_id == 456
    mock_cursor.execute.assert_called()


def test_authenticate_user_with_valid_credentials():
    """Test that authenticate_user returns user_id for valid credentials."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (123, "hashed_password")

    with patch("src.auth.service.verify_password") as mock_verify:
        mock_verify.return_value = True

        user_id = authenticate_user(mock_conn, "test@example.com", "SecurePass123")

        assert user_id == 123
        mock_verify.assert_called_once_with("SecurePass123", "hashed_password")


def test_authenticate_user_with_invalid_password():
    """Test that authenticate_user returns None for invalid password."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (123, "hashed_password")

    with patch("src.auth.service.verify_password") as mock_verify:
        mock_verify.return_value = False

        user_id = authenticate_user(mock_conn, "test@example.com", "WrongPass456")

        assert user_id is None


def test_authenticate_user_with_nonexistent_email():
    """Test that authenticate_user returns None for non-existent email."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    user_id = authenticate_user(mock_conn, "nonexistent@example.com", "password")

    assert user_id is None


def test_get_user_by_id_returns_user():
    """Test that get_user_by_id returns user data."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (
        123,
        "test@example.com",
        "hashed_password",
        None,
        "Test User",
        datetime(2026, 1, 1),
        datetime(2026, 2, 1),
        True,
    )

    user = get_user_by_id(mock_conn, 123)

    assert user is not None
    assert user["id"] == 123
    assert user["email"] == "test@example.com"


def test_get_user_by_id_returns_none_for_nonexistent():
    """Test that get_user_by_id returns None for non-existent user."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    user = get_user_by_id(mock_conn, 999)

    assert user is None


def test_get_user_by_email_returns_user():
    """Test that get_user_by_email returns user data."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (
        123,
        "test@example.com",
        "hashed_password",
        None,
        "Test User",
        datetime(2026, 1, 1),
        datetime(2026, 2, 1),
        True,
    )

    user = get_user_by_email(mock_conn, "test@example.com")

    assert user is not None
    assert user["email"] == "test@example.com"


def test_update_last_login_updates_timestamp():
    """Test that update_last_login updates the last_login_at field."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    update_last_login(mock_conn, 123)

    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called_once()
