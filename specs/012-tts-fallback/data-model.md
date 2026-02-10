# Data Model: TTS Provider Fallback (012)

**Branch**: `012-tts-fallback` | **Date**: 2026-02-10

No new database entities. All changes are to in-memory Pydantic models.

---

## Modified: `AudioGenerationResult`

**File**: `src/models/audio_models.py`

| Field | Type | Description |
| ----- | ---- | ----------- |
| `success` | `bool` | Whether generation completed successfully |
| `output_path` | `Optional[Path]` | Path to output MP3 file |
| `total_items` | `int` | Number of items in the newsletter |
| `items_processed` | `int` | Items successfully synthesised |
| `error_message` | `Optional[str]` | Error detail if `success=False` |
| `duration_seconds` | `float` | Wall-clock time for generation |
| `provider_used` ⭐ | `str` | **NEW** — canonical provider name, e.g. `"Kokoro"` or `"ElevenLabs"` |

---

## New: `ElevenLabsConfig`

**File**: `src/models/audio_models.py`

| Field | Type | Source | Default |
| ----- | ---- | ------ | ------- |
| `api_key` | `str` | `ELEVENLABS_API_KEY` env var | Required |
| `male_voice_id` | `str` | `ELEVENLABS_MALE_VOICE_ID` env var | `"21m00Tcm4TlvDq8ikWAM"` |
| `female_voice_id` | `str` | `ELEVENLABS_FEMALE_VOICE_ID` env var | `"EXAVITQu4vr4xnSDxMaL"` |

Loaded via `ElevenLabsConfig.from_env()` class method. Raises `ValueError` if `ELEVENLABS_API_KEY` is absent.

---

## New: `TTSProvider` Protocol

**File**: `src/services/audio/tts_service.py`

Structural protocol (no ABC inheritance required). Both `KokoroTTSService` and `ElevenLabsTTSService` must satisfy it.

| Method/Property | Signature | Description |
| --------------- | --------- | ----------- |
| `convert_to_speech` | `(request: TTSRequest) -> AudioSegment` | Synthesise text to audio |
| `provider_name` | `@property -> str` | Human-readable provider name for UI display |

---

## Unchanged Models

- `AudioConfig` — Kokoro voice names, loaded from env vars; no changes
- `TTSRequest` — text + voice_name; no changes
- `AudioSegment` — audio bytes (WAV) + metadata; no changes
- `NewsletterItem` — voice gender alternation logic; no changes
