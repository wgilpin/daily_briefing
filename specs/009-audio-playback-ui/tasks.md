# Tasks: Audio Playback UI Controls

**Input**: Design documents from `/specs/009-audio-playback-ui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Backend TDD required per constitution - tests MUST be written first for all Flask routes

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project structure (existing Flask app):
- Backend: `src/web/`, `src/models/`
- Frontend: `src/web/templates/`
- Tests: `tests/unit/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization - add Alpine.js and prepare audio file access

- [ ] T001 Add Alpine.js CDN script to src/web/templates/base.html
- [ ] T002 [P] Verify audio files exist in data/audio_cache/ directory (smoke test)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Per constitution, all backend code requires TDD.

### Tests (Write FIRST, ensure they FAIL)

- [ ] T003 [P] Write failing unit test for HTTP 200 full file response in tests/unit/web/test_audio_routes.py
- [ ] T004 [P] Write failing unit test for HTTP 206 range request handling in tests/unit/web/test_audio_routes.py
- [ ] T005 [P] Write failing unit test for HTTP 401 authentication failure in tests/unit/web/test_audio_routes.py
- [ ] T006 [P] Write failing unit test for HTTP 404 missing file in tests/unit/web/test_audio_routes.py
- [ ] T007 [P] Write failing unit test for HTTP 400 invalid item_id (path traversal) in tests/unit/web/test_audio_routes.py
- [ ] T008 [P] Write failing unit test for HTTP 416 out-of-range request in tests/unit/web/test_audio_routes.py
- [ ] T009 [P] Write failing unit test for cache headers (immutable, max-age) in tests/unit/web/test_audio_routes.py
- [ ] T010 [P] Write failing unit test for Accept-Ranges header in tests/unit/web/test_audio_routes.py

### Implementation (Make tests PASS)

- [ ] T011 Create Flask blueprint for audio serving in src/web/audio_routes.py
- [ ] T012 Implement serve_audio() route with HTTP 200 full file support in src/web/audio_routes.py
- [ ] T013 Add HTTP 206 partial content logic (range header parsing) in src/web/audio_routes.py
- [ ] T014 Add authentication check (@login_required) in src/web/audio_routes.py
- [ ] T015 Add input validation (item_id format, path traversal prevention) in src/web/audio_routes.py
- [ ] T016 Add cache headers (Cache-Control: immutable, max-age=31536000) in src/web/audio_routes.py
- [ ] T017 Register audio blueprint in src/web/app.py
- [ ] T018 Run pytest to verify all foundational tests pass

### Model Extension

- [ ] T019 [P] Write failing unit test for has_audio computed property in tests/unit/models/test_feed_models.py
- [ ] T020 [P] Write failing unit test for audio_path computed property in tests/unit/models/test_feed_models.py
- [ ] T021 Add has_audio @computed_field to FeedItem model in src/models/feed_models.py
- [ ] T022 Add audio_path @computed_field to FeedItem model in src/models/feed_models.py
- [ ] T023 Implement batch file existence check in repository layer (performance optimization) in src/db/repository.py
- [ ] T024 Run pytest to verify model tests pass

**Checkpoint**: Foundation ready - backend audio serving fully functional with TDD coverage. User story UI work can now begin in parallel.

---

## Phase 3: User Story 1 - Basic Audio Playback (Priority: P1) 🎯 MVP

**Goal**: Users can play and pause audio for feed items with global player controls

**Independent Test**: Click play button on any feed item → audio plays, global player shows "Pause", item highlighted. Click pause → audio stops, button shows "Play". Resume playback works from same position.

### Implementation for User Story 1

