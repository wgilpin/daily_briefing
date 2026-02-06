# Research: Newsletter Audio Generation

**Date**: 2026-02-05
**Feature**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)

## Overview

This document captures research findings and technology decisions for implementing text-to-speech conversion of newsletter digests using the ElevenLabs API.

## Technology Decisions

### 1. Text-to-Speech Provider: ElevenLabs

**Decision**: Use ElevenLabs API for TTS conversion

**Rationale**:
- User explicitly requested "eleven labs" in the feature description
- High-quality, natural-sounding voices with emotional nuance
- Supports voice selection (male/female voices readily available)
- Python SDK available (`elevenlabs` package)
- Generous free tier for testing (10,000 characters/month)
- RESTful API with streaming and non-streaming options

**Alternatives Considered**:
- **Google Cloud Text-to-Speech**: Good quality, but user specified ElevenLabs
- **OpenAI TTS**: High quality, but newer and user preference for ElevenLabs
- **Amazon Polly**: Enterprise-grade, but overkill for single-user app
- **pyttsx3 (offline)**: Free but significantly lower quality voices

### 2. ElevenLabs Python SDK

**Decision**: Use official `elevenlabs` Python package (v1.x)

**Rationale**:
- Official SDK with type hints and Pydantic models (aligns with constitution)
- Handles authentication, retries, and error handling
- Supports both streaming and non-streaming modes
- Active maintenance and documentation
- Simpler than raw HTTP requests

**Installation**:
```bash
uv add elevenlabs
```

**API Documentation**: https://elevenlabs.io/docs/api-reference/overview

### 3. Voice Selection Strategy

**Decision**: Use two pre-selected ElevenLabs voice IDs (configurable via environment variables)

**Rationale**:
- ElevenLabs provides pre-made voices in their voice library
- Voice IDs are stable identifiers (e.g., "21m00Tcm4TlvDq8ikWAM" for Rachel)
- Alternating pattern: odd items = male voice, even items = female voice
- Configuration in `.env` allows easy voice swapping without code changes

**Popular Voice Options** (from ElevenLabs library):
- **Male voices**: Adam, Antoni, Arnold, Callum, Charlie
- **Female voices**: Rachel, Domi, Elli, Freya, Grace

**Configuration**:
```bash
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_MALE_VOICE_ID=ErXwobaYiN019PkySvjV  # Antoni (male)
ELEVENLABS_FEMALE_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel (female)
```

### 4. Audio Format: MP3

**Decision**: Generate MP3 files (MPEG Audio Layer 3)

**Rationale**:
- ElevenLabs API supports MP3 output natively
- Universal compatibility (all browsers, players, OS)
- Good compression ratio (smaller files than WAV)
- Specified in feature requirements

**ElevenLabs Parameters**:
- Format: `mp3_44100_128` (44.1kHz sample rate, 128kbps bitrate)
- Model: `eleven_monolingual_v1` (faster, English-optimized)
- Stability: 0.5 (balanced between consistency and expressiveness)
- Similarity boost: 0.75 (voice clarity)

### 5. Audio Generation Architecture

**Decision**: Post-consolidation hook with sequential processing

**Rationale**:
- Integration point: After `save_consolidated_digest()` completes
- Sequential API calls (one item at a time) to avoid rate limits
- Non-blocking: Audio generation failures don't prevent newsletter saving
- Fail-safe: If audio fails, markdown is still available

**Flow**:
```
Newsletter consolidation completes
    ↓
Save markdown to data/output/digest_TIMESTAMP.md
    ↓
Parse markdown to extract items
    ↓
For each item (sequential):
    - Prepare text (title + content, exclude URLs/dates)
    - Select voice (odd=male, even=female)
    - Call ElevenLabs TTS API
    - Receive audio bytes
    ↓
Concatenate all audio segments
    ↓
Save final MP3 to data/output/digest_TIMESTAMP.mp3
    ↓
Log success/failure
```

### 6. Markdown Parsing Strategy

**Decision**: Custom markdown parser using Python regex and structure recognition

**Rationale**:
- Newsletter markdown has consistent structure (explored in codebase)
- Headers follow pattern: `## Category`, `### Subcategory`, `#### Item Title`
- Simple parsing: split by `####` headers, extract title + body
- Exclude lines starting with `*Source:` and `*Date:`
- No need for heavy markdown parsing libraries

