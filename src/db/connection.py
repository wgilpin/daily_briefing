"""PostgreSQL database connection management.

Provides thread-safe connection pooling with retry logic for the unified feed application.
"""

import atexit
import signal
import time
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Generator, Callable, Any

import psycopg2
import psycopg2.pool
from psycopg2.extensions import connection as Connection

from src.utils.config import get_database_url

# Module-level connection pool (thread-safe)
_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

# Legacy singleton connection (kept for backward compatibility)
_connection: Optional[Connection] = None


def retry_on_pool_exhaustion(max_retries: int = 3, backoff_base: float = 1.0) -> Callable:
    """Decorator for retrying on connection pool exhaustion.

    Implements exponential backoff retry logic: 1s, 2s, 4s delays.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_base: Base delay in seconds (default: 1.0)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except psycopg2.pool.PoolError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        delay = backoff_base * (2 ** attempt)
                        time.sleep(delay)
                    # Last attempt - re-raise

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


def initialize_pool(minconn: int = 2, maxconn: int = 10) -> None:
    """Initialize thread-safe connection pool.

    Should be called once during application startup.

    Args:
        minconn: Minimum number of connections to maintain (default: 2)
        maxconn: Maximum number of connections allowed (default: 10)

    Raises:
        ValueError: If DATABASE_URL is not configured
        psycopg2.OperationalError: If connection fails
    """
    global _pool

    if _pool is not None:
        # Pool already initialized
        return

    database_url = get_database_url()
    _pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=minconn,
        maxconn=maxconn,
        dsn=database_url
    )

    # Register cleanup handlers for application shutdown
    atexit.register(closeall_connections)

    # Register signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        closeall_connections()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


@retry_on_pool_exhaustion(max_retries=3, backoff_base=1.0)
def _get_connection_from_pool() -> Connection:
    """Get connection from pool with retry logic.

    Internal helper with retry decorator applied.

    Returns:
        PostgreSQL connection object

    Raises:
        RuntimeError: If pool not initialized
        psycopg2.pool.PoolError: If pool exhausted after retries
    """
    if _pool is None:
        raise RuntimeError("Connection pool not initialized. Call initialize_pool() first.")

    return _pool.getconn()


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    """Get database connection from pool with retry logic.

    Context manager for safe connection acquisition and release.
    Automatically returns connection to pool after use.
    Retries on pool exhaustion with exponential backoff (1s, 2s, 4s).

    Yields:
        Connection: PostgreSQL connection object

    Raises:
        RuntimeError: If pool not initialized
        psycopg2.pool.PoolError: If pool exhausted after all retries

    Example:
        >>> with get_connection() as conn:
        ...     with conn.cursor() as cur:
        ...         cur.execute("SELECT 1")
    """
    conn = None
    try:
        # Use retry-enabled helper to get connection
        conn = _get_connection_from_pool()
        # Clear any previous transaction state
        conn.rollback()
        yield conn
    finally:
        if conn is not None and _pool is not None:
            _pool.putconn(conn)


def closeall_connections() -> None:
    """Close all connections in the pool.

    WARNING: Only call on application shutdown.
    """
    global _pool

    if _pool is not None:
        _pool.closeall()
        _pool = None


# Legacy functions (kept for backward compatibility)
def close_connection() -> None:
    """Close the database connection if open."""
    global _connection

    if _connection is not None and not _connection.closed:
        _connection.close()
        _connection = None


def reset_connection() -> None:
    """Reset the connection (useful after errors)."""
    global _connection

    close_connection()
    _connection = None
