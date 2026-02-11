# Quickstart: TTS Provider Fallback (012)

**Branch**: `012-tts-fallback`

---

## Development (Kokoro + espeak-ng)

```bash
# Install with Kokoro extras
uv sync --extra kokoro

# espeak-ng must be installed at OS level
# Ubuntu/Debian:
sudo apt-get install espeak-ng
# macOS:
brew install espeak-ng

# Run the app — Kokoro will be detected automatically
cd src && flask run
```

Startup log will show: `TTS provider: Kokoro`

---

## Production / Hetzner (ElevenLabs only)

```bash
# Standard install — no extras, kokoro and soundfile are NOT installed
uv sync

# Required env vars (set in Coolify):
# ELEVENLABS_API_KEY=...
# ELEVENLABS_MALE_VOICE_ID=...   (optional, defaults provided)
# ELEVENLABS_FEMALE_VOICE_ID=... (optional, defaults provided)
```

Startup log will show: `TTS provider: ElevenLabs`

---

## Verifying Provider Selection

Check startup logs for:

```
INFO  TTS provider: Kokoro        ← development
INFO  TTS provider: ElevenLabs    ← production / Kokoro unavailable
```

---

## Running Tests

```bash
cd src
pytest tests/unit/services/audio/
```

All TTS tests mock both Kokoro and ElevenLabs — no real API calls, no GPU required.

---

## Troubleshooting

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| `ImportError: No module named 'kokoro'` in dev | Kokoro extras not installed | `uv sync --extra kokoro` |
| `ValueError: ELEVENLABS_API_KEY not set` | Missing env var in prod | Add to Coolify environment config |
| Build fails on Coolify with kokoro/soundfile error | Old `pyproject.toml` with kokoro in core deps | Ensure kokoro is in `[project.optional-dependencies]` |
| Audio generated but no provider label in UI | `provider_used` not wired to template | Check `AudioGenerationResult.provider_used` is passed to template context |
