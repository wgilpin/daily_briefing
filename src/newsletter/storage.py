"""Storage functions for newsletter aggregator.

File-based storage operations for emails, markdown, and parsed items.
Database operations have been migrated to PostgreSQL repository (src/db/repository.py).
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


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


def save_consolidated_digest(markdown_content: str, output_dir: str) -> str:
    """Save consolidated newsletter digest to file system.

    Saves markdown content to a timestamped file in the specified directory.
    File is named: digest_{timestamp}.md

    Args:
        markdown_content: Markdown text of consolidated newsletter
        output_dir: Base output directory path (e.g., 'data/output')

    Returns:
        str: Path to saved file

    Side Effects:
        - Creates file {output_dir}/digest_{timestamp}.md
        - Writes markdown content
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

    return str(file_path)


def get_recent_parsed_items(db_path: str, days: int = 1) -> list[dict]:
    """Get parsed newsletter items from the last N days.

    Queries PostgreSQL feed_items table for newsletter items within the
    specified number of days. The db_path parameter is kept for backward
    compatibility but is ignored (PostgreSQL connection used instead).

    Args:
        db_path: Ignored (kept for backward compatibility)
        days: Number of days to look back (default: 1)

    Returns:
        list[dict]: List of parsed items, each with keys: date, title, summary, link

    Side Effects:
        - Reads from PostgreSQL feed_items table via Repository
    """
    from src.db.connection import get_connection
    from src.db.repository import Repository

    repo = Repository()

    # Calculate cutoff date
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get newsletter items from PostgreSQL
    with get_connection():
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
