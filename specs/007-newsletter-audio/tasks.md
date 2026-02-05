# Tasks: Newsletter Audio Generation

**Input**: Design documents from `/specs/007-newsletter-audio/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are REQUIRED per project constitution (Backend TDD principle). All external APIs (ElevenLabs) must be mocked.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [X] T001 Install ElevenLabs Python SDK via `uv add elevenlabs`
- [X] T002 [P] Add environment variables to .env.example: ELEVENLABS_API_KEY, ELEVENLABS_MALE_VOICE_ID, ELEVENLABS_FEMALE_VOICE_ID, ELEVENLABS_MODEL, ELEVENLABS_TIMEOUT
- [X] T003 [P] Create directory structure: src/services/audio/ and tests/unit/services/audio/
- [X] T004 [P] Create empty __init__.py in src/services/audio/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create AudioConfig model in src/models/audio_models.py with from_env() class method
- [X] T006 [P] Create NewsletterItem model in src/models/audio_models.py with voice_gender property and to_speech_text() method
- [X] T007 [P] Create AudioSegment model in src/models/audio_models.py
- [X] T008 [P] Create TTSRequest and VoiceSettings models in src/models/audio_models.py
- [X] T009 [P] Create AudioGenerationResult model in src/models/audio_models.py with success_rate property
- [X] T010 [P] Create custom exception classes (TTSError, TTSAPIError, TTSTimeoutError, TTSRateLimitError, TTSValidationError) in src/services/audio/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automatic Audio Newsletter Generation (Priority: P1) 🎯 MVP

**Goal**: Generate MP3 audio files for newsletters with alternating male/female voices

**Independent Test**: Generate a newsletter, verify MP3 file is created alongside markdown with alternating voices

### Tests for User Story 1 (TDD - Write tests FIRST) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Write test_parse_newsletter_items in tests/unit/services/audio/test_markdown_parser.py
- [X] T012 [P] [US1] Write test_parse_empty_newsletter in tests/unit/services/audio/test_markdown_parser.py
- [X] T013 [P] [US1] Write test_parse_newsletter_excludes_metadata in tests/unit/services/audio/test_markdown_parser.py
- [X] T014 [P] [US1] Write test_convert_to_speech_success with mocked ElevenLabs client in tests/unit/services/audio/test_tts_service.py
- [X] T015 [P] [US1] Write test_convert_to_speech_timeout in tests/unit/services/audio/test_tts_service.py
- [X] T016 [P] [US1] Write test_convert_to_speech_rate_limit in tests/unit/services/audio/test_tts_service.py
- [X] T017 [P] [US1] Write test_health_check_success in tests/unit/services/audio/test_tts_service.py
- [X] T018 [P] [US1] Write test_generate_audio_for_newsletter_success with mocked TTS service in tests/unit/services/audio/test_audio_generator.py
- [X] T019 [P] [US1] Write test_generate_audio_alternating_voices in tests/unit/services/audio/test_audio_generator.py
- [X] T020 [P] [US1] Write test_generate_audio_concatenation in tests/unit/services/audio/test_audio_generator.py
- [X] T021 [P] [US1] Write test_generate_audio_file_output in tests/unit/services/audio/test_audio_generator.py

### Implementation for User Story 1

- [X] T022 [P] [US1] Implement parse_newsletter_items() function in src/services/audio/markdown_parser.py (extract titles and content only)
- [X] T022a [US1] Add metadata exclusion to parse_newsletter_items() to filter out lines matching "*Date:*" pattern in src/services/audio/markdown_parser.py
- [X] T022b [US1] Add metadata exclusion to parse_newsletter_items() to filter out lines matching "*Source:*" pattern in src/services/audio/markdown_parser.py
- [X] T023 [P] [US1] Implement ElevenLabsTTSService.__init__() in src/services/audio/tts_service.py
- [X] T024 [US1] Implement ElevenLabsTTSService.convert_to_speech() in src/services/audio/tts_service.py (depends on T023)
- [X] T025 [US1] Implement ElevenLabsTTSService.health_check() in src/services/audio/tts_service.py (depends on T023)
- [X] T026 [US1] Implement concatenate_audio_segments() helper function in src/services/audio/audio_generator.py
- [X] T027 [US1] Implement generate_audio_for_newsletter() function in src/services/audio/audio_generator.py (depends on T022, T024, T026)
- [X] T028 [US1] Add error handling for empty newsletters in src/services/audio/audio_generator.py
- [X] T029 [US1] Add error handling for API failures in src/services/audio/audio_generator.py
- [ ] T030 [US1] Add logging for audio generation start/completion/errors in src/services/audio/audio_generator.py
- [ ] T031 [US1] Run pytest tests/unit/services/audio/ and verify all tests pass

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - audio generation works for existing markdown files

---

## Phase 4: User Story 2 - Automatic Processing of New Newsletters (Priority: P2)

**Goal**: Automatically trigger audio generation when newsletters are saved

**Independent Test**: Generate a new newsletter through existing workflow and verify audio file is automatically created

### Tests for User Story 2 (TDD - Write tests FIRST) ⚠️

- [ ] T032 [P] [US2] Write test_save_consolidated_digest_triggers_audio in tests/integration/test_newsletter_audio_workflow.py
- [ ] T033 [P] [US2] Write test_audio_failure_does_not_block_newsletter in tests/integration/test_newsletter_audio_workflow.py
- [ ] T034 [P] [US2] Write test_multiple_newsletters_each_get_audio in tests/integration/test_newsletter_audio_workflow.py

### Implementation for User Story 2

- [X] T035 [US2] Modify save_consolidated_digest() in src/newsletter/storage.py to call generate_audio_for_newsletter() after saving markdown
- [X] T036 [US2] Wrap audio generation call in try/except to prevent blocking newsletter save on failure in src/newsletter/storage.py
- [X] T037 [US2] Add logging for audio generation success/failure in src/newsletter/storage.py
- [X] T038 [US2] Update /api/refresh endpoint response in src/web/feed_routes.py to include audio_generated boolean field
- [X] T039 [US2] Run pytest tests/integration/test_newsletter_audio_workflow.py and verify all tests pass
- [ ] T040 [US2] Manual test: Generate newsletter via web UI and verify MP3 file is created automatically

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - audio is now automatically generated for every newsletter

---

## Phase 5: User Story 3 - Ultra-Clean Audio Content (Priority: P3)

**Goal**: Exclude ALL metadata (headers, titles, dates, URLs) for clean content-only audio

**Independent Test**: Generate audio from a newsletter and verify only article body content is spoken (no titles, headers, dates, or URLs)

### Tests for User Story 3 (TDD - Write tests FIRST) ⚠️

- [X] T041 [P] [US3] Write test_parse_excludes_article_titles in tests/unit/services/audio/test_markdown_parser.py
- [X] T042 [P] [US3] Write test_parse_excludes_category_headers in tests/unit/services/audio/test_markdown_parser.py
- [X] T043 [P] [US3] Write test_parse_excludes_subsection_headers in tests/unit/services/audio/test_markdown_parser.py
- [X] T044 [P] [US3] Write test_audio_contains_only_content in tests/unit/services/audio/test_audio_generator.py

### Implementation for User Story 3

- [X] T045 [US3] Modify parse_newsletter_items() in src/services/audio/markdown_parser.py to skip #### article title lines (extract content only)
- [X] T046 [US3] Modify parse_newsletter_items() in src/services/audio/markdown_parser.py to skip ## category header lines
- [X] T047 [US3] Modify parse_newsletter_items() in src/services/audio/markdown_parser.py to skip ### subsection header lines
- [X] T048 [US3] Update NewsletterItem.to_speech_text() in src/models/audio_models.py to return only content field (no title)
- [X] T049 [US3] Run pytest tests/unit/services/audio/test_markdown_parser.py and verify all tests pass
- [X] T050 [US3] Manual test: Generate audio for existing newsletter and verify only content is spoken (no metadata)

**Checkpoint**: All user stories complete - audio contains only article body content with voice alternation for topic separation

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and finalization

- [X] T053 [P] Add type hints and run mypy src/services/audio/ src/models/audio_models.py to verify type safety
- [X] T054 [P] Run ruff check --fix src/services/audio/ src/models/audio_models.py to ensure code style compliance
- [X] T055 [P] Add docstrings to all public functions and classes following Google style
- [X] T056 [P] Update .env.example with example ElevenLabs voice IDs and comments
- [X] T057 [P] Add performance logging (time per item, total time) in src/services/audio/audio_generator.py
- [X] T058 [P] Add character count estimation and logging in src/services/audio/audio_generator.py
- [X] T059 Run full test suite: pytest tests/unit/services/audio/ tests/integration/test_newsletter_audio_workflow.py --cov=src/services/audio
- [X] T060 Manual validation using quickstart.md steps (test with real ElevenLabs API in dev environment)
- [X] T061 Verify constitution compliance: Strong typing (no Any, no plain dict), all tests pass, code quality gates pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1: Can start after Foundational (Phase 2) - No dependencies on other stories
  - User Story 2: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable
  - User Story 3: Can start after Foundational (Phase 2) - Enhances US1 parser but independently testable
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (core audio generation)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates US1 into newsletter workflow
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 parser with header extraction

### Within Each User Story

**TDD Workflow**:
1. Tests MUST be written FIRST (marked with ⚠️)
2. Run tests and verify they FAIL
3. Implement functionality
4. Run tests and verify they PASS
5. Refactor if needed
6. Commit

**Task Order**:
- Tests before implementation
- Models before services
- Services before integration
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup (Phase 1)**: T002, T003, T004 can run in parallel
- **Foundational (Phase 2)**: T006-T010 can run in parallel after T005
- **User Story 1 Tests**: T011-T021 can all run in parallel (write all tests first)
- **User Story 1 Implementation**: T022, T023, T026 can run in parallel
- **User Story 2 Tests**: T032-T034 can run in parallel
- **User Story 3 Tests**: T041-T044 can run in parallel
- **Polish**: T053-T058 can run in parallel

**Note**: Once Foundational phase completes, all three user stories could be developed in parallel by different developers (if team capacity allows)

---

## Parallel Example: User Story 1

```bash
# Phase 1: Write all tests first (in parallel):
Task: "Write test_parse_newsletter_items in tests/unit/services/audio/test_markdown_parser.py"
Task: "Write test_parse_empty_newsletter in tests/unit/services/audio/test_markdown_parser.py"
Task: "Write test_parse_newsletter_excludes_metadata in tests/unit/services/audio/test_markdown_parser.py"
Task: "Write test_convert_to_speech_success with mocked ElevenLabs client in tests/unit/services/audio/test_tts_service.py"
# ... (all test tasks T011-T021)

