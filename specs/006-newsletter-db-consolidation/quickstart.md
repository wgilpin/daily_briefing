# Quickstart: Newsletter Database Consolidation

**Feature**: Newsletter Database Consolidation
**Branch**: `006-newsletter-db-consolidation`
**Date**: 2026-02-04

## Overview

This quickstart guide provides a concise reference for implementing the newsletter database consolidation feature. It consolidates key decisions from research and design phases.

---

## Architecture Summary

**Goal**: Migrate from dual-database (SQLite + PostgreSQL) to PostgreSQL-only architecture with stable, deterministic IDs.

**Key Components**:
1. **Connection Pool**: Thread-safe psycopg2.pool.ThreadedConnectionPool (minconn=2, maxconn=10)
2. **ID Generation**: SHA-256 deterministic hashing replacing non-deterministic hash()
3. **Migration**: Auto-run idempotent migration on application startup
4. **Storage**: Consolidate into existing feed_items table + new processed_emails table

---

## Quick Reference

### SHA-256 ID Generation

```python
import hashlib

def generate_newsletter_id(title: str, date: str) -> str:
    """Generate stable newsletter ID.

    Format: newsletter:{16-char-sha256-hash}
    """
    norm_title = title.strip().lower()
    norm_date = date.strip() if date else ""
    hash_input = f"{norm_title}:{norm_date}"
    hash_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    return f"newsletter:{hash_hex[:16]}"
```

### Connection Pool Setup

```python
import psycopg2.pool as pool

_pool = pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=database_url
)

# Context manager for safe usage
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = _pool.getconn()
        conn.rollback()  # Clear state
        yield conn
    finally:
        if conn:
            _pool.putconn(conn)
```

### Repository Methods

```python
def is_email_processed(message_id: str) -> bool:
    """Check if email already processed."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM processed_emails WHERE message_id = %s",
                (message_id,)
            )
            return cur.fetchone() is not None

def track_email_processed(
    message_id: str,
    sender_email: str,
    status: str,
    subject: Optional[str] = None
) -> None:
    """Record processed email."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO processed_emails
                (message_id, sender_email, subject, collected_at, status)
                VALUES (%s, %s, %s, NOW(), %s)
                ON CONFLICT (message_id) DO UPDATE
                SET status = EXCLUDED.status, processed_at = NOW()
                """,
                (message_id, sender_email, subject, status)
            )
        conn.commit()
```

---

## File Modifications

### 1. src/db/connection.py (MODIFY)

**Before**: Singleton connection
```python
_connection: Optional[Connection] = None

def get_connection() -> Connection:
    global _connection
    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(database_url)
    return _connection
```

**After**: Connection pool
```python
_pool: Optional[ThreadedConnectionPool] = None

def initialize_pool(minconn=2, maxconn=10):
    global _pool
    _pool = psycopg2.pool.ThreadedConnectionPool(
        minconn, maxconn, dsn=get_database_url()
    )

@contextmanager
def get_connection():
    conn = None
    try:
        conn = _pool.getconn()
        conn.rollback()
        yield conn
    finally:
        if conn:
            _pool.putconn(conn)
```

### 2. src/db/repository.py (MODIFY)

Add methods:
- `is_email_processed(message_id: str) -> bool`
- `get_processed_message_ids(sender_emails: List[str]) -> set[str]`
- `track_email_processed(...) -> None`
- `update_email_status(...) -> None`

### 3. src/newsletter/storage.py (MODIFY)

**Remove**:
- `init_database()` - SQLite table creation
- `get_processed_message_ids()` - Move to repository
- `track_email_processed()` - Move to repository
- `insert_newsletter_items()` - Move to repository
- All SQLite imports and connections

**Keep**:
- `init_data_directories()` - File system setup
- `save_email()` - JSON file operations
- `save_markdown()` - Markdown file operations
- `save_parsed_items()` - JSON file operations

### 4. src/sources/newsletter.py (MODIFY)

**Replace**:
```python
# OLD (line 158)
item_hash = hash(f"{title}:{newsletter_item.get('date', '')}")
item_id = f"newsletter:{abs(item_hash)}"

# NEW
from src.newsletter.id_generation import generate_newsletter_id
item_id = generate_newsletter_id(title, newsletter_item.get("date", ""))
source_id = item_id.split(":", 1)[1]
```

### 5. src/newsletter/email_collector.py (MODIFY)

**Replace SQLite calls** with repository methods:
```python
# OLD
from src.newsletter.storage import get_processed_message_ids, track_email_processed

# NEW
from src.db.repository import Repository

repo = Repository()
processed_ids = repo.get_processed_message_ids(sender_emails)
repo.track_email_processed(message_id, sender, status)
```

---

## New Files

### 1. src/db/migrations/003_newsletter_consolidation.sql

```sql
-- Newsletter email tracking
CREATE TABLE IF NOT EXISTS processed_emails (
    message_id VARCHAR(255) PRIMARY KEY,
    sender_email VARCHAR(255) NOT NULL,
    subject TEXT,
    collected_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_processed_emails_sender ON processed_emails(sender_email);
CREATE INDEX idx_processed_emails_status ON processed_emails(status);

-- Migration tracking
CREATE TABLE IF NOT EXISTS migration_history (
    migration_name VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    rows_migrated INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds NUMERIC(10, 2)
);
```