- [ ] T025 [P] [US1] Create global audio player bar HTML with hx-preserve in src/web/templates/feed.html
- [ ] T026 [P] [US1] Implement Alpine.js audioPlayerState() component in src/web/templates/feed.html
- [ ] T027 [P] [US1] Add play icon button to feed item template in src/web/templates/partials/feed_item.html
- [ ] T028 [P] [US1] Add data-item-id and data-audio-path attributes to feed items in src/web/templates/partials/feed_item.html
- [ ] T029 [US1] Wire up playItem() method in Alpine component (click handler for per-item play buttons) in src/web/templates/feed.html
- [ ] T030 [US1] Implement playPause() method in Alpine component in src/web/templates/feed.html
- [ ] T031 [US1] Add audio event listeners (play, pause, ended) in Alpine component in src/web/templates/feed.html
- [ ] T032 [US1] Add HTMX beforeSwap listener to stop audio on filter changes in src/web/templates/feed.html
- [ ] T033 [P] [US1] Add CSS for global player bar styling in src/web/templates/feed.html
- [ ] T034 [P] [US1] Add CSS for item play button styling in src/web/templates/feed.html
- [ ] T035 [P] [US1] Add CSS for .playing class (item highlight) in src/web/templates/feed.html
- [ ] T036 [P] [US1] Add ARIA labels for accessibility (play/pause button, now playing status) in src/web/templates/feed.html
- [ ] T037 [P] [US1] Add focus indicators for keyboard navigation in src/web/templates/feed.html
- [ ] T038 [US1] Update feed rendering to include has_audio in template context in src/web/feed_routes.py
- [ ] T039 [US1] Test User Story 1: Play audio from item → verify playback, highlight, global controls work

**Checkpoint**: At this point, User Story 1 should be fully functional - users can play/pause audio from feed items with visual feedback. This is the MVP.

---

## Phase 4: User Story 2 - Sequential Navigation (Priority: P2)

**Goal**: Users can navigate between feed items using Next/Previous buttons

**Independent Test**: Start playing any item → click Next → next item plays automatically. Click Previous → previous item plays. Boundary conditions (first/last item) handled correctly with disabled buttons.

### Implementation for User Story 2

- [ ] T040 [US2] Implement next() method in Alpine component in src/web/templates/feed.html
- [ ] T041 [US2] Implement previous() method in Alpine component in src/web/templates/feed.html
- [ ] T042 [US2] Add boundary condition logic (disable Next at last item) in src/web/templates/feed.html
- [ ] T043 [US2] Add boundary condition logic (disable Previous at first item) in src/web/templates/feed.html
- [ ] T044 [US2] Add button enable/disable logic based on currentIndex in src/web/templates/feed.html
- [ ] T045 [US2] Add visual feedback for disabled buttons (opacity, cursor) in src/web/templates/feed.html
- [ ] T046 [US2] Test User Story 2: Navigate with Next/Previous → verify sequential playback and boundary handling

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can play audio and navigate between items.

---

## Phase 5: User Story 3 - Auto-Scroll to Playing Item (Priority: P3)

**Goal**: Page automatically scrolls to keep playing item visible at top

**Independent Test**: Scroll down feed to off-screen items → click play on an item → page smoothly scrolls to bring item to top. Navigate to next item → scrolls to show new playing item.

### Implementation for User Story 3

- [ ] T047 [P] [US3] Add scrollIntoView() call in playItem() method in src/web/templates/feed.html
- [ ] T048 [P] [US3] Add CSS scroll-behavior: smooth to html element in src/web/templates/feed.html
- [ ] T049 [P] [US3] Add prefers-reduced-motion media query for accessibility in src/web/templates/feed.html
- [ ] T050 [US3] Test auto-scroll on playback start in src/web/templates/feed.html
- [ ] T051 [US3] Test auto-scroll on Next/Previous navigation in src/web/templates/feed.html
- [ ] T052 [US3] Test User Story 3: Verify smooth scroll to playing item works for off-screen items

**Checkpoint**: All user stories should now be independently functional. Complete audio playback experience with visual following.

---

## Phase 6: Keyboard Shortcuts & Accessibility (Cross-Story Enhancement)

**Goal**: Keyboard shortcuts (Space, N, P) and full WCAG 2.1 Level AA compliance

**Why separate phase**: This enhances all user stories but isn't blocking for basic functionality

### Implementation

