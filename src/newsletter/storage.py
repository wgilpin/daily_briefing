"""Storage functions for newsletter aggregator."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


def init_database(db_path: str) -> None:
    """
    Initialize SQLite database with required tables and indexes.

    Creates the database file if it doesn't exist, and creates the following tables:
    - processed_emails: Tracks which emails have been collected and processed
    - newsletter_items: Stores parsed newsletter items extracted from emails

    Also creates indexes for efficient querying.

    Args:
        db_path: Path to SQLite database file (e.g., 'data/newsletter_aggregator.db')

    Side Effects:
        - Creates database file if it doesn't exist
        - Creates tables and indexes
        - Does not modify existing data if tables already exist
    """
    db_path_obj = Path(db_path)

    # Create parent directory if it doesn't exist
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect(str(db_path_obj))
    cursor = conn.cursor()

    try:
        # Create processed_emails table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_emails (
                message_id TEXT PRIMARY KEY,
                sender_email TEXT NOT NULL,
                subject TEXT,
                collected_at TIMESTAMP NOT NULL,
                processed_at TIMESTAMP,
                status TEXT NOT NULL,
                error_message TEXT,
                CHECK (status IN ('collected', 'converted', 'parsed', 'failed'))
            )
            """
        )

        # Create indexes for processed_emails
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sender_email 
            ON processed_emails(sender_email)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_processed_at 
            ON processed_emails(processed_at)
            """
        )

        # Create newsletter_items table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS newsletter_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                item_index INTEGER NOT NULL,
                date TEXT,
                title TEXT NOT NULL,
                summary TEXT,
                link TEXT,
                parsed_at TIMESTAMP NOT NULL,
                raw_data TEXT,
                FOREIGN KEY (message_id) REFERENCES processed_emails(message_id),
                CHECK (item_index >= 0)
            )
            """
        )

        # Create indexes for newsletter_items
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_message_id 
            ON newsletter_items(message_id)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_parsed_at 
            ON newsletter_items(parsed_at)
            """
        )

        # Commit changes
        conn.commit()

    finally:
        conn.close()


def init_data_directories(base_data_dir: str = "data") -> None:
    """
    Initialize data directory structure.

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
    from pathlib import Path

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


def get_processed_message_ids(
    db_path: str, sender_emails: list[str] = None
) -> set[str]:
    """
    Get set of already-processed message IDs.

    Queries the database for message IDs that have been processed.
    Optionally filters by sender email addresses.

    Args:
        db_path: Path to SQLite database file
        sender_emails: Optional list of sender email addresses to filter by

    Returns:
        set[str]: Set of message IDs that have been processed

    Side Effects:
        - Queries database (read-only)
        - Returns empty set if database doesn't exist
    """
    db_path_obj = Path(db_path)

    # Return empty set if database doesn't exist
    if not db_path_obj.exists():
        return set()

    conn = sqlite3.connect(str(db_path_obj))
    cursor = conn.cursor()

    try:
        if sender_emails:
            # Filter by sender emails
            placeholders = ",".join("?" * len(sender_emails))
            cursor.execute(
                f"""
                SELECT message_id FROM processed_emails 
                WHERE sender_email IN ({placeholders})
                """,
                sender_emails,
            )
        else:
            # Get all message IDs
            cursor.execute("SELECT message_id FROM processed_emails")

        results = cursor.fetchall()
        return {row[0] for row in results}

    finally:
        conn.close()