### 2. src/newsletter/id_generation.py

```python
"""Stable ID generation for newsletter items using SHA-256."""

import hashlib
from typing import Optional

def generate_newsletter_id(title: str, date: str) -> str:
    """Generate stable newsletter ID."""
    norm_title = title.strip().lower() if title else ""
    norm_date = date.strip() if date else ""
    hash_input = f"{norm_title}:{norm_date}"
    hash_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    return f"newsletter:{hash_hex[:16]}"
```

### 3. src/db/sqlite_migration.py

```python
"""One-time migration from SQLite to PostgreSQL."""

import sqlite3
from pathlib import Path
from psycopg2.extensions import connection as Connection

def migrate_newsletter_data(sqlite_path: str, pg_conn: Connection) -> int:
    """Migrate newsletter data from SQLite to PostgreSQL.

    Returns:
        Number of rows migrated (0 if already completed)
    """
    # Check if migration completed
    if _is_migration_completed(pg_conn):
        return 0

    # Check if SQLite exists
    if not Path(sqlite_path).exists():
        return 0  # Fresh install

    # Stream and migrate data
    sqlite_conn = sqlite3.connect(sqlite_path)
    # ... migration logic
    sqlite_conn.close()

    return rows_migrated
```

---

## Configuration

### pyproject.toml (NO CHANGES NEEDED)

Existing dependencies are sufficient:
- `psycopg2` - PostgreSQL driver (already present)
- `pydantic` - Type validation (already present)
- `hashlib` - SHA-256 (standard library)

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:5432/database
```

---

## Testing Checklist

### Unit Tests

- [  ] Connection pool initialization
- [  ] Connection acquisition/release
- [  ] Pool exhaustion handling
- [  ] Retry logic with exponential backoff
- [  ] SHA-256 ID generation determinism
- [  ] SHA-256 ID collision resistance
- [  ] Repository email tracking methods
- [  ] Migration idempotency check
- [  ] Migration data transformation

### Integration Tests

- [  ] Full newsletter pipeline (collect → convert → parse)
- [  ] Parallel parsing with connection pool
- [  ] SQLite to PostgreSQL migration
- [  ] Auto-migration on application startup

---

## Deployment Steps

1. **Run schema migration**:
   ```bash
   # Migration runs automatically on app startup
   python -m src.web.app
   ```

2. **Verify migration**:
   ```sql
   SELECT * FROM migration_history WHERE migration_name = 'sqlite_newsletter_to_postgres_v1';
   SELECT COUNT(*) FROM processed_emails;
   SELECT COUNT(*) FROM feed_items WHERE source_type = 'newsletter';
   ```

3. **Test newsletter collection**:
   ```bash
   # Should use PostgreSQL, no SQLite files created
   pytest tests/integration/test_newsletter_pipeline.py
   ```

4. **Monitor connection pool**:
   ```python
   # Add health check endpoint
   @app.route('/health/db')
   def db_health():
       return {
           "pool_size": _pool.maxconn,
           "used_connections": len(_pool._used)
       }
   ```

---

## Troubleshooting

### Pool Exhaustion

**Symptom**: `PoolError: pool exhausted`

**Fix**:
1. Check max_workers ≤ maxconn (should be 5 ≤ 10)
2. Verify connections are released (check `putconn()` in finally blocks)
3. Increase maxconn if needed (up to 20 for larger workloads)

### Migration Fails

**Symptom**: Migration status='failed' in migration_history

**Fix**:
1. Check error_message in migration_history table
2. Verify SQLite database path is correct
3. Ensure PostgreSQL schema exists (run schema migrations first)
4. Check PostgreSQL connection permissions

### Duplicate IDs

**Symptom**: Same newsletter item appears twice

**Fix**:
1. Verify SHA-256 ID generation is deterministic:
   ```python
   id1 = generate_newsletter_id("Title", "2026-02-04")
   id2 = generate_newsletter_id("Title", "2026-02-04")
   assert id1 == id2  # Should be identical
   ```
2. Check database UNIQUE constraint on (source_type, source_id)

---

## Performance Benchmarks

### Expected Performance

- **SHA-256 hashing**: <0.2ms for 1000 items
- **Connection pool acquisition**: <1ms (when available)
- **Migration**: ~5-10 seconds for 1000 emails (with batch size 500)
- **Parallel parsing**: 5 newsletters simultaneously without connection errors

### Monitoring

```sql
-- Check migration progress
SELECT migration_name, status, rows_migrated, duration_seconds
FROM migration_history
ORDER BY applied_at DESC;

-- Check processed emails by status
SELECT status, COUNT(*)
FROM processed_emails
GROUP BY status;

-- Check newsletter items count
SELECT COUNT(*)
FROM feed_items
WHERE source_type = 'newsletter';
```

---

## References

- [Spec](spec.md) - Feature requirements
- [Data Model](data-model.md) - Database schema and Pydantic models
- [Research](research.md) - Technical research findings
- [Plan](plan.md) - Implementation plan
- [Repository Contract](contracts/repository_interface.py) - Repository interface
