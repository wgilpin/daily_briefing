# Data Model: Unified Feed App

**Date**: 2026-01-30
**Feature**: 003-unified-feed-app

## Entity Definitions

### FeedItem

Represents a single entry in the unified feed from any source.

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class FeedItem(BaseModel):
    """A normalized feed item from any source."""

    id: str = Field(description="Unique identifier (source_type:source_id)")
    source_type: str = Field(description="Source identifier (zotero, newsletter)")
    source_id: str = Field(description="Original ID from source system")
    title: str
    date: datetime = Field(description="Publication or received date")
    summary: Optional[str] = Field(default=None, description="Abstract or excerpt")
    link: Optional[str] = Field(default=None, description="URL to original")
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Source-specific metadata (authors, sender, etc.)"
    )
    fetched_at: datetime = Field(description="When item was fetched from source")

    class Config:
        frozen = True  # Immutable
```

**Validation Rules**:
- `id` format: `{source_type}:{source_id}`
- `source_type` must be registered source
- `title` required, non-empty
- `date` must be valid datetime

### SourceConfig

Configuration for a specific feed source.

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SourceConfig(BaseModel):
    """Configuration for a feed source."""

    source_type: str = Field(description="Source identifier")
    enabled: bool = Field(default=True)
    last_refresh: Optional[datetime] = Field(default=None)
    last_error: Optional[str] = Field(default=None)
    settings: dict[str, str] = Field(
        default_factory=dict,
        description="Source-specific settings"
    )
```

### ZoteroConfig (Source-specific)

```python
class ZoteroConfig(BaseModel):
    """Zotero-specific configuration."""

    library_id: str
    api_key: str  # From environment, not stored in DB
    days_lookback: int = Field(default=7, ge=1, le=365)
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
```

### NewsletterConfig (Source-specific)

```python
class NewsletterConfig(BaseModel):
    """Newsletter-specific configuration."""

    sender_emails: list[str] = Field(default_factory=list)
    parsing_prompt: Optional[str] = Field(default=None)
    max_emails_per_refresh: int = Field(default=20, ge=1, le=100)
```

### AppSettings

Global application settings.

```python
class AppSettings(BaseModel):
    """Global application settings."""

    default_days_lookback: int = Field(default=7)
    page_size: int = Field(default=50, ge=10, le=100)
    refresh_timeout_seconds: int = Field(default=60)
```

## Database Schema

### PostgreSQL Tables

```sql
-- Feed items from all sources
CREATE TABLE feed_items (
    id VARCHAR(255) PRIMARY KEY,  -- source_type:source_id
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

CREATE INDEX idx_feed_items_source ON feed_items(source_type);
CREATE INDEX idx_feed_items_date ON feed_items(item_date DESC);

-- Source configurations
CREATE TABLE source_configs (
    source_type VARCHAR(50) PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    last_refresh TIMESTAMP,
    last_error TEXT,
    settings JSONB DEFAULT '{}',
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Application settings (key-value)
CREATE TABLE app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- OAuth tokens (encrypted)
CREATE TABLE oauth_tokens (
    provider VARCHAR(50) PRIMARY KEY,  -- e.g., 'gmail'
    encrypted_token TEXT NOT NULL,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## Entity Relationships

```text
┌─────────────────┐
│  AppSettings    │
│  (singleton)    │
└─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│  SourceConfig   │───────│   FeedItem      │
│  (per source)   │  1:N  │ (many per src)  │
└─────────────────┘       └─────────────────┘
        │
        │ source-specific
        ▼
┌─────────────────┐
│ ZoteroConfig    │
│ NewsletterConfig│
│ (future sources)│
└─────────────────┘

┌─────────────────┐
│  OAuthToken     │
│  (per provider) │
└─────────────────┘
```

## State Transitions

### FeedItem Lifecycle

```text
[Not Exists] ──fetch──> [Created] ──update──> [Updated]
                                        │
                                        └──retention──> [Deleted]
```

### SourceConfig States

```text
[Disabled] <──toggle──> [Enabled]
    │                       │
    └───────────────────────┴──refresh──> [Refreshing]
                                              │
                            ┌─────────────────┴─────────────────┐
                            ▼                                   ▼
                    [Success: update last_refresh]    [Error: set last_error]
```

## Data Retention

Per existing newsletter behavior:
- Default retention: 100 most recent items per source
- Configurable via `AppSettings.retention_limit`
- Cleanup runs after each refresh
