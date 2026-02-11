# Research: Senders Database Migration

**Branch**: `013-senders-db-migration` | **Date**: 2026-02-11

## Findings

### 1. Existing senders.json Schema

**Decision**: Map directly to two PostgreSQL tables — no structural transformation needed.

**Rationale**: The file has two distinct shapes: a dict of senders (→ `senders` table, one row per email) and a flat bag of global settings (→ `newsletter_config` key/value table per FR-008).

**Current file structure**:
```json
{
  "senders": {
    "<email>": {
      "parsing_prompt": "",
      "enabled": true,
      "display_name": "Name",
      "created_at": "2026-01-01T00:00:00"
    }
  },
  "consolidation_prompt": "",
  "retention_limit": 100,
  "days_lookback": 30,
  "max_workers": 10,
  "default_parsing_prompt": "...",
  "default_consolidation_prompt": "...",
  "models": { "parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash" },
  "excluded_topics": ["topic1"]
}
```

**Note on `models` and `excluded_topics`**: These are currently in senders.json but not surfaced in the web UI sender management routes. They should be migrated to `newsletter_config` as JSON-serialised text values to avoid losing data, but are out of scope for new UI features.

---

### 2. Files That Must Change

| File | Change Type | Reason |
| ---- | ----------- | ------ |
| `src/db/migrations/004_senders_config.sql` | NEW | Create `senders` and `newsletter_config` tables |
| `src/db/repository.py` | MODIFY | Add CRUD methods for senders and newsletter_config |
| `src/newsletter/config.py` | MODIFY | Replace `load_config`/`save_config` file I/O with Repository calls |
| `src/newsletter/migration.py` | NEW | One-time senders.json → DB migration with rename |
| `src/web/app.py` | MODIFY | Call `migrate_senders_if_needed()` at startup after `initialize_pool()` |
| `src/newsletter/sender_names.py` | MODIFY | Replace file read with Repository call |
| `src/web/feed_routes.py` | MODIFY | Route handlers call Repository instead of config.py file functions |

---

### 3. Existing Patterns to Follow

**Decision**: Follow the exact patterns already established in features 006 (DB consolidation).

**Connection management**: Use `get_connection()` context manager from `src/db/connection.py`. Never call `_pool` directly.

**Repository pattern**: Add methods to the existing `Repository` class in `src/db/repository.py`. Use `with get_connection() as conn:` inside each method.

**Migration numbering**: Next SQL migration file is `004_senders_config.sql`.

**Startup hook**: `src/web/app.py` already calls `initialize_pool()` on startup. The new `migrate_senders_if_needed()` call goes immediately after.

---

### 4. Migration Logic Design

**Decision**: Run migration check on every startup; it is idempotent (checks for senders.json presence before acting).

**Algorithm**:
```
on startup:
  if config/senders.json exists:
    parse JSON → raise RuntimeError on malformed JSON (aborts startup)
    for each sender in file:
      if email NOT in DB: insert
      else: skip (DB wins)
    for each global setting in file:
      if key NOT in newsletter_config: insert
      else: skip (DB wins)
    rename senders.json → senders.json.bak
```

**Alternatives considered**: Running migration as a separate CLI command — rejected because it adds operational complexity; on-startup check is zero-friction and idempotent.

---

### 5. Global Settings Storage

**Decision**: Key/value table `newsletter_config(setting_name TEXT PK, setting_value TEXT)`.

**Rationale**: Allows new settings to be added without schema changes. Values are serialised to/from Python types in the Repository layer (int ↔ str, list ↔ JSON string).

**Settings to migrate**:

| Key | Python Type | Serialisation |
| --- | ----------- | ------------- |
| `consolidation_prompt` | str | direct |
| `retention_limit` | int | str(int) |
| `days_lookback` | int | str(int) |
| `max_workers` | int | str(int) |
| `default_parsing_prompt` | str | direct |
| `default_consolidation_prompt` | str | direct |
| `models` | dict | json.dumps |
| `excluded_topics` | list[str] | json.dumps |
