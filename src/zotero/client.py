"""Zotero API client wrapper."""

from datetime import datetime, timedelta

from pyzotero import zotero

from src.zotero import AuthenticationError, ZoteroConnectionError


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
        ConnectionError: If connection to API fails
    """
    try:
        # Initialize client for user's personal library
        client = zotero.Zotero(library_id, "user", api_key)
        return client
    except Exception as e:
        error_msg = str(e).lower()
        if "authentication" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            raise AuthenticationError() from e
        if "connection" in error_msg or "network" in error_msg or "timeout" in error_msg:
            raise ZoteroConnectionError() from e
        # Re-raise other exceptions as ZoteroConnectionError for now
        # (could be refined based on actual pyzotero exception types)
        raise ZoteroConnectionError(f"Failed to initialize Zotero client: {e}") from e


def fetch_recent_items(client: zotero.Zotero, days: int) -> list[dict]:
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
    
    # Calculate cutoff timestamp
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()
    
    try:
        # Fetch items added since cutoff
        items = client.items(since=cutoff_iso)
        return items
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for authentication errors
        if any(keyword in error_msg for keyword in ["authentication", "unauthorized", "401", "403"]):
            raise AuthenticationError(
                "Invalid Zotero API credentials. "
                "Check your ZOTERO_LIBRARY_ID and ZOTERO_API_KEY."
            ) from e
        
        # Check for connection errors
        if any(keyword in error_msg for keyword in ["connection", "network", "timeout", "refused"]):
            raise ZoteroConnectionError(
                "Failed to connect to Zotero API. "
                "Check your internet connection and try again."
            ) from e
        
        # Re-raise as connection error for unknown exceptions
        raise ZoteroConnectionError(
            f"Failed to fetch items from Zotero API: {e}"
        ) from e

