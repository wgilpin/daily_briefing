"""Pydantic models for newsletter audio generation."""

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AudioConfig(BaseModel):
    """Configuration for audio generation from newsletter content."""

    male_voice_id: str = Field(
        default="ErXwobaYiN019PkySvjV",  # Antoni
        description="ElevenLabs voice ID for male voice",
    )
    female_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",  # Rachel
        description="ElevenLabs voice ID for female voice",
    )
    model_id: str = Field(
        default="eleven_monolingual_v1", description="ElevenLabs model identifier"
    )
    output_format: Literal["mp3_44100_128"] = Field(
        default="mp3_44100_128", description="Audio format: MP3 at 44.1kHz, 128kbps"
    )
    stability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0=varied, 1=consistent)",
    )
    similarity_boost: float = Field(
        default=0.75, ge=0.0, le=1.0, description="Voice clarity enhancement"
    )
    api_timeout: int = Field(
        default=30, gt=0, description="Timeout per TTS API call in seconds"
    )

    @classmethod
    def from_env(cls) -> "AudioConfig":
        """Load configuration from environment variables with defaults."""
        return cls(
            male_voice_id=os.getenv(
                "ELEVENLABS_MALE_VOICE_ID",
                cls.model_fields["male_voice_id"].default,
            ),
            female_voice_id=os.getenv(
                "ELEVENLABS_FEMALE_VOICE_ID",
                cls.model_fields["female_voice_id"].default,
            ),
            model_id=os.getenv("ELEVENLABS_MODEL", cls.model_fields["model_id"].default),
            api_timeout=int(
                os.getenv(
                    "ELEVENLABS_TIMEOUT", str(cls.model_fields["api_timeout"].default)
                )
            ),
        )


class NewsletterItem(BaseModel):
    """A single article/item from the newsletter digest."""

    title: str = Field(..., min_length=1, description="Article title")
    content: str = Field(
        ..., min_length=1, description="Article body text (excluding metadata)"
    )
    item_number: int = Field(
        ..., ge=1, description="Sequential number in newsletter (1-indexed)"
    )
    link: str | None = Field(
        default=None, description="URL to original article (for cache stability)"
    )

    @property
    def voice_gender(self) -> Literal["male", "female"]:
        """Determine voice gender based on item number."""
        return "male" if self.item_number % 2 == 1 else "female"

    def to_speech_text(self) -> str:
        """Format item as text for TTS conversion (content only, no title)."""
        return self.content


class VoiceSettings(BaseModel):
    """ElevenLabs voice settings for fine-tuning."""

    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)


class TTSRequest(BaseModel):
    """Request for converting text to speech via ElevenLabs API."""

    text: str = Field(
        ..., min_length=1, max_length=5000, description="Text to convert to speech"
    )
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    model_id: str = Field(
        default="eleven_monolingual_v1", description="ElevenLabs model identifier"
    )
    voice_settings: VoiceSettings = Field(
        default_factory=VoiceSettings, description="Voice configuration parameters"
    )


class AudioSegment(BaseModel):
    """Audio data for a single newsletter item."""

    item_number: int = Field(
        ..., ge=1, description="Sequential number in newsletter (1-indexed)"
    )
    audio_bytes: bytes = Field(..., description="Raw MP3 audio data")
    voice_id: str = Field(..., description="ElevenLabs voice ID used")
    voice_gender: Literal["male", "female"] = Field(..., description="Voice gender used")
    duration_estimate: float = Field(
        default=0.0, ge=0.0, description="Estimated duration in seconds (if available)"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AudioGenerationResult(BaseModel):
    """Result of audio generation for a newsletter."""

    success: bool = Field(
        ..., description="Whether audio generation completed successfully"
    )
    output_path: Optional[Path] = Field(
        default=None, description="Path to generated MP3 file (if successful)"
    )
    total_items: int = Field(..., ge=0, description="Total number of newsletter items")
    items_processed: int = Field(
        ..., ge=0, description="Number of items successfully converted to audio"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error description (if failed)"
    )
    duration_seconds: float = Field(
        default=0.0, ge=0.0, description="Total time taken for audio generation"
    )

    @property
    def success_rate(self) -> float:
        """Calculate percentage of items successfully processed."""
        if self.total_items == 0:
            return 0.0
        return (self.items_processed / self.total_items) * 100

    model_config = ConfigDict(arbitrary_types_allowed=True)
