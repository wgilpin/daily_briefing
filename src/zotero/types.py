"""Type definitions for Zotero API data structures."""

from typing import TypedDict


class Creator(TypedDict, total=False):
    """Zotero creator/author structure."""
    
    firstName: str
    lastName: str
    creatorType: str  # e.g., "author", "editor"


class Tag(TypedDict, total=False):
    """Zotero tag structure."""
    
    tag: str


class ItemData(TypedDict, total=False):
    """Zotero item data structure."""
    
    title: str
    itemType: str  # e.g., "journalArticle", "book"
    creators: list[Creator]
    date: str  # Publication date
    dateAdded: str  # When added to library
    dateModified: str  # Last modification
    abstractNote: str
    publicationTitle: str  # Journal/conference name
    url: str
    tags: list[Tag]
    DOI: str


class ZoteroItem(TypedDict, total=False):
    """Zotero API item structure."""
    
    key: str
    version: int
    data: ItemData

