"""FeedItem model for unified feed entries.

Represents a normalized feed item from any source (Zotero, Newsletter, etc.).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FeedItem(BaseModel):
    """A normalized feed item from any source.

    Attributes:
        id: Unique identifier in format source_type:source_id
        source_type: Source identifier (zotero, newsletter)
        source_id: Original ID from source system
        title: Item title (required, non-empty)
        date: Publication or received date
        summary: Abstract or excerpt (optional)
        link: URL to original (optional)
        metadata: Source-specific metadata (authors, sender, etc.)
        fetched_at: When item was fetched from source
    """

    id: str = Field(description="Unique identifier (source_type:source_id)")
    source_type: str = Field(description="Source identifier (zotero, newsletter)")
    source_id: str = Field(description="Original ID from source system")
    title: str = Field(min_length=1, description="Item title")
    date: datetime = Field(description="Publication or received date")
    summary: Optional[str] = Field(default=None, description="Abstract or excerpt")
    link: Optional[str] = Field(default=None, description="URL to original")
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Source-specific metadata (authors, sender, etc.)",
    )
    fetched_at: datetime = Field(description="When item was fetched from source")

    model_config = {"frozen": True}

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that title is not empty or whitespace."""
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v
