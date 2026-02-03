# Tasks: Topic Exclusion Filter

**Input**: Design documents from `/specs/005-topic-exclusion/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-routes.md

**Tests**: TDD required per constitution - all tests MUST be written first and FAIL before implementation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

This is a single project with paths at repository root:
- `src/` for source code
- `tests/` for all tests
- `config/` for configuration files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and configuration file preparation

- [X] T001 Add `excluded_topics` field to config/senders.json as empty array

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration model that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create unit test file tests/unit/newsletter/test_config.py
- [X] T003 [P] Write test for NewsletterConfig with excluded_topics in tests/unit/newsletter/test_config.py
- [X] T004 [P] Write test for max 50 topics validation in tests/unit/newsletter/test_config.py
- [X] T005 [P] Write test for max 100 chars validation in tests/unit/newsletter/test_config.py
- [X] T006 [P] Write test for allowing duplicates in tests/unit/newsletter/test_config.py
- [X] T007 [P] Write test for empty exclusions list in tests/unit/newsletter/test_config.py
- [X] T008 Create or extend src/newsletter/config.py with NewsletterConfig Pydantic model
- [X] T009 Add excluded_topics field with Field(default_factory=list) to NewsletterConfig in src/newsletter/config.py
- [X] T010 Add @field_validator for excluded_topics validation in src/newsletter/config.py
- [X] T011 Implement load_config() function with Path parameter in src/newsletter/config.py
- [X] T012 Implement save_config() function with atomic write in src/newsletter/config.py
- [X] T013 Run unit tests to verify NewsletterConfig implementation: pytest tests/unit/newsletter/test_config.py -v
- [X] T014 Run type checker on config module: mypy src/newsletter/config.py

**Checkpoint**: Configuration model ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure Excluded Topics via UI (Priority: P1) 🎯 MVP

**Goal**: Users can add and remove excluded topics through the settings UI with proper validation

**Independent Test**: Add topics through settings UI, verify they persist in config/senders.json, delete topics and verify removal

### Tests for User Story 1 (TDD Required)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Create integration test file tests/integration/web/test_exclusion_routes.py
- [X] T016 [P] [US1] Write test for POST /settings/exclusions/add success in tests/integration/web/test_exclusion_routes.py
- [X] T017 [P] [US1] Write test for POST /settings/exclusions/add at 50-topic limit in tests/integration/web/test_exclusion_routes.py
- [X] T018 [P] [US1] Write test for POST /settings/exclusions/add with empty topic in tests/integration/web/test_exclusion_routes.py
- [X] T019 [P] [US1] Write test for POST /settings/exclusions/add with topic exceeding 100 chars in tests/integration/web/test_exclusion_routes.py
- [X] T020 [P] [US1] Write test for DELETE /settings/exclusions/delete/{index} success in tests/integration/web/test_exclusion_routes.py
- [X] T021 [P] [US1] Write test for DELETE /settings/exclusions/delete/{index} with invalid index in tests/integration/web/test_exclusion_routes.py
- [X] T022 [P] [US1] Write test for GET /settings/exclusions/list with topics in tests/integration/web/test_exclusion_routes.py
- [X] T023 [P] [US1] Write test for GET /settings/exclusions/list empty in tests/integration/web/test_exclusion_routes.py

### Implementation for User Story 1

- [X] T024 [US1] Create Flask blueprint for exclusions in src/web/feed_routes.py or new exclusion_routes.py
- [X] T025 [US1] Implement GET /settings/exclusions/list route in src/web/feed_routes.py
- [X] T026 [US1] Implement POST /settings/exclusions/add route with validation in src/web/feed_routes.py
- [X] T027 [US1] Implement DELETE /settings/exclusions/delete/<int:index> route in src/web/feed_routes.py
- [X] T028 [US1] Register exclusions blueprint in src/web/app.py
- [X] T029 [US1] Create HTML partial template src/web/templates/partials/topic_exclusion_config.html
- [X] T030 [US1] Update src/web/templates/settings.html to include topic_exclusion_config.html partial
- [ ] T031 [US1] Run integration tests to verify routes: pytest tests/integration/web/test_exclusion_routes.py -v
- [ ] T032 [US1] Run type checker on web routes: mypy src/web/
- [ ] T033 [US1] Manual test: Open settings UI in browser and verify add/delete functionality

**Checkpoint**: At this point, User Story 1 should be fully functional - users can manage exclusion list via UI

---

## Phase 4: User Story 2 - Filter Newsletter Content (Priority: P2)

**Goal**: Newsletter consolidation automatically filters out items matching excluded topics using LLM

**Independent Test**: Configure excluded topics, trigger newsletter consolidation with test data containing both included and excluded content, verify excluded topics don't appear in output

### Tests for User Story 2 (TDD Required)

- [X] T034 [P] [US2] Create or extend tests/unit/newsletter/test_consolidator.py
- [X] T035 [P] [US2] Write test for consolidate_newsletters with no exclusions in tests/unit/newsletter/test_consolidator.py
- [X] T036 [P] [US2] Write test for consolidate_newsletters with exclusions parameter in tests/unit/newsletter/test_consolidator.py
- [X] T037 [P] [US2] Write test that exclusions are injected into LLM prompt in tests/unit/newsletter/test_consolidator.py
- [X] T038 [P] [US2] Write test that empty exclusions list doesn't add instructions in tests/unit/newsletter/test_consolidator.py
- [X] T039 [P] [US2] Write test for prompt format with multiple exclusions in tests/unit/newsletter/test_consolidator.py

### Implementation for User Story 2

- [X] T040 [US2] Extend consolidate_newsletters function signature to accept excluded_topics parameter in src/newsletter/consolidator.py
- [X] T041 [US2] Implement exclusion instructions builder in src/newsletter/consolidator.py
- [X] T042 [US2] Inject exclusion instructions at beginning of prompt in src/newsletter/consolidator.py
- [X] T043 [US2] Handle empty result case when all items filtered by exclusions in src/newsletter/consolidator.py
- [X] T044 [US2] Locate consolidate_newsletters invocation in src/newsletter/ or src/web/ and update to pass excluded_topics from loaded config
- [ ] T045 [US2] Run unit tests to verify consolidator logic: pytest tests/unit/newsletter/test_consolidator.py -v
- [ ] T046 [US2] Run type checker on consolidator: mypy src/newsletter/consolidator.py
- [ ] T047 [US2] Manual test: Configure exclusions, trigger consolidation, verify excluded content is filtered

**Checkpoint**: All user stories should now be independently functional - complete feature working end-to-end

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and documentation

- [ ] T048 [P] Run full test suite: pytest
- [ ] T049 [P] Run type checker on entire project: mypy src/
- [X] T050 [P] Run linter: ruff check .
- [ ] T051 Update CLAUDE.md with any new conventions or patterns
- [ ] T052 Manual browser test: Full workflow from settings UI through consolidation
- [ ] T053 Verify backward compatibility: Existing config without excluded_topics still works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 config but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD required)
- Routes depend on config model (from Phase 2)
- Templates depend on routes
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: Only 1 task (T001) - no parallelism
- **Phase 2**: T002-T007 (test file creation and test writing) can run in parallel
- **Phase 3 (US1) Tests**: T016-T023 can all run in parallel (different test cases)
- **Phase 3 (US1) Templates**: T029-T030 can run in parallel with route implementation
- **Phase 4 (US2) Tests**: T035-T039 can all run in parallel (different test cases)
- **Phase 5**: T048-T050 can all run in parallel (different tools)
- **Between Stories**: US1 and US2 can be worked on in parallel by different team members after Phase 2

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all test writing tasks for User Story 1 together:
Task T016: "Write test for POST /settings/exclusions/add success in tests/integration/web/test_exclusion_routes.py"
Task T017: "Write test for POST /settings/exclusions/add at 50-topic limit in tests/integration/web/test_exclusion_routes.py"
Task T018: "Write test for POST /settings/exclusions/add with empty topic in tests/integration/web/test_exclusion_routes.py"
Task T019: "Write test for POST /settings/exclusions/add with topic exceeding 100 chars in tests/integration/web/test_exclusion_routes.py"
Task T020: "Write test for DELETE /settings/exclusions/delete/{index} success in tests/integration/web/test_exclusion_routes.py"
Task T021: "Write test for DELETE /settings/exclusions/delete/{index} with invalid index in tests/integration/web/test_exclusion_routes.py"
Task T022: "Write test for GET /settings/exclusions/list with topics in tests/integration/web/test_exclusion_routes.py"
Task T023: "Write test for GET /settings/exclusions/list empty in tests/integration/web/test_exclusion_routes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → Config file ready
2. Complete Phase 2: Foundational → NewsletterConfig model working
3. Complete Phase 3: User Story 1 → UI for managing exclusions
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo settings UI if ready

**At this point, users can configure exclusions, but they won't affect consolidation yet. This is still useful for validation and UX feedback.**

### Incremental Delivery

1. Complete Setup + Foundational → Configuration model ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - UI works!)
3. Add User Story 2 → Test independently → Deploy/Demo (Full feature - filtering works!)
4. Each story adds value without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational (Phase 2) is done:
   - Developer A: User Story 1 (UI)
   - Developer B: User Story 2 (LLM integration)
3. Stories integrate cleanly since US2 just reads from config that US1 manages

---

## Success Metrics (from spec.md)

After implementation, verify these success criteria:

- **SC-001**: Users can add and remove excluded topics in under 30 seconds per topic
- **SC-002**: Consolidated newsletters exclude at least 90% of items matching configured topics
- **SC-003**: Exclusion configuration persists across application restarts
- **SC-004**: Users spend less time scanning unwanted items
- **SC-005**: Newsletters without excluded topics work identically to previous behavior

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story (US1 or US2)
- Each user story is independently completable and testable
- TDD required: Verify tests FAIL before implementing
- Commit after each logical task group
- Stop at any checkpoint to validate story independently
- Constitution compliance: Strong typing (Pydantic), TDD, mocked external APIs (Gemini LLM)
