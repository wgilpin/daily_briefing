# Implementation Plan: Topic Exclusion Filter

**Branch**: `005-topic-exclusion` | **Date**: 2026-02-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-topic-exclusion/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a topic exclusion filter for newsletter consolidation using prompt engineering. Users configure excluded topics (e.g., "datasette", "low-level coding") via a settings UI, which are stored in config/senders.json. The consolidator module injects exclusion instructions into the LLM prompt to filter out unwanted content during newsletter generation.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Flask, HTMX, Google Gemini (google-genai), Pydantic
**Storage**: PostgreSQL (Coolify) + config/senders.json (file-based configuration)
**Testing**: pytest with mocking (external APIs must be mocked per constitution)
**Target Platform**: Web application (server-side rendered with HTMX)
**Project Type**: Web (Flask backend with HTMX frontend)
**Performance Goals**: <30 seconds to add/remove a topic via UI (per SC-001)
**Constraints**: Max 50 topics, 100 characters per topic, semantic LLM filtering only
**Scale/Scope**: Single-user/small team application, MVP scope with no advanced classification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check

| Principle                   | Status  | Notes                                                                |
|-----------------------------|---------|----------------------------------------------------------------------|
| **I. Technology Stack**     | ✅ PASS | Using Python 3.13+, PostgreSQL (via Coolify), Flask (existing)      |
| **II. Strong Typing**       | ✅ PASS | Will use Pydantic models for config, no plain dict in signatures    |
| **III. Backend TDD**        | ✅ PASS | TDD required for config loading/saving service logic                |
| **IV. Test Isolation**      | ✅ PASS | All Gemini LLM calls will be mocked in tests                        |
| **V. Simplicity First**     | ✅ PASS | MVP using prompt engineering, no ML classification                  |
| **VI. Feature Discipline**  | ✅ PASS | Scope defined in spec, no additional features without approval      |
| **VII. Code Quality Gates** | ✅ PASS | ruff + mypy required before commit                                  |

**Result**: ✅ All gates passed - proceeding to Phase 0 research

### Post-Design Check

*Re-evaluated after Phase 1 design completion*

| Principle                   | Status  | Notes                                                                |
|-----------------------------|---------|----------------------------------------------------------------------|
| **I. Technology Stack**     | ✅ PASS | Design uses Python 3.13+, Flask, Pydantic, HTMX - all approved      |
| **II. Strong Typing**       | ✅ PASS | NewsletterConfig uses Pydantic BaseModel, no plain dicts            |
| **III. Backend TDD**        | ✅ PASS | Quickstart defines test-first approach for all backend logic        |
| **IV. Test Isolation**      | ✅ PASS | Research confirms mocking strategy for Gemini API calls             |
| **V. Simplicity First**     | ✅ PASS | Design avoids over-engineering: file config, prompt-based filtering |
| **VI. Feature Discipline**  | ✅ PASS | Scope unchanged, no feature creep in design phase                   |
| **VII. Code Quality Gates** | ✅ PASS | Quickstart includes ruff + mypy in testing checklist               |

**Result**: ✅ All gates passed - design approved for implementation

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── newsletter/
│   ├── config.py              # Config loading/saving logic (NEW: exclusions)
│   └── consolidator.py        # LLM consolidation (MODIFY: add exclusions param)
├── web/
│   ├── app.py                 # Flask app (existing)
│   ├── feed_routes.py         # Main routes (MODIFY: add exclusion routes)
│   └── templates/
│       ├── settings.html      # Settings page (MODIFY: add exclusions section)
│       └── partials/
│           └── topic_exclusion_config.html  # NEW: exclusions UI partial
└── models/
    └── (no new models needed - using Pydantic for config only)

config/
└── senders.json               # MODIFY: add excluded_topics array

tests/
├── unit/
│   └── newsletter/
│       ├── test_config.py     # NEW: test exclusion config logic
│       └── test_consolidator.py  # MODIFY: test exclusion filtering
└── integration/
    └── web/
        └── test_exclusion_routes.py  # NEW: test settings UI endpoints
```

**Structure Decision**: Web application using existing Flask structure. This is a backend-focused feature with HTMX-enhanced frontend. No new database models needed - configuration stored in JSON file as per spec clarifications.

## Complexity Tracking

No violations detected. All design decisions align with project constitution.

---

## Phase 0: Research (Complete)

**Artifact**: [research.md](research.md)

**Key Decisions**:
- HTMX dynamic list management for add/delete UI
- Pydantic models for type-safe configuration
- Prompt engineering with explicit high-priority instructions
- File-based JSON config with atomic writes

**Status**: ✅ Complete - all unknowns resolved

---

## Phase 1: Design & Contracts (Complete)

**Artifacts**:
- [data-model.md](data-model.md) - NewsletterConfig Pydantic model with validation
- [contracts/api-routes.md](contracts/api-routes.md) - Flask routes for HTMX integration
- [quickstart.md](quickstart.md) - Developer implementation guide

**Key Components**:
1. **NewsletterConfig**: Extended with `excluded_topics: list[str]` field
2. **Flask Routes**: GET /list, POST /add, DELETE /delete/{index}
3. **HTMX Integration**: Server-side rendering with partial templates
4. **LLM Integration**: Exclusion instructions injected into consolidation prompt

**Status**: ✅ Complete - ready for implementation

---

## Next Steps

### For Implementation (Use `/speckit.tasks` command)

The planning phase is complete. To generate actionable tasks:

```bash
/speckit.tasks
```

This will:
1. Break down the design into dependency-ordered tasks
2. Create detailed implementation steps with file paths
3. Include testing requirements per constitution
4. Generate tasks.md in this feature directory

### Manual Next Steps (If Not Using `/speckit.tasks`)

1. **Write Tests First** (TDD required):
   - `tests/unit/newsletter/test_config.py`
   - `tests/unit/newsletter/test_consolidator.py`
   - `tests/integration/web/test_exclusion_routes.py`

2. **Implement Core Logic**:
   - Extend `src/newsletter/config.py` with NewsletterConfig model
   - Modify `src/newsletter/consolidator.py` to accept exclusions parameter
   - Add exclusion instruction injection logic

3. **Build UI**:
   - Add Flask routes to `src/web/feed_routes.py` (or new file)
   - Create `src/web/templates/partials/topic_exclusion_config.html`
   - Update `src/web/templates/settings.html` to include partial

4. **Integration**:
   - Wire exclusions through consolidation pipeline
   - Update caller code to pass exclusions from config

5. **Validation**:
   - Run test suite: `pytest`
   - Type check: `mypy src/`
   - Lint: `ruff check .`
   - Manual browser testing

---

## Generated Artifacts Summary

| Artifact | Path | Purpose |
|----------|------|---------|
| Specification | [spec.md](spec.md) | User requirements and acceptance criteria |
| Clarifications | spec.md (Session 2026-02-03) | 5 resolved ambiguities |
| Implementation Plan | [plan.md](plan.md) | This document |
| Research | [research.md](research.md) | Design decisions and rationale |
| Data Model | [data-model.md](data-model.md) | Pydantic schema and validation rules |
| API Contracts | [contracts/api-routes.md](contracts/api-routes.md) | Flask route specifications |
| Quickstart Guide | [quickstart.md](quickstart.md) | Developer implementation steps |

All planning artifacts are complete and ready for task generation or direct implementation.
