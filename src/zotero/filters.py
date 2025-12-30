"""Filtering and sorting functions for Zotero items."""

from datetime import datetime
from typing import Optional

from src.zotero.types import ZoteroItem


def sort_and_limit_items(items: list[ZoteroItem], limit: int = 10) -> list[ZoteroItem]:
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
    def get_sort_key(item: ZoteroItem) -> tuple[bool, datetime | None]:
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


def filter_by_keywords(
    items: list[ZoteroItem],
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> list[ZoteroItem]:
    """
    Filter items by keyword matching in title, abstract, and tags.

    Case-insensitive substring matching. Searches in title, abstractNote, and tag names.
    Exclusion takes precedence: items matching exclude keywords are removed first.
    Then inclusion filter applied: items must match at least one include keyword (if provided).

    Args:
        items: List of Zotero item dictionaries
        include: Keywords that must be present (empty/None = no filter)
        exclude: Keywords that must be absent (empty/None = no filter)

    Returns:
        Filtered list of items. Original order preserved (filtering only, no sorting).

    Behavior:
        - Case-insensitive substring matching
        - Searches in: title, abstractNote, and tag names
        - Exclusion takes precedence: items matching exclude keywords are removed first
        - Then inclusion filter applied: items must match at least one include keyword (if provided)
        - Empty `include` list means include all (after exclusions)
        - Empty `exclude` list means no exclusions
    """
    if include is None:
        include = []
    if exclude is None:
        exclude = []

    # Normalize keywords to lowercase for case-insensitive matching
    include_lower = [kw.lower() for kw in include if kw]
    exclude_lower = [kw.lower() for kw in exclude if kw]

    def item_matches_keywords(item: ZoteroItem, keywords: list[str]) -> bool:
        """Check if item matches any of the given keywords."""
        if not keywords:
            return False

        def normalize_text(text: str) -> str:
            """Normalize text for matching: lowercase and replace hyphens/underscores with spaces."""
            return text.lower().replace("-", " ").replace("_", " ")

        data = item.get("data", {})
        search_texts = []

        # Search in title
        title = data.get("title", "")
        if title:
            search_texts.append(normalize_text(title))

        # Search in abstract
        abstract = data.get("abstractNote", "")
        if abstract:
            search_texts.append(normalize_text(abstract))

        # Search in tags
        tags = data.get("tags", [])
        for tag in tags:
            tag_name = tag.get("tag", "")
            if tag_name:
                search_texts.append(normalize_text(tag_name))

        # Combine all searchable text
        combined_text = " ".join(search_texts)

        # Check if any keyword matches (substring search)
        # Normalize keywords too
        for keyword in keywords:
            normalized_keyword = normalize_text(keyword)
            if normalized_keyword in combined_text:
                return True

        return False

    # First, apply exclusion filter (takes precedence)
    filtered_items = items
    if exclude_lower:
        filtered_items = [
            item for item in filtered_items
            if not item_matches_keywords(item, exclude_lower)
        ]

    # Then, apply inclusion filter (if provided)
    if include_lower:
        filtered_items = [
            item for item in filtered_items
            if item_matches_keywords(item, include_lower)
        ]

    return filtered_items

