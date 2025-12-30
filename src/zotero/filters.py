"""Filtering and sorting functions for Zotero items."""

from datetime import datetime


def sort_and_limit_items(items: list[dict], limit: int = 10) -> list[dict]:
    """
    Sort items by publication date and limit to N most recent.

    If there are more than `limit` items, sorts by publication date (most recent first)
    and returns only the `limit` most recently published items. Items without
    publication dates are sorted to the end.

    Args:
        items: List of Zotero item dictionaries
        limit: Maximum items to return (default: 10)

    Returns:
        Sorted and limited list of items. If len(items) <= limit, returns all items
        sorted by date. If len(items) > limit, returns the `limit` most recently
        published items.

    Raises:
        ValueError: If limit is not positive
    """
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    
    # Always sort by date, even if we have <= limit items
    # This ensures consistent ordering
    
    # Parse dates and create tuples for sorting: (has_date: bool, date: datetime or None, item)
    def get_sort_key(item: dict) -> tuple[bool, datetime | None]:
        """Extract sort key for an item."""
        date_str = item.get("data", {}).get("date", "").strip()
        
        if not date_str:
            # No date - sort to end (False means comes after True)
            return (False, None)
        
        # Try to parse date
        # Zotero dates can be in various formats: YYYY, YYYY-MM, YYYY-MM-DD, or ISO format
        try:
            # Try ISO format first
            if "T" in date_str or date_str.count("-") >= 2:
                # ISO format or full date
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif date_str.count("-") == 1:
                # YYYY-MM format
                date_obj = datetime.strptime(date_str, "%Y-%m")
            else:
                # Just year
                date_obj = datetime(int(date_str), 1, 1)
            
            # Has date, return True and date object (True sorts before False)
            return (True, date_obj)
        except (ValueError, TypeError):
            # Invalid date format - treat as missing
            return (False, None)
    
    # Sort: items with dates first (True > False), then by date descending (newest first)
    sorted_items = sorted(
        items,
        key=get_sort_key,
        reverse=True  # True dates come first, then newest dates first
    )
    
    # Return first `limit` items
    return sorted_items[:limit]

