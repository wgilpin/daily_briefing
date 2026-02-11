# Implementation Plan: Senders Database Migration

**Branch**: `013-senders-db-migration` | **Date**: 2026-02-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-senders-db-migration/spec.md`

## Summary

Migrate newsletter sender configuration and global settings from `config/senders.json` to PostgreSQL. Two new tables: `senders` (one row per sender email) and `newsletter_config` (key/value pairs for global settings). On startup, if `senders.json` exists, migrate its contents into the DB (DB wins on conflict), then rename the file to `senders.json.bak`. Replace all read/write calls to `config.py` file-based functions with `Repository` calls.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: psycopg2 (existing), Flask (existing), Pydantic (existing)
**Storage**: Coolify PostgreSQL via `DATABASE_URL` env var
**Testing**: pytest with mocked DB connections
**Target Platform**: Linux server (Coolify)
**Project Type**: Web application (Flask + HTMX)
**Performance Goals**: No change from existing — config loaded once at startup
**Constraints**: No new library dependencies; keep changes minimal
**Scale/Scope**: Single-user admin app; handful of senders (<100)

## Constitution Check

| Principle                                         | Status    | Notes                                                          |
| ------------------------------------------------- | --------- | -------------------------------------------------------------- |
| I. Technology Stack (PostgreSQL for persistence)  | PASS      | Moving file config to PostgreSQL as required                   |
| I. Config file exception                          | N/A       | senders.json was config; this migration removes it per spec    |
| II. Strong Typing                                 | PASS      | Will use Pydantic models; no plain dict in function signatures |
| III. Backend TDD                                  | PASS      | Tests written first for Repository methods and migration logic |
| IV. Test Isolation                                | PASS      | All DB calls mocked in tests                                   |
| V. Simplicity First                               | PASS      | No new libraries; minimal new code                             |
| VI. Feature Discipline                            | PASS      | Scope limited to storage backend swap                          |
| VII. Code Quality Gates                           | PASS      | ruff + mypy required before save                               |

**Gate result**: PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/013-senders-db-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (affected files)

```text
src/
├── db/
│   ├── migrations/
│   │   └── 004_senders_config.sql       # NEW: senders + newsletter_config tables
│   └── repository.py                    # MODIFY: add sender/config CRUD methods
├── newsletter/
│   ├── config.py                        # MODIFY: replace file I/O with DB calls
│   └── migration.py                     # NEW: senders.json → DB migration logic
└── web/
    └── app.py                           # MODIFY: call migrate_senders_if_needed() on startup

tests/
├── unit/
│   ├── test_sender_repository.py        # NEW: TDD for repository methods
│   └── test_senders_migration.py        # NEW: TDD for migration logic
└── integration/
    └── (existing integration tests)
```

**Structure Decision**: Single web application (existing layout). No new directories needed beyond one new migration file and one new module.

## Complexity Tracking

No constitution violations.
