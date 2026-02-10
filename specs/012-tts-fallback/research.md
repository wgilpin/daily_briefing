# Research: TTS Provider Fallback (012)

**Branch**: `012-tts-fallback` | **Date**: 2026-02-10

## Decision 1: How to detect Kokoro availability

**Decision**: Try importing `kokoro` in a `try/except ImportError` block at startup. If the import fails, Kokoro is unavailable.

**Rationale**: Kokoro being importable means it is installed. If `kokoro` is not in the build's dependency set (production), the import will always fail cleanly and fast — no network call, no subprocess, no timeout risk. This is the idiomatic Python availability check.

**Alternatives considered**:
- Subprocess check (`which espeak-ng`) — fragile, platform-dependent, doesn't confirm the Python package is usable.
- Try instantiating `KPipeline` — too expensive at startup (model load).
- Environment variable flag — adds manual config burden; import check is automatic.

---

## Decision 2: How to structure provider selection (pattern)

**Decision**: A thin `TTSProvider` protocol/abstract interface with two concrete implementations: `KokoroTTSService` (existing) and `ElevenLabsTTSService` (new/restored). A factory function `get_tts_provider()` runs the availability check and returns the appropriate instance.

**Rationale**: The existing `KokoroTTSService` already has a clean interface. The factory pattern is the simplest way to make provider selection a one-time startup decision without spreading conditionals through the codebase. Per constitution Principle V (Simplicity First), a protocol + factory is the minimal correct abstraction here.

**Alternatives considered**:
- Global `if kokoro_available:` branches throughout `audio_generator.py` — spreads logic, harder to test.
- Plugin/registry pattern — over-engineered for two providers.

---

## Decision 3: How to move kokoro/soundfile out of core deps

**Decision**: Move `kokoro` and `soundfile` to `[project.optional-dependencies]` under a group named `kokoro`. Production builds (`uv sync`) skip extras by default; dev installs use `uv sync --extra kokoro`.

**Rationale**: `pyproject.toml` optional extras is the standard `uv`/PEP 508 mechanism. Coolify's build command can stay as `uv sync` with no flags — it will simply not install Kokoro. Dev machines add `--extra kokoro`. No separate requirements files to maintain.

**Alternatives considered**:
- Separate `requirements-prod.txt` / `requirements-dev.txt` — duplicates dependency management, violates constitution preference for uv.
- Env-var-controlled conditional install — non-standard, fragile.

---

## Decision 4: ElevenLabs restoration approach

**Decision**: Restore the ElevenLabs client from the pre-Kokoro implementation (commit `f5b9c32`). The interface contract (voice_id, API key from env var, returns MP3 bytes) is already documented in `specs/007-newsletter-audio/contracts/elevenlabs-tts-integration.md`. The new `ElevenLabsTTSService` must produce `AudioSegment` objects with `audio_bytes` in WAV format (converted from MP3 via ffmpeg or soundfile) to maintain a uniform interface with `KokoroTTSService`.

**Rationale**: Uniform output format (WAV `AudioSegment`) means `audio_generator.py` needs no changes to its post-processing pipeline.

**Alternatives considered**:
- Have ElevenLabs return MP3 directly and branch in `audio_generator.py` — complicates the generator.
- Separate audio_generator paths per provider — violates Simplicity First.

---

## Decision 5: UI status message location

**Decision**: The audio generation status message ("Generating with ElevenLabs" or "Generating with Kokoro") is surfaced via the existing `AudioGenerationResult.error_message` field (or a new `provider_name` field) and rendered wherever `AudioGenerationResult` is already displayed in the UI. No new UI components needed.

**Rationale**: The spec requires showing provider name in the existing audio status/progress area. `AudioGenerationResult` already flows back to the Flask route and is used to update the UI. Adding a `provider_used` field to the result model is the minimal change.

---

## Key Existing Files

| File | Role |
|------|------|
| `src/services/audio/tts_service.py` | KokoroTTSService — replace with provider factory |
| `src/services/audio/audio_generator.py` | Orchestration — inject provider, add status message |
| `src/models/audio_models.py` | AudioConfig, TTSRequest, AudioSegment, AudioGenerationResult |
| `src/services/audio/__init__.py` | Exception hierarchy — add ElevenLabsError |
| `src/web/audio_routes.py` | Flask routes — no changes expected |
| `src/web/templates/feed.html` | Global player bar — check for status display point |
| `pyproject.toml` | Move kokoro + soundfile to optional extras |
| `Dockerfile` | Already uses uv; no changes needed if uv sync skips extras by default |
