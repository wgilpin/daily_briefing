"""Email collection orchestration for newsletter aggregator."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from src.db.repository import Repository
from src.newsletter.gmail_client import authenticate_gmail, collect_emails
from src.newsletter.markdown_converter import convert_to_markdown
from src.newsletter.parser import create_llm_client, parse_newsletter
from src.newsletter.storage import (
    save_email,
    save_markdown,
    save_parsed_items,
)
from src.utils.config import load_config

logger = logging.getLogger(__name__)


def collect_newsletter_emails(
    config_path: str = "config/senders.json",
    credentials_path: str = "config/credentials.json",
    tokens_path: str = "data/tokens.json",
    data_dir: str = "data/emails",
    days_lookback: Optional[int] = None,
) -> dict:
    """
    Collect newsletter emails from Gmail.

    Authenticates with Gmail API, retrieves emails from configured senders,
    and saves them locally. Tracks processed emails in PostgreSQL database.

    Args:
        config_path: Path to newsletter configuration file (default: config/senders.json)
        credentials_path: Path to Gmail OAuth credentials (default: config/credentials.json)
        tokens_path: Path to store OAuth tokens (default: data/tokens.json)
        data_dir: Directory to save email files (default: data/emails)
        days_lookback: Days to look back for emails (overrides config, default: from config or 30)

    Returns:
        dict: Result dictionary with keys:
            - success (bool): Whether collection succeeded
            - emails_collected (int): Number of new emails collected
            - errors (list[str]): List of error messages

    Side Effects:
        - Authenticates with Gmail (may open browser for OAuth)
        - Saves email JSON files to data/emails/
        - Updates database with processed message IDs
    """
    result = {
        "success": False,
        "emails_collected": 0,
        "errors": [],
    }

    # Load configuration
    try:
        config = load_config(config_path)
        senders = config.get("senders", {})
        # Use provided days_lookback or fall back to config or default
        if days_lookback is None:
            days_lookback = config.get("days_lookback", 30)
    except Exception as e:
        result["errors"].append(f"Failed to load configuration: {str(e)}")
        return result

    if not senders:
        result["errors"].append("No senders configured in config/senders.json")
        return result

    # Get enabled sender emails
    sender_emails = [
        email for email, cfg in senders.items() if cfg.get("enabled", True)
    ]

    if not sender_emails:
        result["errors"].append("No enabled senders found in configuration")
        return result

    # Authenticate with Gmail
    try:
        service = authenticate_gmail(credentials_path, tokens_path)
    except Exception as e:
        result["errors"].append(f"Gmail authentication failed: {str(e)}")
        return result

    # Get already processed message IDs
    try:
        repo = Repository()
        processed_ids = repo.get_processed_message_ids(sender_emails)
    except Exception as e:
        result["errors"].append(f"Failed to get processed message IDs: {str(e)}")
        return result

    # Get max emails per sender from config (default 1)
    max_per_sender = config.get("max_emails_per_sender", 1)

    # Collect emails
    try:
        emails = collect_emails(service, sender_emails, processed_ids, days_lookback, max_per_sender)
    except Exception as e:
        result["errors"].append(f"Failed to collect emails: {str(e)}")
        return result

    # Save emails and track in database
    emails_collected = 0
    for email in emails:
        try:
            # Save email to file
            save_email(email, data_dir)

            # Track in database
            repo.track_email_processed(
                email["message_id"],
                email["sender"],
                "collected",
                subject=email.get("subject"),
            )

            emails_collected += 1
        except Exception as e:
            result["errors"].append(
                f"Failed to save email {email.get('message_id', 'unknown')}: {str(e)}"
            )

    result["success"] = True
    result["emails_collected"] = emails_collected

    return result


def convert_emails_to_markdown(
    emails_dir: str = "data/emails",
    markdown_dir: str = "data/markdown",
) -> dict:
    """
    Convert collected email files to markdown format.

    Reads email JSON files, converts HTML/text content to markdown,
    and saves markdown files. Updates database status.

    Args:
        emails_dir: Directory containing email JSON files (default: data/emails)
        markdown_dir: Directory to save markdown files (default: data/markdown)

    Returns:
        dict: Result dictionary with keys:
            - success (bool): Whether conversion succeeded
            - emails_converted (int): Number of emails converted
            - errors (list[str]): List of error messages

    Side Effects:
        - Reads email JSON files from data/emails/
        - Saves markdown files to data/markdown/
        - Updates database status to 'converted'
    """
    result = {
        "success": False,
        "emails_converted": 0,
        "errors": [],
    }

    emails_path = Path(emails_dir)

    if not emails_path.exists():
        result["errors"].append(f"Emails directory not found: {emails_dir}")
        return result

    # Get all email JSON files
    email_files = list(emails_path.glob("*.json"))

    if not email_files:
        result["errors"].append("No email files found to convert")
        result["success"] = True  # Not an error, just nothing to do
        return result

    emails_converted = 0
    repo = Repository()

    for email_file in email_files:
        message_id = email_file.stem

        try:
            # Load email
            with open(email_file, "r", encoding="utf-8") as f:
                email = json.load(f)

            # Convert to markdown
            markdown_content = convert_to_markdown(email)

            # Save markdown
            save_markdown(message_id, markdown_content, markdown_dir)

            # Update status to converted
            repo.track_email_processed(message_id, email.get("sender"), "converted")

            emails_converted += 1

        except Exception as e:
            result["errors"].append(
                f"Failed to convert {email_file.name}: {str(e)}"
            )
            continue

    result["success"] = True
    result["emails_converted"] = emails_converted

    return result


def _parse_single_newsletter(
    markdown_file: Path,
    llm_client,
    senders: dict,
    default_parsing_prompt: str,
    model_name: str,
    parsed_dir: str,
    total_count: int,
    index: int,
) -> tuple[str, bool, str, list]:
    """
    Parse a single newsletter file.

    Args:
        markdown_file: Path to markdown file
        llm_client: LLM client instance
        senders: Dictionary of sender configurations
        default_parsing_prompt: Default parsing prompt
        model_name: Gemini model name to use
        parsed_dir: Directory to save parsed items
        total_count: Total number of files being processed
        index: Current file index (1-based)

    Returns:
        tuple: (message_id, success, error_message, parsed_items)
    """
    message_id = markdown_file.stem
    logger.info(f"[{index}/{total_count}] Processing {message_id}")

    repo = Repository()

    try:
        # Check if already parsed by checking if feed items exist for this message
        from src.db.connection import get_connection
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT status FROM processed_emails WHERE message_id = %s
                    """,
                    (message_id,)
                )
                email_status = cursor.fetchone()

            if email_status and email_status[0] == "parsed":
                logger.info(f"[{index}/{total_count}] Skipping {message_id} - already parsed")
                return (message_id, True, None, [])
        
        # Load markdown content
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        
        if not markdown_content.strip():
            return (message_id, False, f"Markdown file {markdown_file.name} is empty", [])
        
        # Determine sender from email metadata
        email_file = Path(f"data/emails/{message_id}.json")
        sender_email = None
        if email_file.exists():
            with open(email_file, "r", encoding="utf-8") as f:
                email_data = json.load(f)
                sender_email = email_data.get("sender")
        
        # Get sender-specific prompt or use default
        # Falls back to default_parsing_prompt if sender-specific one is empty/missing
        parsing_prompt = default_parsing_prompt
        if sender_email and sender_email in senders:
            sender_config = senders[sender_email]
            sender_prompt = sender_config.get("parsing_prompt", "").strip()
            if sender_prompt:
                parsing_prompt = sender_prompt
        
        # Parse with LLM
        logger.info(f"[{index}/{total_count}] Calling {model_name} for {message_id}...")
        parsed_items = parse_newsletter(markdown_content, parsing_prompt, llm_client, model_name)
        logger.info(f"[{index}/{total_count}] Extracted {len(parsed_items)} items from {message_id}")

        # Save parsed items to file and convert to FeedItem format for PostgreSQL
        if parsed_items:
            from datetime import datetime, timezone
            from src.models.feed_item import FeedItem
            from src.newsletter.id_generation import generate_newsletter_id

            # Save to file for legacy compatibility
            save_parsed_items(message_id, parsed_items, parsed_dir)

            # Convert to FeedItem objects and save to PostgreSQL
            feed_items = []
            for item in parsed_items:
                try:
                    # Generate stable ID using SHA-256
                    item_id = generate_newsletter_id(
                        item.get("title", ""),
                        item.get("date", "")
                    )

                    # Parse date string to datetime
                    date_str = item.get("date", "")
                    try:
                        if date_str:
                            item_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            item_date = datetime.now(timezone.utc)
                    except (ValueError, AttributeError):
                        item_date = datetime.now(timezone.utc)

                    # Ensure timezone-aware datetime
                    if item_date.tzinfo is None:
                        item_date = item_date.replace(tzinfo=timezone.utc)

                    # Build metadata
                    metadata = {}
                    if sender_email:
                        metadata["sender"] = sender_email
                    metadata["message_id"] = message_id

                    # Create FeedItem
                    feed_item = FeedItem(
                        id=item_id,
                        source_type="newsletter",
                        source_id=item_id.split(":", 1)[1],  # Extract hash part after "newsletter:"
                        title=item.get("title", "Untitled"),
                        date=item_date,
                        summary=item.get("summary"),
                        link=item.get("link"),
                        metadata=metadata,
                        fetched_at=datetime.now(timezone.utc),
                    )
                    feed_items.append(feed_item)
                except Exception as e:
                    logger.warning(f"Failed to convert item to FeedItem: {e}")
                    continue

            # Save all feed items to PostgreSQL
            if feed_items:
                repo.save_feed_items(feed_items)

        # Update status
        repo.track_email_processed(message_id, sender_email, "parsed")

        return (message_id, True, None, parsed_items)

    except Exception as e:
        error_msg = f"Error parsing {message_id}: {str(e)}"
        logger.error(f"[{index}/{total_count}] {error_msg}")
        try:
            repo.track_email_processed(
                message_id, sender_email or "", "error", error_message=error_msg
            )
        except:
            pass
        return (message_id, False, error_msg, [])


