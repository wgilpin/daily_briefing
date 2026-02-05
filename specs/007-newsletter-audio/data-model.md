# Data Model: Newsletter Audio Generation

**Date**: 2026-02-05
**Feature**: [spec.md](spec.md)
**Research**: [research.md](research.md)

## Overview

This document defines the Pydantic models and data structures for the newsletter audio generation feature. All models follow the project constitution requirement for strong typing.

## Core Models

### 1. AudioConfig

Configuration for audio generation behavior.

```python
from pydantic import BaseModel, Field
from typing import Literal

class AudioConfig(BaseModel):
    """Configuration for audio generation from newsletter content."""

    male_voice_id: str = Field(
        default="ErXwobaYiN019PkySvjV",  # Antoni
        description="ElevenLabs voice ID for male voice"
    )
    female_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",  # Rachel
        description="ElevenLabs voice ID for female voice"
    )
    model_id: str = Field(
        default="eleven_monolingual_v1",
        description="ElevenLabs model identifier"
    )
    output_format: Literal["mp3_44100_128"] = Field(
        default="mp3_44100_128",
        description="Audio format: MP3 at 44.1kHz, 128kbps"
    )
    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0=varied, 1=consistent)"
    )
    similarity_boost: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Voice clarity enhancement"
    )
    api_timeout: int = Field(
        default=30,
        gt=0,
        description="Timeout per TTS API call in seconds"
    )

    @classmethod
    def from_env(cls) -> "AudioConfig":
        """Load configuration from environment variables with defaults."""
        import os
        return cls(
            male_voice_id=os.getenv("ELEVENLABS_MALE_VOICE_ID", cls.model_fields["male_voice_id"].default),
            female_voice_id=os.getenv("ELEVENLABS_FEMALE_VOICE_ID", cls.model_fields["female_voice_id"].default),
            model_id=os.getenv("ELEVENLABS_MODEL", cls.model_fields["model_id"].default),
            api_timeout=int(os.getenv("ELEVENLABS_TIMEOUT", str(cls.model_fields["api_timeout"].default)))
        )
```

**Validation Rules**:
- Voice IDs must be non-empty strings
- Stability and similarity_boost must be between 0.0 and 1.0
- Timeout must be positive integer
- Output format is restricted to supported MP3 format

### 2. NewsletterItem

Represents a single newsletter item extracted from markdown.

```python
from pydantic import BaseModel, Field

class NewsletterItem(BaseModel):
    """A single article/item from the newsletter digest."""

    title: str = Field(
        ...,
        min_length=1,
        description="Article title"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Article body text (excluding metadata)"
    )
    item_number: int = Field(
        ...,
        ge=1,
        description="Sequential number in newsletter (1-indexed)"
    )

    @property
    def voice_gender(self) -> Literal["male", "female"]:
        """Determine voice gender based on item number."""
        return "male" if self.item_number % 2 == 1 else "female"

    def to_speech_text(self) -> str:
        """Format item as text for TTS conversion."""
        return f"{self.title}. {self.content}"
```

**Validation Rules**:
- Title and content must be non-empty
- Item number must be positive integer (1-indexed)
- Voice gender is computed property (odd=male, even=female)

### 3. AudioSegment

Represents generated audio for a single newsletter item.

```python
from pydantic import BaseModel, Field
from typing import Literal

class AudioSegment(BaseModel):
    """Audio data for a single newsletter item."""

    item_number: int = Field(
        ...,
        ge=1,
        description="Sequential number in newsletter (1-indexed)"
    )
    audio_bytes: bytes = Field(
        ...,
        description="Raw MP3 audio data"
    )
    voice_id: str = Field(
        ...,
        description="ElevenLabs voice ID used"
    )
    voice_gender: Literal["male", "female"] = Field(
        ...,
        description="Voice gender used"
    )
    duration_estimate: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated duration in seconds (if available)"
    )

    class Config:
        arbitrary_types_allowed = True  # Allow bytes type
```

**Validation Rules**:
- Item number must be positive integer
- Audio bytes must be non-empty
- Voice ID must match config
- Duration estimate must be non-negative

### 4. AudioGenerationResult

Result summary for audio generation operation.

