# Implementation Plan: TTS Provider Fallback

**Branch**: `012-tts-fallback` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-tts-fallback/spec.md`

## Summary

Add automatic TTS provider selection: detect Kokoro via import at startup, use it if available, fall back to ElevenLabs if not. Separate `kokoro` and `soundfile` into an optional dependency group so the Coolify/Hetzner production build excludes them. Surface the active provider name in the existing audio status UI.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Flask, kokoro (optional extra), soundfile (optional extra), elevenlabs SDK (to be restored), ffmpeg (system dep, already present)
**Storage**: N/A (no new persistent data; audio cache files unchanged)
**Testing**: pytest with mocking (constitution IV — no real API calls in tests)
**Target Platform**: Development PC (Kokoro + espeak-ng) and Linux server via Coolify (ElevenLabs only)
**Project Type**: Web application (Flask + HTMX)
**Performance Goals**: Provider detection must complete at startup with negligible delay (<100ms)
**Constraints**: Production build must not install `kokoro` or `soundfile`; no code changes to switch profiles
**Scale/Scope**: Single-user app; TTS runs sequentially per newsletter digest

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Technology Stack (Python 3.13+, uv, PostgreSQL) | ✅ Pass | No new storage; uv optional extras used |
| II. Strong Typing (mypy + Pydantic) | ✅ Pass | New provider protocol and models must be fully typed |
| III. Backend TDD | ✅ Pass | TTS service and factory logic require tests written first |
| IV. Test Isolation (no real APIs) | ✅ Pass | ElevenLabs and Kokoro both mocked in tests |
| V. Simplicity First | ✅ Pass | Protocol + factory is minimal; no plugin registry |
| VI. Feature Discipline | ✅ Pass | Scope matches spec exactly |
| VII. Code Quality Gates | ✅ Pass | ruff + mypy must pass before commit |

**Gate result**: PASS — proceed.

## Project Structure

### Documentation (this feature)

```text
specs/012-tts-fallback/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (changes only)

```text
src/
├── models/
│   └── audio_models.py          # Add provider_used field to AudioGenerationResult
├── services/
│   └── audio/
│       ├── __init__.py          # Add ElevenLabsTTSError
│       ├── tts_service.py       # Add ElevenLabsTTSService + get_tts_provider() factory
│       └── audio_generator.py   # Inject provider via factory; pass provider_used to result
├── web/
│   └── templates/
│       └── (feed.html or partial) # Display provider_used in existing audio status area

tests/
├── unit/
│   └── services/
│       └── audio/
│           ├── test_tts_service.py        # Extend: add ElevenLabs + factory tests
│           └── test_audio_generator.py    # Extend: test provider injection
pyproject.toml                             # Move kokoro + soundfile to optional extras
```

**Structure Decision**: Single project layout (existing). No new directories. All changes are modifications to existing files plus test extensions.

## Phase 0: Research

See [research.md](research.md) — all unknowns resolved.

**Key decisions**:

1. Kokoro detection: `try: import kokoro` at module load time
2. Pattern: Protocol interface + factory function `get_tts_provider()`
3. Dependency isolation: `[project.optional-dependencies] kokoro = ["kokoro>=0.9.4", "soundfile>=0.13.1"]`
4. ElevenLabs output: convert MP3 → WAV via ffmpeg to maintain uniform `AudioSegment` interface
5. UI status: add `provider_used: str` field to `AudioGenerationResult`

## Phase 1: Design & Contracts

### Data Model Changes

See [data-model.md](data-model.md).

**`AudioGenerationResult`** — add one field:

- `provider_used: str` — canonical provider name shown in UI (e.g., `"Kokoro"`, `"ElevenLabs"`)

**`AudioConfig`** — no changes needed; ElevenLabs voice config comes from env vars.

**New: `ElevenLabsConfig`** (Pydantic model):

- `api_key: str` — from `ELEVENLABS_API_KEY` env var
- `male_voice_id: str` — from `ELEVENLABS_MALE_VOICE_ID` env var (default: existing voice ID)
- `female_voice_id: str` — from `ELEVENLABS_FEMALE_VOICE_ID` env var (default: existing voice ID)

### Provider Interface

```python
# Protocol (structural typing — no ABC required)
class TTSProvider(Protocol):
    def convert_to_speech(self, request: TTSRequest) -> AudioSegment: ...
    @property
    def provider_name(self) -> str: ...
```

### Factory

```python
def get_tts_provider(config: AudioConfig) -> TTSProvider:
    try:
        import kokoro  # noqa: F401
        from .tts_service import KokoroTTSService
        return KokoroTTSService(config)
    except ImportError:
        from .elevenlabs_service import ElevenLabsTTSService
        return ElevenLabsTTSService(ElevenLabsConfig.from_env())
```

### API Contracts

No new HTTP endpoints. The existing audio generation route (`POST /api/refresh` → `generate_audio_for_newsletter()`) is unchanged. The only contract change is the `provider_used` field on `AudioGenerationResult` flowing to the UI.

See [contracts/tts-provider-interface.md](contracts/tts-provider-interface.md).

### UI Change

The `provider_used` field from `AudioGenerationResult` is rendered in the audio generation status area. The message format is `"Generating with {provider_used}"` shown during generation, and `"Generated with {provider_used}"` on completion. The existing Alpine.js / HTMX update mechanism is reused.

## Implementation Order

1. **`pyproject.toml`** — move `kokoro` and `soundfile` to optional extras (unblocks Coolify build immediately)
2. **`src/models/audio_models.py`** — add `provider_used` field and `ElevenLabsConfig` model
3. **`src/services/audio/elevenlabs_service.py`** — new file: `ElevenLabsTTSService` (restore from pre-Kokoro, adapt to `AudioSegment` interface)
4. **`src/services/audio/tts_service.py`** — add `TTSProvider` protocol + `get_tts_provider()` factory
5. **`src/services/audio/audio_generator.py`** — replace direct `KokoroTTSService` instantiation with `get_tts_provider()`, populate `provider_used`
6. **UI template** — render `provider_used` in audio status area
7. **Tests** — unit tests for factory, ElevenLabs service, and updated generator (TDD: tests first for steps 3–5)
8. **`Dockerfile`** — verify `uv sync` without `--extra kokoro` is the build command (no Kokoro installed in prod image)