**Parsing Logic**:
```python
# Pseudo-code
items = []
for section in markdown.split('#### '):
    if not section.strip():
        continue
    lines = section.strip().split('\n')
    title = lines[0].strip()
    body = [line for line in lines[1:]
            if not line.startswith('*Source:')
            and not line.startswith('*Date:')]
    items.append({'title': title, 'content': '\n'.join(body)})
```

### 7. Error Handling & Resilience

**Decision**: Graceful degradation with comprehensive logging

**Rationale**:
- Audio is a "nice-to-have" feature - don't block core newsletter functionality
- Catch all exceptions during audio generation
- Log detailed errors (API failures, rate limits, parsing issues)
- Continue with partial audio if some items fail
- Return status summary (e.g., "10/12 items converted successfully")

**Error Scenarios**:
- **ElevenLabs API down**: Log error, skip audio generation
- **Rate limit exceeded**: Log warning, skip remaining items
- **Invalid voice ID**: Log error with config hint, fail fast
- **Empty markdown**: Log info, skip audio generation
- **Disk full**: Log critical error, alert user

### 8. Testing Strategy

**Decision**: Mock ElevenLabs API responses in all tests

**Rationale**:
- Constitution requirement: No remote API calls in tests
- Mock responses with realistic audio bytes (small MP3 samples)
- Test error scenarios (API failures, malformed responses)
- Integration test: End-to-end with mocked API

**Mocking Approach**:
```python
@pytest.fixture
def mock_elevenlabs_client(mocker):
    mock_client = mocker.Mock()
    mock_client.generate.return_value = b'\xff\xfb\x90...'  # Mock MP3 bytes
    return mock_client
```

### 9. Performance Considerations

**Decision**: Sequential processing with timeout per item

**Rationale**:
- ElevenLabs API has rate limits (avoid parallel requests)
- Newsletter items are small (1-2 paragraphs each)
- Estimated time: ~5-10 seconds per item (API call + processing)
- Target: 50 items in 5 minutes = 6 seconds per item (acceptable)
- Timeout: 30 seconds per API call (fail fast on hangs)

**Optimization Opportunities** (future):
- Stream audio responses (process while receiving)
- Parallel requests with rate limiter (if API allows)
- Cache repeated phrases (unlikely to help with unique content)

### 10. Configuration Management

**Decision**: Environment variables for all external config

**Rationale**:
- Follows project pattern (never overwrite .env per CLAUDE.md)
- Secrets in .env (API key)
- Sensible defaults for voice IDs (can override)
- No new config files needed

**Environment Variables**:
```bash
# Required
ELEVENLABS_API_KEY=sk_...

# Optional (with defaults)
ELEVENLABS_MALE_VOICE_ID=ErXwobaYiN019PkySvjV
ELEVENLABS_FEMALE_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL=eleven_monolingual_v1
ELEVENLABS_TIMEOUT=30
```

## Integration Points

### Existing Code Modification Sites

1. **src/newsletter/storage.py** (line ~205)
   - Function: `save_consolidated_digest()`
   - Modification: Add audio generation call after markdown save
   - Pattern: Try/except wrapper to prevent blocking

2. **src/web/feed_routes.py** (line ~356)
   - Endpoint: `/api/refresh`
   - Modification: Return audio status in response
   - Pattern: Add `audio_generated: bool` to success response

## Dependencies to Add

```toml
# Add to pyproject.toml via `uv add`
elevenlabs = "^1.0.0"  # Official ElevenLabs Python SDK
```

## API Rate Limits

**ElevenLabs Free Tier**:
- 10,000 characters/month
- No concurrent request limits documented
- Recommended: Sequential requests to avoid issues

**Estimation**:
- Average item: ~500 characters
- Average newsletter: 10-20 items = 5,000-10,000 characters
- Free tier: ~1-2 newsletters/month (testing only)
- Production: Requires paid plan ($5/month for 30k characters)

## Security Considerations

1. **API Key Storage**: Environment variable in .env (never committed)
2. **File Permissions**: MP3 files saved with restrictive permissions (0644)
3. **Input Validation**: Sanitize markdown input before TTS (remove injection attempts)
4. **Error Messages**: Don't expose API keys in logs or error messages

## Next Steps (Phase 1)

1. Define Pydantic models for audio configuration and responses
2. Design API contract for ElevenLabs integration
3. Create quickstart guide for developers (setup, testing, troubleshooting)
4. Generate tasks for TDD implementation

## References

- [ElevenLabs API Documentation](https://elevenlabs.io/docs/api-reference/overview)
- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
- [MP3 Format Specification](https://en.wikipedia.org/wiki/MP3)
