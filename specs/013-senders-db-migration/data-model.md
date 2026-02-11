# Data Model: Senders Database Migration

**Branch**: `013-senders-db-migration` | **Date**: 2026-02-11

## New Database Tables

### Table: `senders`

Stores one row per newsletter sender email address.

| Column | Type | Constraints | Notes |
| ------ | ---- | ----------- | ----- |
| `email` | TEXT | PRIMARY KEY | Sender email address; identity key |
| `display_name` | TEXT | NULL | Optional friendly name for audio attribution |
| `parsing_prompt` | TEXT | NOT NULL DEFAULT '' | Per-sender parsing prompt; empty string = use default |
| `enabled` | BOOLEAN | NOT NULL DEFAULT TRUE | Whether sender is processed |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT NOW() | Creation time; preserved from file on migration |

**Identity rule**: `email` is the natural primary key. No surrogate ID needed.

**State transitions**:
- `enabled = TRUE` → sender emails are collected and parsed
- `enabled = FALSE` → sender is skipped during newsletter processing

---

### Table: `newsletter_config`

Stores global newsletter settings as key/value pairs.

| Column | Type | Constraints | Notes |
| ------ | ---- | ----------- | ----- |
| `setting_name` | TEXT | PRIMARY KEY | Setting identifier (e.g. `retention_limit`) |
| `setting_value` | TEXT | NOT NULL | Value serialised to string; see type map below |

**Type serialisation map** (enforced in Repository layer):

| setting_name | Python type | Serialisation |
| ------------ | ----------- | ------------- |
| `consolidation_prompt` | str | direct |
| `retention_limit` | int | str(int) / int(str) |
| `days_lookback` | int | str(int) / int(str) |
| `max_workers` | int | str(int) / int(str) |
| `default_parsing_prompt` | str | direct |
| `default_consolidation_prompt` | str | direct |
| `models` | dict | json.dumps / json.loads |
| `excluded_topics` | list[str] | json.dumps / json.loads |

---

## Pydantic Models

### `SenderRecord` (in `src/models/newsletter_models.py` or inline in `config.py`)

```python
class SenderRecord(BaseModel):
    email: str
    display_name: str | None = None
    parsing_prompt: str = ""
    enabled: bool = True
    created_at: datetime | None = None
```

### `NewsletterConfig` (updated in `src/newsletter/config.py`)

Keep existing `NewsletterConfig` Pydantic model signature unchanged — callers receive the same type. Only the loading/saving implementation changes to use the DB.

---

## Migration SQL File

`src/db/migrations/004_senders_config.sql`

```sql
-- 004_senders_config.sql
-- Migrate sender configuration from senders.json to PostgreSQL

CREATE TABLE IF NOT EXISTS senders (
    email         TEXT PRIMARY KEY,
    display_name  TEXT,
    parsing_prompt TEXT NOT NULL DEFAULT '',
    enabled       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS newsletter_config (
    setting_name  TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL
);
```

---

## Relationship Diagram

```
senders                    newsletter_config
-----------------------    -------------------------
email (PK)                 setting_name (PK)
display_name               setting_value
parsing_prompt
enabled
created_at

(no FK relationships — independent config tables)
```