# Phase 2: Verify tests fail
Run: pytest tests/unit/services/audio/ (expect failures)

# Phase 3: Implement in parallel where possible:
Task: "Implement parse_newsletter_items() function in src/services/audio/markdown_parser.py"
Task: "Implement ElevenLabsTTSService.__init__() in src/services/audio/tts_service.py"
Task: "Implement concatenate_audio_segments() helper function in src/services/audio/audio_generator.py"

# Phase 4: Sequential implementation for dependent tasks:
Task: "Implement ElevenLabsTTSService.convert_to_speech() in src/services/audio/tts_service.py"
Task: "Implement generate_audio_for_newsletter() function in src/services/audio/audio_generator.py"

# Phase 5: Verify tests pass
Run: pytest tests/unit/services/audio/ (expect success)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010) - CRITICAL blocking phase
3. Complete Phase 3: User Story 1 (T011-T031)
   - Write all tests first (T011-T021)
   - Verify tests fail
   - Implement functionality (T022-T030)
   - Verify tests pass (T031)
4. **STOP and VALIDATE**: Test User Story 1 independently with real newsletter markdown files
5. Deploy/demo if ready - users can now generate audio for existing newsletters

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
   - Users can manually generate audio for any newsletter markdown file
3. Add User Story 2 → Test independently → Deploy/Demo
   - Audio now automatically generated with every newsletter
