# Tasks: Newsletter Database Consolidation

**Input**: Design documents from `/specs/006-newsletter-db-consolidation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per constitution Principle III (Backend TDD), tests are REQUIRED and must be written FIRST for all backend services and business logic.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/`, `tests/` at repository root
- Paths reference existing Flask application structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database schema

- [X] T001 Create PostgreSQL migration file src/db/migrations/003_newsletter_consolidation.sql with processed_emails and migration_history tables
- [X] T002 [P] Create Pydantic models file src/models/newsletter_models.py with ProcessedEmail, NewsletterItemInput, ConnectionPoolConfig models
- [X] T003 [P] Create SHA-256 ID generation module src/newsletter/id_generation.py with normalize_text() and generate_newsletter_id() functions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Write failing unit tests for connection pool in tests/unit/test_connection_pool.py (test initialization, getconn, putconn, pool exhaustion)
- [X] T005 Implement ThreadedConnectionPool in src/db/connection.py replacing singleton pattern (minconn=2, maxconn=10, context manager for safe usage)
- [X] T006 [P] Write failing unit tests for SHA-256 ID generation in tests/unit/test_sha256_ids.py (test determinism, normalization, collision resistance)
- [X] T007 [P] Implement SHA-256 ID generation functions in src/newsletter/id_generation.py per research.md specifications
- [X] T008 Write failing unit tests for repository email tracking methods in tests/unit/test_repository_emails.py (test is_email_processed, get_processed_message_ids, track_email_processed)
- [X] T009 Implement repository email tracking methods in src/db/repository.py (is_email_processed, get_processed_message_ids, track_email_processed, update_email_status)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Newsletter System Functions Without SQLite (Priority: P1) 🎯 MVP

**Goal**: Eliminate SQLite dependency, use PostgreSQL for all newsletter tracking and storage

**Independent Test**: Run newsletter collection pipeline and verify no SQLite files created, all data in PostgreSQL

### Tests for User Story 1 (TDD REQUIRED)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write failing integration test for SQLite-free newsletter collection in tests/integration/test_newsletter_pipeline.py (verify no data/newsletter_aggregator.db created)
- [X] T011 [P] [US1] Write failing test for PostgreSQL email deduplication in tests/integration/test_newsletter_pipeline.py (verify same message_id not processed twice)

### Implementation for User Story 1

- [X] T012 [US1] Remove SQLite imports and database functions from src/newsletter/storage.py (remove init_database, get_processed_message_ids, track_email_processed, insert_newsletter_items, get_all_parsed_items, get_recent_parsed_items functions)
- [X] T013 [US1] Update src/newsletter/email_collector.py to use Repository instead of SQLite (replace storage.get_processed_message_ids with repo.get_processed_message_ids, replace storage.track_email_processed with repo.track_email_processed)
- [X] T014 [US1] Update src/newsletter/email_collector.py to use Repository for parsed item storage (replace storage.insert_newsletter_items with repo.save_feed_items)
- [X] T015 [US1] Update src/sources/newsletter.py to fetch items from PostgreSQL (replace storage.get_all_parsed_items with repo.get_feed_items filtered by source_type='newsletter')
- [X] T016 [US1] Remove legacy SQLite initialization from src/web/app.py create_app() function (remove init_database and init_data_directories calls related to SQLite)

**Checkpoint**: Newsletter system fully functional without SQLite - verify tests pass

---

## Phase 4: User Story 2 - ID Generation is Stable Across Restarts (Priority: P1)

**Goal**: Replace non-deterministic hash() with SHA-256 for stable, deterministic IDs

**Independent Test**: Process same newsletter twice (with restart), verify identical IDs and no duplicates

### Tests for User Story 2 (TDD REQUIRED)

- [X] T017 [P] [US2] Write failing test for ID stability across restarts in tests/integration/test_newsletter_pipeline.py (process newsletter, restart app, process same newsletter, verify same ID)
- [X] T018 [P] [US2] Write failing test for duplicate prevention in tests/integration/test_newsletter_pipeline.py (process newsletter with duplicate title+date, verify only one record in database)

### Implementation for User Story 2

- [X] T019 [US2] Update src/sources/newsletter.py _to_feed_item() method to use generate_newsletter_id() instead of hash() (replace lines 156-159 with SHA-256 ID generation)
- [X] T020 [US2] Update FeedItem source_id extraction in src/sources/newsletter.py (extract hash portion from newsletter:{hash} format for source_id field)
- [X] T021 [US2] Verify database UNIQUE constraint on (source_type, source_id) exists in src/db/migrations/001_initial.sql (should already exist from original schema)

