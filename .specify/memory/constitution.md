<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0 (configuration storage clarification)
- Modified principles: I. Technology Stack (added config file exception)
- Added sections: Configuration file criteria
- Removed sections: N/A
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (compatible)
  - .specify/templates/spec-template.md ✅ (compatible)
  - .specify/templates/tasks-template.md ✅ (compatible)
- Follow-up TODOs: None
-->

# Daily Briefing Constitution

## Core Principles

### I. Technology Stack

Python 3.13+ with uv for package management. Coolify PostgreSQL for all persistent user data and application state. Coolify platform-level authentication for access control.

**Configuration files** (settings, prompts, system parameters) MAY use JSON files when:

- Data is user-editable configuration, not transactional data
- Changes are infrequent (configuration updates, not user actions)
- File size remains small (<1MB)
- Atomic write operations are used

No local SQLite or file-based storage for user data in production.

### II. Strong Typing (NON-NEGOTIABLE)

All code MUST use strong typing enforced by mypy. Function arguments and return values MUST use Pydantic models or TypedDict - never plain `dict`. The `Any` type is prohibited except where absolutely unavoidable (document justification). All type hints MUST be explicit and complete.

### III. Backend TDD

Test-Driven Development is REQUIRED for backend services and business logic:
- Write tests first, verify they fail, then implement
- Red-Green-Refactor cycle strictly enforced
- Tests are NOT required for: frontend components, API endpoint handlers, UI templates

### IV. Test Isolation (NON-NEGOTIABLE)

Tests MUST NOT call remote APIs. All external dependencies MUST be mocked:
- Zotero API: mock responses
- Gmail API: mock responses
- Gemini LLM: mock responses
- PostgreSQL: use test database or mock

If a test inherently requires a real remote API (e.g., LLM behavior verification), DO NOT write that test. Skip it entirely rather than creating flaky or slow tests.

### V. Simplicity First

This is a demo/prototype, not a production system. Code MUST be as simple as possible:
- No premature abstractions
- No over-engineering
- No "future-proofing" beyond stated extensibility requirements
- Prefer explicit over clever
- Delete unused code immediately

### VI. Feature Discipline (NON-NEGOTIABLE)

NEVER add new features without explicitly checking with the user first. The scope is defined in the spec. If implementation reveals a gap, ASK before adding functionality. This applies to:
- New endpoints
- New UI elements
- New configuration options
- New integrations

### VII. Code Quality Gates

All code MUST pass the linter (ruff) before saving. No exceptions. Fix lint errors immediately, not "later". This includes:
- Type checking (mypy)
- Import sorting
- Code formatting
- Unused imports/variables

## Technology Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| Language | Python 3.13+ | Use modern Python features |
| Package Manager | uv | Fast, reliable dependency management |
| Database | Coolify PostgreSQL | All persistence via DATABASE_URL env var |
| Authentication | Coolify Auth | Platform-level, not in-app |
| Web Framework | Flask | Existing codebase |
| LLM | Google Gemini | For newsletter parsing only |
| Type Checking | mypy + Pydantic | Strict mode |
| Linting | ruff | Must pass before commit |
| Testing | pytest | With mocking for external APIs |

## Development Workflow

### Before Writing Code
1. Verify task is in scope (check spec)
2. If adding backend service: write failing test first
3. If unclear: ASK before implementing

### While Writing Code
1. Use strong types (Pydantic/TypedDict)
2. Mock all external APIs in tests
3. Keep it simple - minimal code to meet requirement
4. Run linter frequently

### Before Saving/Committing
1. Run `ruff check --fix`
2. Run `mypy`
3. Run `pytest` (for changed areas)
4. Verify no `Any` types added without justification
5. Verify no plain `dict` in function signatures

## Governance

This constitution supersedes all other development practices for this project. Amendments require:
1. Explicit user approval
2. Documentation of change rationale
3. Version increment

All code reviews and implementations MUST verify compliance with these principles. Violations require justification documented in code comments.

**Version**: 1.1.0 | **Ratified**: 2026-01-30 | **Last Amended**: 2026-02-03
