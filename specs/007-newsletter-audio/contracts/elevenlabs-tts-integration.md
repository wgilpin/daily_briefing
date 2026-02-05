# ElevenLabs TTS API Integration Contract

**Date**: 2026-02-05
**Feature**: [../spec.md](../spec.md)
**Data Model**: [../data-model.md](../data-model.md)

## Overview

This document defines the integration contract for the ElevenLabs Text-to-Speech API. It specifies request/response patterns, error handling, and implementation expectations.

## API Authentication

**Method**: Bearer token authentication via HTTP header

**Header**:
```http
Authorization: Bearer {ELEVENLABS_API_KEY}
```

**Credential Management**:
- API key stored in `.env` file: `ELEVENLABS_API_KEY=sk_...`
- Loaded via environment variable
- Never logged or exposed in error messages
- Validated on service initialization

## Core API Endpoint

### Text-to-Speech Conversion

**Endpoint**: `POST /v1/text-to-speech/{voice_id}`

**Base URL**: `https://api.elevenlabs.io`

**Request**:
```http
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "text": "Article title. Article content without URLs or metadata.",
  "model_id": "eleven_monolingual_v1",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.75
  }
}
```

**Request Parameters**:
- `voice_id` (path): ElevenLabs voice identifier (e.g., "21m00Tcm4TlvDq8ikWAM")
- `text` (body): Text to convert (max 5000 characters)
- `model_id` (body): Model identifier (default: "eleven_monolingual_v1")
- `voice_settings` (body): Voice tuning parameters

**Response (Success)**:
```http
HTTP/1.1 200 OK
Content-Type: audio/mpeg
Content-Length: {size_in_bytes}

{binary MP3 audio data}
```

**Response Body**: Raw MP3 audio bytes (binary data)

## Python SDK Integration

### Installation

```bash
uv add elevenlabs
```

### Basic Usage Pattern

```python
from elevenlabs import ElevenLabs, VoiceSettings
import os

# Initialize client
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Generate audio
audio_bytes = client.generate(
    text="This is the article title. This is the article content.",
    voice="21m00Tcm4TlvDq8ikWAM",  # Rachel (female)
    model="eleven_monolingual_v1",
    voice_settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.75
    )
)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
```

### Service Interface Contract

```python
from typing import Protocol
from src.models.audio_models import TTSRequest, AudioSegment

class TTSService(Protocol):
    """Protocol for text-to-speech service implementations."""

    def convert_to_speech(self, request: TTSRequest) -> AudioSegment:
        """
        Convert text to speech audio.

        Args:
            request: TTS request with text and voice configuration

        Returns:
            AudioSegment with generated audio bytes

        Raises:
            TTSAPIError: API call failed
            TTSTimeoutError: API call timed out
            TTSRateLimitError: Rate limit exceeded
            ValueError: Invalid request parameters
        """
        ...

    def health_check(self) -> bool:
        """
        Check if TTS service is available.

        Returns:
            True if service is operational, False otherwise
        """
        ...
```

## Error Handling

### HTTP Error Codes

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Return audio bytes |
| 400 | Bad Request (invalid text/voice ID) | Log error, raise ValueError |
| 401 | Unauthorized (invalid API key) | Log critical, raise TTSAPIError |
| 429 | Rate Limit Exceeded | Log warning, raise TTSRateLimitError |
| 500 | Server Error | Log error, retry once, then raise TTSAPIError |
| 503 | Service Unavailable | Log error, raise TTSAPIError |

### Exception Hierarchy

```python
class TTSError(Exception):
    """Base exception for TTS operations."""
    pass

class TTSAPIError(TTSError):
    """API call failed (server error, auth failure)."""
    pass

class TTSTimeoutError(TTSError):
    """API call timed out."""
    pass

class TTSRateLimitError(TTSError):
    """Rate limit exceeded."""
    pass

class TTSValidationError(TTSError):
    """Invalid request parameters."""
    pass
```

### Retry Strategy

**Retryable Errors**:
- 500 (Internal Server Error)
- 503 (Service Unavailable)
- Network timeouts (connection errors)