- [ ] T053 [P] Add document-level keydown event listener in src/web/templates/feed.html
- [ ] T054 [P] Implement Space key handler (play/pause toggle) in src/web/templates/feed.html
- [ ] T055 [P] Implement N key handler (next item) in src/web/templates/feed.html
- [ ] T056 [P] Implement P key handler (previous item) in src/web/templates/feed.html
- [ ] T057 [P] Add input field focus check (prevent shortcuts when typing) in src/web/templates/feed.html
- [ ] T058 [P] Add Arrow Left/Right handlers for seek (5 second jumps) in src/web/templates/feed.html
- [ ] T059 Test keyboard-only navigation (no mouse)
- [ ] T060 Test with screen reader (NVDA or JAWS)
- [ ] T061 Run Lighthouse accessibility audit (target >= 90 score)

---

## Phase 7: Integration Testing & Polish

**Purpose**: End-to-end validation and cross-cutting improvements

### Integration Tests

- [ ] T062 [P] Write integration test for feed rendering with audio metadata in tests/integration/test_feed_audio.py
- [ ] T063 [P] Write integration test for audio route with mocked file system in tests/integration/test_feed_audio.py
- [ ] T064 [P] Write integration test for boundary conditions (first/last item) in tests/integration/test_feed_audio.py
- [ ] T065 [P] Write integration test for filter change stops playback in tests/integration/test_feed_audio.py
- [ ] T066 Run full pytest suite and verify all tests pass

### Manual Testing Checklist

- [ ] T067 Manual test: Click play on item with audio → audio plays
- [ ] T068 Manual test: Click pause → audio stops
- [ ] T069 Manual test: Resume paused audio → continues from same position
- [ ] T070 Manual test: Click next → plays next item's audio
- [ ] T071 Manual test: Click previous → plays previous item's audio
- [ ] T072 Manual test: Next on last item → stops playback, disables button
- [ ] T073 Manual test: Previous on first item → stops playback, disables button
- [ ] T074 Manual test: Change filter while playing → audio stops
- [ ] T075 Manual test: Search while playing → audio stops
- [ ] T076 Manual test: Playing item is visually highlighted
- [ ] T077 Manual test: Page scrolls to playing item
- [ ] T078 Manual test: Press spacebar → toggles play/pause
- [ ] T079 Manual test: Press N → plays next item
- [ ] T080 Manual test: Press P → plays previous item
- [ ] T081 Manual test: Items without audio don't show play button

### Browser Compatibility

- [ ] T082 [P] Test in Chrome (latest)
- [ ] T083 [P] Test in Firefox (latest)
- [ ] T084 [P] Test in Safari (latest)
- [ ] T085 [P] Test in Edge (latest)
- [ ] T086 [P] Test in Mobile Safari (iOS)
- [ ] T087 [P] Test in Mobile Chrome (Android)

### Performance & Security Verification

- [ ] T088 Verify /audio/<id> returns Accept-Ranges: bytes header in DevTools
- [ ] T089 Verify HTTP 206 responses when seeking in DevTools Network tab
- [ ] T090 Verify Cache-Control headers (max-age=31536000, immutable) in DevTools
- [ ] T091 Verify authentication required for /audio/<id> route
- [ ] T092 Verify path traversal attacks blocked (try /audio/../../etc/passwd)
- [ ] T093 Verify audio playback starts in under 2 seconds
- [ ] T094 Verify page scroll completes in under 500ms
- [ ] T095 Verify Next/Previous navigation completes in under 1 second

### Code Quality

- [ ] T096 Run ruff check on all Python files and fix any issues
- [ ] T097 Run mypy on all Python files and verify no type errors
- [ ] T098 Review Alpine.js code for any console errors
- [ ] T099 Verify no unused imports or variables
- [ ] T100 Run quickstart.md validation (follow step-by-step guide)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational - No dependencies on User Story 1 (shares same Alpine component)
  - User Story 3 (P3): Can start after Foundational - No dependencies on other stories (just adds scroll behavior)
