# Tasks: Newsletter Aggregator

**Input**: Design documents from `/specs/002-newsletter-aggregator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Unit tests for backend logic only (per constitution testing policy). No tests for UI components or API endpoints.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per implementation plan (src/newsletter/, data/, config/ - note: src/web/ and src/utils/ already exist)
- [X] T002 Create requirements.txt with Flask, HTMX, google-api-python-client, google-auth, html2text, openai, pytest dependencies
- [X] T003 [P] Create __init__.py files in src/newsletter/, tests/unit/, tests/integration/ (note: src/web/ and src/utils/ __init__.py may already exist)
- [X] T004 [P] Create .gitignore file excluding data/, config/credentials.json, config/tokens.json, *.db, __pycache__/, venv/
- [X] T005 [P] Create README.md with basic project description and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement database initialization function in src/newsletter/storage.py (create SQLite database, processed_emails and newsletter_items tables with indexes)
- [X] T007 Implement configuration loading function in src/utils/config.py (load_config() to read config/senders.json with defaults - add new function to existing config.py file, separate from Zotero Configuration class)
- [X] T008 Implement configuration saving function in src/utils/config.py (save_config() to write config/senders.json - add new function to existing config.py file, separate from Zotero Configuration class)
- [X] T009 Create base Flask application structure in src/web/app.py (Flask app initialization, basic error handling - add to existing src/web/ directory)
- [X] T010 [P] Create base HTML template in src/web/templates/base.html (HTML structure, HTMX script inclusion, basic layout - add to existing src/web/ directory)
- [X] T011 [P] Create minimal CSS file in src/web/static/style.css (basic styling for forms and layout - add to existing src/web/ directory)
- [X] T012 Create data directory structure initialization (ensure data/emails/, data/markdown/, data/parsed/, data/output/, data/ exist for tokens.json)
- [X] T013 [P] Unit test for load_config() in tests/unit/test_config.py (test loading newsletter config from config/senders.json with defaults, missing file handling)
- [X] T014 [P] Unit test for save_config() in tests/unit/test_config.py (test saving newsletter config to config/senders.json, file creation, JSON formatting)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Collect Emails from Specified Senders (Priority: P1) 🎯 MVP

**Goal**: Collect emails from configured newsletter senders via Gmail API, store locally, and track processed emails to avoid duplicates.

**Independent Test**: Configure sender email addresses, run collection process, verify emails are retrieved from Gmail and stored in data/emails/ with database tracking records.

### Tests for User Story 1

- [X] T015 [P] [US1] Unit test for get_processed_message_ids() in tests/unit/test_storage.py
- [X] T016 [P] [US1] Unit test for track_email_processed() in tests/unit/test_storage.py
- [X] T017 [P] [US1] Unit test for save_email() in tests/unit/test_storage.py (test saving email dict to JSON file)
- [X] T018 [P] [US1] Integration test for Gmail authentication flow in tests/integration/test_gmail_client.py (mocked OAuth)
- [X] T019 [P] [US1] Integration test for collect_emails() in tests/integration/test_gmail_client.py (mocked Gmail API)

### Implementation for User Story 1

- [X] T020 [US1] Implement authenticate_gmail() function in src/newsletter/gmail_client.py (OAuth 2.0 flow, token storage in data/tokens.json)
- [X] T021 [US1] Implement automatic token refresh handling in src/newsletter/gmail_client.py (handle token expiration, refresh tokens automatically per FR-013)
- [X] T022 [US1] Implement collect_emails() function in src/newsletter/gmail_client.py (query Gmail API, filter by sender, exclude processed)
- [X] T023 [US1] Implement get_processed_message_ids() function in src/newsletter/storage.py (query SQLite for processed message IDs)
- [X] T024 [US1] Implement track_email_processed() function in src/newsletter/storage.py (insert/update processed_emails table)
- [X] T025 [US1] Implement save_email() function in src/newsletter/storage.py (save email dict to data/emails/{message_id}.json)
- [X] T026 [US1] Implement email collection orchestration in src/newsletter/email_collector.py (load config, authenticate, collect, save, track)
- [X] T027 [US1] Implement GET / route handler in src/web/routes.py (display dashboard with collection status)
- [X] T028 [US1] Implement POST /collect route handler in src/web/routes.py (trigger email collection, return HTMX status update)
- [X] T029 [US1] Create index.html template in src/web/templates/index.html (dashboard with collect button, status display, HTMX integration)
- [X] T030 [US1] Add error handling for Gmail authentication failures in src/newsletter/gmail_client.py (clear error messages per FR-014)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can configure senders and collect emails from Gmail.

---

## Phase 4: User Story 2 - Convert Newsletters to Standard Format (Priority: P1)

**Goal**: Convert collected email content (HTML or plain text) to markdown format, preserving structure and formatting.

**Independent Test**: Provide sample newsletter emails (HTML and plain text), run conversion process, verify markdown files are created in data/markdown/ with preserved formatting.

### Tests for User Story 2

- [X] T031 [P] [US2] Unit test for convert_to_markdown() with HTML email in tests/unit/test_markdown_converter.py
- [X] T032 [P] [US2] Unit test for convert_to_markdown() with plain text email in tests/unit/test_markdown_converter.py
- [X] T033 [P] [US2] Unit test for convert_to_markdown() with images/attachments in tests/unit/test_markdown_converter.py
- [X] T034 [P] [US2] Unit test for save_markdown() in tests/unit/test_storage.py (test saving markdown string to file)

### Implementation for User Story 2

- [X] T035 [US2] Implement convert_to_markdown() function in src/newsletter/markdown_converter.py (use html2text for HTML, format plain text)
- [X] T036 [US2] Implement save_markdown() function in src/newsletter/storage.py (save markdown string to data/markdown/{message_id}.md)
- [X] T037 [US2] Implement email conversion orchestration in src/newsletter/email_collector.py (load emails from data/emails/, convert, save markdown, update status to 'converted')
- [X] T038 [US2] Update POST /process route handler in src/web/routes.py (add conversion step before parsing)
- [X] T039 [US2] Add error handling for conversion failures in src/newsletter/markdown_converter.py (log errors, continue with other emails per FR-014)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can collect emails and convert them to markdown.

---

## Phase 5: User Story 3 - Parse Newsletters Using Configurable Prompts (Priority: P1)

**Goal**: Parse newsletter markdown using LLM with configurable prompts per sender, extracting structured items (date, title, summary, link).

**Independent Test**: Configure prompt for a sender, provide markdown newsletter, run parsing, verify structured items are extracted and stored in data/parsed/ and newsletter_items table.

### Tests for User Story 3

- [X] T040 [P] [US3] Unit test for parse_newsletter() with single article in tests/unit/test_parser.py (mocked LLM client)
- [X] T041 [P] [US3] Unit test for parse_newsletter() with multiple articles in tests/unit/test_parser.py (mocked LLM client)
- [X] T042 [P] [US3] Unit test for parse_newsletter() with missing fields in tests/unit/test_parser.py (mocked LLM client)
- [X] T043 [P] [US3] Unit test for save_parsed_items() in tests/unit/test_storage.py (test saving JSON array to file)
- [X] T044 [P] [US3] Unit test for insert_newsletter_items() in tests/unit/test_storage.py (test inserting parsed items into database with item_index)

### Implementation for User Story 3

- [X] T045 [US3] Implement LLM client wrapper in src/newsletter/parser.py (OpenAI-compatible interface, API key from environment)
- [X] T046 [US3] Implement parse_newsletter() function in src/newsletter/parser.py (call LLM with prompt and markdown, parse JSON response)
- [X] T047 [US3] Implement save_parsed_items() function in src/newsletter/storage.py (save JSON array to data/parsed/{message_id}.json)
- [X] T048 [US3] Implement insert_newsletter_items() function in src/newsletter/storage.py (insert parsed items into newsletter_items table with item_index)
- [X] T049 [US3] Implement parsing orchestration in src/newsletter/email_collector.py (load markdown, get sender prompt from config, parse, save items, update status to 'parsed')
- [X] T050 [US3] Update POST /process route handler in src/web/routes.py (add parsing step after conversion)
- [X] T051 [US3] Add error handling for parsing failures in src/newsletter/parser.py (log errors, mark status as 'failed', include partial data if available per FR-014, FR-015)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. Users can collect, convert, and parse newsletters.

---

## Phase 6: User Story 4 - Generate Consolidated Newsletter Digest (Priority: P1)

**Goal**: Generate consolidated newsletter from all parsed items using LLM consolidation prompt, output as markdown.

**Independent Test**: Provide multiple parsed newsletter items, run consolidation, verify consolidated markdown is generated and saved to data/output/digest_{timestamp}.md.

### Tests for User Story 4

- [X] T052 [P] [US4] Unit test for consolidate_newsletters() with multiple items in tests/unit/test_consolidator.py (mocked LLM client)
- [X] T053 [P] [US4] Unit test for consolidate_newsletters() with empty items list in tests/unit/test_consolidator.py
- [X] T054 [P] [US4] Unit test for get_all_parsed_items() in tests/unit/test_storage.py (test querying newsletter_items table, returning list of dicts)
- [X] T055 [P] [US4] Unit test for save_consolidated_digest() in tests/unit/test_storage.py (test saving markdown to timestamped file)

### Implementation for User Story 4

- [X] T056 [US4] Implement get_all_parsed_items() function in src/newsletter/storage.py (query newsletter_items table, return list of dicts)
- [X] T057 [US4] Implement consolidate_newsletters() function in src/newsletter/consolidator.py (call LLM with consolidation prompt and parsed items, return markdown)
- [X] T058 [US4] Implement save_consolidated_digest() function in src/newsletter/storage.py (save markdown to data/output/digest_{timestamp}.md)
- [X] T059 [US4] Implement POST /consolidate route handler in src/web/routes.py (trigger consolidation, return HTMX response with digest content or download link)
- [X] T060 [US4] Implement GET /digest/{timestamp} route handler in src/web/routes.py (serve consolidated markdown file for download)
- [X] T061 [US4] Create digest.html template in src/web/templates/digest.html (display consolidated newsletter or download link)
- [X] T062 [US4] Update index.html template in src/web/templates/index.html (add consolidate button, display digest section)
- [X] T063 [US4] Add error handling for consolidation failures in src/newsletter/consolidator.py (log error, provide raw structured lists as fallback per edge case spec)

**Checkpoint**: At this point, User Stories 1, 2, 3, AND 4 should all work independently. Users can complete full workflow: collect → convert → parse → consolidate.

---

## Phase 7: User Story 5 - Configure Newsletter Prompts (Priority: P2)

**Goal**: Allow users to configure parsing prompts per sender and consolidation prompt via web UI.

**Independent Test**: Add new sender with custom prompt via UI, verify configuration is saved, verify prompt is used during processing.

### Tests for User Story 5

- [X] T064 [P] [US5] Unit test for save_config() with new sender in tests/unit/test_config.py
- [X] T065 [P] [US5] Unit test for save_config() with updated consolidation prompt in tests/unit/test_config.py

### Implementation for User Story 5

- [X] T066 [US5] Implement GET /config route handler in src/web/routes.py (display configuration page with current senders and prompts)
- [X] T067 [US5] Implement POST /config/senders route handler in src/web/routes.py (add/update sender configuration, save to config/senders.json)
- [X] T068 [US5] Implement POST /config/consolidation route handler in src/web/routes.py (update consolidation prompt, save to config/senders.json)
- [X] T069 [US5] Create config.html template in src/web/templates/config.html (form to add/edit senders, form to update consolidation prompt, list of configured senders with HTMX updates)
- [X] T070 [US5] Add navigation links between index.html and config.html templates
- [X] T071 [US5] Add validation for sender email format and prompt non-empty in src/web/routes.py (per data model validation rules)
- [X] T072 [US5] Update email_collector.py to respect enabled/disabled sender flag from config
- [X] T085 [US5] Allow config/senders.json to be edited and saved from the UI (enable full CRUD operations: create, read, update, delete senders; edit consolidation prompt; save all changes to config/senders.json)

**Checkpoint**: At this point, all user stories should be independently functional. Users can configure prompts and complete full newsletter aggregation workflow.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T073 [P] Unit test for apply_retention_policy() in tests/unit/test_storage.py (test deleting oldest records, cleaning up files and database)
- [X] T074 [P] Implement apply_retention_policy() function in src/newsletter/storage.py (delete oldest records beyond retention_limit, clean up files and database)
- [X] T075 [P] Add retention policy execution after processing in src/newsletter/email_collector.py (call apply_retention_policy after successful processing)
- [X] T076 [P] Add retention limit configuration to config.html template (input field for retention_limit, save to config)
- [X] T077 [P] Improve error messages and user feedback in all route handlers (clear, actionable messages per FR-014)
- [X] T078 [P] Add logging throughout application (use Python logging module, log to console and optionally file)
- [X] T079 [P] Add status indicators in index.html template (show collection status, processing status, number of items parsed)
- [X] T080 [P] Create minimal JavaScript file in src/web/static/app.js (only for HTMX enhancements not possible with HTMX alone)
- [X] T081 [P] Improve CSS styling in src/web/static/style.css (better form styling, status indicators, responsive layout)
- [X] T082 [P] Add input validation and sanitization for all user inputs (email addresses, prompts, retention limit)
- [X] T083 [P] Update README.md with complete setup instructions, usage guide, and troubleshooting
- [X] T084 [P] Run quickstart.md validation (verify all setup steps work, update if needed)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories should proceed sequentially in priority order (US1 → US2 → US3 → US4 → US5)
  - Each story builds on previous stories (US2 needs emails from US1, US3 needs markdown from US2, etc.)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (needs collected emails) - Must complete US1 first
- **User Story 3 (P1)**: Depends on US2 (needs markdown files) - Must complete US2 first
- **User Story 4 (P1)**: Depends on US3 (needs parsed items) - Must complete US3 first
- **User Story 5 (P2)**: Can start after US1 (needs config system from Foundational) - Can run in parallel with US2-4 but easier sequentially

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Storage functions before orchestration functions
- Core functions before route handlers
- Route handlers before templates
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- All Foundational tasks marked [P] can run in parallel (T010, T011)
- All tests for a user story marked [P] can run in parallel
- Polish phase tasks marked [P] can run in parallel
- Different components within a story can be worked on in parallel if no dependencies (e.g., storage functions while working on Gmail client)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for get_processed_message_ids() in tests/unit/test_storage.py"
Task: "Unit test for track_email_processed() in tests/unit/test_storage.py"
Task: "Integration test for Gmail authentication flow in tests/integration/test_gmail_client.py"
Task: "Integration test for collect_emails() in tests/integration/test_gmail_client.py"

# Launch storage functions in parallel (after tests):
Task: "Implement get_processed_message_ids() function in src/newsletter/storage.py"
Task: "Implement track_email_processed() function in src/newsletter/storage.py"
Task: "Implement save_email() function in src/newsletter/storage.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Collect Emails)
4. **STOP and VALIDATE**: Test User Story 1 independently - verify emails can be collected from Gmail and stored locally
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Collect) → Test independently → Deploy/Demo (MVP - can collect emails!)
3. Add User Story 2 (Convert) → Test independently → Deploy/Demo (can convert to markdown!)
4. Add User Story 3 (Parse) → Test independently → Deploy/Demo (can extract structured data!)
5. Add User Story 4 (Consolidate) → Test independently → Deploy/Demo (full workflow complete!)
6. Add User Story 5 (Configure) → Test independently → Deploy/Demo (user can customize prompts!)
7. Add Polish phase → Final polish → Production ready

### Sequential Story Dependencies

Due to the workflow nature (collect → convert → parse → consolidate), stories must be implemented sequentially:
- US1 provides emails for US2
- US2 provides markdown for US3
- US3 provides parsed items for US4
- US5 can be added at any point after US1 (config system exists)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Per constitution: Tests only for backend logic, not UI/API endpoints
- LLM API calls should be mocked in tests to avoid costs and external dependencies
- Gmail API calls should be mocked in integration tests

