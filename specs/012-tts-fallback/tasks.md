# Tasks: TTS Provider Fallback

**Input**: Design documents from `/specs/012-tts-fallback/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included per constitution Principle III (Backend TDD required for services and business logic).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Move Kokoro/soundfile to optional extras so the Coolify build is unblocked immediately. This is the single highest-priority change.

- [ ] T001 Move `kokoro>=0.9.4` and `soundfile>=0.13.1` from `[project.dependencies]` to `[project.optional-dependencies]` group `kokoro` in `pyproject.toml`
- [ ] T002 Add `elevenlabs` SDK to `[project.dependencies]` in `pyproject.toml` (always installed, required for fallback)
- [ ] T003 Verify `uv sync` (no extras) installs cleanly without kokoro/soundfile errors

**Checkpoint**: `uv sync` succeeds. Coolify prod build is unblocked.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model and interface changes that all three user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add `provider_used: str` field to `AudioGenerationResult` in `src/models/audio_models.py`
- [ ] T005 Add `ElevenLabsConfig` Pydantic model with `api_key`, `male_voice_id`, `female_voice_id` fields (loaded from env vars `ELEVENLABS_API_KEY`, `ELEVENLABS_MALE_VOICE_ID`, `ELEVENLABS_FEMALE_VOICE_ID`) and `from_env()` classmethod in `src/models/audio_models.py`
- [ ] T006 Add `TTSProvider` Protocol class with `convert_to_speech(request: TTSRequest) -> AudioSegment` method and `provider_name: str` property to `src/services/audio/tts_service.py`
- [ ] T007 Add `ElevenLabsTTSError` to the exception hierarchy in `src/services/audio/__init__.py`

**Checkpoint**: Models and interface defined. No audio generation logic changed yet — existing Kokoro path still works.

---

## Phase 3: User Story 1 - Audio Generation Works on Any Environment (Priority: P1) 🎯 MVP

**Goal**: System automatically uses Kokoro if available, falls back to ElevenLabs if not. Audio generation succeeds in both cases.

**Independent Test**: Run with Kokoro installed → audio generates via Kokoro. Uninstall kokoro extra (`uv sync` without `--extra kokoro`) → audio generates via ElevenLabs.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Write failing unit test: factory returns `KokoroTTSService` when kokoro is importable in `tests/unit/services/audio/test_tts_service.py`
- [ ] T009 [P] [US1] Write failing unit test: factory returns `ElevenLabsTTSService` when kokoro raises `ImportError` in `tests/unit/services/audio/test_tts_service.py`
- [ ] T010 [P] [US1] Write failing unit test: `ElevenLabsTTSService.convert_to_speech()` calls ElevenLabs API and returns `AudioSegment` in `tests/unit/services/audio/test_elevenlabs_service.py`
- [ ] T011 [P] [US1] Write failing unit test: `audio_generator.py` populates `AudioGenerationResult.provider_used` from selected provider in `tests/unit/services/audio/test_audio_generator.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `ElevenLabsTTSService` in `src/services/audio/elevenlabs_service.py`: `convert_to_speech()` calls ElevenLabs API, converts MP3 response to WAV via ffmpeg, returns `AudioSegment`; `provider_name` returns `"ElevenLabs"` (depends on T005, T006, T007)
- [ ] T013 [US1] Add `provider_name` property returning `"Kokoro"` to `KokoroTTSService` in `src/services/audio/tts_service.py` so it satisfies `TTSProvider` protocol (depends on T006)
- [ ] T014 [US1] Implement `get_tts_provider(config: AudioConfig) -> TTSProvider` factory in `src/services/audio/tts_service.py`: try `import kokoro`, return `KokoroTTSService` on success, `ElevenLabsTTSService` on `ImportError` (depends on T012, T013)
- [ ] T015 [US1] Replace direct `KokoroTTSService` instantiation in `src/services/audio/audio_generator.py` with `get_tts_provider()` call; populate `result.provider_used` from `provider.provider_name` (depends on T004, T014)
- [ ] T016 [US1] Add log line `"TTS provider: {provider_name}"` inside `get_tts_provider()` in `src/services/audio/tts_service.py` immediately after provider is selected (depends on T015)

**Checkpoint**: Audio generation succeeds with or without Kokoro installed. `provider_used` is populated on every result. Tests pass.

---

## Phase 4: User Story 2 - Development Environment Uses Kokoro with espeak-ng (Priority: P2)

**Goal**: Dev machines with Kokoro + espeak-ng use Kokoro automatically; those without fall back to ElevenLabs. No manual switching.

**Independent Test**: On dev machine with `uv sync --extra kokoro` and espeak-ng installed, trigger audio generation — confirm logs show `"TTS provider: Kokoro"`. Run `uv sync` (no extras), trigger again — confirm `"TTS provider: ElevenLabs"`.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US2] Write failing unit test: when kokoro import succeeds but `KPipeline` raises an exception (simulating broken espeak-ng), factory falls back to `ElevenLabsTTSService` in `tests/unit/services/audio/test_tts_service.py`
- [ ] T018 [P] [US2] Write failing unit test: `ElevenLabsConfig.from_env()` raises `ValueError` when `ELEVENLABS_API_KEY` is missing in `tests/unit/services/audio/test_elevenlabs_service.py`

### Implementation for User Story 2

