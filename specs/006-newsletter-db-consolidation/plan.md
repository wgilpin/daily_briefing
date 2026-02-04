# Implementation Plan: Newsletter Database Consolidation

**Branch**: `006-newsletter-db-consolidation` | **Date**: 2026-02-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-newsletter-db-consolidation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Consolidate newsletter system from dual-database architecture (SQLite + PostgreSQL) to PostgreSQL-only. Fix critical ID stability bug by replacing Python's non-deterministic hash() with SHA-256 hashing. Implement connection pooling for thread-safe parallel newsletter parsing. Automatically migrate existing SQLite data on application startup.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: psycopg2 (PostgreSQL driver), hashlib (SHA-256), existing Flask/HTMX stack
**Storage**: PostgreSQL (Coolify) - existing feed_items table + new processed_emails table
**Testing**: pytest with mocked database operations
**Target Platform**: Linux server (Coolify deployment)
**Project Type**: Single web application (existing Flask backend)
**Performance Goals**: Support max_workers=5 parallel LLM parsing without connection errors
**Constraints**: <7s total retry delay on connection failure (3 retries: 1s, 2s, 4s), idempotent migration
**Scale/Scope**: 10 newsletters in parallel, 100+ historical emails, minconn=2 maxconn=10 connection pool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Technology Stack
✅ **PASS** - Using Python 3.13+, Coolify PostgreSQL, existing uv package management
- Migration removes SQLite (aligning with "No local SQLite" principle)
- Newsletter configuration in config/senders.json is acceptable per constitution (user-editable, infrequent changes, <1MB)

### Principle II: Strong Typing
⚠️ **NEEDS VERIFICATION** - Will use Pydantic models for connection pool configuration and repository methods
- Repository methods must use Pydantic models, not plain dict
- Migration data structures need TypedDict or Pydantic models

### Principle III: Backend TDD
✅ **APPLICABLE** - Backend service changes require TDD
- Repository methods: write tests first
- Connection pool initialization: write tests first
- Migration logic: write tests first

### Principle IV: Test Isolation
✅ **PASS** - Tests will mock PostgreSQL connections
- Use pytest fixtures for mock connection pool
- Mock psycopg2.pool.ThreadedConnectionPool
- Use in-memory test database or full mocking

### Principle V: Simplicity First
✅ **PASS** - Simple point solution using standard library
- psycopg2 ThreadedConnectionPool (standard library for connection pooling)
- hashlib.sha256 (standard library for deterministic hashing)
- No new frameworks or complex abstractions

### Principle VI: Feature Discipline
✅ **PASS** - Scope limited to specification
- SQLite removal
- Connection pooling
- SHA-256 ID generation
- Auto-migration on startup
- No additional features planned

### Principle VII: Code Quality Gates
✅ **PASS** - Will run ruff and mypy before commit
- Type hints on all new functions
- Pydantic models for data structures
- No plain dict in function signatures

## Project Structure

### Documentation (this feature)

```text
specs/006-newsletter-db-consolidation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (repository interface)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── db/
│   ├── connection.py          # MODIFY: Add ThreadedConnectionPool
│   ├── repository.py          # MODIFY: Add email tracking methods
│   └── migrations/
│       └── 003_newsletter_consolidation.sql  # NEW: Migration script
├── newsletter/
│   ├── storage.py             # MODIFY: Remove SQLite, keep file ops
│   ├── email_collector.py     # MODIFY: Use PostgreSQL repository
│   └── parser.py              # (no changes needed)
├── sources/
│   └── newsletter.py          # MODIFY: SHA-256 IDs, use repository
└── utils/
    └── migration.py           # NEW: Auto-migration runner

tests/
├── unit/
│   ├── test_connection_pool.py       # NEW: Pool behavior
│   ├── test_repository_emails.py     # NEW: Email tracking
│   ├── test_sha256_ids.py            # NEW: ID stability
│   └── test_migration.py             # NEW: Migration logic
└── integration/
    └── test_newsletter_pipeline.py   # MODIFY: PostgreSQL-only tests
```

**Structure Decision**: Single project structure (existing Flask application). All changes within `src/` directory following established patterns. Tests mirror source structure under `tests/unit/` and `tests/integration/`.

## Complexity Tracking

> **No violations - table not needed**

All constitution principles pass. No complexity justification required.