def track_email_processed(
    db_path: str,
    message_id: str,
    sender_email: str,
    status: str,
    subject: str = None,
    error_message: str = None,
) -> None:
    """
    Record email in database as processed.

    Inserts a new record or updates an existing record in the processed_emails table.
    Sets collected_at timestamp for new records, processed_at for status updates.

    Args:
        db_path: Path to SQLite database file
        message_id: Gmail message ID (unique identifier)
        sender_email: Email address of newsletter sender
        status: Processing status ('collected', 'converted', 'parsed', 'failed')
        subject: Optional email subject line
        error_message: Optional error message if status is 'failed'

    Side Effects:
        - Inserts or updates record in processed_emails table
        - Creates database/table if doesn't exist
    """
    db_path_obj = Path(db_path)

    # Ensure database exists
    if not db_path_obj.exists():
        init_database(str(db_path_obj))

    conn = sqlite3.connect(str(db_path_obj))
    cursor = conn.cursor()

    try:
        # Check if record exists
        cursor.execute(
            "SELECT message_id FROM processed_emails WHERE message_id = ?",
            (message_id,),
        )
        exists = cursor.fetchone() is not None

        now = datetime.now().isoformat()

        if exists:
            # Update existing record
            cursor.execute(
                """
                UPDATE processed_emails 
                SET status = ?, 
                    processed_at = ?,
                    error_message = ?
                WHERE message_id = ?
                """,
                (status, now, error_message, message_id),
            )
        else:
            # Insert new record
            cursor.execute(
                """
                INSERT INTO processed_emails 
                (message_id, sender_email, subject, collected_at, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, sender_email, subject, now, status, error_message),
            )

        conn.commit()

    finally:
        conn.close()


def save_email(email: dict, data_dir: str) -> str:
    """
    Save email to file system.

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
    """
    Save markdown content to file system.

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
    """
    Save parsed newsletter items to file system.

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


def insert_newsletter_items(
    db_path: str, message_id: str, parsed_items: list[dict]
) -> None:
    """
    Insert parsed newsletter items into database.

    Inserts parsed items into the newsletter_items table with item_index
    to track multiple items per email.

    Args:
        db_path: Path to SQLite database file
        message_id: Gmail message ID (must exist in processed_emails table)
        parsed_items: List of parsed item dictionaries with keys: date, title, summary, link

    Side Effects:
        - Inserts records into newsletter_items table
        - Creates database/table if doesn't exist
        - Stores raw_data as JSON for reference

    Raises:
        ValueError: If message_id is empty or parsed_items is not a list
    """
    if not message_id:
        raise ValueError("message_id must be non-empty")

    if not isinstance(parsed_items, list):
        raise ValueError("parsed_items must be a list")

    db_path_obj = Path(db_path)

    # Ensure database exists
    if not db_path_obj.exists():
        init_database(str(db_path_obj))

    conn = sqlite3.connect(str(db_path_obj))
    cursor = conn.cursor()

    try:
        now = datetime.now().isoformat()

        for item_index, item in enumerate(parsed_items):
            # Extract fields (with defaults)
            title = item.get("title", "").strip()
            if not title:
                # Skip items without title (required field)
                continue

            date = item.get("date")
            summary = item.get("summary")
            link = item.get("link")

            # Store raw_data as JSON for reference
            raw_data_json = json.dumps(item, ensure_ascii=False)

            # Insert item
            cursor.execute(
                """
                INSERT INTO newsletter_items 
                (message_id, item_index, date, title, summary, link, parsed_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (message_id, item_index, date, title, summary, link, now, raw_data_json),
            )

        conn.commit()

    finally:
        conn.close()


def get_all_parsed_items(db_path: str) -> list[dict]:
    """
    Get all parsed newsletter items from database.

    Queries the newsletter_items table and returns all items as a list of dictionaries.

    Args:
        db_path: Path to SQLite database file

    Returns:
        list[dict]: List of parsed items, each with keys: date, title, summary, link

    Side Effects:
        - Reads from newsletter_items table
        - Returns empty list if no items exist

    Postconditions:
        - Returns list (may be empty)
        - Each item has at least 'title' field
        - Items are ordered by parsed_at DESC (most recent first)
    """
    db_path_obj = Path(db_path)

    if not db_path_obj.exists():
        return []

    conn = sqlite3.connect(str(db_path_obj))
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT date, title, summary, link
            FROM newsletter_items
            ORDER BY parsed_at DESC
            """
        )

        rows = cursor.fetchall()

        # Convert rows to list of dicts
        items = []
        for row in rows:
            item = {
                "date": row[0],
                "title": row[1],
                "summary": row[2],
                "link": row[3],
            }
            items.append(item)

        return items

    finally:
        conn.close()


def save_consolidated_digest(markdown_content: str, output_dir: str) -> str:
    """
    Save consolidated newsletter digest to file system.

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


def apply_retention_policy(
    db_path: str, data_dirs: list[str], retention_limit: int
) -> int:
    """
    Remove oldest records to maintain retention limit.

    Deletes the oldest processed emails and their associated files (emails,
    markdown, parsed items) when the number of records exceeds the retention
    limit. Records are ordered by processed_at timestamp (oldest first).

    Args:
        db_path: Path to SQLite database
        data_dirs: List of data directories to clean
            (e.g., ['data/emails', 'data/markdown', 'data/parsed'])
        retention_limit: Maximum number of records to keep

    Returns:
        int: Number of records deleted

    Side Effects:
        - Deletes database records from processed_emails and newsletter_items
        - Deletes files from data_dirs
        - Updates database

    Preconditions:
        - retention_limit > 0
        - Write permissions on database and data directories

    Postconditions:
        - Only retention_limit most recent records remain
        - Corresponding files deleted
        - Returns count of deleted records
    """
    if retention_limit <= 0:
        raise ValueError("retention_limit must be positive")

    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        return 0  # No database, nothing to clean

    conn = sqlite3.connect(str(db_path_obj))
    cursor = conn.cursor()

    try:
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE processed_at IS NOT NULL")
        total_count = cursor.fetchone()[0]

        # If we're under the limit, nothing to delete
        if total_count <= retention_limit:
            return 0

        # Calculate how many to delete
        records_to_delete = total_count - retention_limit

        # Get oldest records ordered by processed_at ASC
        cursor.execute(
            """
            SELECT message_id 
            FROM processed_emails 
            WHERE processed_at IS NOT NULL
            ORDER BY processed_at ASC 
            LIMIT ?
            """,
            (records_to_delete,),
        )
        message_ids_to_delete = [row[0] for row in cursor.fetchall()]

        if not message_ids_to_delete:
            return 0

        deleted_count = len(message_ids_to_delete)

        # Delete newsletter_items for these message_ids
        placeholders = ",".join("?" * len(message_ids_to_delete))
        cursor.execute(
            f"DELETE FROM newsletter_items WHERE message_id IN ({placeholders})",
            message_ids_to_delete,
        )

        # Delete files from data directories
        for data_dir in data_dirs:
            data_dir_obj = Path(data_dir)
            if not data_dir_obj.exists():
                continue

            for message_id in message_ids_to_delete:
                # Try to delete email JSON file
                email_file = data_dir_obj / f"{message_id}.json"
                if email_file.exists():
                    try:
                        email_file.unlink()
                    except OSError:
                        pass  # Ignore file deletion errors

                # Try to delete markdown file
                markdown_file = data_dir_obj / f"{message_id}.md"
                if markdown_file.exists():
                    try:
                        markdown_file.unlink()
                    except OSError:
                        pass  # Ignore file deletion errors

        # Delete processed_emails records
        cursor.execute(
            f"DELETE FROM processed_emails WHERE message_id IN ({placeholders})",
            message_ids_to_delete,
        )

        conn.commit()

        return deleted_count

    finally:
        conn.close()

