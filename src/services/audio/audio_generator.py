"""Audio generator orchestrator for newsletter TTS conversion."""

import hashlib
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path

from src.models.audio_models import (
    AudioConfig,
    AudioGenerationResult,
    AudioSegment,
    TTSRequest,
)
from src.services.audio.markdown_parser import parse_newsletter_items
from src.services.audio.tts_service import KokoroTTSService
from src.services.audio import TTSError

logger = logging.getLogger(__name__)

# Cache directory for audio segments
CACHE_DIR = Path("data/audio_cache")


def get_content_hash(link: str | None, voice_id: str) -> str:
    """
    Generate a hash for article link + voice combination.

    Uses article link (if available) for stable caching across LLM regenerations.
    Falls back to content hash if link is not available.

    Args:
        link: Article URL (preferred) or None to use content hash fallback
        voice_id: Voice ID used

    Returns:
        16-character hash string
    """
    if link:
        # Use stable link for caching (survives LLM rewrites)
        content = f"{link}:{voice_id}"
    else:
        # Fallback: generate random hash (no caching benefit)
        import time
        content = f"nocache:{time.time()}:{voice_id}"

    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_cached_audio(link: str | None, voice_id: str) -> bytes | None:
    """
    Retrieve cached audio for given article link and voice.

    Args:
        link: Article URL (for cache stability)
        voice_id: Voice ID used

    Returns:
        Audio bytes if cached, None otherwise
    """
    if not link:
        return None  # Can't cache without stable identifier

    cache_key = get_content_hash(link, voice_id)
    cache_file = CACHE_DIR / f"{cache_key}.wav"

    if cache_file.exists():
        logger.info(f"Cache hit for link {link[:50]}...")
        return cache_file.read_bytes()

    return None


def cache_audio(link: str | None, voice_id: str, audio_bytes: bytes) -> None:
    """
    Cache audio for given article link and voice.

    Args:
        link: Article URL (for cache stability)
        voice_id: Voice ID used
        audio_bytes: Audio data to cache
    """
    if not link:
        logger.warning("No link provided - skipping cache")
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = get_content_hash(link, voice_id)
    cache_file = CACHE_DIR / f"{cache_key}.wav"

    cache_file.write_bytes(audio_bytes)
    logger.info(f"Cached audio for link: {link[:50]}...")


def concatenate_audio_segments(segments: list[AudioSegment]) -> bytes:
    """
    Concatenate multiple audio segments into single MP3 with normalized volume.

    Uses ffmpeg to normalize volume levels before concatenation to avoid
    volume differences between male and female voices.

    Args:
        segments: List of AudioSegment objects

    Returns:
        Combined audio bytes as MP3
    """
    if not segments:
        return b""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Save each segment to a temp file and normalize with ffmpeg
        normalized_files = []
        for i, segment in enumerate(segments):
            input_file = tmpdir_path / f"segment_{i:03d}_input.wav"
            output_file = tmpdir_path / f"segment_{i:03d}_normalized.wav"

            # Write segment to temp file
            input_file.write_bytes(segment.audio_bytes)

            try:
                # Normalize audio using ffmpeg loudnorm filter
                # This ensures consistent volume levels across all segments
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        str(input_file),
                        "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11",  # EBU R128 normalization
                        "-y",  # Overwrite output file
                        str(output_file),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                normalized_files.append(output_file)
            except subprocess.CalledProcessError as e:
                logger.warning(
                    f"Failed to normalize segment {segment.item_number}: {e.stderr}"
                )
                # Fall back to original file without normalization
                normalized_files.append(input_file)

        # Create concat file list for ffmpeg
        concat_file = tmpdir_path / "concat_list.txt"
        with open(concat_file, "w") as f:
            for file_path in normalized_files:
                # Use forward slashes for ffmpeg compatibility
                file_str = str(file_path).replace("\\", "/")
                f.write(f"file '{file_str}'\n")

        # Concatenate all normalized segments
        output_file = tmpdir_path / "combined.mp3"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c",
                    "copy",  # Copy codec, no re-encoding
                    "-y",
                    str(output_file),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Read and return the combined audio
            return output_file.read_bytes()

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to concatenate audio segments: {e.stderr}")
            # Fall back to simple byte concatenation
            logger.warning("Falling back to simple concatenation without normalization")
            return b"".join(segment.audio_bytes for segment in segments)


