"""Pydantic models for newsletter database consolidation.

This module provides strongly-typed models for newsletter email tracking,
connection pool configuration, and newsletter item processing.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class ConnectionPoolConfig(BaseModel):
    """Configuration for PostgreSQL connection pool."""

    minconn: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Minimum number of connections to maintain"
    )
    maxconn: int = Field(
        default=10,
        ge=2,
        le=50,
        description="Maximum number of connections allowed"
    )
    database_url: str = Field(
        ...,
        description="PostgreSQL connection string"
    )

    @field_validator("maxconn")
    @classmethod
    def maxconn_greater_than_minconn(cls, v: int, info) -> int:
        """Validate that maxconn > minconn."""
        if "minconn" in info.data and v <= info.data["minconn"]:
            raise ValueError("maxconn must be greater than minconn")
        return v


class ProcessedEmail(BaseModel):
    """Email tracking record in processed_emails table."""

    message_id: str = Field(
        ...,
        min_length=1,
        description="Gmail message ID (unique identifier)"
    )
    sender_email: str = Field(
        ...,
        pattern=r'^[^@]+@[^@]+\.[^@]+$',
        description="Email address of newsletter sender"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Email subject line"
    )
    collected_at: datetime = Field(
        ...,
        description="When email was fetched from Gmail"
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="When processing completed"
    )
    status: str = Field(
        ...,
        pattern=r'^(collected|converted|parsed|failed)$',
        description="Processing status"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if status is 'failed'"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "message_id": "18d3f4a5b6c7d8e9",
                "sender_email": "newsletter@example.com",
                "subject": "Weekly Tech News",
                "collected_at": "2026-02-04T10:00:00Z",
                "processed_at": "2026-02-04T10:05:00Z",
                "status": "parsed",
                "error_message": None
            }
        }


class NewsletterItemInput(BaseModel):
    """Input model for creating newsletter item (from LLM parsing)."""

    title: str = Field(
        ...,
        min_length=1,
        description="Article title"
    )
    date: str = Field(
        default="",
        description="Publication date (may be empty)"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Article summary"
    )
    link: Optional[str] = Field(
        default=None,
        description="Article URL"
    )
    sender: Optional[str] = Field(
        default=None,
        description="Newsletter sender email"
    )
    message_id: Optional[str] = Field(
        default=None,
        description="Source Gmail message ID"
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that title is not empty or whitespace."""
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v


class NewsletterItemOutput(BaseModel):
    """Output model for newsletter item (stored in feed_items table)."""

    id: str = Field(
        ...,
        pattern=r'^newsletter:[0-9a-f]{16}$',
        description="Stable ID: newsletter:{16-char-sha256-hash}"
    )
    source_type: str = Field(
        default="newsletter",
        description="Source type (always 'newsletter')"
    )
    source_id: str = Field(
        ...,
        pattern=r'^[0-9a-f]{16}$',
        description="16-character SHA-256 hash"
    )
    title: str = Field(
        ...,
        min_length=1,
        description="Article title"
    )
    item_date: datetime = Field(
        ...,
        description="Publication date"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Article summary"
    )
    link: Optional[str] = Field(
        default=None,
        description="Article URL"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (sender, message_id, etc.)"
    )
    fetched_at: datetime = Field(
        ...,
        description="When item was fetched"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "newsletter:a1b2c3d4e5f6g7h8",
                "source_type": "newsletter",
                "source_id": "a1b2c3d4e5f6g7h8",
                "title": "AI Breakthrough in 2026",
                "item_date": "2026-02-04T10:00:00Z",
                "summary": "Major AI research announcement...",
                "link": "https://example.com/article",
                "metadata": {
                    "sender": "ai-newsletter@example.com",
                    "message_id": "18d3f4a5b6c7d8e9"
                },
                "fetched_at": "2026-02-04T10:30:00Z"
            }
        }


class MigrationStatus(BaseModel):
    """Status of a data migration."""

    migration_name: str = Field(
        ...,
        description="Unique identifier for migration"
    )
    applied_at: datetime = Field(
        ...,
        description="When migration started"
    )
    status: str = Field(
        ...,
        pattern=r'^(running|completed|failed)$',
        description="Migration status"
    )
    rows_migrated: int = Field(
        default=0,
        ge=0,
        description="Number of rows migrated"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if failed"
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="Migration duration in seconds"
    )
