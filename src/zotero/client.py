"""Zotero API client wrapper."""

import logging
from datetime import datetime, timedelta, timezone

from pyzotero import zotero

from src.zotero import AuthenticationError, ZoteroConnectionError
from src.zotero.types import ZoteroItem

logger = logging.getLogger(__name__)


def create_zotero_client(library_id: str, api_key: str) -> zotero.Zotero:
    """
    Create and initialize a Zotero API client.

    Args:
        library_id: Zotero user/library ID
        api_key: Zotero API key

    Returns:
        zotero.Zotero: Initialized Zotero client instance

    Raises:
        AuthenticationError: If credentials are invalid
        ZoteroConnectionError: If connection to API fails
    """
    try:
        # Initialize client for user's personal library
        client = zotero.Zotero(library_id, "user", api_key)
        return client
    except Exception as e:
        error_msg = str(e).lower()
        if (
            "authentication" in error_msg
            or "unauthorized" in error_msg
            or "401" in error_msg
        ):
            raise AuthenticationError() from e
        if (
            "connection" in error_msg
            or "network" in error_msg
            or "timeout" in error_msg
        ):
            raise ZoteroConnectionError() from e
        # Re-raise other exceptions as ZoteroConnectionError for now
        # (could be refined based on actual pyzotero exception types)
        raise ZoteroConnectionError(f"Failed to initialize Zotero client: {e}") from e


def fetch_recent_items(client: zotero.Zotero, days: int) -> list[ZoteroItem]:
    """
    Retrieve library items added within the specified time window.

    Args:
        client: Initialized pyzotero client instance
        days: Number of days to look back (must be > 0)

    Returns:
        List of Zotero API item dictionaries added within the time window

    Raises:
        ValueError: If days <= 0
        AuthenticationError: If API credentials are invalid
        ZoteroConnectionError: If connection to API fails
    """
    if days <= 0:
        raise ValueError("days must be a positive integer")

    # Calculate cutoff timestamp in UTC
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        logger.info("Fetching items added since %s (last %d day(s))", cutoff_iso, days)
        # Note: Zotero API's 'since' parameter expects a version number, not a timestamp
        # Strategy: Fetch ALL items sorted by dateAdded, then filter to only those added in time window
        # Use everything() to get all items (handles pagination automatically)
        all_items = client.everything(client.items(sort="dateAdded", direction="desc"))
        
        # Filter items by dateAdded (client-side filtering) - only items added in time window
        filtered_items = []
        for item in all_items:
            date_added_str = item.get("data", {}).get("dateAdded", "")
            if date_added_str:
                try:
                    # Parse dateAdded (format: "2010-01-04T14:50:40Z")
                    date_added = datetime.fromisoformat(date_added_str.replace("Z", "+00:00"))
                    if date_added >= cutoff:
                        filtered_items.append(item)
                    else:
                        # Since items are sorted by dateAdded descending, once we hit items older than cutoff,
                        # we can stop (all remaining items will be older)
                        break
                except (ValueError, TypeError):
                    # Skip items with invalid dateAdded
                    continue
        
        logger.info("Fetched %d item(s) from Zotero API, %d item(s) added in last %d day(s)", len(all_items), len(filtered_items), days)
        
        # Return items (will be sorted by publication date in sort_and_limit_items)
        return filtered_items
    except Exception as e:
        error_msg = str(e).lower()

        # Check for authentication errors
        if any(
            keyword in error_msg
            for keyword in ["authentication", "unauthorized", "401", "403"]
        ):
            raise AuthenticationError(
                "Invalid Zotero API credentials. "
                "Check your ZOTERO_LIBRARY_ID and ZOTERO_API_KEY."
            ) from e

        # Check for connection errors
        if any(
            keyword in error_msg
            for keyword in ["connection", "network", "timeout", "refused"]
        ):
            raise ZoteroConnectionError(
                "Failed to connect to Zotero API. "
                "Check your internet connection and try again."
            ) from e

        # Re-raise as connection error for unknown exceptions
        raise ZoteroConnectionError(
            f"Failed to fetch items from Zotero API: {e}"
        ) from e
