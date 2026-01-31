# Research: Unified Feed App

**Date**: 2026-01-30
**Feature**: 003-unified-feed-app

## Technical Decisions

### 1. Source Abstraction Pattern

**Decision**: Protocol-based interface using Python's `typing.Protocol`

**Rationale**:
- Simplest approach for duck-typing in Python
- No inheritance hierarchy needed
- Works with existing code via adapter pattern
- Satisfies FR-016 (standard interface for sources)

**Alternatives considered**:
- ABC (Abstract Base Class): More verbose, requires explicit inheritance
- Plugin system: Over-engineered for 2-3 source types

**Interface definition**:
```python
class FeedSource(Protocol):
    source_type: str

    def fetch_items(self, config: SourceConfig) -> list[FeedItem]: ...
    def get_config_schema(self) -> type[BaseModel]: ...
```

### 2. PostgreSQL ORM Strategy

**Decision**: Raw SQL with psycopg2, Pydantic for validation

**Rationale**:
- Simplicity First principle - no ORM learning curve
- Direct control over queries
- Pydantic handles serialization/deserialization
- Small schema (3-4 tables) doesn't need ORM

**Alternatives considered**:
- SQLAlchemy: Too heavy for demo app
- SQLModel: Still adds complexity
- asyncpg: No async needed for simple app

### 3. Migration Strategy

**Decision**: Manual SQL migration scripts in `db/migrations/`

**Rationale**:
- Simple demo app doesn't need Alembic complexity
- Single developer, predictable schema changes
- Can manually apply via psql or on startup

**Alternatives considered**:
- Alembic: Over-engineered for prototype
- No migrations (recreate): Loses data on schema change

### 4. Existing Code Reuse

**Decision**: Wrap existing modules as source adapters

**Rationale**:
- Minimal changes to working code
- Reduces risk of breaking existing functionality
- SC-008/SC-009 require existing features to remain functional

**Approach**:
- `src/sources/zotero.py` wraps `src/zotero/client.py`
- `src/sources/newsletter.py` wraps `src/newsletter/` modules
- Adapters implement `FeedSource` protocol

### 5. Configuration Storage

**Decision**: PostgreSQL for runtime config, environment vars for secrets

**Rationale**:
- FR-021 requires env vars for credentials
- FR-012 requires PostgreSQL for all persistence
- Settings UI can modify runtime config in DB

**Schema**:
- `app_settings` table: key-value store for runtime settings
- Secrets (API keys, OAuth tokens) stay in environment variables

### 6. OAuth Token Storage

**Decision**: Encrypted storage in PostgreSQL

**Rationale**:
- FR-012 requires PostgreSQL for OAuth tokens
- Gmail OAuth tokens must persist across container restarts
- Simple AES encryption with key from environment

**Alternatives considered**:
- File-based (existing): Violates FR-022 (no file storage)
- Secrets manager: Over-engineered for single-user app

### 7. UI Approach

**Decision**: Server-side rendering with HTMX (existing approach)

**Rationale**:
- Existing newsletter app uses Flask + HTMX
- No need to change working pattern
- Simplicity First - no frontend build step

### 8. Retry Logic

**Decision**: tenacity library for exponential backoff

**Rationale**:
- Well-tested library for retry patterns
- Satisfies FR-011a (exponential backoff on 429)
- Minimal code - decorator-based

**Alternatives considered**:
- Custom implementation: More code to maintain
- No retry: Poor user experience on rate limits

## Dependencies to Add

```toml
# pyproject.toml additions
dependencies = [
    # Existing deps remain...
    "psycopg2-binary>=2.9.9",  # PostgreSQL
    "tenacity>=8.2.0",         # Retry logic
    "cryptography>=42.0.0",    # OAuth token encryption
]
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| ZOTERO_LIBRARY_ID | Yes | Zotero user library ID |
| ZOTERO_API_KEY | Yes | Zotero API key |
| GEMINI_API_KEY | Yes | Google Gemini API key |
| ENCRYPTION_KEY | Yes | 32-byte key for OAuth token encryption |
| GOOGLE_CLIENT_ID | For OAuth | Gmail OAuth client ID |
| GOOGLE_CLIENT_SECRET | For OAuth | Gmail OAuth client secret |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Gmail OAuth complexity | Medium | Medium | Reuse existing OAuth flow, just change storage |
| PostgreSQL migration | Low | Low | Simple schema, manual migration |
| Breaking existing CLI | Low | Low | Keep CLI module separate, test both paths |
