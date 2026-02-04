# Data Model: Newsletter Database Consolidation

**Feature**: Newsletter Database Consolidation
**Branch**: `006-newsletter-db-consolidation`
**Date**: 2026-02-04

## Overview

This document defines the data models for the newsletter consolidation feature. All models use Pydantic for strong typing per constitution requirements.

---

## PostgreSQL Schema

### 1. processed_emails Table (NEW)

Tracks newsletter emails that have been collected and processed.

```sql
CREATE TABLE IF NOT EXISTS processed_emails (
    message_id VARCHAR(255) PRIMARY KEY,
    sender_email VARCHAR(255) NOT NULL,
    subject TEXT,
    collected_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL CHECK (status IN ('collected', 'converted', 'parsed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processed_emails_sender ON processed_emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_processed_emails_status ON processed_emails(status);
CREATE INDEX IF NOT EXISTS idx_processed_emails_processed_at ON processed_emails(processed_at DESC);
```

### 2. feed_items Table (EXISTING - receives newsletter items)

Newsletter items are stored here with `source_type='newsletter'`.

```sql
-- Existing table from 001_initial.sql
CREATE TABLE IF NOT EXISTS feed_items (
    id VARCHAR(255) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    item_date TIMESTAMP NOT NULL,
    summary TEXT,
    link TEXT,
    metadata JSONB DEFAULT '{}',
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(source_type, source_id)
);

-- Newsletter items will use:
-- id: "newsletter:{16-char-sha256-hash}"
-- source_type: "newsletter"
-- source_id: "{16-char-sha256-hash}"
-- metadata: {"sender": "example@example.com", "message_id": "...", ...}
```

### 3. migration_history Table (NEW)

Tracks one-time data migrations for idempotency.

```sql
CREATE TABLE IF NOT EXISTS migration_history (
    migration_name VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    rows_migrated INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds NUMERIC(10, 2)
);
```

---

## Pydantic Models

### Connection Pool Configuration

```python
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
```

### Processed Email Model

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

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
```

### Newsletter Item Input Model

```python
from typing import Optional
from pydantic import BaseModel, Field, field_validator

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
```

### Newsletter Item Output Model

```python
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

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
```

### Migration Status Model

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

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
```

---

## Entity Relationships

```
┌─────────────────────┐
│ processed_emails    │
│ ───────────────     │
│ message_id (PK)     │──┐
│ sender_email        │  │
│ subject             │  │
│ collected_at        │  │
│ processed_at        │  │
│ status              │  │
│ error_message       │  │
└─────────────────────┘  │
                         │ message_id referenced
                         │ in metadata
                         ▼
┌─────────────────────┐
│ feed_items          │
│ ──────────          │
│ id (PK)             │◄── "newsletter:{hash}"
│ source_type         │◄── "newsletter"
│ source_id           │◄── "{hash}"
│ title               │
│ item_date           │
│ summary             │
│ link                │
│ metadata (JSONB)    │◄── {"sender": "...", "message_id": "..."}
│ fetched_at          │
└─────────────────────┘

┌─────────────────────┐
│ migration_history   │
│ ────────────────    │
│ migration_name (PK) │
│ applied_at          │
│ status              │
│ rows_migrated       │
│ error_message       │
│ duration_seconds    │
└─────────────────────┘
```

---

## Data Flow

### 1. Email Collection Flow

```
Gmail API
    ↓
collect_newsletter_emails()
    ↓
Save to data/emails/{message_id}.json
    ↓
INSERT INTO processed_emails
    (status='collected')
```

### 2. Parsing Flow

```
data/markdown/{message_id}.md
    ↓
parse_newsletters() [parallel threads]
    ↓
generate_newsletter_id(title, date)  ← SHA-256 deterministic
    ↓
INSERT INTO feed_items
    (id='newsletter:{hash}', source_type='newsletter')
    ↓
UPDATE processed_emails
    (status='parsed')
```

### 3. Migration Flow

```
SQLite: newsletter_aggregator.db
    ├── processed_emails table
    └── newsletter_items table
        ↓
migrate_newsletter_data()
    ↓
PostgreSQL
    ├── processed_emails (copied)
    └── feed_items (newsletter_items → feed_items)
        ↓
migration_history
    (status='completed')
```

---

## Validation Rules

### ProcessedEmail

- **message_id**: Required, non-empty Gmail message ID
- **sender_email**: Required, valid email format
- **status**: Must be one of: collected, converted, parsed, failed
- **error_message**: Required when status='failed', otherwise optional

### NewsletterItemInput

- **title**: Required, non-empty after stripping whitespace
- **date**: Optional (empty string allowed)
- **link**: Optional URL (if provided, should be valid)

### NewsletterItemOutput

- **id**: Format `newsletter:{16-hex-chars}`
- **source_id**: Format `{16-hex-chars}`
- **source_type**: Always "newsletter"
- **title**: Non-empty
- **metadata**: Must be valid JSON object

---

## Indexing Strategy

### processed_emails

```sql
-- Primary key for deduplication
PRIMARY KEY (message_id)

-- Filter by sender for specific newsletter queries
CREATE INDEX idx_processed_emails_sender ON processed_emails(sender_email);

-- Filter by status for finding failed/pending items
CREATE INDEX idx_processed_emails_status ON processed_emails(status);

-- Order by processing time for recent items
CREATE INDEX idx_processed_emails_processed_at ON processed_emails(processed_at DESC);
```

### feed_items (existing)

```sql
-- Primary key for item lookups
PRIMARY KEY (id)

-- Unique constraint prevents duplicate items
UNIQUE (source_type, source_id)

-- Filter by source type
CREATE INDEX idx_feed_items_source ON feed_items(source_type);

-- Order by date
CREATE INDEX idx_feed_items_date ON feed_items(item_date DESC);
```

---

## State Transitions

### ProcessedEmail Status

```
┌───────────┐
│ collected │──► Initial state after Gmail fetch
└───────────┘
      │
      ▼
┌───────────┐
│ converted │──► After markdown conversion
└───────────┘
      │
      ├──► Success
      │    ┌───────────┐
      └──► │  parsed   │──► LLM parsing succeeded
           └───────────┘
      │
      └──► Failure
           ┌───────────┐
           │  failed   │──► Error during any step
           └───────────┘
```

### Migration Status

```
┌─────────┐
│ running │──► Migration in progress
└─────────┘
     │
     ├──► Success
     │    ┌───────────┐
     └──► │ completed │──► All rows migrated
          └───────────┘
     │
     └──► Failure
          ┌────────┐
          │ failed │──► Error during migration
          └────────┘
```

---

## Summary

**Key Design Decisions**:

1. **Strong Typing**: All models use Pydantic (constitution requirement)
2. **No Plain Dicts**: Function signatures use typed models, not `dict`
3. **SHA-256 IDs**: Deterministic, 16-character truncation
4. **Unified Storage**: Newsletter items in existing feed_items table
5. **Idempotent Migration**: migration_history tracks completion
6. **Status Tracking**: processed_emails tracks email lifecycle

**Tables**:
- `processed_emails` (NEW) - Email tracking
- `feed_items` (EXISTING) - Unified item storage
- `migration_history` (NEW) - Migration tracking

**Models**: 6 Pydantic models with full validation
- ConnectionPoolConfig
- ProcessedEmail
- NewsletterItemInput
- NewsletterItemOutput
- MigrationStatus