4. Add User Story 3 → Test independently → Deploy/Demo
   - Audio now includes structural context (headers)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (critical path)
2. Once Foundational is done:
   - Developer A: User Story 1 (core audio generation)
   - Developer B: User Story 2 (integration with newsletter workflow)
   - Developer C: User Story 3 (header enhancement)
3. Stories complete and integrate independently
4. Note: US2 and US3 both modify the parser, so coordinate merge conflicts

---

## Task Summary

**Total Tasks**: 61

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 6 tasks
- Phase 3 (User Story 1): 22 tasks (11 tests + 11 implementation) - includes metadata exclusion
- Phase 4 (User Story 2): 9 tasks (3 tests + 6 implementation)
- Phase 5 (User Story 3): 10 tasks (4 tests + 6 implementation) - content-only audio
- Phase 6 (Polish): 9 tasks

**Parallel Opportunities Identified**: 32 tasks marked [P]

**Independent Test Criteria**:
- **US1**: Generate audio from existing markdown → verify MP3 with alternating voices
- **US2**: Generate newsletter via UI → verify automatic audio creation
- **US3**: Generate audio → verify spoken headers match markdown structure

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = 30 tasks

**Constitution Compliance Checkpoints**:
- T010: Custom exceptions (strong typing)
- T031: All US1 tests pass (TDD + test isolation)
- T039: All US2 tests pass (TDD + test isolation)
- T051: All US3 tests pass (TDD + test isolation)
- T053: mypy type checking (strong typing enforcement)
- T054: ruff linting (code quality gates)
- T059: Full test coverage (test isolation + TDD)
- T061: Final constitution validation

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD REQUIRED: Write tests first, verify they fail, then implement
- All ElevenLabs API calls MUST be mocked in tests (no remote API calls)
- Verify tests fail before implementing (red-green-refactor)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow quickstart.md for setup and troubleshooting guidance