**Retry Configuration**:
- Max retries: 1 (single retry)
- Retry delay: 2 seconds
- Exponential backoff: No (simple fixed delay)

**Non-Retryable Errors**:
- 400 (Bad Request)
- 401 (Unauthorized)
- 429 (Rate Limit)

### Timeout Configuration

**Per-request timeout**: 30 seconds (configurable via `ELEVENLABS_TIMEOUT` env var)

**Timeout handling**:
```python
import requests
from requests.exceptions import Timeout

try:
    response = requests.post(url, json=payload, timeout=timeout)
except Timeout:
    raise TTSTimeoutError(f"API call timed out after {timeout} seconds")
```

## Rate Limiting

### ElevenLabs Rate Limits

**Free Tier**:
- 10,000 characters/month
- No documented concurrent request limits

**Paid Tier** (Starter - $5/month):
- 30,000 characters/month
- Higher request rates

### Client-Side Rate Limiting

**Strategy**: Sequential processing (no concurrent requests)

**Rationale**:
- Avoids hitting undocumented rate limits
- Predictable processing time
- Simpler error handling

**Implementation**: Process items one at a time in a loop (no need for rate limiter library)

## Audio Format Specifications

### Output Format

**Format**: MP3 (MPEG Audio Layer 3)
**Sample Rate**: 44.1 kHz
**Bitrate**: 128 kbps
**Channels**: Mono
**File Extension**: `.mp3`

**ElevenLabs Format Code**: `mp3_44100_128`

### Audio Concatenation

**Method**: Binary concatenation of MP3 files

**Implementation**:
```python
def concatenate_audio_segments(segments: list[AudioSegment]) -> bytes:
    """Concatenate multiple audio segments into single MP3."""
    audio_data = b"".join(segment.audio_bytes for segment in segments)
    return audio_data
```

**Note**: Simple byte concatenation works for MP3 format (no special merging required for our use case)

## Voice Configuration

### Available Voices

**Male Voices** (Pre-built):
- **Antoni**: `ErXwobaYiN019PkySvjV` (default male)
- **Adam**: `pNInz6obpgDQGcFmaJgB`
- **Arnold**: `VR6AewLTigWG4xSOukaG`

**Female Voices** (Pre-built):
- **Rachel**: `21m00Tcm4TlvDq8ikWAM` (default female)
- **Domi**: `AZnzlk1XvdvUeBnXmlld`
- **Elli**: `MF3mGyEYCl7XYWbV9V6O`

### Voice Selection Logic

```python
def select_voice_id(item_number: int, config: AudioConfig) -> str:
    """Select voice ID based on item number (alternating pattern)."""
    if item_number % 2 == 1:  # Odd items
        return config.male_voice_id
    else:  # Even items
        return config.female_voice_id
```

## Service Implementation Contract

### Required Methods

```python
class ElevenLabsTTSService:
    """ElevenLabs text-to-speech service implementation."""

    def __init__(self, api_key: str, config: AudioConfig):
        """Initialize service with API credentials and configuration."""
        ...

    def convert_to_speech(self, request: TTSRequest) -> AudioSegment:
        """Convert text to speech using ElevenLabs API."""
        ...

    def health_check(self) -> bool:
        """Verify API connectivity and credentials."""
        ...

    def get_available_voices(self) -> list[dict]:
        """Fetch list of available voices (optional utility)."""
        ...
```

### Testing Contract

**Unit Tests** (with mocking):
```python
def test_convert_to_speech_success(mock_elevenlabs_client):
    """Test successful TTS conversion."""
    # Mock client.generate() to return fake MP3 bytes
    mock_elevenlabs_client.generate.return_value = b'\xff\xfb\x90...'

    service = ElevenLabsTTSService(api_key="test_key", config=AudioConfig())
    request = TTSRequest(text="Test text", voice_id="test_voice")

    result = service.convert_to_speech(request)

    assert isinstance(result, AudioSegment)
    assert len(result.audio_bytes) > 0
    mock_elevenlabs_client.generate.assert_called_once()
```

