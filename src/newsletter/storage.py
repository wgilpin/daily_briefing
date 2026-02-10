"""Storage functions for newsletter aggregator.

File-based storage operations for emails, markdown, and parsed items.
Database operations have been migrated to PostgreSQL repository (src/db/repository.py).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def init_data_directories(base_data_dir: str = "data") -> None:
    """Initialize data directory structure.

    Creates all required data directories if they don't exist:
    - data/emails/ - Raw email storage
    - data/markdown/ - Converted markdown files
    - data/parsed/ - Parsed newsletter items (JSON)
    - data/output/ - Consolidated newsletter outputs
    - data/ - Base directory (for tokens.json)

    Args:
        base_data_dir: Base data directory path (default: "data")

    Side Effects:
        - Creates directory structure if it doesn't exist
    """
    base_path = Path(base_data_dir)

    # Create all required directories
    directories = [
        base_path,  # data/ (for tokens.json)
        base_path / "emails",  # data/emails/
        base_path / "markdown",  # data/markdown/
        base_path / "parsed",  # data/parsed/
        base_path / "output",  # data/output/
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def save_email(email: dict, data_dir: str) -> str:
    """Save email to file system.

    Saves email dictionary as JSON file in the specified directory.
    File is named using the message_id: {message_id}.json

    Args:
        email: Email dictionary (must have 'message_id' key)
        data_dir: Base data directory path (e.g., 'data/emails')

    Returns:
        str: Path to saved file

    Side Effects:
        - Creates file {data_dir}/{message_id}.json
        - Writes email as JSON
        - Creates directory if needed

    Raises:
        KeyError: If email dict doesn't have 'message_id' key
    """
    if "message_id" not in email:
        raise KeyError("Email dictionary must have 'message_id' key")

    data_dir_obj = Path(data_dir)
    data_dir_obj.mkdir(parents=True, exist_ok=True)

    file_path = data_dir_obj / f"{email['message_id']}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(email, f, indent=2, ensure_ascii=False)

    return str(file_path)


def save_markdown(message_id: str, markdown_content: str, data_dir: str) -> str:
    """Save markdown content to file system.

    Saves markdown string to file in the specified directory.
    File is named using the message_id: {message_id}.md

    Args:
        message_id: Gmail message ID (unique identifier)
        markdown_content: Markdown-formatted content string
        data_dir: Base data directory path (e.g., 'data/markdown')

    Returns:
        str: Path to saved file

    Side Effects:
        - Creates file {data_dir}/{message_id}.md
        - Writes markdown content
        - Creates directory if needed

    Raises:
        ValueError: If message_id is empty
    """
    if not message_id:
        raise ValueError("message_id must be non-empty")

    data_dir_obj = Path(data_dir)
    data_dir_obj.mkdir(parents=True, exist_ok=True)

    file_path = data_dir_obj / f"{message_id}.md"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return str(file_path)


def save_parsed_items(
    message_id: str, parsed_items: list[dict], data_dir: str
) -> str:
    """Save parsed newsletter items to file system.

    Saves parsed items as JSON array to file in the specified directory.
    File is named using the message_id: {message_id}.json

    Args:
        message_id: Gmail message ID (unique identifier)
        parsed_items: List of parsed item dictionaries
        data_dir: Base data directory path (e.g., 'data/parsed')

    Returns:
        str: Path to saved file

    Side Effects:
        - Creates file {data_dir}/{message_id}.json
        - Writes parsed items as JSON array
        - Creates directory if needed

    Raises:
        ValueError: If message_id is empty
    """
    if not message_id:
        raise ValueError("message_id must be non-empty")

    data_dir_obj = Path(data_dir)
    data_dir_obj.mkdir(parents=True, exist_ok=True)

    file_path = data_dir_obj / f"{message_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(parsed_items, f, indent=2, ensure_ascii=False)

    return str(file_path)


def get_last_digest_timestamp(output_dir: str = "data/output") -> datetime | None:
    """Get the timestamp of the most recent digest file.

    Parses digest filenames to find the most recent one and extracts its timestamp.
    Returns None if no digest files exist.

    Args:
        output_dir: Output directory path (default: 'data/output')

    Returns:
        datetime | None: Timestamp of most recent digest, or None if no digests exist

    Side Effects:
        - Reads directory listing from output_dir
    """
    output_dir_obj = Path(output_dir)

    if not output_dir_obj.exists():
        return None

    # Find all digest files matching pattern: digest_YYYYMMDD_HHMMSS_ffffff.md
    digest_files = list(output_dir_obj.glob("digest_*.md"))

    if not digest_files:
        return None

    # Sort by filename (which naturally sorts by timestamp) and get the most recent
    digest_files.sort(reverse=True)
    most_recent = digest_files[0]

    # Extract timestamp from filename: digest_20260204_184222_737575.md
    filename = most_recent.stem  # Remove .md extension
    parts = filename.split("_")  # ['digest', '20260204', '184222', '737575']

    if len(parts) != 4:
        return None

    try:
        # Parse: YYYYMMDD_HHMMSS_ffffff
        date_str = parts[1]  # '20260204'
        time_str = parts[2]  # '184222'
        microsec_str = parts[3]  # '737575'

        # Construct datetime
        timestamp_str = f"{date_str}_{time_str}_{microsec_str}"
        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S_%f")

        # Convert to UTC timezone-aware datetime
        return timestamp.replace(tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def save_consolidated_digest(markdown_content: str, output_dir: str) -> str:
    """Save consolidated newsletter digest to file system.

    Saves markdown content to a timestamped file in the specified directory.
    File is named: digest_{timestamp}.md
    Also generates an MP3 audio file via text-to-speech if ElevenLabs API is configured.

    Args:
        markdown_content: Markdown text of consolidated newsletter
        output_dir: Base output directory path (e.g., 'data/output')

    Returns:
        str: Path to saved file

    Side Effects:
        - Creates file {output_dir}/digest_{timestamp}.md
        - Writes markdown content
        - Optionally creates {output_dir}/digest_{timestamp}.mp3 (audio file)
        - Creates directory if needed

    Raises:
        ValueError: If markdown_content is empty
    """
    if not markdown_content or not markdown_content.strip():
        raise ValueError("markdown_content must be non-empty")

    output_dir_obj = Path(output_dir)
    output_dir_obj.mkdir(parents=True, exist_ok=True)

    # Generate timestamp in format: YYYYMMDD_HHMMSS_ffffff (includes microseconds for uniqueness)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_path = output_dir_obj / f"digest_{timestamp}.md"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    # Generate audio file for newsletter
    audio_provider = None
    try:
        from src.services.audio.audio_generator import generate_audio_for_newsletter

        logger.info(f"Generating audio for newsletter: {file_path}")
        audio_result = generate_audio_for_newsletter(file_path)
        audio_provider = audio_result.provider_used or None

        if audio_result.success:
            logger.info(
                f"Audio generated successfully: {audio_result.output_path} "
                f"({audio_result.items_processed}/{audio_result.total_items} items, "
                f"{audio_result.duration_seconds:.2f}s, provider: {audio_result.provider_used})"
            )
        else:
            logger.warning(
                f"Audio generation failed or incomplete: "
                f"{audio_result.items_processed}/{audio_result.total_items} items processed. "
                f"Error: {audio_result.error_message}"
            )
    except Exception as e:
        # Don't fail newsletter save if audio generation fails
        logger.error(f"Audio generation failed: {e}", exc_info=True)

    return str(file_path), audio_provider


def get_recent_parsed_items(
    db_path: str, days: int | None = None, since: datetime | None = None
) -> list[dict]:
    """Get parsed newsletter items from the last N days or since a specific datetime.

    Queries PostgreSQL feed_items table for newsletter items within the
    specified number of days OR since a specific datetime. The db_path parameter
    is kept for backward compatibility but is ignored (PostgreSQL connection used instead).

    Args:
        db_path: Ignored (kept for backward compatibility)
        days: Number of days to look back (default: None)
        since: Get items since this datetime (default: None)
              If both days and since are None, defaults to 1 day

    Returns:
        list[dict]: List of parsed items, each with keys: date, title, summary, link

    Side Effects:
        - Reads from PostgreSQL feed_items table via Repository
    """
    from src.db.connection import get_connection
    from src.db.repository import Repository

    repo = Repository()

    # Get newsletter items from PostgreSQL
    with get_connection():
        if since is not None:
            # Get items since a specific datetime
            feed_items = repo.get_feed_items_since(
                source_type="newsletter", since=since
            )
        else:
            # Get items from last N days (default to 1 if not specified)
            if days is None:
                days = 1
            feed_items = repo.get_feed_items(source_type="newsletter", days=days)

    # Convert FeedItem objects to dict format expected by consolidator
    items = []
    for item in feed_items:
        items.append({
            "date": item.date.isoformat() if item.date else None,
            "title": item.title,
            "summary": item.summary or "",
            "link": item.link,
        })

    return items
