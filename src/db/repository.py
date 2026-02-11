"""Repository for database CRUD operations.

Provides data access methods for feed items and source configurations.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from src.db.connection import get_connection
from src.models.feed_item import FeedItem
from src.models.newsletter_models import NewsletterConfigValues, SenderRecord
from src.models.source import SourceConfig


class Repository:
    """Database repository for feed items and source configurations."""

    def save_feed_item(self, item: FeedItem) -> None:
        """Save a feed item to the database.

        Uses INSERT ... ON CONFLICT to upsert the item.

        Args:
            item: FeedItem to save
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO feed_items
                        (id, source_type, source_id, title, item_date, summary, link, metadata, fetched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        link = EXCLUDED.link,
                        metadata = EXCLUDED.metadata,
                        fetched_at = EXCLUDED.fetched_at
                    """,
                    (
                        item.id,
                        item.source_type,
                        item.source_id,
                        item.title,
                        item.date,
                        item.summary,
                        item.link,
                        json.dumps(item.metadata),
                        item.fetched_at,
                    ),
                )
            conn.commit()

    def save_feed_items(self, items: list[FeedItem]) -> None:
        """Save multiple feed items in a batch.

        Args:
            items: List of FeedItems to save
        """
        if not items:
            return

        with get_connection() as conn:
            with conn.cursor() as cursor:
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO feed_items
                            (id, source_type, source_id, title, item_date, summary, link, metadata, fetched_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            summary = EXCLUDED.summary,
                            link = EXCLUDED.link,
                            metadata = EXCLUDED.metadata,
                            fetched_at = EXCLUDED.fetched_at
                        """,
                        (
                            item.id,
                            item.source_type,
                            item.source_id,
                            item.title,
                            item.date,
                            item.summary,
                            item.link,
                            json.dumps(item.metadata),
                            item.fetched_at,
                        ),
                    )
            conn.commit()

    def get_feed_items(
        self,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        days: Optional[int] = None,
    ) -> list[FeedItem]:
        """Retrieve feed items from the database.

        Args:
            source_type: Filter by source type (optional)
            limit: Maximum items to return
            offset: Number of items to skip
            days: Filter to items from last N days (optional)

        Returns:
            List of FeedItem objects sorted by date descending
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT id, source_type, source_id, title, item_date,
                           summary, link, metadata, fetched_at
                    FROM feed_items
                    WHERE 1=1
                """
                params: list = []

                if source_type:
                    query += " AND source_type = %s"
                    params.append(source_type)

                if days:
                    query += " AND item_date >= NOW() - INTERVAL '%s days'"
                    params.append(days)

                query += " ORDER BY item_date DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                cursor.execute(query, params)
                rows = cursor.fetchall()

            return [
                FeedItem(
                    id=row[0],
                    source_type=row[1],
                    source_id=row[2],
                    title=row[3],
                    date=row[4],
                    summary=row[5],
                    link=row[6],
                    metadata=row[7] if isinstance(row[7], dict) else json.loads(row[7] or "{}"),
                    fetched_at=row[8],
                )
                for row in rows
            ]

    def get_feed_items_since(
        self,
        since: datetime,
        source_type: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[FeedItem]:
        """Get feed items since a specific datetime.

        Args:
            since: Get items with item_date >= this datetime
            source_type: Filter by source type (optional)
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            List of FeedItem objects sorted by date descending
        """
        import logging
        logger = logging.getLogger(__name__)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT id, source_type, source_id, title, item_date,
                           summary, link, metadata, fetched_at
                    FROM feed_items
                    WHERE item_date >= %s
                """
                params: list = [since]

                if source_type:
                    query += " AND source_type = %s"
                    params.append(source_type)

                query += " ORDER BY item_date DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])

                logger.info(f"get_feed_items_since query: since={since}, source_type={source_type}, limit={limit}")
                cursor.execute(query, params)
                rows = cursor.fetchall()
                logger.info(f"get_feed_items_since returned {len(rows)} rows")

                # Also log what items exist for debugging
                if len(rows) == 0 and source_type:
                    cursor.execute(
                        "SELECT COUNT(*), MIN(item_date), MAX(item_date) FROM feed_items WHERE source_type = %s",
                        (source_type,)
                    )
                    debug_row = cursor.fetchone()
                    if debug_row:
                        count, min_date, max_date = debug_row
                        logger.info(f"Debug: {source_type} has {count} total items, date range: {min_date} to {max_date}")

            return [
                FeedItem(
                    id=row[0],
                    source_type=row[1],
                    source_id=row[2],
                    title=row[3],
                    date=row[4],
                    summary=row[5],
                    link=row[6],
                    metadata=row[7] if isinstance(row[7], dict) else json.loads(row[7] or "{}"),
                    fetched_at=row[8],
                )
                for row in rows
            ]

    def delete_feed_item(self, item_id: str) -> None:
        """Delete a feed item by ID.

        Args:
            item_id: The feed item ID to delete
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM feed_items WHERE id = %s", (item_id,))
            conn.commit()

    def delete_old_feed_items(self, source_type: str, keep_count: int = 100) -> int:
        """Delete old feed items, keeping only the most recent.

        Args:
            source_type: Source type to clean up
            keep_count: Number of recent items to keep

        Returns:
            Number of deleted items
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM feed_items
                    WHERE source_type = %s
                    AND id NOT IN (
                        SELECT id FROM feed_items
                        WHERE source_type = %s
                        ORDER BY item_date DESC
                        LIMIT %s
                    )
                    """,
                    (source_type, source_type, keep_count),
                )
                deleted = cursor.rowcount
            conn.commit()
            return deleted

    def save_source_config(self, config: SourceConfig) -> None:
        """Save source configuration.

        Args:
            config: SourceConfig to save
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO source_configs
                        (source_type, enabled, last_refresh, last_error, settings, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_type) DO UPDATE SET
                        enabled = EXCLUDED.enabled,
                        last_refresh = EXCLUDED.last_refresh,
                        last_error = EXCLUDED.last_error,
                        settings = EXCLUDED.settings,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        config.source_type,
                        config.enabled,
                        config.last_refresh,
                        config.last_error,
                        json.dumps(config.settings),
                        datetime.now(timezone.utc),
                    ),
                )
            conn.commit()

    def get_source_config(self, source_type: str) -> Optional[SourceConfig]:
        """Retrieve source configuration by type.

        Args:
            source_type: The source type to retrieve

        Returns:
            SourceConfig or None if not found
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT source_type, enabled, last_refresh, last_error, settings
                    FROM source_configs
                    WHERE source_type = %s
                    """,
                    (source_type,),
                )
                row = cursor.fetchone()

            if row is None:
                return None

            return SourceConfig(
                source_type=row[0],
                enabled=row[1],
                last_refresh=row[2],
                last_error=row[3],
                settings=row[4] if isinstance(row[4], dict) else json.loads(row[4] or "{}"),
            )

    def get_all_source_configs(self) -> list[SourceConfig]:
        """Retrieve all source configurations.

        Returns:
            List of SourceConfig objects
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT source_type, enabled, last_refresh, last_error, settings
                    FROM source_configs
                    ORDER BY source_type
                    """
                )
                rows = cursor.fetchall()

            return [
                SourceConfig(
                    source_type=row[0],
                    enabled=row[1],
                    last_refresh=row[2],
                    last_error=row[3],
                    settings=row[4] if isinstance(row[4], dict) else json.loads(row[4] or "{}"),
                )
                for row in rows
            ]

    # =========================================================================
    # OAuth Token Methods
    # =========================================================================

    def save_oauth_token(
        self,
        provider: str,
        token_data: dict,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Save an encrypted OAuth token.

        Args:
            provider: OAuth provider name (e.g., 'gmail')
            token_data: Token dictionary to encrypt and store
            expires_at: Token expiration datetime (optional)
        """
        from src.utils.crypto import encrypt_token

        encrypted = encrypt_token(token_data)
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO oauth_tokens
                        (provider, encrypted_token, expires_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (provider) DO UPDATE SET
                        encrypted_token = EXCLUDED.encrypted_token,
                        expires_at = EXCLUDED.expires_at,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        provider,
                        encrypted.decode("latin-1"),  # Store bytes as text
                        expires_at,
                        datetime.now(timezone.utc),
                    ),
                )
            conn.commit()

    def get_oauth_token(
        self, provider: str
    ) -> Optional[tuple[dict, Optional[datetime]]]:
        """Retrieve and decrypt an OAuth token.

        Args:
            provider: OAuth provider name (e.g., 'gmail')

        Returns:
            Tuple of (token_data dict, expires_at datetime) or None if not found
        """
        from src.utils.crypto import decrypt_token

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT provider, encrypted_token, expires_at, updated_at
                    FROM oauth_tokens
                    WHERE provider = %s
                    """,
                    (provider,),
                )
                row = cursor.fetchone()

            if row is None:
                return None

            encrypted = row[1].encode("latin-1")  # Convert text back to bytes
            token_data = decrypt_token(encrypted)
            expires_at = row[2]

            return token_data, expires_at

    def delete_oauth_token(self, provider: str) -> None:
        """Delete an OAuth token.

        Args:
            provider: OAuth provider name (e.g., 'gmail')
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM oauth_tokens WHERE provider = %s",
                    (provider,),
                )
            conn.commit()

    def save_feed_items_batch(self, items: list[FeedItem]) -> None:
        """Save multiple feed items in a batch (alias for save_feed_items).

        Args:
            items: List of FeedItems to save
        """
        self.save_feed_items(items)

    # =========================================================================
    # Newsletter Email Tracking Methods
    # =========================================================================

    def is_email_processed(self, message_id: str) -> bool:
        """Check if email has been processed.

        Args:
            message_id: Gmail message ID

        Returns:
            True if email exists in processed_emails table
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM processed_emails WHERE message_id = %s",
                    (message_id,)
                )
                return cursor.fetchone() is not None

    def get_processed_message_ids(
        self, sender_emails: Optional[list[str]] = None
    ) -> set[str]:
        """Get set of processed message IDs.

        Args:
            sender_emails: Optional filter by sender emails

        Returns:
            Set of message IDs that have been processed
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                if sender_emails:
                    cursor.execute(
                        """
                        SELECT message_id FROM processed_emails
                        WHERE sender_email = ANY(%s)
                        """,
                        (sender_emails,)
                    )
                else:
                    cursor.execute("SELECT message_id FROM processed_emails")

                rows = cursor.fetchall()
                return {row[0] for row in rows}

    def track_email_processed(
        self,
        message_id: str,
        sender_email: str,
        status: str,
        subject: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Record email as processed.

        Args:
            message_id: Gmail message ID
            sender_email: Newsletter sender email
            status: Processing status (collected, converted, parsed, failed)
            subject: Email subject (optional)
            error_message: Error details if status='failed'
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO processed_emails
                    (message_id, sender_email, subject, collected_at, status, error_message)
                    VALUES (%s, %s, %s, NOW(), %s, %s)
                    ON CONFLICT (message_id) DO UPDATE
                    SET status = EXCLUDED.status,
                        processed_at = NOW(),
                        error_message = EXCLUDED.error_message
                    """,
                    (message_id, sender_email, subject, status, error_message)
                )
            conn.commit()

    def update_email_status(
        self,
        message_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update status of existing processed email.

        Args:
            message_id: Gmail message ID
            status: New processing status
            error_message: Error details if status='failed'

        Raises:
            ValueError: If message_id not found
        """
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE processed_emails
                    SET status = %s,
                        processed_at = NOW(),
                        error_message = %s
                    WHERE message_id = %s
                    """,
                    (status, error_message, message_id)
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"Email with message_id '{message_id}' not found")
            conn.commit()

    # =========================================================================
    # Sender CRUD Methods
    # =========================================================================

    def get_all_senders(self) -> list[SenderRecord]:
        """Return all rows from the senders table."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT email, display_name, parsing_prompt, enabled, created_at FROM senders ORDER BY email"
                )
                rows = cursor.fetchall()
        return [
            SenderRecord(
                email=row[0],
                display_name=row[1],
                parsing_prompt=row[2],
                enabled=row[3],
                created_at=row[4],
            )
            for row in rows
        ]

    def get_sender(self, email: str) -> Optional[SenderRecord]:
        """Return a single sender by email, or None."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT email, display_name, parsing_prompt, enabled, created_at FROM senders WHERE email = %s",
                    (email,),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return SenderRecord(
            email=row[0],
            display_name=row[1],
            parsing_prompt=row[2],
            enabled=row[3],
            created_at=row[4],
        )

    def add_sender(self, sender: SenderRecord) -> None:
        """Insert a new sender row."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                if sender.created_at is not None:
                    cursor.execute(
                        """
                        INSERT INTO senders (email, display_name, parsing_prompt, enabled, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            sender.email,
                            sender.display_name,
                            sender.parsing_prompt,
                            sender.enabled,
                            sender.created_at,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO senders (email, display_name, parsing_prompt, enabled)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            sender.email,
                            sender.display_name,
                            sender.parsing_prompt,
                            sender.enabled,
                        ),
                    )
            conn.commit()

    def update_sender(self, sender: SenderRecord) -> None:
        """Update all mutable fields of an existing sender."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE senders
                    SET display_name = %s, parsing_prompt = %s, enabled = %s
                    WHERE email = %s
                    """,
                    (sender.display_name, sender.parsing_prompt, sender.enabled, sender.email),
                )
            conn.commit()

    def update_sender_display_name(self, email: str, display_name: Optional[str]) -> None:
        """Update only the display_name field of a sender."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE senders SET display_name = %s WHERE email = %s",
                    (display_name, email),
                )
            conn.commit()

    def delete_sender(self, email: str) -> None:
        """Delete a sender row by email."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM senders WHERE email = %s", (email,))
            conn.commit()

    def sender_exists(self, email: str) -> bool:
        """Return True if a sender with this email exists."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM senders WHERE email = %s", (email,))
                return cursor.fetchone() is not None

    # =========================================================================
    # Newsletter Config Methods
    # =========================================================================

    def get_newsletter_config(self) -> NewsletterConfigValues:
        """Return all newsletter_config rows as a typed dict with deserialised values."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT setting_name, setting_value FROM newsletter_config")
                rows = cursor.fetchall()
        raw: dict = {row[0]: row[1] for row in rows}
        result: dict = {}
        int_keys = {"retention_limit", "days_lookback", "max_workers"}
        json_keys = {"models", "excluded_topics"}
        for key, value in raw.items():
            if key in int_keys:
                result[key] = int(value)
            elif key in json_keys:
                result[key] = json.loads(value)
            else:
                result[key] = value
        return result  # type: ignore[return-value]

    def get_config_value(self, key: str) -> Optional[str]:
        """Return the raw string value for a config key, or None."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT setting_value FROM newsletter_config WHERE setting_name = %s",
                    (key,),
                )
                row = cursor.fetchone()
        return row[0] if row else None

    def set_config_value(self, key: str, value: str) -> None:
        """Upsert a single config key/value pair."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO newsletter_config (setting_name, setting_value)
                    VALUES (%s, %s)
                    ON CONFLICT (setting_name) DO UPDATE SET setting_value = EXCLUDED.setting_value
                    """,
                    (key, value),
                )
            conn.commit()

    def set_config_values(self, values: dict[str, str]) -> None:
        """Upsert multiple config key/value pairs in a single transaction."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                for key, value in values.items():
                    cursor.execute(
                        """
                        INSERT INTO newsletter_config (setting_name, setting_value)
                        VALUES (%s, %s)
                        ON CONFLICT (setting_name) DO UPDATE SET setting_value = EXCLUDED.setting_value
                        """,
                        (key, value),
                    )
            conn.commit()

    def config_key_exists(self, key: str) -> bool:
        """Return True if a config key exists in newsletter_config."""
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM newsletter_config WHERE setting_name = %s",
                    (key,),
                )
                return cursor.fetchone() is not None
