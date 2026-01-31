"""PostgreSQL database connection management.

Provides connection handling for the unified feed application.
"""

from typing import Optional

import psycopg2
from psycopg2.extensions import connection as Connection

from src.utils.config import get_database_url

# Module-level connection (singleton pattern for simplicity)
_connection: Optional[Connection] = None


def get_connection() -> Connection:
    """Get PostgreSQL database connection.

    Returns a cached connection or creates a new one if needed.

    Returns:
        Connection: PostgreSQL connection object

    Raises:
        ValueError: If DATABASE_URL is not configured
        psycopg2.OperationalError: If connection fails
    """
    global _connection

    if _connection is None or _connection.closed:
        database_url = get_database_url()
        _connection = psycopg2.connect(database_url)

    return _connection


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