def parse_newsletters(
    markdown_dir: str = "data/markdown",
    parsed_dir: str = "data/parsed",
    config_path: str = "config/senders.json",
    emails_dir: str = "data/emails",
    max_workers: int = 5,
) -> dict:
    """
    Parse newsletter markdown files using LLM with parallel processing.

    Loads markdown files and uses LLM with configurable prompts to extract
    structured newsletter items. Processes multiple newsletters in parallel
    for better performance. Saves parsed items and tracks status.

    Args:
        markdown_dir: Directory containing markdown files
        parsed_dir: Directory to save parsed JSON files
        config_path: Path to config/senders.json
        emails_dir: Directory containing email files (to get sender info)
        max_workers: Maximum number of parallel workers (default: 5)

    Returns:
        dict: Parsing results with keys:
            - success: bool indicating if parsing succeeded
            - emails_parsed: int number of emails parsed
            - errors: list of error messages (if any)

    Side Effects:
        - Reads markdown files from data/markdown/
        - Makes LLM API calls (in parallel)
        - Saves parsed items to data/parsed/
        - Updates database status to 'parsed' or 'error'
    """
    result = {
        "success": False,
        "emails_parsed": 0,
        "errors": [],
    }

    markdown_path = Path(markdown_dir)

    if not markdown_path.exists():
        result["errors"].append(f"Markdown directory not found: {markdown_dir}")
        return result

    # Load configuration
    try:
        config = load_config(config_path)
        senders = config.get("senders", {})
        # Models are validated in load_config - will raise ValueError if missing
        parsing_model = config["models"]["parsing"]
        # Use config max_workers if provided, otherwise use function parameter default
        if "max_workers" in config:
            max_workers = config["max_workers"]
        default_parsing_prompt = config.get(
            "default_parsing_prompt",
            "Extract articles from this newsletter. "
            "Return a JSON array with items containing: date, title, summary, link (optional).",
        )
    except Exception as e:
        result["errors"].append(f"Failed to load configuration: {str(e)}")
        return result

    # Create LLM client
    try:
        llm_client = create_llm_client()
    except ValueError as e:
        result["errors"].append(
            f"LLM client setup failed: {str(e)}\n"
            "Please set GEMINI_API_KEY environment variable."
        )
        result["success"] = False
        return result
    except Exception as e:
        result["errors"].append(f"Failed to create LLM client: {str(e)}")
        result["success"] = False
        return result

    # Get all markdown files
    markdown_files = list(markdown_path.glob("*.md"))

    if not markdown_files:
        result["errors"].append("No markdown files found to parse")
        result["success"] = True  # Not an error, just nothing to do
        return result

    total_files = len(markdown_files)
    logger.info(f"Found {total_files} markdown files to process (using {max_workers} parallel workers, model: {parsing_model})")
    
    emails_parsed = 0
    errors = []
    
    # Process newsletters in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(
                _parse_single_newsletter,
                markdown_file,
                llm_client,
                senders,
                default_parsing_prompt,
                parsing_model,
                parsed_dir,
                total_files,
                idx,
            ): markdown_file
            for idx, markdown_file in enumerate(markdown_files, 1)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            markdown_file = future_to_file[future]
            try:
                message_id, success, error_msg, parsed_items = future.result()
                if success and parsed_items:  # Only count if actually parsed (not skipped)
                    emails_parsed += 1
                if error_msg:
                    errors.append(error_msg)
            except Exception as e:
                error_message = f"Unexpected error processing {markdown_file.name}: {str(e)}"
                logger.error(error_message)
                errors.append(error_message)
    
    # Update result with collected data
    result["errors"] = errors
    result["emails_parsed"] = emails_parsed
    
    # Mark as successful if at least one email was parsed or no errors occurred
    if emails_parsed > 0 or (not errors and markdown_files):
        result["success"] = True
    elif not markdown_files:
        result["success"] = True  # No files to parse is not a failure
    else:
        result["success"] = False
        if not errors:
            result["errors"].append("No newsletters could be parsed. Check GEMINI_API_KEY and model availability.")
    
    logger.info(f"Parsing complete: {emails_parsed} newsletters parsed, {len(errors)} errors")

    # Apply retention policy for PostgreSQL feed items
    try:
        retention_limit = config.get("retention_limit", 100)
        if retention_limit > 0:
            repo = Repository()
            deleted_count = repo.delete_old_feed_items("newsletter", retention_limit)
            if deleted_count > 0:
                logger.info(f"Retention policy applied: {deleted_count} old feed item(s) deleted from PostgreSQL")
    except Exception as e:
        logger.warning(f"Failed to apply retention policy: {str(e)}")
        # Don't fail the whole operation if retention policy fails

    return result
