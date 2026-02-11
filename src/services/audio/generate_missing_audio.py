"""Generate audio for feed items missing audio files."""
import logging
from pathlib import Path

from src.db.repository import Repository
from src.db.connection import get_connection
from src.services.audio.tts_service import KokoroTTSService
from src.models.audio_models import AudioConfig, TTSRequest
from src.newsletter.sender_names import get_sender_display_name

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/audio_cache")


def generate_missing_audio_for_feed_items(items=None) -> dict:
    """Generate audio files for feed items that don't have audio yet.

    Args:
        items: Optional list of FeedItem objects to process. If None, queries all newsletter items.

    Returns:
        dict with 'generated', 'skipped', 'errors' counts
    """
    result = {"generated": 0, "skipped": 0, "errors": []}

    # Load configuration
    config = AudioConfig.from_env()

    # Initialize TTS service
    tts_service = KokoroTTSService(config=config)

    if items is None:
        # Fallback: query all newsletter items (used when called standalone)
        repo = Repository()
        with get_connection():
            items = repo.get_feed_items(source_type='newsletter', limit=1000)

    logger.info(f"Checking {len(items)} newsletter items for missing audio")

    for idx, item in enumerate(items, 1):
        audio_file = CACHE_DIR / f"{item.source_id}.wav"

        if audio_file.exists():
            result["skipped"] += 1
            continue

        try:
            # Get sender display name for attribution
            sender_email = item.metadata.get("sender", "")
            sender_name = get_sender_display_name(sender_email) if sender_email else None

            # Generate audio from item title + summary with source attribution
            if sender_name:
                text = f"{sender_name} reports that {item.title}. {item.summary or ''}"
            else:
                # Fallback for items without sender (e.g., Zotero items)
                text = f"{item.title}. {item.summary or ''}"

            # Alternate voices (odd = male, even = female)
            voice_name = config.male_voice if idx % 2 == 1 else config.female_voice

            source_info = f" ({sender_name})" if sender_name else ""
            logger.info(f"Generating audio {idx}/{len(items)}{source_info}: {item.title[:60]}...")

            request = TTSRequest(text=text, voice_name=voice_name)
            segment = tts_service.convert_to_speech(request)

            # Save audio file
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            audio_file.write_bytes(segment.audio_bytes)

            result["generated"] += 1
            logger.info(f"✓ Saved {audio_file.name}")

        except Exception as e:
            error_msg = f"Failed to generate audio for {item.source_id}: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

    logger.info(f"Audio generation complete: {result['generated']} generated, {result['skipped']} skipped, {len(result['errors'])} errors")
    return result
