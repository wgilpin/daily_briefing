"""Authentication service - business logic for user management."""

from typing import Optional

from src.auth.password import hash_password, verify_password


def create_user(
    conn,
    email: str,
    password: Optional[str] = None,
    name: Optional[str] = None,
    google_id: Optional[str] = None,
) -> int:
    """Create a new user account.

    Args:
        conn: Database connection
        email: User email address
        password: Optional password (hashed before storage)
        name: Optional user name
        google_id: Optional Google OAuth ID

    Returns:
        Created user ID

    Raises:
        Exception: If email already exists
    """
    password_hash = hash_password(password) if password else None

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, google_id, name)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (email, password_hash, google_id, name),
        )
        user_id = cur.fetchone()[0]
    conn.commit()

    return user_id


def authenticate_user(conn, email: str, password: str) -> Optional[int]:
    """Authenticate a user with email and password.

    Args:
        conn: Database connection
        email: User email address
        password: Plain text password

    Returns:
        User ID if authentication successful, None otherwise
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, password_hash
            FROM users
            WHERE email = %s AND is_active = TRUE
            """,
            (email,),
        )
        result = cur.fetchone()

        if not result:
            return None

        user_id, password_hash = result

        if not password_hash:
            # User has no password (Google-only account)
            return None

        if verify_password(password, password_hash):
            return user_id

        return None


def get_user_by_id(conn, user_id: int) -> Optional[dict]:
    """Get user by ID.

    Args:
        conn: Database connection
        user_id: User ID to fetch

    Returns:
        User dictionary if found, None otherwise
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, password_hash, google_id, name, created_at, last_login_at, is_active
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
        result = cur.fetchone()

        if not result:
            return None

        return {
            "id": result[0],
            "email": result[1],
            "password_hash": result[2],
            "google_id": result[3],
            "name": result[4],
            "created_at": result[5],
            "last_login_at": result[6],
            "is_active": result[7],
        }


def get_user_by_email(conn, email: str) -> Optional[dict]:
    """Get user by email.

    Args:
        conn: Database connection
        email: User email to fetch

    Returns:
        User dictionary if found, None otherwise
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, password_hash, google_id, name, created_at, last_login_at, is_active
            FROM users
            WHERE email = %s
            """,
            (email,),
        )
        result = cur.fetchone()

        if not result:
            return None

        return {
            "id": result[0],
            "email": result[1],
            "password_hash": result[2],
            "google_id": result[3],
            "name": result[4],
            "created_at": result[5],
            "last_login_at": result[6],
            "is_active": result[7],
        }


def update_last_login(conn, user_id: int) -> None:
    """Update the last login timestamp for a user.

    Args:
        conn: Database connection
        user_id: User ID to update
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET last_login_at = NOW()
            WHERE id = %s
            """,
            (user_id,),
        )
    conn.commit()


def link_google_account(conn, user_id: int, google_id: str) -> None:
    """Link a Google account to an existing user (account merging).

    Args:
        conn: Database connection
        user_id: Existing user ID
        google_id: Google OAuth ID to link
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET google_id = %s
            WHERE id = %s
            """,
            (google_id, user_id),
        )
    conn.commit()
