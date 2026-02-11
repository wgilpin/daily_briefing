# Tasks: Senders Database Migration

**Input**: Design documents from `/specs/013-senders-db-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Tests**: Included — constitution requires TDD for backend services and business logic.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and apply DB schema before any code changes.

- [X] T001 Apply DB migration `src/db/migrations/004_senders_config.sql` — create `senders` and `newsletter_config` tables (SQL file contents: see data-model.md)
- [X] T002 Create `src/newsletter/migration.py` as empty module with placeholder `migrate_senders_if_needed(config_path: Path) -> None`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repository methods that all user stories depend on. Must be complete before Phase 3+.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

> **TDD**: Write tests first, verify they fail, then implement.

### Tests (write first, verify they fail)

- [X] T003 [P] Write failing unit tests for `Repository.get_all_senders`, `get_sender`, `add_sender`, `update_sender`, `delete_sender`, `sender_exists` in `tests/unit/test_sender_repository.py` — mock `get_connection`
- [X] T004 [P] Write failing unit tests for `Repository.get_newsletter_config`, `get_config_value`, `set_config_value`, `set_config_values`, `config_key_exists` in `tests/unit/test_sender_repository.py`

### Implementation

- [X] T005 Add `SenderRecord` Pydantic model and `NewsletterConfigValues` TypedDict to `src/models/newsletter_models.py`: `SenderRecord` fields: `email: str`, `display_name: str | None`, `parsing_prompt: str`, `enabled: bool`, `created_at: datetime | None`; `NewsletterConfigValues` fields: `consolidation_prompt: str`, `retention_limit: int`, `days_lookback: int`, `max_workers: int`, `default_parsing_prompt: str`, `default_consolidation_prompt: str`, `models: dict[str, str]`, `excluded_topics: list[str]`
- [X] T006 Add sender CRUD methods to `Repository` class in `src/db/repository.py`: `get_all_senders() -> list[SenderRecord]`, `get_sender(email: str) -> SenderRecord | None`, `add_sender(sender: SenderRecord) -> None`, `update_sender(sender: SenderRecord) -> None`, `update_sender_display_name(email: str, display_name: str | None) -> None`, `delete_sender(email: str) -> None`, `sender_exists(email: str) -> bool`
- [X] T007 Add newsletter config methods to `Repository` class in `src/db/repository.py`: `get_newsletter_config() -> NewsletterConfigValues`, `get_config_value(key: str) -> str | None`, `set_config_value(key: str, value: str) -> None`, `set_config_values(values: dict[str, str]) -> None`, `config_key_exists(key: str) -> bool` — deserialise int and JSON fields inside `get_newsletter_config` (return typed `NewsletterConfigValues`, not `dict`)
- [X] T008 Run tests T003/T004 — verify they now pass

**Checkpoint**: Repository methods complete and tested. User story phases can now begin.

---

## Phase 3: User Story 1 — Sender Configuration Persists in Database (Priority: P1) 🎯 MVP

**Goal**: Replace file-based sender read/write in `config.py` and web routes with Repository calls. App loads senders from DB on startup; all CRUD operations persist to DB.

**Independent Test**: Add a sender via the UI, restart the app, verify it reappears with correct fields.

### Tests (write first, verify they fail)

- [X] T009 [P] [US1] Write failing unit tests for updated `load_senders_config()` and `save_senders_config()` in `tests/unit/test_newsletter_config.py` — assert they call Repository methods, not file I/O
- [X] T010 [P] [US1] Write failing unit tests for `api_settings_newsletter_sender`, `api_settings_update_display_name`, `api_settings_delete_sender` route handlers in `tests/unit/test_feed_routes_senders.py` — assert Repository methods called; mock Repository

### Implementation

- [X] T011 [US1] Update `load_senders_config(config_path)` in `src/newsletter/config.py` to call `Repository.get_all_senders()` and return `dict[str, SenderRecord]` keyed by email — remove file read; update callers that previously expected `dict[str, dict]` to use `SenderRecord` attributes
- [X] T012 [US1] Update `save_senders_config(senders, config_path)` in `src/newsletter/config.py` to call `Repository.add_sender` / `update_sender` as appropriate — remove file write
- [X] T013 [US1] Update `api_settings_newsletter_sender()` in `src/web/feed_routes.py` to call `Repository.add_sender()` instead of `save_senders_config()`
- [X] T014 [US1] Update `api_settings_update_display_name()` in `src/web/feed_routes.py` to call `Repository.update_sender_display_name()` instead of file save
- [X] T015 [US1] Update `api_settings_delete_sender(email)` in `src/web/feed_routes.py` to call `Repository.delete_sender()` instead of file save
- [X] T016 [US1] Update `get_sender_display_name(sender_email)` in `src/newsletter/sender_names.py` to call `Repository.get_sender()` instead of reading senders.json
- [X] T017 [US1] Run tests T009/T010 — verify they now pass

**Checkpoint**: Sender CRUD fully persists to DB. US1 independently testable.

---

## Phase 4: User Story 2 — Global Configuration Persists in Database (Priority: P2)

**Goal**: Replace file-based global settings read/write with `newsletter_config` DB table calls. App loads global config from DB on startup.

**Independent Test**: Change `retention_limit` via the UI, restart the app, verify it is retained.

### Tests (write first, verify they fail)

- [X] T018 [P] [US2] Write failing unit tests for updated `load_config()` and `save_config()` in `tests/unit/test_newsletter_config.py` — assert they call `Repository.get_newsletter_config` / `set_config_values`, not file I/O

### Implementation

- [X] T019 [US2] Update `load_config(path)` in `src/newsletter/config.py` to call `Repository.get_newsletter_config()` — deserialisation (int/JSON fields) is handled inside `Repository.get_newsletter_config()` (returns `NewsletterConfigValues`) — remove file read
- [X] T020 [US2] Update `save_config(config, path)` in `src/newsletter/config.py` to serialise `NewsletterConfig` fields to strings and call `Repository.set_config_values()` — remove file write
- [X] T020a [US2] Update `list_exclusions()`, `add_exclusion()`, and `delete_exclusion()` routes in `src/web/feed_routes.py` — these call `load_config`/`save_config` for `excluded_topics`; replace with direct `Repository.get_config_value('excluded_topics')` / `Repository.set_config_value('excluded_topics', ...)` calls (confirmed routes exist at lines 897, 950, and ~1040)
- [X] T021 [US2] Run tests T018 — verify they now pass

**Checkpoint**: Global config persists to DB. US2 independently testable alongside US1.

---

## Phase 5: User Story 3 — Migration from Existing File (Priority: P3)

**Goal**: On startup, if `config/senders.json` exists, migrate its contents to the DB (DB wins on conflict), then rename the file to `senders.json.bak`. Malformed JSON aborts startup.

**Independent Test**: Start app with an existing `senders.json`; verify senders and global config appear in DB; verify file renamed to `.bak`.

### Tests (write first, verify they fail)

- [X] T022 [P] [US3] Write failing unit tests for `migrate_senders_if_needed()` in `tests/unit/test_senders_migration.py` covering: file absent (no-op), valid file with no DB records (all inserted, file renamed), valid file with existing DB records (skipped, file renamed), malformed JSON (RuntimeError raised, file not renamed), duplicate email (DB record kept unchanged)

### Implementation

- [X] T023 [US3] Implement `migrate_senders_if_needed(config_path: Path) -> None` in `src/newsletter/migration.py`:
  - If `config_path` does not exist: return immediately
  - Parse JSON; raise `RuntimeError` with message on `json.JSONDecodeError`
  - For each email in `senders` dict: call `Repository.sender_exists()`; if False call `Repository.add_sender()`
  - For each global key (excluding `senders`): call `Repository.config_key_exists()`; if False call `Repository.set_config_value()` (serialise to str)
  - Rename `config_path` to `config_path.parent / (config_path.name + '.bak')`
- [X] T024 [US3] Call `migrate_senders_if_needed(Path(__file__).parent.parent.parent / 'config' / 'senders.json')` in `src/web/app.py` immediately after `initialize_pool()` — use absolute path derived from `__file__` to avoid working-directory sensitivity; wrap in try/except RuntimeError to log and re-raise (aborts startup)
- [X] T025 [US3] Run tests T022 — verify they now pass

**Checkpoint**: All three user stories complete and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Remove now-unused file I/O code paths from `src/newsletter/config.py` (any dead `open()`/`json.load()`/`json.dump()` calls no longer reachable)
- [X] T027 [P] Remove `senders.json` from `.gitignore` or `config/` tracking if present — add `senders.json.bak` to `.gitignore`
- [X] T028 Run `ruff check --fix src/` and `mypy src/` — fix all errors
- [X] T029 Run full test suite `pytest` — verify no regressions
- [X] T030 Validate quickstart.md steps manually: start app without senders.json, confirm empty sender list loads; add sender via UI, restart, confirm persists

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user story phases
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on Phase 2; independent of Phase 3
- **Phase 5 (US3)**: Depends on Phase 2; independent of Phases 3 and 4
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5 all complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependency on US2 or US3
- **US2 (P2)**: Can start after Phase 2 — no dependency on US1 or US3
- **US3 (P3)**: Can start after Phase 2 — no dependency on US1 or US2

### Within Each User Story

- TDD: tests written and confirmed failing before implementation
- Models (`SenderRecord`) before Repository methods
- Repository methods before route handler / config.py updates

### Parallel Opportunities

- T003 and T004 can run in parallel (different test groups)
- T005, T006, T007 can run in parallel (different files)
- T009 and T010 can run in parallel
- Once Phase 2 complete: US1, US2, US3 phases can run in parallel
- T026 and T027 can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch in parallel after T001/T002 complete:
Task: "Write failing tests for sender Repository methods in tests/unit/test_sender_repository.py"  # T003
Task: "Write failing tests for config Repository methods in tests/unit/test_sender_repository.py"  # T004
Task: "Add SenderRecord model to src/models/newsletter_models.py"  # T005
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001, T002)
2. Complete Phase 2: Foundational (T003–T008)
3. Complete Phase 3: User Story 1 (T009–T017)
4. **STOP and VALIDATE**: Add sender via UI, restart, verify persistence
5. Deploy if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → Repository ready
2. Phase 3 (US1) → Sender CRUD persists to DB ✓
3. Phase 4 (US2) → Global config persists to DB ✓
4. Phase 5 (US3) → Existing senders.json migrated automatically ✓
5. Phase 6 → Clean up and validate

---

## Notes

- [P] tasks = different files, no dependency conflicts
- TDD required by constitution for all backend service/logic tasks
- `config_path` in migration.py takes an absolute `Path` for testability
- The `load_config` / `save_config` signatures in config.py retain their existing signatures (backward-compatible API) — callers unchanged
- `models` and `excluded_topics` fields in senders.json are migrated to `newsletter_config` as JSON strings (keys: `models`, `excluded_topics`)
