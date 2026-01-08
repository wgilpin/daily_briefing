"""Zotero API integration module."""

from typing import Optional


class AuthenticationError(Exception):
    """Raised when Zotero API authentication fails."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = (
                "Invalid Zotero API credentials. "
                "Check your ZOTERO_LIBRARY_ID and ZOTERO_API_KEY."
            )
        super().__init__(message)


class ZoteroConnectionError(Exception):
    """Raised when connection to Zotero API fails."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = (
                "Failed to connect to Zotero API. "
                "Check your internet connection and try again."
            )
        super().__init__(message)


from src.zotero.types import Creator, ItemData, Tag, ZoteroItem

__all__ = [
    "AuthenticationError",
    "ZoteroConnectionError",
    "Creator",
    "ItemData",
    "Tag",
    "ZoteroItem",
]
