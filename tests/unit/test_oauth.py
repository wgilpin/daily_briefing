"""Unit tests for OAuth token encryption and decryption.

Tests the crypto utility for encrypting/decrypting OAuth tokens.
"""

import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import pytest

from src.models.source import SourceConfig


class TestTokenEncryption:
    """Tests for OAuth token encryption/decryption."""

    def test_encrypt_token_returns_bytes(self, mock_env_vars: dict[str, str]) -> None:
        """Test that encryption returns encrypted bytes."""
        from src.utils.crypto import encrypt_token

        token_data = {"access_token": "test_access", "refresh_token": "test_refresh"}
        encrypted = encrypt_token(token_data)

        assert isinstance(encrypted, bytes)
        # Encrypted data should be different from plaintext
        assert b"test_access" not in encrypted

    def test_decrypt_token_returns_original(self, mock_env_vars: dict[str, str]) -> None:
        """Test that decryption returns original token data."""
        from src.utils.crypto import encrypt_token, decrypt_token

        token_data = {"access_token": "test_access", "refresh_token": "test_refresh"}
        encrypted = encrypt_token(token_data)
        decrypted = decrypt_token(encrypted)

        assert decrypted == token_data

    def test_encrypt_decrypt_roundtrip(self, mock_env_vars: dict[str, str]) -> None:
        """Test full encryption/decryption roundtrip."""
        from src.utils.crypto import encrypt_token, decrypt_token

        token_data = {
            "access_token": "ya29.complex_token_value",
            "refresh_token": "1//long_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "client_id.apps.googleusercontent.com",
            "expiry": "2026-01-30T12:00:00Z",
        }

        encrypted = encrypt_token(token_data)
        decrypted = decrypt_token(encrypted)

        assert decrypted == token_data

    def test_decrypt_invalid_data_raises_error(self, mock_env_vars: dict[str, str]) -> None:
        """Test that decrypting invalid data raises an error."""
        from src.utils.crypto import decrypt_token

        with pytest.raises(Exception):
            decrypt_token(b"invalid_encrypted_data")

    def test_encryption_uses_encryption_key(self) -> None:
        """Test that encryption uses ENCRYPTION_KEY from environment."""
        from src.utils.crypto import encrypt_token, decrypt_token

        token_data = {"access_token": "test"}

        # Encrypt with one key
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "key1_32_bytes_padding_here_123!"}):
            encrypted1 = encrypt_token(token_data)

        # Encrypt with different key
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "key2_32_bytes_padding_here_456!"}):
            encrypted2 = encrypt_token(token_data)

        # Encrypted values should be different
        assert encrypted1 != encrypted2

    def test_missing_encryption_key_raises_error(self) -> None:
        """Test that missing ENCRYPTION_KEY raises an error."""
        from src.utils.crypto import encrypt_token

        with patch.dict(os.environ, {}, clear=True):
            # Remove ENCRYPTION_KEY
            if "ENCRYPTION_KEY" in os.environ:
                del os.environ["ENCRYPTION_KEY"]

            with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
                encrypt_token({"access_token": "test"})


class TestOAuthTokenRepository:
    """Tests for OAuth token storage in repository."""

    def test_save_oauth_token(self, mock_db_connection, mock_env_vars: dict[str, str]) -> None:
        """Test saving an OAuth token."""
        mock_conn, mock_cursor = mock_db_connection

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            token_data = {
                "access_token": "test_access",
                "refresh_token": "test_refresh",
            }
            expires_at = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)

            repo.save_oauth_token("gmail", token_data, expires_at)

            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()

    def test_get_oauth_token(self, mock_db_connection, mock_env_vars: dict[str, str]) -> None:
        """Test retrieving an OAuth token."""
        mock_conn, mock_cursor = mock_db_connection

        # First encrypt a token to get valid encrypted data
        from src.utils.crypto import encrypt_token
        token_data = {"access_token": "test_access", "refresh_token": "test_refresh"}
        encrypted = encrypt_token(token_data)

        mock_cursor.fetchone.return_value = (
            "gmail",
            encrypted.decode("latin-1"),  # Stored as text
            datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 30, 10, 0, 0, tzinfo=timezone.utc),
        )

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            result = repo.get_oauth_token("gmail")

            assert result is not None
            token, expires_at = result
            assert token["access_token"] == "test_access"
            assert token["refresh_token"] == "test_refresh"

    def test_get_oauth_token_not_found(self, mock_db_connection, mock_env_vars: dict[str, str]) -> None:
        """Test retrieving non-existent OAuth token."""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            result = repo.get_oauth_token("nonexistent")

            assert result is None

    def test_delete_oauth_token(self, mock_db_connection, mock_env_vars: dict[str, str]) -> None:
        """Test deleting an OAuth token."""
        mock_conn, mock_cursor = mock_db_connection

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            repo.delete_oauth_token("gmail")

            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
