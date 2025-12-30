# Tasks: Zotero API Digest

**Input**: Design documents from `/specs/001-zotero-api-digest/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit tests included per constitution policy (tests for backend logic, not API endpoints)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per implementation plan (src/zotero/, src/cli/, src/utils/, tests/unit/, tests/integration/)
- [X] T002 [P] Create __init__.py files in src/zotero/, src/cli/, src/utils/ for Python package structure
- [X] T003 [P] Add pytest to dev dependencies in pyproject.toml
- [X] T004 [P] Create .gitignore entry for .env file if not already present
- [X] T005 [P] Create tests/__init__.py and tests/unit/__init__.py, tests/integration/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create Configuration dataclass in src/utils/config.py with fields: library_id, api_key, output_path, days, include_keywords, exclude_keywords
- [X] T007 Implement load_configuration() function in src/utils/config.py to load from .env and validate required fields
- [X] T008 Create custom exception classes (AuthenticationError, ConnectionError) in src/zotero/__init__.py or src/utils/exceptions.py
- [X] T009 Create Zotero client wrapper initialization function in src/zotero/client.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Fetch Recent Zotero Library Additions (Priority: P1) 🎯 MVP

**Goal**: Retrieve recent Zotero library additions, filter by addition date, and sort by publication date (limiting to 10 most recent when >10 items found)

**Independent Test**: Run application with valid Zotero credentials and verify library items are retrieved, sorted by publication date, and limited to 10 when >10 items exist.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Create unit test for sort_and_limit_items() with >10 items in tests/unit/test_filters.py
- [X] T011 [P] [US1] Create unit test for sort_and_limit_items() with <=10 items in tests/unit/test_filters.py
- [X] T012 [P] [US1] Create unit test for sort_and_limit_items() with missing publication dates in tests/unit/test_filters.py
- [X] T013 [P] [US1] Create integration test for fetch_recent_items() with mocked Zotero client in tests/integration/test_zotero_client.py

### Implementation for User Story 1

- [X] T014 [US1] Implement fetch_recent_items() function in src/zotero/client.py that uses pyzotero client.items(since=timestamp) to retrieve items
- [X] T015 [US1] Implement sort_and_limit_items() function in src/zotero/filters.py that sorts by publication date descending and limits to 10 items
- [X] T016 [US1] Add error handling in fetch_recent_items() for AuthenticationError and ConnectionError with clear messages
- [X] T017 [US1] Add date parsing logic in sort_and_limit_items() to handle ISO date strings and missing dates gracefully

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - can fetch and sort items from Zotero API

---

## Phase 4: User Story 2 - Generate Markdown Digest Output (Priority: P1) 🎯 MVP

**Goal**: Format fetched library items as a readable markdown file with hierarchical organization by item type

**Independent Test**: Run application with fetched items and verify a properly formatted markdown file is generated in the specified output location with correct structure.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T018 [P] [US2] Create unit test for format_item_markdown() with complete item data in tests/unit/test_formatter.py
- [X] T019 [P] [US2] Create unit test for format_item_markdown() with missing optional fields in tests/unit/test_formatter.py
- [X] T020 [P] [US2] Create unit test for format_item_markdown() with special markdown characters in titles in tests/unit/test_formatter.py
- [X] T021 [P] [US2] Create unit test for generate_digest() with multiple item types in tests/unit/test_formatter.py
- [X] T022 [P] [US2] Create unit test for generate_digest() with empty items list in tests/unit/test_formatter.py
- [X] T023 [P] [US2] Create unit test for write_digest() file creation in tests/unit/test_formatter.py

### Implementation for User Story 2

- [X] T024 [US2] Implement format_item_markdown() function in src/zotero/formatter.py to format single item with title, authors, date, venue, abstract, URL
- [X] T025 [US2] Implement generate_digest() function in src/zotero/formatter.py that groups items by itemType and creates markdown sections
- [X] T026 [US2] Implement write_digest() function in src/zotero/formatter.py that creates output directory if needed and writes markdown file
- [X] T027 [US2] Add markdown escaping logic in format_item_markdown() for special characters (#, *, etc.)
- [X] T028 [US2] Add author formatting logic in format_item_markdown() to format creators as "LastName, FirstName" comma-separated

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - can fetch items and generate markdown digest file

---

## Phase 5: User Story 3 - Configure Application via Command Line (Priority: P2)

**Goal**: Enable configuration through command-line arguments for output path, time range, and help

**Independent Test**: Run application with various command-line arguments (--output, --days, --help) and verify behavior changes accordingly.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T029 [P] [US3] Create unit test for CLI argument parsing with --output flag in tests/unit/test_cli.py
- [X] T030 [P] [US3] Create unit test for CLI argument parsing with --days flag in tests/unit/test_cli.py
- [X] T031 [P] [US3] Create unit test for CLI argument parsing with --help flag in tests/unit/test_cli.py
- [X] T032 [P] [US3] Create unit test for CLI argument parsing with default values in tests/unit/test_cli.py

### Implementation for User Story 3

- [X] T033 [US3] Implement argparse setup in src/cli/main.py with --output, --days, --help arguments
- [X] T034 [US3] Integrate CLI argument parsing with load_configuration() in src/cli/main.py to merge CLI args with env vars
- [X] T035 [US3] Add --help text with descriptions for all options in src/cli/main.py
- [X] T036 [US3] Add main() entry point function in src/cli/main.py that orchestrates fetch → sort → format → write workflow
- [X] T037 [US3] Add __main__.py in src/cli/ or configure pyproject.toml entry point for running as module

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - full CLI application with configurable options

---

## Phase 6: User Story 4 - Filter Content by Keywords (Priority: P3)

**Goal**: Filter digest content by keywords for inclusion and exclusion

**Independent Test**: Run application with --include and --exclude keyword filters and verify only matching items appear in output.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T038 [P] [US4] Create unit test for filter_by_keywords() with include keywords in tests/unit/test_filters.py
- [X] T039 [P] [US4] Create unit test for filter_by_keywords() with exclude keywords in tests/unit/test_filters.py
- [X] T040 [P] [US4] Create unit test for filter_by_keywords() with both include and exclude (exclusion takes precedence) in tests/unit/test_filters.py
- [X] T041 [P] [US4] Create unit test for filter_by_keywords() with empty filters (no filtering) in tests/unit/test_filters.py
- [X] T042 [P] [US4] Create unit test for filter_by_keywords() case-insensitive matching in tests/unit/test_filters.py
- [X] T043 [P] [US4] Create unit test for filter_by_keywords() searching in title, abstract, and tags in tests/unit/test_filters.py

### Implementation for User Story 4

- [X] T044 [US4] Implement filter_by_keywords() function in src/zotero/filters.py with case-insensitive substring matching
- [X] T045 [US4] Add keyword search logic in filter_by_keywords() to search in title, abstractNote, and tag names
- [X] T046 [US4] Add exclusion-first logic in filter_by_keywords() so exclusions take precedence over inclusions
- [X] T047 [US4] Add --include and --exclude CLI arguments in src/cli/main.py for keyword filtering
- [X] T048 [US4] Integrate filter_by_keywords() into main workflow in src/cli/main.py (after fetch, before sort)

**Checkpoint**: All user stories should now be independently functional - complete feature with filtering capabilities

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T049 [P] Update README.md with setup instructions and usage examples from quickstart.md
- [X] T050 [P] Add docstrings to all public functions in src/zotero/, src/cli/, src/utils/
- [X] T051 [P] Add type hints to all function signatures per Python 3.13+ best practices
- [X] T052 Code cleanup and refactoring - ensure consistent error handling patterns across all modules
- [X] T053 [P] Add logging statements for key operations (fetch start, item count, file write) in src/zotero/client.py and src/zotero/formatter.py
- [X] T054 Run quickstart.md validation - verify all examples work as documented
- [X] T055 [P] Add .env.example file with placeholder values for ZOTERO_LIBRARY_ID and ZOTERO_API_KEY
- [X] T056 [P] Document Success Criteria validation approach: SC-001 (performance) via manual timing, SC-002 (setup time) via user testing, SC-003 (markdown rendering) via visual inspection, SC-004 (item count) via automated test, SC-005 (error messages) via manual testing
- [X] T057 Create validation checklist in README.md or docs/ for verifying all Success Criteria are met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Uses same dict structure from Zotero API (no custom data structure needed)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 and US2 but should be independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core functions before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002-T005)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1 and 4 can start in parallel (different modules)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create unit test for sort_and_limit_items() with >10 items in tests/unit/test_filters.py"
Task: "Create unit test for sort_and_limit_items() with <=10 items in tests/unit/test_filters.py"
Task: "Create unit test for sort_and_limit_items() with missing publication dates in tests/unit/test_filters.py"
Task: "Create integration test for fetch_recent_items() with mocked Zotero client in tests/integration/test_zotero_client.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: "Create unit test for format_item_markdown() with complete item data in tests/unit/test_formatter.py"
Task: "Create unit test for format_item_markdown() with missing optional fields in tests/unit/test_formatter.py"
Task: "Create unit test for format_item_markdown() with special markdown characters in titles in tests/unit/test_formatter.py"
Task: "Create unit test for generate_digest() with multiple item types in tests/unit/test_formatter.py"
Task: "Create unit test for generate_digest() with empty items list in tests/unit/test_formatter.py"
Task: "Create unit test for write_digest() file creation in tests/unit/test_formatter.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (fetch and sort items)
4. Complete Phase 4: User Story 2 (generate markdown output)
5. **STOP and VALIDATE**: Test User Stories 1 & 2 independently - should be able to fetch items and generate digest
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Can fetch and sort items
3. Add User Story 2 → Test independently → Can generate markdown digest (MVP!)
4. Add User Story 3 → Test independently → Can configure via CLI
5. Add User Story 4 → Test independently → Can filter by keywords
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (fetch/sort)
   - Developer B: User Story 2 (formatting) - can start after US1 items structure is known
   - Developer C: User Story 4 (filtering) - can work in parallel with US1/US2
3. After US1 and US2 complete:
   - Developer A: User Story 3 (CLI integration)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are for backend logic only (per constitution) - no API endpoint tests, no UI tests

---

## Task Summary

**Total Tasks**: 57

**Tasks by Phase**:
- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (US1 - Fetch): 8 tasks (4 tests + 4 implementation)
- Phase 4 (US2 - Markdown): 11 tasks (6 tests + 5 implementation)
- Phase 5 (US3 - CLI): 9 tasks (4 tests + 5 implementation)
- Phase 6 (US4 - Filtering): 11 tasks (6 tests + 5 implementation)
- Phase 7 (Polish): 9 tasks (includes Success Criteria validation)

**Tasks by User Story**:
- User Story 1: 8 tasks
- User Story 2: 11 tasks
- User Story 3: 9 tasks
- User Story 4: 11 tasks

**Parallel Opportunities**: 
- Setup phase: 4 parallel tasks
- Foundational phase: All can be parallel
- Each user story's tests can run in parallel
- US1 and US4 can be developed in parallel after foundational phase

**Suggested MVP Scope**: User Stories 1 & 2 (fetch items and generate markdown digest) - 19 tasks total

