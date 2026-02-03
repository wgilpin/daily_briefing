"""Newsletter feed source adapter.

Wraps existing src/newsletter/ functionality to implement FeedSource protocol.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.models.feed_item import FeedItem
from src.models.source import NewsletterConfig
from src.newsletter.email_collector import (
    collect_newsletter_emails,
    convert_emails_to_markdown,
    parse_newsletters,
)
from src.newsletter.storage import get_all_parsed_items

logger = logging.getLogger(__name__)


class NewsletterSource:
    """Newsletter feed source implementing FeedSource protocol.

    Wraps the existing newsletter storage to fetch items and convert them
    to the unified FeedItem format.
    """

    source_type: str = "newsletter"

    def __init__(
        self,
        config: NewsletterConfig,
        db_path: str = "data/newsletter_aggregator.db",
    ) -> None:
        """Initialize Newsletter source with configuration.

        Args:
            config: NewsletterConfig with settings
            db_path: Path to SQLite database (legacy storage)
        """
        self._config = config
        self._db_path = db_path

    def fetch_items(self) -> list[FeedItem]:
        """Fetch newsletter items from Gmail and storage.

        Executes the full newsletter collection pipeline:
        1. Collect new emails from Gmail
        2. Convert emails to markdown
        3. Parse newsletters with LLM
        4. Return items from recent emails only (based on config lookback period)

        Returns:
            List of FeedItem objects from recently collected newsletters
        """
        # Execute newsletter collection pipeline
        logger.info("Starting newsletter collection pipeline")

        # Track items before pipeline starts (to identify new ones)
        items_before = set(item.get("title") for item in self._fetch_from_storage())

        # Step 1: Collect emails from Gmail
        logger.info("Step 1: Collecting emails from Gmail")
        collect_result = collect_newsletter_emails(
            config_path="config/senders.json",
            credentials_path="config/credentials.json",
            tokens_path="data/tokens.json",
            data_dir="data/emails",
            db_path=self._db_path,
        )

        if collect_result["errors"]:
            for error in collect_result["errors"]:
                logger.warning(f"Email collection: {error}")

        logger.info(f"Collected {collect_result['emails_collected']} new emails")

        # If no new emails, skip remaining steps
        if collect_result['emails_collected'] == 0:
            logger.info("No new emails collected, skipping conversion and parsing")
            return []

        # Step 2: Convert emails to markdown
        logger.info("Step 2: Converting emails to markdown")
        convert_result = convert_emails_to_markdown(
            emails_dir="data/emails",
            markdown_dir="data/markdown",
            db_path=self._db_path,
        )

        if convert_result["errors"]:
            for error in convert_result["errors"]:
                logger.warning(f"Markdown conversion: {error}")

        logger.info(f"Converted {convert_result['emails_converted']} emails to markdown")

        # Step 3: Parse newsletters with LLM
        logger.info("Step 3: Parsing newsletters with LLM")
        parse_result = parse_newsletters(
            markdown_dir="data/markdown",
            parsed_dir="data/parsed",
            db_path=self._db_path,
            config_path="config/senders.json",
            emails_dir="data/emails",
        )

        if parse_result["errors"]:
            for error in parse_result["errors"]:
                logger.warning(f"Newsletter parsing: {error}")

        logger.info(f"Parsed {parse_result['emails_parsed']} newsletters")

        # Step 4: Fetch items from storage and return only NEW items
        all_items = self._fetch_from_storage()
        new_items = [item for item in all_items if item.get("title") not in items_before]

        # Convert to FeedItem format
        feed_items = [
            item
            for item in (self._to_feed_item(raw, idx) for idx, raw in enumerate(new_items))
            if item is not None
        ]

        logger.info(f"Returning {len(feed_items)} new newsletter items (out of {len(all_items)} total)")
        return feed_items

    def _fetch_from_storage(self) -> list[dict[str, Any]]:
        """Fetch raw items from storage.

        This method exists to allow easy mocking in tests.

        Returns:
            List of raw newsletter item dictionaries
        """
        return get_all_parsed_items(self._db_path)

    def _to_feed_item(
        self, newsletter_item: dict[str, Any], index: int
    ) -> Optional[FeedItem]:
        """Convert newsletter item to FeedItem.

        Args:
            newsletter_item: Raw newsletter item dictionary
            index: Item index for ID generation

        Returns:
            FeedItem with normalized data, or None if invalid
        """
        # Extract title (required)
        title = newsletter_item.get("title", "").strip()
        if not title:
            return None

        # Generate unique ID
        # Use a hash of title and date for uniqueness
        item_hash = hash(f"{title}:{newsletter_item.get('date', '')}")
        item_id = f"newsletter:{abs(item_hash)}"

        # Extract date
        date_str = newsletter_item.get("date", "")
        date = self._parse_date(date_str)

        # Extract other fields
        summary = newsletter_item.get("summary", "")
        link = newsletter_item.get("link")
        sender = newsletter_item.get("sender", "")

        # Build metadata
        metadata: dict[str, str] = {}
        if sender:
            metadata["sender"] = sender

        return FeedItem(
            id=item_id,
            source_type="newsletter",
            source_id=str(abs(item_hash)),
            title=title,
            date=date,
            summary=summary if summary else None,
            link=link if link else None,
            metadata=metadata,
            fetched_at=datetime.now(timezone.utc),
        )

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime.

        Args:
            date_str: Date string in various formats

        Returns:
            Parsed datetime (or current time if parsing fails)
        """
        if not date_str:
            return datetime.now(timezone.utc)

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        # Default to current time if parsing fails
        return datetime.now(timezone.utc)
