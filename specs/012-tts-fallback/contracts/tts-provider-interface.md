# Contract: TTS Provider Interface (012)

**Branch**: `012-tts-fallback` | **Date**: 2026-02-10

---

## TTSProvider Protocol

All TTS providers must implement this interface. No inheritance required — structural typing via `Protocol`.

```python
from typing import Protocol

class TTSProvider(Protocol):
    def convert_to_speech(self, request: TTSRequest) -> AudioSegment: ...

    @property
    def provider_name(self) -> str: ...
```

---

## Provider: KokoroTTSService (existing, adapted)

| Aspect | Detail |
| ------ | ------ |
| Availability | Detected via `import kokoro` — ImportError means unavailable |
| `provider_name` | `"Kokoro"` |
| Input | `TTSRequest(text: str, voice_name: str)` |
| Output | `AudioSegment` with WAV bytes at 24kHz |
| Error | Raises `TTSGenerationError` on synthesis failure |
| Dependencies | `kokoro>=0.9.4`, `soundfile>=0.13.1` (optional extras) |

---

## Provider: ElevenLabsTTSService (new)

| Aspect | Detail |
| ------ | ------ |
| Availability | Always available if `ELEVENLABS_API_KEY` is set |
| `provider_name` | `"ElevenLabs"` |
| Input | `TTSRequest(text: str, voice_name: str)` — `voice_name` maps to `ElevenLabsConfig.male_voice_id` or `female_voice_id` |
| Output | `AudioSegment` with WAV bytes (MP3 from API converted via ffmpeg) |
| Error | Raises `TTSGenerationError` on API or conversion failure |
| Dependencies | `elevenlabs` SDK (core dep, always installed) |
| API endpoint | `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` |
| Auth | `xi-api-key: {ELEVENLABS_API_KEY}` header |

---

## Factory: get_tts_provider()

```python
def get_tts_provider(config: AudioConfig) -> TTSProvider:
    """
    Returns KokoroTTSService if kokoro is importable, else ElevenLabsTTSService.
    Called once at audio generation time (not at app startup).
    """
```

| Condition | Returns |
| --------- | ------- |
| `import kokoro` succeeds | `KokoroTTSService(config)` |
| `import kokoro` raises `ImportError` | `ElevenLabsTTSService(ElevenLabsConfig.from_env())` |

---

## AudioGenerationResult.provider_used

Populated by `audio_generator.py` from `provider.provider_name` after factory selection.

- Passed to UI as part of the generation result
- Rendered in the audio status area as: `"Generating with {provider_used}"` / `"Generated with {provider_used}"`