- [ ] T019 [US2] Extend `get_tts_provider()` factory in `src/services/audio/tts_service.py` to catch `Exception` from `KokoroTTSService.__init__()` (e.g. broken espeak-ng) and fall back to `ElevenLabsTTSService` with a warning log (depends on T014)
- [ ] T019a [US2] In `get_tts_provider()`, if `ElevenLabsConfig.from_env()` raises `ValueError` (missing API key) after Kokoro also failed, raise `TTSError` with message naming both missing providers (e.g. "No TTS provider available: Kokoro not installed, ELEVENLABS_API_KEY not set") in `src/services/audio/tts_service.py`
- [ ] T020 [US2] Update `quickstart.md` in `specs/012-tts-fallback/quickstart.md` with dev setup instructions (`uv sync --extra kokoro`, espeak-ng OS install)

**Checkpoint**: Broken Kokoro installation falls back to ElevenLabs gracefully. Tests pass.

---

## Phase 5: User Story 3 - Hetzner Cloud Deployment Uses ElevenLabs Only (Priority: P2)

**Goal**: Production Coolify build (`uv sync`, no extras) installs without Kokoro/soundfile and uses ElevenLabs exclusively.

**Independent Test**: Run `uv sync` (no extras) in a clean environment → confirm `kokoro` and `soundfile` are not installed → trigger audio generation → confirm `"TTS provider: ElevenLabs"` in logs with no Kokoro-related errors.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [US3] Write failing unit test: `get_tts_provider()` returns `ElevenLabsTTSService` when kokoro module is absent from sys.modules (simulate prod environment) in `tests/unit/services/audio/test_tts_service.py`

### Implementation for User Story 3

- [ ] T022 [US3] Verify `Dockerfile` build command uses `uv sync` without `--extra kokoro` — update if needed so prod image never installs Kokoro deps in `Dockerfile`
- [ ] T023 [US3] Verify `docker-compose.yml` includes `ELEVENLABS_API_KEY` in environment variables section — add if missing in `docker-compose.yml`
- [ ] T024 [US3] Add `ELEVENLABS_MALE_VOICE_ID` and `ELEVENLABS_FEMALE_VOICE_ID` to `docker-compose.yml` environment section with documented defaults in `docker-compose.yml`

**Checkpoint**: `docker build` succeeds without Kokoro. Container runs and uses ElevenLabs. Tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: UI status message and final validation across all stories.

- [ ] T025 [P] Add `provider_used` value to the audio generation status area in the relevant UI template (`src/web/templates/feed.html` or appropriate partial) — display `"Generating with {provider_used}"` during generation
- [ ] T026 [P] Run `ruff check --fix` across all modified files (`src/models/audio_models.py`, `src/services/audio/tts_service.py`, `src/services/audio/elevenlabs_service.py`, `src/services/audio/audio_generator.py`)
- [ ] T027 [P] Run `mypy` on all modified files and resolve any type errors
- [ ] T028 Run full test suite `pytest tests/unit/services/audio/` and confirm all tests pass
- [ ] T029 Validate quickstart.md scenarios manually: dev path (with kokoro extra) and prod path (without extras)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; unblocks Coolify build
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user story phases
- **US1 (Phase 3)**: Depends on Phase 2 — implement and validate before US2/US3
- **US2 (Phase 4)**: Depends on Phase 3 (needs factory from T014, T019 extends it)
- **US3 (Phase 5)**: Depends on Phase 3 (T014 `get_tts_provider()` must exist) — can run in parallel with US2 once Phase 3 is complete
- **Polish (Phase 6)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — implement first, core fallback logic
- **US2 (P2)**: Depends on US1 (extends factory error handling) — implement second
- **US3 (P2)**: Depends on US1 (T014 factory must exist) — can proceed in parallel with US2 once Phase 3 is complete

### Within Each Phase

- Tests (T008–T011, T017–T018, T021) MUST be written and confirmed FAILING before implementation tasks
- T005 (ElevenLabsConfig) must complete before T012 (ElevenLabsTTSService)
- T006 (TTSProvider protocol) must complete before T013 and T014
- T014 (factory) must complete before T015 (audio_generator wiring)

### Parallel Opportunities

- T008, T009, T010, T011 — all test stubs, parallel within Phase 3
- T017, T018 — test stubs, parallel within Phase 4
- T022, T023, T024 — different files, parallel within Phase 5
- T025, T026, T027 — different concerns, parallel within Phase 6

---

## Parallel Example: User Story 1

```bash
# Write all failing tests in parallel (Phase 3):
Task: T008 - factory Kokoro test in test_tts_service.py
Task: T009 - factory ElevenLabs fallback test in test_tts_service.py
Task: T010 - ElevenLabsTTSService test in test_elevenlabs_service.py
Task: T011 - audio_generator provider_used test in test_audio_generator.py

# Then implement sequentially:
T012 → T013 → T014 → T015 → T016
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Move deps to optional extras — **immediate Coolify fix**
2. Complete Phase 2: Models + interface — no behaviour change yet
3. Complete Phase 3: Factory + ElevenLabs service + generator wiring
4. **STOP and VALIDATE**: Audio works with and without Kokoro
5. Deploy — production build now works

### Incremental Delivery

1. Phase 1 → Coolify build unblocked immediately
2. Phase 1 + 2 + 3 → MVP: auto-detection working end-to-end
3. Phase 4 → Broken Kokoro handled gracefully
4. Phase 5 → Production deployment verified
5. Phase 6 → UI message + quality gates

---

## Notes

- [P] tasks = different files, no dependencies between them
- [Story] label maps task to specific user story for traceability
- Constitution III (TDD): tests are written FIRST and must fail before implementation
- Constitution IV: ElevenLabs API must be mocked in all tests — no real API calls
- T001 is the single most impactful task: it immediately unblocks the Coolify build
- `ElevenLabsTTSService` must output WAV-format `AudioSegment` (not MP3) so `audio_generator.py` needs no branching logic
