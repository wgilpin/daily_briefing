# Implementation Plan: Audio Playback UI Controls

**Branch**: `009-audio-playback-ui` | **Date**: 2026-02-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-audio-playback-ui/spec.md`

## Summary

Add audio playback controls to the unified feed interface, enabling users to listen to narrated versions of feed items with Play/Pause/Next/Previous controls. Uses HTML5 audio with Alpine.js for reactive UI state, Flask HTTP 206 range support for streaming, and browser-native accessibility features.

**Technical Approach:**
- **Frontend**: Alpine.js (12KB) + HTML5 `<audio>` element + HTMX preservation
- **Backend**: Flask route serving MP3 files with HTTP 206 partial content support
- **UX**: Global player bar (top right) + per-item play buttons + keyboard shortcuts
- **Performance**: Content-addressed caching (1 year), batch file existence checks, GPU-accelerated smooth scroll

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Flask, Alpine.js (CDN), HTMX (existing), Pydantic
**Storage**: File system (`data/audio_cache/*.mp3`) - audio files already exist from feature 007/008
**Testing**: pytest with mocked file system for integration tests
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge 2024+)
**Project Type**: Web application (Flask backend + HTMX frontend)
**Performance Goals**: <2s audio playback start, <500ms scroll to item, <1s next/previous navigation
**Constraints**: 12KB JavaScript overhead (Alpine.js only), zero external API calls, WCAG 2.1 Level AA compliance
**Scale/Scope**: ~10-50 audio files per feed page, single user session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gate 1: Technology Stack Compliance ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| Python 3.13+ | ✅ PASS | All backend code in Python |
| Flask | ✅ PASS | Using existing Flask web framework |
| PostgreSQL for data | ✅ PASS | No new database tables - audio availability computed from files |
| No local SQLite | ✅ PASS | Audio metadata not stored in DB, just file existence checks |
| uv for packages | ✅ PASS | Alpine.js via CDN (no package), no Python deps added |

**Justification for file storage**: Audio files are immutable artifacts (content-addressed by hash), not transactional user data. Constitution allows configuration/artifact storage in files when immutable and <1MB per file. This qualifies.

### Gate 2: Strong Typing ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| mypy enforcement | ✅ PASS | All Flask routes use Pydantic models |
| No plain `dict` | ✅ PASS | FeedItem model uses `@computed_field` for audio metadata |
| No `Any` type | ✅ PASS | All type hints explicit |

**Example:**
```python
@computed_field
@property
def has_audio(self) -> bool:  # Explicit bool return
    """Check if audio file exists."""
    audio_file = Path(f"data/audio_cache/{self.id}.mp3")
    return audio_file.exists()
```

### Gate 3: Backend TDD ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| Tests required for backend | ✅ PASS | Flask `/audio/<id>` route requires unit tests |
| Tests NOT required for UI | ✅ PASS | Alpine.js components exempt (frontend) |
| Red-Green-Refactor | ✅ PASS | Write tests first for audio serving logic |

**Test Coverage:**
- HTTP 206 range request handling
- Authentication check (@login_required)
- Path traversal prevention (invalid item_id)
- Missing file handling (404)
- File system mocking (no real files in tests)

### Gate 4: Test Isolation ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| No remote API calls | ✅ PASS | Zero external dependencies - all local file serving |
| Mock file system | ✅ PASS | Use pytest `tmp_path` fixture for audio file tests |
| No flaky tests | ✅ PASS | All tests deterministic (file existence mocked) |

### Gate 5: Simplicity First ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| No premature abstractions | ✅ PASS | Single Flask route, no service layer needed |
| No future-proofing | ✅ PASS | No playlist/history/analytics - only spec requirements |
| Delete unused code | ✅ PASS | No dead code introduced |

**Complexity Justification:**
- Alpine.js (12KB library) justified: Prevents 100+ lines of vanilla JS boilerplate for reactive UI
- HTTP 206 support required: Browser media controls won't work without it (technical necessity, not over-engineering)

### Gate 6: Feature Discipline ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| No unspecified features | ✅ PASS | Implementing exactly spec requirements, no extras |
| Ask before adding | ✅ PASS | No volume controls, playlists, or analytics added |

### Gate 7: Code Quality Gates ✅

| Principle | Status | Notes |
|-----------|--------|-------|
| ruff linting | ✅ PASS | All Python code must pass `ruff check` |
| mypy type checking | ✅ PASS | All functions fully typed |
| No unused imports | ✅ PASS | Linter enforces |

---

**POST-DESIGN RE-CHECK** (after Phase 1):

| Gate | Status | Changes |
|------|--------|---------|
| Technology Stack | ✅ PASS | Alpine.js added (CDN, no package manager change) |
| Strong Typing | ✅ PASS | `@computed_field` pattern confirmed in data-model.md |
| Simplicity | ✅ PASS | research.md confirms minimal approach (12KB total overhead) |

**No constitution violations.**

## Project Structure

### Documentation (this feature)

```text
specs/009-audio-playback-ui/
├── spec.md                  # Feature specification (requirements, clarifications)
├── plan.md                  # This file (implementation plan)
├── research.md              # Phase 0 output (technology decisions, best practices)
├── data-model.md            # Phase 1 output (state model, file structure)
├── quickstart.md            # Phase 1 output (step-by-step implementation guide)
├── contracts/               # Phase 1 output (API contracts)
│   └── audio-api.yaml       # OpenAPI spec for /audio/<id> endpoint
└── checklists/
    └── requirements.md      # Spec quality validation checklist
```

### Source Code (repository root)

```text
src/
├── models/
│   └── feed_models.py           # [MODIFY] Add has_audio computed property
├── services/
│   └── audio/                    # [EXISTING] Audio generation from feature 007/008
│       ├── tts_service.py
│       └── audio_generator.py
├── web/
│   ├── app.py                    # [MODIFY] Register audio blueprint
│   ├── feed_routes.py            # [EXISTING] Feed rendering
│   ├── audio_routes.py           # [NEW] Audio file serving endpoint
│   └── templates/
│       ├── base.html             # [MODIFY] Add Alpine.js CDN script
│       ├── feed.html             # [MODIFY] Add player bar, Alpine component, CSS
│       └── partials/
│           └── feed_item.html    # [MODIFY] Add play button, data attributes

tests/
├── unit/
│   └── web/
│       └── test_audio_routes.py  # [NEW] Unit tests for HTTP 206, auth, validation
├── integration/
│   └── test_feed_audio.py        # [NEW] E2E feed with audio playback
└── conftest.py                    # [MODIFY] Add audio file fixtures

data/
└── audio_cache/                   # [EXISTING] MP3 files from feature 007/008
    ├── 1a4f6b0976cc66ba.mp3
    ├── 1e54af0387a05e32.mp3
    └── ...
```

**Structure Decision**: Single project structure (existing). No new backend/frontend split needed - this is a pure extension of existing Flask app. All changes are incremental modifications to current files plus one new route file.

## Complexity Tracking

**No constitution violations requiring justification.**

Alpine.js library addition is within simplicity guidelines:
- 12KB minified (smaller than hand-written equivalent ~150 lines)
- Purpose-built for HTMX architectures (industry best practice pairing in 2026)
- Prevents reactive UI boilerplate (querySelector/addEventListener cycles)
- No build step required (CDN script tag)

## Phase 0: Research & Decisions

**Completed**: See [research.md](research.md)

### Key Decisions

1. **Client-side state**: Vanilla JavaScript + HTMLMediaElement API (zero dependencies)
2. **Audio serving**: Flask HTTP 206 partial content with `send_file()` + range headers
3. **UI synchronization**: Alpine.js (12KB) + HTMX `hx-preserve` attribute
4. **Keyboard accessibility**: Native `<button>` elements + ARIA + standard media shortcuts
5. **Smooth scrolling**: Browser-native `scrollIntoView()` + CSS `scroll-behavior: smooth`

### Rationale

All decisions prioritize simplicity and browser-native APIs over libraries:
- Total JavaScript overhead: **12KB** (Alpine.js only)
- Zero backend dependencies added (Flask built-ins sufficient)
- No build tools required (CDN scripts)
- WCAG 2.1 Level AA compliance via semantic HTML

See research.md for full alternatives analysis and sources.

## Phase 1: Design & Contracts

**Completed**: See design artifacts below

### Data Model

**File**: [data-model.md](data-model.md)

**Client-Side State** (Alpine.js component):
- `isPlaying`: boolean - playback status
- `currentItem`: object | null - metadata (id, title, audioPath)
- `currentIndex`: number - position in feed (>= -1)
- `itemCount`: number - total items with audio

**Server-Side Extension** (existing FeedItem model):
- `has_audio`: computed boolean - file existence check
- `audio_path`: computed string - URL path to audio file

**No database changes required** - all audio metadata derived from file system.

### API Contracts

**File**: [contracts/audio-api.yaml](contracts/audio-api.yaml)

**Endpoint**: `GET /audio/<item_id>`

**Authentication**: Required (`@login_required`)

**Responses**:
- `200 OK`: Full audio file
- `206 Partial Content`: Byte range (for seeking)
- `304 Not Modified`: Cached version valid
- `400 Bad Request`: Invalid item_id format
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Audio file missing
- `416 Range Not Satisfiable`: Invalid byte range

**Headers**:
- `Accept-Ranges: bytes` (required for media controls)
- `Content-Range: bytes <start>-<end>/<total>` (206 responses)
- `Cache-Control: public, max-age=31536000, immutable` (content-addressed)

### Quickstart Guide

**File**: [quickstart.md](quickstart.md)

Step-by-step implementation guide with:
- Alpine.js CDN setup
- Global player bar HTML + Alpine component
- Flask route for audio serving
- FeedItem model extension
- CSS styling
- Testing checklist
- Troubleshooting tips

## Implementation Phases (for /speckit.tasks)

### Phase 1: Backend Audio Serving (P1 - Critical)

**Goal**: Serve audio files with HTTP 206 range support for browser seeking

**Tasks**:
1. Create `src/web/audio_routes.py` with `serve_audio()` route
2. Implement HTTP 206 partial content logic (range parsing)
3. Add authentication check (`@login_required`)
4. Add input validation (item_id format, path traversal prevention)
5. Register blueprint in `app.py`
6. Write unit tests for route (206, 404, 401, 400 cases)

**Success Criteria**: `/audio/<id>` returns 206 responses with `Accept-Ranges: bytes`

### Phase 2: Feed Item Audio Metadata (P1 - Critical)

**Goal**: Add `has_audio` computed property to FeedItem model

**Tasks**:
1. Add `@computed_field` for `has_audio` in `feed_models.py`
2. Batch file existence check in repository layer (performance optimization)
3. Update feed rendering to include `has_audio` in template context
4. Write unit tests for computed property

**Success Criteria**: Feed items know whether audio exists without individual file checks

### Phase 3: Frontend Player Bar UI (P1 - Critical)

**Goal**: Global audio player with Play/Pause/Next/Previous controls

**Tasks**:
1. Add Alpine.js CDN script to `base.html`
2. Create player bar HTML in `feed.html` with `hx-preserve`
3. Implement Alpine.js `audioPlayerState()` component
4. Add HTMX `beforeSwap` listener (stop audio on filter change)
5. Style player bar (CSS in `feed.html`)
6. Add ARIA labels for accessibility

**Success Criteria**: Player bar visible, controls functional, state preserved across HTMX swaps

### Phase 4: Per-Item Play Buttons (P1 - Critical)

**Goal**: Play button on each feed item card (only if audio exists)

**Tasks**:
1. Update `feed_item.html` template with conditional play button
2. Add `data-item-id` and `data-audio-path` attributes
3. Wire up click handler to `playItem()` method
4. Add CSS for play button styling
5. Add `.playing` class style for highlighted item

**Success Criteria**: Clicking play button starts audio, highlights item

### Phase 5: Sequential Navigation (P2 - High Priority)

**Goal**: Next/Previous buttons navigate between feed items

**Tasks**:
1. Implement `next()` method in Alpine component
2. Implement `previous()` method in Alpine component
3. Handle boundary conditions (disable buttons at list ends)
4. Add button enable/disable logic based on `currentIndex`

**Success Criteria**: Next/Previous navigate sequentially, buttons disabled at boundaries

### Phase 6: Auto-Scroll to Playing Item (P3 - Medium Priority)

**Goal**: Page auto-scrolls to keep playing item visible

**Tasks**:
1. Add `scrollIntoView()` call in `playItem()` method
2. Add CSS `scroll-behavior: smooth` to `html` element
3. Add `prefers-reduced-motion` media query for accessibility
4. Test scroll behavior on long feeds

**Success Criteria**: Page smoothly scrolls to show playing item at top

### Phase 7: Keyboard Shortcuts (P2 - High Priority)

**Goal**: Space/N/P keyboard shortcuts for audio control

**Tasks**:
1. Add document-level `keydown` event listener
2. Implement Space (play/pause), N (next), P (previous) handlers
3. Prevent shortcuts when input fields focused
4. Add Arrow keys for seek (optional enhancement)
5. Test keyboard-only navigation

**Success Criteria**: All audio controls accessible via keyboard

### Phase 8: Integration Testing (P1 - Critical)

**Goal**: End-to-end testing of full audio playback flow

**Tasks**:
1. Write integration test for feed rendering with audio metadata
2. Test audio route with mocked file system
3. Test boundary conditions (first/last item)
4. Test filter change stops playback
5. Test keyboard shortcuts in browser
6. Test with screen reader (NVDA/JAWS)

**Success Criteria**: All acceptance scenarios from spec pass

## Testing Strategy

### Unit Tests (pytest)

**File**: `tests/unit/web/test_audio_routes.py`

Test cases:
- HTTP 200 for full file request
- HTTP 206 for range request (with valid range)
- HTTP 304 for cached request (with ETag)
- HTTP 401 without authentication
- HTTP 404 for missing file
- HTTP 400 for invalid item_id (path traversal attempt)
- HTTP 416 for out-of-range request
- Cache headers present (immutable, max-age)
- Accept-Ranges header present

**File**: `tests/unit/models/test_feed_models.py`

Test cases:
- `has_audio` returns True when file exists
- `has_audio` returns False when file missing
- `audio_path` returns correct URL when audio exists
- `audio_path` returns None when no audio

### Integration Tests

**File**: `tests/integration/test_feed_audio.py`

Test cases:
- Feed page renders with play buttons on items with audio
- Feed page hides play buttons on items without audio
- Clicking play button triggers audio load (mocked)
- Filter change stops playback (HTMX interaction)

### Manual Testing

**Accessibility**:
- Tab through all controls (visual focus indicator)
- Use only keyboard (Space, N, P keys)
- Test with screen reader (NVDA/JAWS)
- Lighthouse accessibility audit (>= 90 score)

**Browser Compatibility**:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS)
- Mobile Chrome (Android)

## Deployment Notes

### Files Modified

| File | Type | Description |
|------|------|-------------|
| `src/web/templates/base.html` | Modified | Added Alpine.js CDN script |
| `src/web/templates/feed.html` | Modified | Added player bar, Alpine component, CSS, keyboard handlers |
| `src/web/templates/partials/feed_item.html` | Modified | Added play button, data attributes |
| `src/web/audio_routes.py` | New | Audio serving endpoint with HTTP 206 |
| `src/models/feed_models.py` | Modified | Added `has_audio` computed property |
| `src/web/app.py` | Modified | Registered audio blueprint |

### Environment Variables

**No new environment variables required.**

### Dependencies

**No new Python dependencies added.**

**Frontend**: Alpine.js via CDN (no package manager change)

### Migration

**No database migrations required.**

Audio files already exist from feature 007/008. This feature only adds UI for playback.

### Performance Impact

- **Page load**: +12KB (Alpine.js minified)
- **Feed rendering**: +1 file system operation (batch audio file existence check)
- **Audio playback**: Browser-native streaming (zero server CPU after file served)
- **Caching**: Audio files cached for 1 year (immutable, content-addressed)

### Security Considerations

- Authentication enforced via `@login_required` decorator
- Path traversal prevented (item_id validation)
- Audio files only served from `data/audio_cache/` directory
- No directory listing exposed
- Content-Security-Policy compatible (Alpine.js from CDN with SRI hash if needed)

## Monitoring & Observability

**No new logging required** - standard Flask request logging sufficient:
- 404s on `/audio/<id>` indicate missing audio files (investigate if frequent)
- 401s indicate auth failures (expected for non-logged-in users)
- 206 responses expected for all audio requests after initial load

**Performance Metrics** (if Flask metrics exist):
- Audio route response time should be <100ms (file serving)
- Cache hit rate should be >90% (long-lived cache headers)

## Rollback Plan

If issues arise:

1. **Disable audio routes**: Comment out blueprint registration in `app.py`
2. **Hide player UI**: Add CSS `display: none` to `.audio-player-bar`
3. **Revert templates**: Git revert changes to feed templates

**No data loss risk** - no database changes, audio files untouched.

## Next Steps

After `/speckit.plan` completion:

1. Run `/speckit.tasks` to generate executable task breakdown
2. Implement tasks in priority order (P1 → P2 → P3)
3. Run `pytest` after each task completion
4. Manual accessibility testing before deployment
5. Deploy to staging environment for user acceptance testing

## References

- [research.md](research.md) - Full technology research and alternatives analysis
- [data-model.md](data-model.md) - State model, file structure, performance notes
- [contracts/audio-api.yaml](contracts/audio-api.yaml) - OpenAPI specification
- [quickstart.md](quickstart.md) - Step-by-step implementation guide
- [spec.md](spec.md) - Original feature specification and requirements