```python
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path

class AudioGenerationResult(BaseModel):
    """Result of audio generation for a newsletter."""

    success: bool = Field(
        ...,
        description="Whether audio generation completed successfully"
    )
    output_path: Optional[Path] = Field(
        default=None,
        description="Path to generated MP3 file (if successful)"
    )
    total_items: int = Field(
        ...,
        ge=0,
        description="Total number of newsletter items"
    )
    items_processed: int = Field(
        ...,
        ge=0,
        description="Number of items successfully converted to audio"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description (if failed)"
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total time taken for audio generation"
    )

    @property
    def success_rate(self) -> float:
        """Calculate percentage of items successfully processed."""
        if self.total_items == 0:
            return 0.0
        return (self.items_processed / self.total_items) * 100

    class Config:
        arbitrary_types_allowed = True  # Allow Path type
```

**Validation Rules**:
- Total items and items_processed must be non-negative
- Items processed cannot exceed total items
- Duration must be non-negative
- Success is False if items_processed < total_items

### 5. TTSRequest

Request payload for text-to-speech conversion (per item).

```python
from pydantic import BaseModel, Field
from typing import Literal

class TTSRequest(BaseModel):
    """Request for converting text to speech via ElevenLabs API."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to convert to speech"
    )
    voice_id: str = Field(
        ...,
        description="ElevenLabs voice ID"
    )
    model_id: str = Field(
        default="eleven_monolingual_v1",
        description="ElevenLabs model identifier"
    )
    voice_settings: "VoiceSettings" = Field(
        default_factory=lambda: VoiceSettings(),
        description="Voice configuration parameters"
    )

class VoiceSettings(BaseModel):
    """ElevenLabs voice settings for fine-tuning."""

    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0
    )
    similarity_boost: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0
    )
```

**Validation Rules**:
- Text must be between 1 and 5000 characters (API limit)
- Voice ID must be non-empty
- Voice settings must be within valid ranges

## Data Flow

### Input: Markdown File

```
data/output/digest_20260205_135306_678384.md
    ↓ [Parse]
    ↓
List[NewsletterItem]
```

### Processing: TTS Conversion

```
For each NewsletterItem:
    ↓ [Prepare]
    ↓
    TTSRequest
    ↓ [API Call]
    ↓
    AudioSegment
```

### Output: MP3 File

```
List[AudioSegment]
    ↓ [Concatenate]
    ↓
data/output/digest_20260205_135306_678384.mp3
    ↓ [Result]
    ↓
AudioGenerationResult
```

## State Transitions

### AudioGenerationResult States

```
Initial State: {success: False, total_items: N, items_processed: 0}
    ↓
Processing: For each item, increment items_processed
    ↓
    ├─ Success: {success: True, items_processed: N, output_path: Path}
    │
    └─ Partial Success: {success: False, items_processed: <N, error_message: "..."}
    │
    └─ Complete Failure: {success: False, items_processed: 0, error_message: "..."}
```

## File Naming Convention

**Markdown Input**: `digest_YYYYMMDD_HHMMSS_ffffff.md`
**Audio Output**: `digest_YYYYMMDD_HHMMSS_ffffff.mp3`

**Matching Logic**:
```python
from pathlib import Path

def get_audio_path(markdown_path: Path) -> Path:
    """Generate audio file path matching markdown file."""
    return markdown_path.with_suffix(".mp3")
```

## Error Handling

All models use Pydantic validation. Invalid data raises `ValidationError` with detailed field-level errors.

**Common Validation Errors**:
- Missing required fields
- Type mismatches (e.g., string instead of int)
- Range violations (e.g., negative duration)
- Format violations (e.g., invalid voice ID)

**Error Response Model**:
```python
from pydantic import BaseModel, Field
from typing import List

class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    value: str = Field(..., description="Invalid value provided")
```

## Database Impact

**No database changes required**. This feature uses file-based storage only:
- Input: Read markdown from `data/output/`
- Output: Write MP3 to `data/output/`
- No new database tables or columns

## Configuration Storage

All configuration is environment-based (no JSON config files):

**.env**:
```bash
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_MALE_VOICE_ID=ErXwobaYiN019PkySvjV
ELEVENLABS_FEMALE_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL=eleven_monolingual_v1
ELEVENLABS_TIMEOUT=30
```

**Loading Pattern**:
```python
config = AudioConfig.from_env()
```

## Type Safety Guarantees

All models enforce:
1. **No `Any` types**: All fields have explicit types
2. **No plain `dict`**: Use Pydantic models or TypedDict
3. **Validation at boundaries**: Parse external data (env vars, API responses) into models
4. **Immutable after creation**: Models are frozen after validation (where appropriate)

## Next Steps

1. Implement models in `src/models/audio_models.py`
2. Write unit tests for model validation
3. Create service layer using these models
4. Integrate with newsletter generation pipeline
