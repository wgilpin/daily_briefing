# Quickstart: Senders Database Migration

**Branch**: `013-senders-db-migration` | **Date**: 2026-02-11

## What This Feature Does

Moves newsletter sender configuration and global settings from `config/senders.json` into PostgreSQL. After this migration, the app no longer requires the file to exist.

## Developer Setup

No new dependencies. All changes use existing psycopg2, Flask, and Pydantic.

```bash
cd src
# Run DB migration (creates senders and newsletter_config tables)
# Apply 004_senders_config.sql to your local PostgreSQL instance
psql $DATABASE_URL -f db/migrations/004_senders_config.sql
```

## Testing the Migration

1. Ensure `config/senders.json` exists with some senders
2. Start the app — migration runs automatically on startup
3. Verify `config/senders.json.bak` was created
4. Verify senders appear in the Settings UI
5. Delete `.bak` file, restart — app works from DB only

## Running Tests

```bash
cd src
pytest tests/unit/test_sender_repository.py -v
pytest tests/unit/test_senders_migration.py -v
```

## Key Files

| File | Purpose |
| ---- | ------- |
| `src/db/migrations/004_senders_config.sql` | Creates `senders` and `newsletter_config` tables |
| `src/newsletter/migration.py` | One-time migration logic (senders.json → DB) |
| `src/db/repository.py` | New sender CRUD and config key/value methods |
| `src/newsletter/config.py` | Updated to read/write DB instead of file |
| `src/web/app.py` | Calls `migrate_senders_if_needed()` at startup |

## Rollback

If rollback is needed before `.bak` file is deleted:

1. Rename `config/senders.json.bak` → `config/senders.json`
2. Revert code to previous branch
3. Drop new tables: `DROP TABLE senders; DROP TABLE newsletter_config;`