**Checkpoint**: IDs are stable and deterministic - verify tests pass

---

## Phase 5: User Story 3 - Parallel Newsletter Parsing is Thread-Safe (Priority: P1)

**Goal**: Enable safe concurrent parsing with connection pooling

**Independent Test**: Parse 10 newsletters in parallel (max_workers=5), verify no connection errors

### Tests for User Story 3 (TDD REQUIRED)

- [X] T022 [P] [US3] Write failing test for parallel parsing without connection errors in tests/integration/test_newsletter_pipeline.py (parse 10 newsletters with max_workers=5, verify all succeed)
- [X] T023 [P] [US3] Write failing test for connection pool retry logic in tests/unit/test_connection_pool.py (simulate pool exhaustion, verify exponential backoff 1s/2s/4s)

### Implementation for User Story 3

- [X] T024 [US3] Add exponential backoff retry decorator to src/db/connection.py (retry_on_db_error with 3 retries, 1s/2s/4s delays)
- [X] T025 [US3] Update get_connection() context manager in src/db/connection.py to handle pool exhaustion gracefully (use retry decorator)
- [X] T026 [US3] Update src/newsletter/email_collector.py parse_newsletters() to use get_connection() context manager for all database operations
- [X] T027 [US3] Initialize connection pool on application startup in src/web/app.py create_app() (call initialize_pool before run_migrations)
- [X] T028 [US3] Add pool cleanup handlers in src/db/connection.py (atexit and signal handlers for closeall)

**Checkpoint**: Parallel parsing is thread-safe - verify tests pass

---

## Phase 6: User Story 4 - Migration Preserves Existing Data (Priority: P2)

**Goal**: Auto-migrate SQLite data to PostgreSQL on application startup

**Independent Test**: Run migration with SQLite database containing 50+ emails, verify all data in PostgreSQL

### Tests for User Story 4 (TDD REQUIRED)

- [ ] T029 [P] [US4] Write failing test for migration idempotency in tests/unit/test_migration.py (run migration twice, verify runs only once)
- [ ] T030 [P] [US4] Write failing test for migration with missing SQLite in tests/unit/test_migration.py (verify graceful skip when no SQLite database exists)
- [ ] T031 [P] [US4] Write failing test for processed_emails migration in tests/unit/test_migration.py (migrate 50 emails from SQLite, verify all in PostgreSQL)
- [ ] T032 [P] [US4] Write failing test for newsletter_items migration in tests/unit/test_migration.py (migrate 200 items from SQLite, verify all in feed_items with source_type='newsletter')

### Implementation for User Story 4

- [ ] T033 [US4] Create migration tracker module src/db/migration_tracker.py (MigrationTracker class with is_completed, mark_started, mark_completed, mark_failed methods)
- [ ] T034 [US4] Create SQLite migration module src/db/sqlite_migration.py (migrate_newsletter_data function with batch streaming, data transformation, idempotency check)
- [ ] T035 [US4] Implement data transformation in src/db/sqlite_migration.py (_transform_row function to convert SQLite newsletter_items to feed_items format with SHA-256 IDs)
- [ ] T036 [US4] Add auto-migration trigger in src/web/app.py create_app() (run_data_migrations function called after run_migrations, before legacy init)
- [ ] T037 [US4] Add migration progress logging in src/db/sqlite_migration.py (log batch progress, completion stats, errors)

