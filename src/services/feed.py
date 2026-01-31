"""Feed aggregation service.

Aggregates, sorts, and paginates feed items from multiple sources.
"""

import logging
from datetime import datetime
from typing import Any, Optional, Protocol

from src.db.repository import Repository
from src.models.feed_item import FeedItem

logger = logging.getLogger(__name__)


class FeedSource(Protocol):
    """Protocol for feed source implementations."""

    @property
    def source_type(self) -> str:
        """Return the unique identifier for this source type."""
        ...

    def fetch_items(self) -> list[FeedItem]:
        """Fetch items from the source."""
        ...


class FeedService:
    """Service for managing the unified feed.

    Provides methods to retrieve, filter, and sort feed items
    from the database (which aggregates items from all sources).
    """

    def __init__(self, repository: Optional[Repository] = None) -> None:
        """Initialize FeedService.

        Args:
            repository: Repository instance (creates one if not provided)
        """
        self._repository = repository or Repository()
        self._sources: dict = {}

    def get_unified_feed(
        self,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        days: Optional[int] = None,
    ) -> list[FeedItem]:
        """Get unified feed items from all sources.

        Retrieves items from the database, sorted by date (newest first).

        Args:
            source_type: Filter by source type (optional)
            limit: Maximum number of items to return
            offset: Number of items to skip (for pagination)
            days: Filter to items from last N days (optional)

        Returns:
            List of FeedItem objects sorted by date descending
        """
        items = self._repository.get_feed_items(
            source_type=source_type,
            limit=limit,
            offset=offset,
            days=days,
        )

        # Ensure sorted by date descending (in case DB doesn't guarantee order)
        return sorted(items, key=lambda x: x.date, reverse=True)

    def get_feed_count(
        self,
        source_type: Optional[str] = None,
        days: Optional[int] = None,
    ) -> int:
        """Get total count of feed items.

        Args:
            source_type: Filter by source type (optional)
            days: Filter to items from last N days (optional)

        Returns:
            Total number of matching items
        """
        # For now, retrieve all items and count
        # Could be optimized with a COUNT query in repository
        items = self._repository.get_feed_items(
            source_type=source_type,
            limit=10000,  # High limit to get all
            offset=0,
            days=days,
        )
        return len(items)

    @property
    def sources(self) -> dict[str, FeedSource]:
        """Get registered sources."""
        return self._sources

    def register_source(self, source: FeedSource) -> None:
        """Register a feed source.

        Args:
            source: FeedSource implementation to register
        """
        self._sources[source.source_type] = source
        logger.info(f"Registered feed source: {source.source_type}")

    def refresh_all(self) -> dict[str, Any]:
        """Refresh feed from all registered sources.

        Fetches items from all sources and saves them to the repository.
        Handles partial failures gracefully.

        Returns:
            dict with:
                - success: True if at least one source succeeded
                - sources: dict of source_type -> {items_fetched, error}
                - total_items: Total items fetched across all sources
        """
        result: dict[str, Any] = {
            "success": False,
            "sources": {},
            "total_items": 0,
        }

        if not self._sources:
            logger.warning("No sources registered for refresh")
            return result

        all_items: list[FeedItem] = []
        any_success = False

        for source_type, source in self._sources.items():
            source_result: dict[str, Any] = {
                "items_fetched": 0,
                "error": None,
            }

            try:
                logger.info(f"Refreshing source: {source_type}")
                items = source.fetch_items()
                source_result["items_fetched"] = len(items)
                all_items.extend(items)
                any_success = True
                logger.info(f"Fetched {len(items)} items from {source_type}")
            except Exception as e:
                source_result["error"] = str(e)
                logger.error(f"Error refreshing {source_type}: {e}")

            result["sources"][source_type] = source_result

        # Save all items to repository
        if all_items:
            try:
                self._repository.save_feed_items_batch(all_items)
                logger.info(f"Saved {len(all_items)} items to repository")
            except Exception as e:
                logger.error(f"Error saving items to repository: {e}")
                # Still mark as partial success if we fetched items
                if not any_success:
                    result["success"] = False
                    return result

        result["success"] = any_success
        result["total_items"] = len(all_items)
        return result

    def filter_items(
        self,
        source_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedItem]:
        """Filter feed items by criteria.

        Args:
            source_type: Filter by source type (optional)
            start_date: Filter items on or after this date (optional)
            end_date: Filter items on or before this date (optional)
            limit: Maximum number of items to return
            offset: Number of items to skip (for pagination)

        Returns:
            List of FeedItem objects matching the criteria
        """
        # Get all items from repository (with source filter if provided)
        items = self._repository.get_feed_items(
            source_type=source_type,
            limit=10000,  # Get all for filtering
            offset=0,
        )

        # Apply date filters in memory
        if start_date:
            items = [item for item in items if item.date >= start_date]
        if end_date:
            items = [item for item in items if item.date <= end_date]

        # Sort by date descending
        items = sorted(items, key=lambda x: x.date, reverse=True)

        # Apply pagination
        return items[offset:offset + limit]

    def search_items(
        self,
        query: str,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedItem]:
        """Search feed items by keyword.

        Searches in title and summary fields (case-insensitive).

        Args:
            query: Search query string
            source_type: Filter by source type (optional)
            limit: Maximum number of items to return
            offset: Number of items to skip (for pagination)

        Returns:
            List of FeedItem objects matching the search query
        """
        # If empty query, return all items
        if not query.strip():
            return self.get_unified_feed(
                source_type=source_type,
                limit=limit,
                offset=offset,
            )

        # Get all items from repository
        items = self._repository.get_feed_items(
            source_type=source_type,
            limit=10000,  # Get all for searching
            offset=0,
        )

        # Search in title and summary (case-insensitive)
        query_lower = query.lower()
        matching_items = []

        for item in items:
            title_match = query_lower in item.title.lower()
            summary_match = (
                query_lower in (item.summary or "").lower() if item.summary else False
            )

            if title_match or summary_match:
                matching_items.append(item)

        # Sort by date descending
        matching_items = sorted(matching_items, key=lambda x: x.date, reverse=True)

        # Apply pagination
        return matching_items[offset:offset + limit]
