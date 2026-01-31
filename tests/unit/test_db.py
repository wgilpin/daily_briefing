"""Unit tests for database connection module.

Tests PostgreSQL connection handling with mocked psycopg2.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestDatabaseConnection:
    """Tests for database connection module."""

    def test_get_connection_success(self, mock_env_vars: dict[str, str]) -> None:
        """Test successful database connection."""
        mock_conn = MagicMock()

        with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
            from src.db.connection import get_connection

            conn = get_connection()

            mock_connect.assert_called_once()
            assert conn == mock_conn

    def test_get_connection_uses_database_url(
        self, mock_env_vars: dict[str, str]
    ) -> None:
        """Test that connection uses DATABASE_URL from environment."""
        mock_conn = MagicMock()

        with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
            from src.db.connection import get_connection

            get_connection()

            # Verify DATABASE_URL was used
            call_args = mock_connect.call_args
            assert mock_env_vars["DATABASE_URL"] in str(call_args)

    def test_get_connection_missing_database_url(self, monkeypatch) -> None:
        """Test error when DATABASE_URL is not set."""
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with patch.dict("os.environ", {}, clear=True):
            from src.db import connection

            # Force reload to pick up new env
            import importlib

            importlib.reload(connection)

            with pytest.raises(ValueError, match="DATABASE_URL"):
                connection.get_connection()

    def test_close_connection(self, mock_env_vars: dict[str, str]) -> None:
        """Test closing database connection."""
        mock_conn = MagicMock()
        mock_conn.closed = False  # Simulate open connection

        with patch("psycopg2.connect", return_value=mock_conn):
            from src.db import connection

            # Reset module state
            connection._connection = None

            connection.get_connection()
            connection.close_connection()

            mock_conn.close.assert_called_once()

    def test_connection_error_handling(self, mock_env_vars: dict[str, str]) -> None:
        """Test handling of connection errors."""
        import psycopg2

        with patch(
            "psycopg2.connect", side_effect=psycopg2.OperationalError("Connection refused")
        ):
            from src.db.connection import get_connection

            with pytest.raises(psycopg2.OperationalError):
                get_connection()
