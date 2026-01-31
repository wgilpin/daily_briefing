# Tasks: Unified Feed App

**Input**: Design documents from `/specs/003-unified-feed-app/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/api.md, research.md

**Tests**: Per constitution, TDD is required for backend services. Tests NOT required for Flask routes/templates.

## Phase 1: Setup (Project Initialization)

**Purpose**: Project structure, dependencies, configuration

- [x] T001 Add new dependencies to pyproject.toml (psycopg2-binary, tenacity, cryptography)
- [x] T002 [P] Create src/models/__init__.py with model exports
- [x] T003 [P] Create src/sources/__init__.py with source exports
- [x] T004 [P] Create src/services/__init__.py with service exports
- [x] T005 [P] Create src/db/__init__.py with db exports
- [x] T006 Create tests/conftest.py with shared fixtures (mock DB, mock APIs)
- [x] T007 Update src/utils/config.py to load all environment variables (DATABASE_URL, ENCRYPTION_KEY)
- [x] T008 Create src/utils/logging.py with structured logging to stdout

**Checkpoint**: Project structure ready, dependencies installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database layer and core models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational (TDD)

- [x] T009 [P] Write test for FeedItem model validation in tests/unit/test_models.py
- [x] T010 [P] Write test for SourceConfig model validation in tests/unit/test_models.py
- [x] T011 [P] Write test for database connection in tests/unit/test_db.py (mock psycopg2)
- [x] T012 [P] Write test for repository CRUD operations in tests/unit/test_repository.py (mock DB)

### Implementation for Foundational

- [x] T013 [P] Create FeedItem Pydantic model in src/models/feed_item.py
- [x] T014 [P] Create SourceConfig Pydantic model in src/models/source.py
- [x] T015 [P] Create ZoteroConfig model in src/models/source.py
- [x] T016 [P] Create NewsletterConfig model in src/models/source.py
- [x] T017 [P] Create AppSettings model in src/models/source.py
- [x] T018 Create database connection module in src/db/connection.py
- [x] T019 Create repository with CRUD operations in src/db/repository.py
- [x] T020 Create SQL migration script in src/db/migrations/001_initial.sql

**Checkpoint**: Foundation ready - models validated, database layer working

---

## Phase 3: User Story 1 - View Unified Feed (Priority: P1) 🎯 MVP

**Goal**: Display combined feed from Zotero and newsletters sorted by date

**Independent Test**: Open web UI, see items from both sources in single feed with source badges

### Tests for User Story 1 (TDD - Services Only)

- [x] T021 [P] [US1] Write test for FeedSource protocol in tests/unit/test_sources.py
- [x] T022 [P] [US1] Write test for ZoteroSource.fetch_items in tests/unit/test_zotero_source.py (mock pyzotero)
- [x] T023 [P] [US1] Write test for NewsletterSource.fetch_items in tests/unit/test_newsletter_source.py (mock existing modules)
- [x] T024 [P] [US1] Write test for FeedService.get_unified_feed in tests/unit/test_feed_service.py (mock sources)

### Implementation for User Story 1

- [x] T025 [US1] Create FeedSource protocol in src/sources/base.py
- [x] T026 [US1] Create ZoteroSource adapter in src/sources/zotero.py (wrap existing src/zotero/)
- [x] T027 [US1] Create NewsletterSource adapter in src/sources/newsletter.py (wrap existing src/newsletter/)
- [x] T028 [US1] Create FeedService in src/services/feed.py (aggregate, sort, paginate)
- [x] T029 [US1] Create unified feed template in src/web/templates/feed.html
- [x] T030 [US1] Create feed item partial in src/web/templates/partials/feed_item.html
- [x] T031 [US1] Add GET / route in src/web/feed_routes.py (render unified feed)
- [x] T032 [US1] Add GET /api/feed route in src/web/feed_routes.py (HTMX partial)

**Checkpoint**: User Story 1 complete - unified feed displays items from both sources

---

## Phase 4: User Story 2 - Refresh Feed On-Demand (Priority: P1)

**Goal**: Manual refresh button fetches latest from all sources

**Independent Test**: Click Refresh, see loading indicator, new items appear

### Tests for User Story 2 (TDD - Services Only)

- [x] T033 [P] [US2] Write test for retry utility in tests/unit/test_retry.py
- [x] T034 [P] [US2] Write test for FeedService.refresh_all in tests/unit/test_retry.py (mock sources, test partial failure)

### Implementation for User Story 2

- [x] T035 [US2] Create retry utility with exponential backoff in src/services/retry.py
- [x] T036 [US2] Add FeedService.refresh_all method in src/services/feed.py
- [x] T037 [US2] Add POST /api/refresh route in src/web/feed_routes.py
- [x] T038 [US2] Add refresh button with HTMX to feed template in src/web/templates/feed.html
- [x] T039 [US2] Create refresh status partial in src/web/templates/partials/refresh_status.html

**Checkpoint**: User Story 2 complete - on-demand refresh working with partial failure handling

---

## Phase 5: User Story 3 - Configure Data Sources (Priority: P2)

**Goal**: Unified settings page for Zotero and newsletter configuration

**Independent Test**: Go to Settings, modify config, save, verify changes persist

### Tests for User Story 3 (TDD - Services Only)

- [x] T040 [P] [US3] Write test for repository.save_source_config in tests/unit/test_repository.py
- [x] T041 [P] [US3] Write test for repository.get_source_config in tests/unit/test_repository.py
- [x] T042 [P] [US3] Write test for OAuth token encryption/decryption in tests/unit/test_oauth.py

### Implementation for User Story 3

- [x] T043 [US3] Add OAuth token encryption utility in src/utils/crypto.py
- [x] T044 [US3] Add repository methods for source_configs table in src/db/repository.py
- [x] T045 [US3] Add repository methods for oauth_tokens table in src/db/repository.py
- [x] T046 [US3] Create settings page template in src/web/templates/settings.html
- [x] T047 [US3] Create Zotero config form partial in src/web/templates/partials/zotero_config.html
- [x] T048 [US3] Create newsletter config form partial in src/web/templates/partials/newsletter_config.html
- [x] T049 [US3] Add GET /settings route in src/web/feed_routes.py
- [x] T050 [US3] Add POST /api/settings/zotero route in src/web/feed_routes.py
- [x] T051 [US3] Add POST /api/settings/newsletter route in src/web/feed_routes.py
- [x] T052 [US3] Add POST /api/settings/newsletter/senders route in src/web/feed_routes.py
- [x] T053 [US3] Add DELETE /api/settings/newsletter/senders/{email} route in src/web/feed_routes.py

**Checkpoint**: User Story 3 complete - all configuration via unified settings page

---

## Phase 6: User Story 4 - Filter and Search Feed (Priority: P3)

**Goal**: Filter by source, search by keyword, date range filter

**Independent Test**: Apply filters, verify feed updates to show matching items only

### Tests for User Story 4 (TDD - Services Only)

- [x] T054 [P] [US4] Write test for FeedService.filter_items in tests/unit/test_feed_service.py
- [x] T055 [P] [US4] Write test for FeedService.search_items in tests/unit/test_feed_service.py

### Implementation for User Story 4

- [x] T056 [US4] Add filter_items method to FeedService in src/services/feed.py
- [x] T057 [US4] Add search_items method to FeedService in src/services/feed.py
- [x] T058 [US4] Add filter controls to feed template in src/web/templates/feed.html
- [x] T059 [US4] Add search input to feed template in src/web/templates/feed.html
- [x] T060 [US4] Update GET /api/feed route to handle filter/search params in src/web/feed_routes.py

**Checkpoint**: User Story 4 complete - filtering and search working

---

## Phase 7: User Story 5 - Extensible Source Architecture (Priority: P2)

**Goal**: New sources can be added via standard interface without modifying core code

**Independent Test**: Review code to confirm new source only requires implementing FeedSource protocol

### Implementation for User Story 5

- [x] T061 [US5] Document FeedSource protocol in src/sources/base.py with docstrings
- [x] T062 [US5] Add source registry pattern in src/sources/__init__.py
- [x] T063 [US5] Create get_config_schema method on FeedSource protocol in src/sources/base.py
- [x] T064 [US5] Update FeedService to use source registry in src/services/feed.py
- [x] T065 [US5] Update settings page to dynamically render source configs in src/web/templates/settings.html

**Checkpoint**: User Story 5 complete - architecture supports adding new sources

---

## Phase 8: User Story 6 - Container Deployment (Priority: P2)

**Goal**: Deploy to Coolify with env var configuration and health checks

**Independent Test**: Build container, deploy to Coolify, verify app works

### Implementation for User Story 6

- [x] T066 [US6] Create Dockerfile at repository root
- [x] T067 [US6] Create .dockerignore at repository root
- [x] T068 [US6] Add GET /api/health route in src/web/feed_routes.py
- [x] T069 [US6] Update src/web/app.py to run migrations on startup
- [x] T070 [US6] Create docker-compose.yml for local testing with PostgreSQL
- [x] T071 [US6] Create .env.example with all required environment variables
- [x] T072 [US6] Update README.md with Coolify deployment instructions

**Checkpoint**: User Story 6 complete - containerized and deployable

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [x] T073 [P] Run ruff check --fix on all new files
- [x] T074 [P] Run mypy on all new files, fix type errors (new files clean, pre-existing issues remain)
- [x] T075 [P] Run pytest, ensure all tests pass (180 tests passing)
- [x] T076 Verify quickstart.md scenarios work end-to-end
- [ ] T077 Remove any unused code from existing src/zotero/ and src/newsletter/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-8 (User Stories)**: All depend on Phase 2 completion
- **Phase 9 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (View Feed)**: Can start after Phase 2 - No dependencies
- **US2 (Refresh)**: Depends on US1 (needs feed to refresh)
- **US3 (Configure)**: Can start after Phase 2 - Independent of US1/US2
- **US4 (Filter/Search)**: Depends on US1 (needs feed to filter)
- **US5 (Extensible)**: Depends on US1 (refines source architecture)
- **US6 (Deploy)**: Can start after Phase 2 - Independent

### Parallel Opportunities

```text
After Phase 2 complete:
├── US1 (View Feed) ────────────────┐
│                                   ├── US2 (Refresh) ──┐
├── US3 (Configure) ───────────────────────────────────────┤
│                                   ├── US4 (Filter) ──────┤
│                                   └── US5 (Extensible) ──┤
└── US6 (Deploy) ──────────────────────────────────────────┴── Phase 9
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (View Feed)
4. Complete Phase 4: User Story 2 (Refresh)
5. **STOP and VALIDATE**: Test MVP independently
6. Deploy MVP if ready

### Full Implementation

Continue after MVP validation:
7. Complete Phase 5: US3 (Configure)
8. Complete Phase 6: US4 (Filter/Search)
9. Complete Phase 7: US5 (Extensible)
10. Complete Phase 8: US6 (Deploy)
11. Complete Phase 9: Polish

---

## Notes

- [P] = parallelizable (different files, no dependencies)
- [USn] = belongs to User Story n
- Tests use mocks for all external APIs (Zotero, Gmail, Gemini, PostgreSQL)
- No tests for Flask routes per constitution (backend TDD only)
- Commit after each task or logical group
