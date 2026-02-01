"""Zotero feed source adapter.

Wraps existing src/zotero/ functionality to implement FeedSource protocol.
"""

from datetime import datetime, timezone
from typing import Any, Union

from src.models.feed_item import FeedItem
from src.models.source import ZoteroConfig
from src.zotero.client import create_zotero_client, fetch_recent_items
from src.zotero.filters import filter_by_keywords
from src.zotero.types import ZoteroItem


class ZoteroSource:
    """Zotero feed source implementing FeedSource protocol.

    Wraps the existing Zotero client to fetch items and convert them
    to the unified FeedItem format.
    """

    source_type: str = "zotero"

    def __init__(self, config: ZoteroConfig) -> None:
        """Initialize Zotero source with configuration.

        Args:
            config: ZoteroConfig with credentials and settings
        """
        self._config = config
        self._client = create_zotero_client(config.library_id, config.api_key)

    def fetch_items(self) -> list[FeedItem]:
        """Fetch recent items from Zotero library.

        Returns:
            List of FeedItem objects from Zotero
        """
        # Fetch raw items from Zotero API
        raw_items = fetch_recent_items(self._client, self._config.days_lookback)

        # Apply keyword filters if configured
        if self._config.include_keywords or self._config.exclude_keywords:
            raw_items = filter_by_keywords(
                raw_items,
                include=self._config.include_keywords,
                exclude=self._config.exclude_keywords,
            )

        # Filter out attachments and notes (keep only top-level items)
        top_level_items = [
            item for item in raw_items
            if item.get("data", {}).get("itemType") not in ("attachment", "note")
        ]

        # Convert to FeedItem format
        return [self._to_feed_item(item) for item in top_level_items]

    def _to_feed_item(self, zotero_item: Union[ZoteroItem, dict[str, Any]]) -> FeedItem:
        """Convert Zotero API item to FeedItem.

        Args:
            zotero_item: Raw Zotero API response item

        Returns:
            FeedItem with normalized data
        """
        data = zotero_item.get("data", {})
        key = zotero_item.get("key", "")

        # Extract title
        title = data.get("title", "Untitled")

        # Extract date (use dateAdded as the item date)
        date_added_str = data.get("dateAdded", "")
        try:
            date = datetime.fromisoformat(date_added_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            date = datetime.now(timezone.utc)

        # Extract authors
        creators = data.get("creators", [])
        authors = self._format_authors(creators)

        # Extract other fields
        summary = data.get("abstractNote", "")
        link = data.get("url", "")

        return FeedItem(
            id=f"zotero:{key}",
            source_type="zotero",
            source_id=key,
            title=title,
            date=date,
            summary=summary if summary else None,
            link=link if link else None,
            metadata={"authors": authors} if authors else {},
            fetched_at=datetime.now(timezone.utc),
        )

    def _format_authors(self, creators: list[Any]) -> str:
        """Format creator list as author string.

        Args:
            creators: List of Zotero creator objects

        Returns:
            Formatted author string (e.g., "Smith, Jones, Doe")
        """
        author_names = []
        for creator in creators:
            if creator.get("creatorType") in ("author", None):
                last_name = creator.get("lastName", "")
                first_name = creator.get("firstName", "")
                if last_name:
                    author_names.append(last_name)
                elif first_name:
                    author_names.append(first_name)

        return ", ".join(author_names)
