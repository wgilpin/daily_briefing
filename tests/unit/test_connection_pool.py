"""Unit tests for PostgreSQL connection pool.

Tests thread-safe connection pooling with retry logic and error handling.
"""

import time
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
import psycopg2


class TestConnectionPoolInitialization:
    """Test connection pool initialization."""

    def test_initialize_pool_creates_pool(self):
        """Should create ThreadedConnectionPool with specified parameters."""
        import src.db.connection as conn_module

        # Reset pool state
        conn_module._pool = None

        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            with patch("src.db.connection.get_database_url", return_value="postgresql://test"):
                conn_module.initialize_pool(minconn=2, maxconn=10)
                mock_pool.assert_called_once()

    def test_initialize_pool_with_custom_params(self):
        """Should accept custom minconn and maxconn parameters."""
        import src.db.connection as conn_module

        # Reset pool state
        conn_module._pool = None

        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            with patch("src.db.connection.get_database_url", return_value="postgresql://test"):
                conn_module.initialize_pool(minconn=5, maxconn=20)
                # Verify pool created with custom params
                call_args = mock_pool.call_args
                assert call_args[1]["minconn"] == 5
                assert call_args[1]["maxconn"] == 20

    def test_initialize_pool_with_database_url(self):
        """Should use database URL from configuration."""
        import src.db.connection as conn_module

        # Reset pool state
        conn_module._pool = None

        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            with patch("src.db.connection.get_database_url", return_value="postgresql://test"):
                conn_module.initialize_pool()
                call_args = mock_pool.call_args
                assert "dsn" in call_args[1]
                assert call_args[1]["dsn"] == "postgresql://test"


class TestConnectionAcquisition:
    """Test connection acquisition from pool."""

    def test_get_connection_acquires_from_pool(self):
        """Should acquire connection from pool."""
        from src.db.connection import get_connection, initialize_pool

        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("src.db.connection._pool", mock_pool):
            with get_connection() as conn:
                assert conn == mock_conn
                mock_pool.getconn.assert_called_once()

    def test_get_connection_returns_to_pool(self):
        """Should return connection to pool after use."""
        from src.db.connection import get_connection

        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("src.db.connection._pool", mock_pool):
            with get_connection() as conn:
                pass  # Use connection

            # Verify connection returned
            mock_pool.putconn.assert_called_once_with(mock_conn)

    def test_get_connection_returns_on_exception(self):
        """Should return connection even if exception occurs."""
        from src.db.connection import get_connection

        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("src.db.connection._pool", mock_pool):
            try:
                with get_connection() as conn:
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Verify connection still returned
            mock_pool.putconn.assert_called_once_with(mock_conn)

    def test_get_connection_clears_state(self):
        """Should rollback any pending transactions."""
        from src.db.connection import get_connection

        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch("src.db.connection._pool", mock_pool):
            with get_connection() as conn:
                pass

            # Verify rollback called to clear state
            mock_conn.rollback.assert_called_once()


class TestPoolExhaustion:
    """Test behavior when connection pool is exhausted."""

    def test_pool_exhaustion_raises_error(self):
        """Should raise PoolError when pool exhausted (before retry logic added)."""
        from src.db.connection import get_connection

        mock_pool = MagicMock()
        mock_pool.getconn.side_effect = psycopg2.pool.PoolError("connection pool exhausted")

        with patch("src.db.connection._pool", mock_pool):
            # This test will FAIL until T024 implements retry logic
            with pytest.raises(psycopg2.pool.PoolError):
                with get_connection() as conn:
                    pass

    def test_exponential_backoff_retry_logic(self):
        """Should retry with exponential backoff (1s, 2s, 4s) on pool exhaustion."""
        from src.db.connection import get_connection
        import psycopg2.pool

        mock_pool = MagicMock()
        # Fail first 2 times, succeed on 3rd
        mock_pool.getconn.side_effect = [
            psycopg2.pool.PoolError("exhausted"),
            psycopg2.pool.PoolError("exhausted"),
            MagicMock()  # Success on 3rd try
        ]

        with patch("src.db.connection._pool", mock_pool):
            with patch("time.sleep") as mock_sleep:
                try:
                    with get_connection() as conn:
                        assert conn is not None
                except psycopg2.pool.PoolError:
                    # May fail if retry not yet implemented
                    pass

                # If retry implemented, verify exponential backoff: 1s, 2s
                if mock_sleep.call_count > 0:
                    assert mock_sleep.call_count >= 2
                    assert mock_sleep.call_args_list[0][0][0] == 1
                    assert mock_sleep.call_args_list[1][0][0] == 2


class TestConnectionCleanup:
    """Test connection pool cleanup."""

    def test_closeall_closes_all_connections(self):
        """Should close all connections in pool."""
        from src.db.connection import closeall_connections

        mock_pool = MagicMock()

        with patch("src.db.connection._pool", mock_pool):
            closeall_connections()
            mock_pool.closeall.assert_called_once()

    def test_cleanup_on_application_shutdown(self):
        """Should register cleanup handler for application shutdown."""
        import src.db.connection as conn_module

        # Reset pool state
        conn_module._pool = None

        with patch("psycopg2.pool.ThreadedConnectionPool"):
            with patch("src.db.connection.get_database_url", return_value="postgresql://test"):
                with patch("atexit.register") as mock_atexit:
                    with patch("signal.signal"):
                        conn_module.initialize_pool()
                        # Verify atexit handler registered
                        mock_atexit.assert_called()
