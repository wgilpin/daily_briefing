# Data Model: Newsletter Aggregator

**Date**: 2024-12-30  
**Feature**: Newsletter Aggregator

## Overview

The application uses a hybrid storage approach:
- **SQLite database**: For tracking processed emails (relational queries needed)
- **JSON files**: For configuration (human-readable, easy to edit)
- **File system**: For emails, markdown files, and parsed data (large content)

## Database Schema (SQLite)

### Table: `processed_emails`

Tracks which emails have been collected and processed to avoid duplicates.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `message_id` | TEXT | PRIMARY KEY | Gmail message ID (unique identifier) |
| `sender_email` | TEXT | NOT NULL | Email address of newsletter sender |
| `subject` | TEXT | | Email subject line |
| `collected_at` | TIMESTAMP | NOT NULL | When email was collected from Gmail |
| `processed_at` | TIMESTAMP | | When email was fully processed (converted + parsed) |
| `status` | TEXT | NOT NULL | Status: 'collected', 'converted', 'parsed', 'failed' |
| `error_message` | TEXT | | Error message if status is 'failed' |

**Indexes**:
- `idx_sender_email` on `sender_email` (for filtering by sender)
- `idx_processed_at` on `processed_at` (for retention policy cleanup)

**Validation Rules**:
- `status` must be one of: 'collected', 'converted', 'parsed', 'failed'
- `message_id` must be non-empty and unique
- `collected_at` must be set when record is created

### Table: `newsletter_items`

Stores parsed newsletter items extracted from emails.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal ID |
| `message_id` | TEXT | NOT NULL, FOREIGN KEY | References processed_emails.message_id |
| `item_index` | INTEGER | NOT NULL | Index within email (0-based, for multiple items per email) |
| `date` | TEXT | | Extracted date (ISO format or as extracted) |
| `title` | TEXT | NOT NULL | Extracted title |
| `summary` | TEXT | | Extracted summary |
| `link` | TEXT | | Extracted link URL (optional) |
| `parsed_at` | TIMESTAMP | NOT NULL | When item was parsed |
| `raw_data` | TEXT | | JSON of full parsed data for reference |

**Indexes**:
- `idx_message_id` on `message_id` (for joining with processed_emails)
- `idx_parsed_at` on `parsed_at` (for retention policy cleanup)

**Validation Rules**:
- `title` must be non-empty
- `item_index` must be >= 0
- `link` must be valid URL format if provided

## Configuration Files (JSON)

### File: `config/senders.json`

Stores newsletter sender configurations and associated parsing prompts.

```json
{
  "senders": {
    "newsletter@example.com": {
      "parsing_prompt": "Extract articles from this newsletter...",
      "enabled": true,
      "created_at": "2024-12-30T10:00:00Z"
    }
  },
  "consolidation_prompt": "Create a consolidated newsletter from these items...",
  "retention_limit": 100
}
```

**Structure**:
- `senders`: Object mapping sender email → configuration
  - `parsing_prompt`: String prompt for LLM to parse this sender's newsletters
  - `enabled`: Boolean, whether to collect from this sender
  - `created_at`: ISO timestamp when sender was added
- `consolidation_prompt`: String prompt for final consolidation
- `retention_limit`: Integer, number of most recent records to keep

**Validation Rules**:
- Sender email addresses must be valid email format
- `retention_limit` must be > 0
- Prompts must be non-empty strings

## File System Structure

### Directory: `data/emails/`

Raw email files stored as JSON.

**File naming**: `{message_id}.json`

**Structure**:
```json
{
  "message_id": "abc123",
  "sender": "newsletter@example.com",
  "subject": "Weekly Newsletter",
  "date": "2024-12-30T10:00:00Z",
  "body_html": "<html>...</html>",
  "body_text": "Plain text version",
  "headers": {...}
}
```

### Directory: `data/markdown/`

Converted markdown files.

**File naming**: `{message_id}.md`

**Content**: Markdown text converted from email HTML/text.

### Directory: `data/parsed/`

Parsed newsletter items stored as JSON arrays.

**File naming**: `{message_id}.json`

**Structure**:
```json
[
  {
    "date": "2024-12-30",
    "title": "Article Title",
    "summary": "Article summary...",
    "link": "https://example.com/article"
  },
  {
    "date": "2024-12-29",
    "title": "Another Article",
    "summary": "Another summary...",
    "link": null
  }
]
```

### Directory: `data/output/`

Consolidated newsletter outputs.

**File naming**: `digest_{timestamp}.md`

**Content**: Final consolidated markdown newsletter.

## Entity Relationships

```
processed_emails (1) ──→ (many) newsletter_items
     │
     └─── message_id used to locate files in:
          - data/emails/{message_id}.json
          - data/markdown/{message_id}.md
          - data/parsed/{message_id}.json
```

## State Transitions

### Email Processing States

```
[New Email from Gmail]
    ↓
[collected] → stored in data/emails/, record in processed_emails
    ↓
[converted] → markdown file created in data/markdown/
    ↓
[parsed] → parsed items stored in data/parsed/ and newsletter_items table
    ↓
[failed] → error logged, can be retried
```

## Data Retention

When retention limit (N) is reached:

1. Query `processed_emails` ordered by `processed_at` ASC
2. Select oldest records beyond limit N
3. Delete from `newsletter_items` where `message_id` matches
4. Delete files: `data/emails/{message_id}.json`, `data/markdown/{message_id}.md`, `data/parsed/{message_id}.json`
5. Delete records from `processed_emails`

**Retention applies to**: All data types (emails, markdown, parsed items, database records)

## Validation and Constraints

### Email Collection
- Message ID must be unique (Gmail guarantees this)
- Sender email must match configured sender (case-insensitive)
- Email must not already be in `processed_emails` table

### Parsing
- Each parsed item must have at least a `title`
- `date` should be parseable (flexible format accepted)
- `link` must be valid URL if provided
- Multiple items per email are allowed (stored with `item_index`)

### Configuration
- Sender email addresses must be valid format
- Prompts must be non-empty
- Retention limit must be positive integer

## Data Access Patterns

### Common Queries

1. **Check if email processed**: `SELECT message_id FROM processed_emails WHERE message_id = ?`
2. **Get unprocessed senders**: Query Gmail API, filter by `message_id NOT IN (SELECT message_id FROM processed_emails)`
3. **Get items for consolidation**: `SELECT * FROM newsletter_items ORDER BY parsed_at DESC LIMIT ?`
4. **Cleanup old records**: `SELECT message_id FROM processed_emails ORDER BY processed_at ASC LIMIT ? OFFSET ?`

## Migration Considerations

- Database schema is simple, can be created fresh on first run
- No migration needed for MVP (single-user local app)
- Configuration files can be edited manually if needed
- File system structure is flat, easy to reorganize later if needed

