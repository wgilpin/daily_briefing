"""Session management for user authentication."""

import secrets
from datetime import datetime, timedelta
from typing import Optional


def create_session(
    conn, user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None
) -> str:
    """Create a new session for a user.

    Args:
        conn: Database connection
        user_id: User ID to create session for
        ip_address: Optional IP address of the client
        user_agent: Optional user agent string

    Returns:
        Session ID string
    """
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=30)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (session_id, user_id, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session_id, user_id, expires_at, ip_address, user_agent),
        )
    conn.commit()

    return session_id


def validate_session(conn, session_id: str) -> Optional[int]:
    """Validate a session and return the user ID if valid.

    Args:
        conn: Database connection
        session_id: Session ID to validate

    Returns:
        User ID if session is valid and not expired, None otherwise
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, expires_at
            FROM sessions
            WHERE session_id = %s
            """,
            (session_id,),
        )
        result = cur.fetchone()

        if not result:
            return None

        user_id, expires_at = result

        # Check if session is expired
        if expires_at < datetime.utcnow():
            return None

        # Update last_accessed_at
        cur.execute(
            """
            UPDATE sessions
            SET last_accessed_at = NOW()
            WHERE session_id = %s
            """,
            (session_id,),
        )
        conn.commit()

        return user_id


def cleanup_expired_sessions(conn) -> None:
    """Delete all expired sessions from the database.

    Args:
        conn: Database connection
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM sessions
            WHERE expires_at < NOW()
            """
        )
    conn.commit()


def delete_session(conn, session_id: str) -> None:
    """Delete a specific session (logout).

    Args:
        conn: Database connection
        session_id: Session ID to delete
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM sessions
            WHERE session_id = %s
            """,
            (session_id,),
        )
    conn.commit()


def delete_user_sessions(conn, user_id: int) -> None:
    """Delete all sessions for a specific user.

    Args:
        conn: Database connection
        user_id: User ID whose sessions to delete
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM sessions
            WHERE user_id = %s
            """,
            (user_id,),
        )
    conn.commit()