def generate_audio_for_newsletter(markdown_path: Path) -> AudioGenerationResult:
    """
    Generate audio file for newsletter markdown.

    Args:
        markdown_path: Path to newsletter markdown file

    Returns:
        AudioGenerationResult with status and output path
    """
    start_time = time.time()
    total_items = 0
    items_processed = 0
    segments = []
    error_message = None

    try:
        # Load configuration
        config = AudioConfig.from_env()

        # Initialize TTS service (Kokoro runs locally, no API key needed)
        logger.info("Initializing Kokoro TTS service")
        tts_service = KokoroTTSService(config=config)

        # Parse newsletter items
        logger.info(f"Parsing newsletter: {markdown_path}")
        items = parse_newsletter_items(markdown_path)
        total_items = len(items)

        if total_items == 0:
            error_message = "No items found in newsletter"
            logger.warning(error_message)
            return AudioGenerationResult(
                success=False,
                total_items=0,
                items_processed=0,
                error_message=error_message,
                duration_seconds=time.time() - start_time,
            )

        logger.info(f"Generating audio for {total_items} items")

        # Generate audio for each item
        for item in items:
            try:
                # Select voice based on item number
                voice_name = (
                    config.male_voice
                    if item.voice_gender == "male"
                    else config.female_voice
                )

                text = item.to_speech_text()

                # Check cache first (using article link for stability)
                cached_audio = get_cached_audio(item.link, voice_name)

                if cached_audio:
                    # Use cached audio
                    logger.info(
                        f"Using cached audio for item {item.item_number}/{total_items} (link: {item.link})"
                    )
                    segment = AudioSegment(
                        item_number=item.item_number,
                        audio_bytes=cached_audio,
                        voice_name=voice_name,
                        voice_gender=item.voice_gender,
                    )
                else:
                    # Generate new audio
                    logger.info(
                        f"Converting item {item.item_number}/{total_items} "
                        f"(voice: {item.voice_gender})"
                    )
                    request = TTSRequest(
                        text=text,
                        voice_name=voice_name,
                    )
                    segment = tts_service.convert_to_speech(request)
                    segment.item_number = item.item_number

                    # Cache the audio (using article link for stability)
                    cache_audio(item.link, voice_name, segment.audio_bytes)

                segments.append(segment)
                items_processed += 1

            except TTSError as e:
                logger.error(f"Failed to convert item {item.item_number}: {e}")
                error_message = f"Failed to convert item {item.item_number}: {e}"
                # Continue with remaining items

        # Check if any items were processed
        if items_processed == 0:
            return AudioGenerationResult(
                success=False,
                total_items=total_items,
                items_processed=0,
                error_message=error_message or "All items failed to convert",
                duration_seconds=time.time() - start_time,
            )

        # Concatenate audio segments
        logger.info(f"Concatenating {len(segments)} audio segments")
        audio_bytes = concatenate_audio_segments(segments)

        # Save to file
        audio_path = markdown_path.with_suffix(".mp3")
        logger.info(f"Saving audio to: {audio_path}")
        audio_path.write_bytes(audio_bytes)

        duration = time.time() - start_time
        success = items_processed == total_items

        logger.info(
            f"Audio generation {'completed' if success else 'partial'}: "
            f"{items_processed}/{total_items} items in {duration:.2f}s"
        )

        return AudioGenerationResult(
            success=success,
            output_path=audio_path,
            total_items=total_items,
            items_processed=items_processed,
            error_message=error_message if not success else None,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        error_message = str(e)
        logger.error(f"Audio generation failed: {e}", exc_info=True)

        return AudioGenerationResult(
            success=False,
            total_items=total_items,
            items_processed=items_processed,
            error_message=error_message,
            duration_seconds=duration,
        )
