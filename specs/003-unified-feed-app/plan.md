# Implementation Plan: Unified Feed App

**Branch**: `003-unified-feed-app` | **Date**: 2026-01-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-unified-feed-app/spec.md`

## Summary

Integrate existing Zotero digest CLI and Newsletter aggregator web app into a single unified feed application. The app displays items from both sources in a chronological feed, supports on-demand refresh, and is deployable to Coolify with PostgreSQL persistence.

**Approach**: Minimal refactoring of existing code. Create a source abstraction layer, migrate storage to PostgreSQL, and build a unified web UI.

## Technical Context

**Language/Version**: Python 3.13+
**Package Manager**: uv
**Primary Dependencies**: Flask, pyzotero, google-api-python-client, google-genai, psycopg2-binary, Pydantic
**Storage**: Coolify PostgreSQL (DATABASE_URL env var)
**Testing**: pytest with mocks (no real API calls)
**Target Platform**: Coolify container (Linux)
**Project Type**: Web application (single project structure)
**Performance Goals**: 3s page load, 60s refresh for 50 Zotero + 20 newsletters
**Constraints**: Single-user, no in-app auth, stateless container
**Scale/Scope**: Personal tool, ~100 items max

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Technology Stack | ✓ PASS | Python 3.13+, uv, Coolify PostgreSQL, Coolify Auth |
| II. Strong Typing | ✓ PASS | Will use Pydantic models for all entities |
| III. Backend TDD | ✓ PASS | Tests for services, not for Flask routes |
| IV. Test Isolation | ✓ PASS | Mock Zotero, Gmail, Gemini APIs |
| V. Simplicity First | ✓ PASS | Minimal demo app, reuse existing code |
| VI. Feature Discipline | ✓ PASS | Scope defined in spec, Out of Scope documented |
| VII. Code Quality Gates | ✓ PASS | ruff + mypy before commit |

**Gate Status**: PASS - All principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/003-unified-feed-app/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Technical decisions
├── data-model.md        # Entity definitions
├── quickstart.md        # Integration scenarios
├── contracts/           # API contracts
│   └── api.md           # REST endpoint definitions
└── checklists/          # Validation checklists
```

### Source Code (repository root)

```text
src/
├── models/              # Pydantic models (shared)
│   ├── __init__.py
│   ├── feed_item.py     # UnifiedFeedItem model
│   └── source.py        # FeedSource, SourceConfig models
├── sources/             # Source implementations
│   ├── __init__.py
│   ├── base.py          # Abstract source interface
│   ├── zotero.py        # Zotero source (refactored from src/zotero/)
│   └── newsletter.py    # Newsletter source (refactored from src/newsletter/)
├── services/            # Business logic
│   ├── __init__.py
│   ├── feed.py          # Feed aggregation service
│   └── retry.py         # Exponential backoff utility
├── db/                  # Database layer
│   ├── __init__.py
│   ├── connection.py    # PostgreSQL connection
│   └── repository.py    # CRUD operations
├── web/                 # Flask application (existing, modified)
│   ├── __init__.py
│   ├── app.py           # Flask app factory
│   ├── routes.py        # Unified routes
│   └── templates/       # Jinja templates
├── cli/                 # Keep existing CLI for backwards compat
└── utils/               # Shared utilities
    ├── __init__.py
    ├── config.py        # Environment config loader
    └── logging.py       # Structured logging

tests/
├── unit/                # Unit tests with mocks
│   ├── test_feed_service.py
│   ├── test_zotero_source.py
│   └── test_newsletter_source.py
└── conftest.py          # Shared fixtures
```

**Structure Decision**: Single project structure. Refactor existing `src/zotero/` and `src/newsletter/` into new `src/sources/` with common interface. Keep existing `src/cli/` for backwards compatibility.

## Complexity Tracking

No violations requiring justification. Following Simplicity First principle.
