"""Newsletter feed source adapter.

Wraps existing src/newsletter/ functionality to implement FeedSource protocol.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from src.models.feed_item import FeedItem
from src.models.source import NewsletterConfig
from src.newsletter.storage import get_all_parsed_items


class NewsletterSource:
    """Newsletter feed source implementing FeedSource protocol.

    Wraps the existing newsletter storage to fetch items and convert them
    to the unified FeedItem format.
    """

    source_type: str = "newsletter"

    def __init__(
        self,
        config: NewsletterConfig,
        db_path: str = "data/newsletter_aggregator.db",
    ) -> None:
        """Initialize Newsletter source with configuration.

        Args:
            config: NewsletterConfig with settings
            db_path: Path to SQLite database (legacy storage)
        """
        self._config = config
        self._db_path = db_path

    def fetch_items(self) -> list[FeedItem]:
        """Fetch newsletter items from storage.

        Returns:
            List of FeedItem objects from newsletter storage
        """
        # Fetch from internal method (allows mocking in tests)
        raw_items = self._fetch_from_storage()

        # Convert to FeedItem format
        return [
            item
            for item in (self._to_feed_item(raw, idx) for idx, raw in enumerate(raw_items))
            if item is not None
        ]

    def _fetch_from_storage(self) -> list[dict[str, Any]]:
        """Fetch raw items from storage.

        This method exists to allow easy mocking in tests.

        Returns:
            List of raw newsletter item dictionaries
        """
        return get_all_parsed_items(self._db_path)

    def _to_feed_item(
        self, newsletter_item: dict[str, Any], index: int
    ) -> Optional[FeedItem]:
        """Convert newsletter item to FeedItem.

        Args:
            newsletter_item: Raw newsletter item dictionary
            index: Item index for ID generation

        Returns:
            FeedItem with normalized data, or None if invalid
        """
        # Extract title (required)
        title = newsletter_item.get("title", "").strip()
        if not title:
            return None

        # Generate unique ID
        # Use a hash of title and date for uniqueness
        item_hash = hash(f"{title}:{newsletter_item.get('date', '')}")
        item_id = f"newsletter:{abs(item_hash)}"

        # Extract date
        date_str = newsletter_item.get("date", "")
        date = self._parse_date(date_str)

        # Extract other fields
        summary = newsletter_item.get("summary", "")
        link = newsletter_item.get("link")
        sender = newsletter_item.get("sender", "")

        # Build metadata
        metadata: dict[str, str] = {}
        if sender:
            metadata["sender"] = sender

        return FeedItem(
            id=item_id,
            source_type="newsletter",
            source_id=str(abs(item_hash)),
            title=title,
            date=date,
            summary=summary if summary else None,
            link=link if link else None,
            metadata=metadata,
            fetched_at=datetime.now(timezone.utc),
        )

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime.

        Args:
            date_str: Date string in various formats

        Returns:
            Parsed datetime (or current time if parsing fails)
        """
        if not date_str:
            return datetime.now(timezone.utc)

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        # Default to current time if parsing fails
        return datetime.now(timezone.utc)
