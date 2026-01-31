"""Source configuration models for the unified feed application.

Defines configuration models for:
- SourceConfig: Generic source configuration
- ZoteroConfig: Zotero-specific settings
- NewsletterConfig: Newsletter-specific settings
- AppSettings: Global application settings
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    """Configuration for a feed source.

    Attributes:
        source_type: Source identifier (zotero, newsletter)
        enabled: Whether the source is active
        last_refresh: Timestamp of last successful refresh
        last_error: Error message from last failed refresh
        settings: Source-specific settings dictionary
    """

    source_type: str = Field(description="Source identifier")
    enabled: bool = Field(default=True)
    last_refresh: Optional[datetime] = Field(default=None)
    last_error: Optional[str] = Field(default=None)
    settings: dict[str, str] = Field(
        default_factory=dict,
        description="Source-specific settings",
    )


class ZoteroConfig(BaseModel):
    """Zotero-specific configuration.

    Attributes:
        library_id: Zotero library ID
        api_key: Zotero API key (from environment, not stored in DB)
        days_lookback: Days to look back for items (1-365)
        include_keywords: Keywords to include in results
        exclude_keywords: Keywords to exclude from results
    """

    library_id: str
    api_key: str = Field(description="From environment, not stored in DB")
    days_lookback: int = Field(default=7, ge=1, le=365)
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)


class NewsletterConfig(BaseModel):
    """Newsletter-specific configuration.

    Attributes:
        sender_emails: List of sender email addresses to collect from
        parsing_prompt: Custom LLM prompt for parsing newsletters
        max_emails_per_refresh: Maximum emails to process per refresh (1-100)
    """

    sender_emails: list[str] = Field(default_factory=list)
    parsing_prompt: Optional[str] = Field(default=None)
    max_emails_per_refresh: int = Field(default=20, ge=1, le=100)


class AppSettings(BaseModel):
    """Global application settings.

    Attributes:
        default_days_lookback: Default days to look back
        page_size: Items per page (10-100)
        refresh_timeout_seconds: Timeout for refresh operations
    """

    default_days_lookback: int = Field(default=7)
    page_size: int = Field(default=50, ge=10, le=100)
    refresh_timeout_seconds: int = Field(default=60)
