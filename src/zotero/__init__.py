"""Zotero API integration module."""

class AuthenticationError(Exception):
    """Raised when Zotero API authentication fails."""

    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Invalid Zotero API credentials. "
                "Check your ZOTERO_LIBRARY_ID and ZOTERO_API_KEY."
            )
        super().__init__(message)


class ZoteroConnectionError(Exception):
    """Raised when connection to Zotero API fails."""

    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Failed to connect to Zotero API. "
                "Check your internet connection and try again."
            )
        super().__init__(message)


# Alias for backward compatibility with contracts
ConnectionError = ZoteroConnectionError


__all__ = [
    "zotero",
    "AuthenticationError",
    "ZoteroConnectionError",
    "ConnectionError",
]