**Checkpoint**: Migration preserves all existing data - verify tests pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Run full integration test suite with pytest (verify all user stories work independently and together)
- [ ] T039 [P] Run mypy type checking on all modified files (verify no type errors, no plain dict in function signatures)
- [ ] T040 [P] Run ruff linter on all modified files (fix any linting errors)
- [ ] T041 [P] Verify quickstart.md examples match implementation (test code snippets, verify file paths)
- [ ] T042 Remove deprecated SQLite test files from tests/ (remove tests that reference newsletter_aggregator.db)
- [ ] T043 [P] Add database health check endpoint in src/web/app.py (route /health/db showing pool status)
- [ ] T044 Update CLAUDE.md with final implementation notes if needed (document any deviations from plan)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (US1): Independent - can start after Foundational
  - User Story 2 (US2): Depends on US1 (needs PostgreSQL storage working)
  - User Story 3 (US3): Depends on US1 (needs PostgreSQL operations to test concurrency)
  - User Story 4 (US4): Independent - can run in parallel with US1-US3
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on User Story 1 completion (needs PostgreSQL storage layer)
- **User Story 3 (P1)**: Depends on User Story 1 completion (needs PostgreSQL operations)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent of US1-US3 (can be parallelized)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD requirement)
- Unit tests before integration tests
- Repository methods before service layer
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1: T002 and T003 can run in parallel
- Phase 2: T006-T007 can run in parallel with T008-T009 (different modules)
- User Story 1: T010 and T011 can run in parallel (different test cases)
- User Story 2: T017 and T018 can run in parallel (different test cases)
- User Story 3: T022 and T023 can run in parallel (integration vs unit tests)
- User Story 4: All tests T029-T032 can run in parallel (different test scenarios)
- User Story 4: Can be worked on in parallel with US1-US3 if team capacity allows
- Phase 7: T038, T039, T040, T041 can all run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T010: "Write failing integration test for SQLite-free newsletter collection"
Task T011: "Write failing test for PostgreSQL email deduplication"

# After tests written and failing, implementation tasks run sequentially:
Task T012: "Remove SQLite imports from storage.py"
Task T013: "Update email_collector.py to use Repository"
# ... etc
```

---

## Parallel Example: User Story 4 (Can Work Alongside US1-US3)

```bash
# While other developers work on US1-US3, a separate developer can work on US4:
# Team Member A: Working on US1 (SQLite removal)
# Team Member B: Working on US4 (Migration) - independent work in parallel

US4 Test tasks (can all run in parallel):
Task T029: "Write failing test for migration idempotency"
Task T030: "Write failing test for migration with missing SQLite"
Task T031: "Write failing test for processed_emails migration"
Task T032: "Write failing test for newsletter_items migration"
```

---

## Implementation Strategy

### MVP First (User Stories 1+2+3 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T010-T016) - SQLite removal
4. Complete Phase 4: User Story 2 (T017-T021) - Stable IDs
5. Complete Phase 5: User Story 3 (T022-T028) - Thread safety
6. **STOP and VALIDATE**: Test all P1 stories work together
7. Deploy/demo if ready (User Story 4 migration can be added later)

### Full Implementation (All User Stories)

1. Complete Setup + Foundational (T001-T009) → Foundation ready
2. Add User Story 1 (T010-T016) → Test independently
3. Add User Story 2 (T017-T021) → Test independently
4. Add User Story 3 (T022-T028) → Test independently
5. Add User Story 4 (T029-T037) → Test independently
6. Polish (T038-T044) → Final validation

### Parallel Team Strategy

With 2+ developers after Foundational phase completes:

1. Team completes Setup + Foundational together (T001-T009)
2. Once Foundational is done:
   - Developer A: User Story 1+2+3 (sequential dependencies)
   - Developer B: User Story 4 (independent - migration work)
3. Merge and integrate at end

---

## Notes

- **TDD Required**: Per constitution Principle III, all backend service tests MUST be written first and FAIL before implementation
- **Strong Typing**: All functions use Pydantic models, no plain `dict` (Principle II)
- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **US1-US3 are sequential**: US2 depends on US1, US3 depends on US1 (same database operations)
- **US4 is parallel**: Migration work can happen alongside US1-US3 if team capacity allows
- Verify tests fail before implementing (Red-Green-Refactor cycle)
- Run mypy and ruff after each task to catch type errors early
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 6 tasks (BLOCKING)
- **Phase 3 (US1)**: 7 tasks (2 tests + 5 implementation)
- **Phase 4 (US2)**: 5 tasks (2 tests + 3 implementation)
- **Phase 5 (US3)**: 7 tasks (2 tests + 5 implementation)
- **Phase 6 (US4)**: 9 tasks (4 tests + 5 implementation)
- **Phase 7 (Polish)**: 7 tasks

**Total**: 44 tasks

**Parallel Opportunities**: 15 tasks marked [P] can run in parallel within their phase

**Independent Stories**: US1 (after Foundational), US4 (after Foundational) can start independently

**MVP Scope**: Phase 1+2+3+4+5 (29 tasks) delivers core P1 functionality (SQLite removal + stable IDs + thread safety)
