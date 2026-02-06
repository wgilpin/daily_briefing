"""Pydantic models for newsletter audio generation."""

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AudioConfig(BaseModel):
    """Configuration for audio generation from newsletter content."""

    male_voice: str = Field(
        default="bm_george",
        description="Kokoro voice name for male voice (British English)",
    )
    female_voice: str = Field(
        default="bf_emma",
        description="Kokoro voice name for female voice (British English)",
    )

    @classmethod
    def from_env(cls) -> "AudioConfig":
        """Load configuration from environment variables with defaults."""
        return cls(
            male_voice=os.getenv(
                "KOKORO_MALE_VOICE",
                cls.model_fields["male_voice"].default,
            ),
            female_voice=os.getenv(
                "KOKORO_FEMALE_VOICE",
                cls.model_fields["female_voice"].default,
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


class TTSRequest(BaseModel):
    """Request for converting text to speech via Kokoro TTS."""

    text: str = Field(
        ..., min_length=1, max_length=5000, description="Text to convert to speech"
    )
    voice_name: str = Field(..., description="Kokoro voice name (e.g., bm_george, bf_emma)")


class AudioSegment(BaseModel):
    """Audio data for a single newsletter item."""

    item_number: int = Field(
        ..., ge=1, description="Sequential number in newsletter (1-indexed)"
    )
    audio_bytes: bytes = Field(..., description="Raw WAV audio data")
    voice_name: str = Field(..., description="Kokoro voice name used")
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