- **Keyboard Shortcuts (Phase 6)**: Can start after any user story is complete (enhances all stories)
- **Integration Testing (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - FULLY INDEPENDENT
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - FULLY INDEPENDENT (extends same Alpine component)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - FULLY INDEPENDENT (just adds CSS + one line of code)

**Key Insight**: All three user stories are highly independent. US2 and US3 add incremental enhancements to the same Alpine component created in US1, but each can be tested independently.

### Within Each User Story

- Tests (Foundational phase) MUST be written and FAIL before implementation
- Models/routes before frontend components
- Alpine component structure before specific methods
- Core playback before navigation enhancements
- Basic functionality before accessibility polish

### Parallel Opportunities

**Phase 1 (Setup)**:
- Both tasks can run in parallel

**Phase 2 (Foundational) - Tests**:
- ALL test-writing tasks (T003-T010) can run in parallel - different test functions
- Model tests (T019-T020) can run in parallel - different test functions

**Phase 2 (Foundational) - Models**:
- T021-T022 can run in parallel - different @computed_field properties

**Phase 3 (User Story 1)**:
- T025, T026, T027 can run in parallel - different files/sections
- T033, T034, T035 can run in parallel - independent CSS rules
- T036, T037 can run in parallel - different HTML attributes

**Phase 5 (User Story 3)**:
- T047, T048, T049 can run in parallel - independent changes

**Phase 6 (Keyboard Shortcuts)**:
- T053-T058 can run in parallel - independent key handlers

**Phase 7 (Integration Tests)**:
- T062-T065 can run in parallel - different test functions
- T082-T087 can run in parallel - different browsers

---

## Parallel Example: User Story 1

```bash
# Launch all CSS styling tasks together:
Task: "Add CSS for global player bar styling in src/web/templates/feed.html"
Task: "Add CSS for item play button styling in src/web/templates/feed.html"
Task: "Add CSS for .playing class (item highlight) in src/web/templates/feed.html"

# Launch all accessibility tasks together:
Task: "Add ARIA labels for accessibility (play/pause button, now playing status) in src/web/templates/feed.html"
Task: "Add focus indicators for keyboard navigation in src/web/templates/feed.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (2 tasks)
2. Complete Phase 2: Foundational (24 tasks - CRITICAL TDD foundation)
3. Complete Phase 3: User Story 1 (15 tasks)
4. **STOP and VALIDATE**: Test User Story 1 independently (T039)
5. Deploy/demo if ready - users can now play/pause audio!

**Total MVP**: 41 tasks to functional audio playback

### Incremental Delivery

1. Complete Setup + Foundational → Backend ready (26 tasks)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - 41 tasks total)
3. Add User Story 2 → Test independently → Deploy/Demo (48 tasks total - adds navigation)
4. Add User Story 3 → Test independently → Deploy/Demo (54 tasks total - adds auto-scroll)
5. Add Keyboard Shortcuts → Full experience (61 tasks total)
6. Run Integration Tests & Polish → Production ready (100 tasks total)

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (26 tasks)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (15 tasks)
   - **Developer B**: User Story 2 (7 tasks - can start immediately, same file)
   - **Developer C**: User Story 3 (6 tasks - can start immediately)
3. Stories complete independently, then merge
4. Together: Keyboard Shortcuts + Integration Testing

**Warning**: US1, US2, US3 all modify the same file (feed.html Alpine component). While they're logically independent, parallel work will require careful merge coordination. Consider completing US1 first, then US2 and US3 in parallel.

---

## Notes

- **[P] tasks** = different files or independent sections, safe to parallelize
- **[Story] label** maps task to specific user story for traceability
- **TDD required**: All backend tasks (Foundational phase) follow Red-Green-Refactor
- Each user story should be independently completable and testable
- Verify backend tests fail before implementing (Phase 2)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Total tasks**: 100 (26 foundational + 15 US1 + 7 US2 + 6 US3 + 8 keyboard + 38 testing/polish)
- **MVP minimum**: 41 tasks (Setup + Foundational + US1)
- **Full feature**: 100 tasks for production-ready implementation with full test coverage