**Integration Tests** (mocked API):
```python
@pytest.fixture
def mock_elevenlabs_api(requests_mock):
    """Mock ElevenLabs API endpoints."""
    requests_mock.post(
        "https://api.elevenlabs.io/v1/text-to-speech/test_voice",
        content=b'\xff\xfb\x90...',  # Fake MP3 data
        status_code=200,
        headers={"Content-Type": "audio/mpeg"}
    )
```

## Performance Expectations

### Latency

**Target**: < 10 seconds per item (including API call + processing)

**Breakdown**:
- API request: ~5-8 seconds (network + TTS generation)
- Processing: ~1-2 seconds (parsing, file I/O)

**Total for 50 items**: < 5 minutes (spec requirement: SC-004)

### Throughput

**Sequential processing**: 1 item at a time
**Concurrency**: None (avoid rate limits)

### Resource Usage

**Memory**: ~1-2 MB per audio segment (transient)
**Disk**: ~500 KB - 5 MB per complete newsletter MP3
**Network**: ~100-200 KB per API call (text + audio)

## Security Considerations

### API Key Protection

- **Never log API key** in error messages or debug output
- **Never commit `.env`** to version control
- **Validate key on startup** with health check
- **Rotate keys regularly** (recommended best practice)

### Input Sanitization

**Risk**: Malicious markdown injection

**Mitigation**:
- Validate text length (max 5000 characters per API call)
- Strip dangerous characters (if any escape sequences could affect TTS)
- Log suspicious inputs

### Output Validation

**Risk**: Corrupted or malicious audio data from API

**Mitigation**:
- Verify response is binary data
- Check MP3 file signature (optional: first bytes should be `\xff\xfb` or `ID3`)
- Limit file size (reject if > 10 MB per item)

## Monitoring & Logging

### Log Levels

**INFO**:
- Audio generation started
- Audio generation completed successfully
- Number of items processed

**WARNING**:
- Rate limit approaching
- Partial audio generation (some items failed)

**ERROR**:
- API authentication failure
- API timeout
- Invalid voice ID
- File I/O error

**CRITICAL**:
- API key missing
- Complete audio generation failure

### Metrics to Track

- **Success rate**: (items_processed / total_items) * 100
- **Average latency**: Total duration / items_processed
- **API error rate**: Failed API calls / total API calls
- **File sizes**: MP3 output file sizes

## Example Integration Flow

```python
# src/services/audio/audio_generator.py

from src.models.audio_models import AudioConfig, AudioGenerationResult
from src.services.audio.tts_service import ElevenLabsTTSService
from src.services.audio.markdown_parser import parse_newsletter_items
from pathlib import Path

def generate_audio_for_newsletter(markdown_path: Path) -> AudioGenerationResult:
    """Generate audio file for newsletter markdown."""

    # 1. Load configuration
    config = AudioConfig.from_env()
    api_key = os.getenv("ELEVENLABS_API_KEY")

    # 2. Initialize TTS service
    tts_service = ElevenLabsTTSService(api_key=api_key, config=config)

    # 3. Parse newsletter items
    items = parse_newsletter_items(markdown_path)

    # 4. Generate audio for each item
    segments = []
    for item in items:
        voice_id = config.male_voice_id if item.voice_gender == "male" else config.female_voice_id
        request = TTSRequest(text=item.to_speech_text(), voice_id=voice_id)
        segment = tts_service.convert_to_speech(request)
        segments.append(segment)

    # 5. Concatenate and save
    audio_bytes = concatenate_audio_segments(segments)
    audio_path = markdown_path.with_suffix(".mp3")
    audio_path.write_bytes(audio_bytes)

    # 6. Return result
    return AudioGenerationResult(
        success=True,
        output_path=audio_path,
        total_items=len(items),
        items_processed=len(segments)
    )
```

## Next Steps

1. Implement `ElevenLabsTTSService` class
2. Write unit tests with mocked API responses
3. Create integration tests with full workflow
4. Integrate into newsletter generation pipeline
5. Add monitoring and logging
