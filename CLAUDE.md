# daily_briefing Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-02

## Active Technologies
- Python 3.13+ + Flask, HTMX, Google Gemini (google-genai), Pydantic (005-topic-exclusion)
- PostgreSQL (Coolify) + config/senders.json (file-based configuration) (005-topic-exclusion)
- Python 3.13+ + psycopg2 (PostgreSQL driver), hashlib (SHA-256), existing Flask/HTMX stack (006-newsletter-db-consolidation)
- PostgreSQL (Coolify) - existing feed_items table + new processed_emails table (006-newsletter-db-consolidation)
- Python 3.13+ + ElevenLabs Python SDK, existing Flask stack (007-newsletter-audio)
- File-based (MP3 files in data/output/, credentials in .env) (007-newsletter-audio)
- Python 3.13+ + Flask, kokoro (optional extra), soundfile (optional extra), elevenlabs SDK (to be restored), ffmpeg (system dep, already present) (012-tts-fallback)
- N/A (no new persistent data; audio cache files unchanged) (012-tts-fallback)

- Python 3.13+ (existing project requirement) (004-user-login)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.13+ (existing project requirement): Follow standard conventions

## Recent Changes
- 012-tts-fallback: Added Python 3.13+ + Flask, kokoro (optional extra), soundfile (optional extra), elevenlabs SDK (to be restored), ffmpeg (system dep, already present)
- 007-newsletter-audio: Added Python 3.13+ + ElevenLabs Python SDK, existing Flask stack

- 006-newsletter-db-consolidation: Completed newsletter database consolidation - migrated from SQLite to PostgreSQL with thread-safe connection pooling, SHA-256 stable IDs, and comprehensive test coverage

## Newsletter Database Consolidation (006) - Implementation Notes

**Completed**: 2026-02-04

### Key Changes

- **Removed SQLite**: All newsletter tracking now uses PostgreSQL (`processed_emails` and `feed_items` tables)
- **Connection Pooling**: ThreadedConnectionPool (minconn=2, maxconn=10) with exponential backoff retry (1s/2s/4s)
- **Stable IDs**: SHA-256 deterministic hashing replaces non-deterministic `hash()` - format: `newsletter:{16-char-hash}`
- **Thread Safety**: Parallel newsletter parsing (max_workers=5) without connection errors
- **Repository Pattern**: All database operations through `Repository` class with context managers

### Files Modified

- `src/db/connection.py` - Added connection pooling with retry logic and cleanup handlers
- `src/db/repository.py` - Added email tracking methods (is_email_processed, get_processed_message_ids, track_email_processed, update_email_status)
- `src/newsletter/storage.py` - Added get_recent_parsed_items() to query PostgreSQL (backward-compatible API), kept file operations
- `src/newsletter/email_collector.py` - Uses Repository instead of SQLite
- `src/sources/newsletter.py` - Fetches from PostgreSQL feed_items table
- `src/web/app.py` - Calls initialize_pool() on startup
- `src/web/feed_routes.py` - Uses context managers for all get_connection() calls
- `src/web/auth_routes.py` - Uses context managers for all get_connection() calls
- `tests/conftest.py` - Added context manager support to mock_db_connection fixture

### Files Created

- `src/db/migrations/003_newsletter_consolidation.sql` - PostgreSQL schema for processed_emails and migration_history
- `src/models/newsletter_models.py` - Pydantic models (ProcessedEmail, ConnectionPoolConfig, etc.)
- `src/newsletter/id_generation.py` - SHA-256 ID generation with normalization
- Multiple test files for comprehensive coverage

### Migration Notes

- **No data migration implemented** - Existing SQLite data can be discarded
- Fresh start recommended - just delete `data/newsletter_aggregator.db` if it exists
- All new emails will be tracked in PostgreSQL from first run

<!-- MANUAL ADDITIONS START -->

## Dependency Management

- Use `uv add <package>` for adding dependencies instead of directly editing pyproject.toml
- Only edit pyproject.toml directly when pinning is required for compatibility, security, or explicit user requirements
- Let uv handle version resolution and lock file management

## Simplicity Over Generalization (NON-NEGOTIABLE)

Never use a library when a short point solution will do. Never over-generalize the solution beyond the specified scope.

**Core Principles:**

- Prefer <20 lines of direct code over adding a new library dependency
- Only add dependencies that provide significant complexity reduction for the CURRENT scope
- No premature abstraction or engineering beyond requirements
- Every dependency is a liability (maintenance, security, breaking changes)

**Examples:**

❌ **Bad: Over-engineering**

```python
# Adding Flask-Limiter for rate limiting in a personal single-user app
from flask_limiter import Limiter
limiter = Limiter(app, storage_uri="memory://", ...)
@limiter.limit("5 per minute")
```

✅ **Good: Simple point solution**

```python
# Simple 5-second delay for brute-force protection
import time
if not authenticate_user(...):
    time.sleep(5)
    return error_response()
```

**When to use libraries:**

- Complex algorithms (cryptography, parsing, protocols)
- Well-established frameworks (Flask, pytest, SQLAlchemy)
- Proven tools for specific domains (argon2 for password hashing)

**When NOT to use libraries:**

- Simple utilities that can be written in <20 lines
- Single-use helpers or wrappers
- Configuration or glue code
- Features only needed for one specific use case

<!-- MANUAL ADDITIONS END -->
