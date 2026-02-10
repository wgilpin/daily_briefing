"""Newsletter feed source adapter.

Wraps existing src/newsletter/ functionality to implement FeedSource protocol.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.models.feed_item import FeedItem
from src.models.source import NewsletterConfig
from src.db.repository import Repository
from src.newsletter.email_collector import (
    collect_newsletter_emails,
    convert_emails_to_markdown,
    parse_newsletters,
)

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
    ) -> None:
        """Initialize Newsletter source with configuration.

        Args:
            config: NewsletterConfig with settings
        """
        self._config = config

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

        # Initialize repository
        repo = Repository()

        # Track items before pipeline starts (to identify new ones)
        items_before = {item.id for item in repo.get_feed_items(source_type="newsletter", limit=1000)}

        # Step 1: Collect emails from Gmail
        logger.info(f"Step 1: Collecting emails from Gmail (days_lookback={self._config.days_lookback})")
        collect_result = collect_newsletter_emails(
            config_path="config/senders.json",
            credentials_path="config/credentials.json",
            tokens_path="data/tokens.json",
            data_dir="data/emails",
            days_lookback=self._config.days_lookback,
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
            config_path="config/senders.json",
            emails_dir="data/emails",
        )

        if parse_result["errors"]:
            for error in parse_result["errors"]:
                logger.warning(f"Newsletter parsing: {error}")

        logger.info(f"Parsed {parse_result['emails_parsed']} newsletters")

        # Step 3: Apply topic exclusions before clustering
        try:
            from src.newsletter.config import load_config as load_newsletter_config
            newsletter_cfg = load_newsletter_config()
            excluded_topics = newsletter_cfg.excluded_topics
            if excluded_topics:
                candidates = repo.get_feed_items(source_type="newsletter", limit=1000, days=self._config.days_lookback)
                excluded_count = 0
                for item in candidates:
                    text = f"{item.title} {item.summary or ''}".lower()
                    if any(topic.lower() in text for topic in excluded_topics):
                        repo.delete_feed_item(item.id)
                        excluded_count += 1
                        logger.info(f"Excluded item: {item.title[:60]}")
                if excluded_count:
                    logger.info(f"Step 3: Excluded {excluded_count} items matching {excluded_topics}")
        except Exception as e:
            logger.error(f"Exclusion step failed: {e}")

        # Step 3.5: Deduplicate newly-added items before audio generation
        logger.info("Step 3.5: Starting deduplication")
        try:
            import os
            import google.genai as genai
            from src.newsletter.deduplicator import deduplicate_items
            from src.newsletter.id_generation import generate_newsletter_id

            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if gemini_api_key:
                llm_client = genai.Client(api_key=gemini_api_key)
                from src.newsletter.config import load_config as _load_cfg
                model_name = _load_cfg().models["consolidation"]

                all_newsletter_items = repo.get_feed_items(source_type="newsletter", limit=1000, days=self._config.days_lookback)

                if len(all_newsletter_items) > 1:
                    logger.info(f"Step 3.5: Deduplicating {len(all_newsletter_items)} newsletter items")
                    items_as_dicts = [
                        {
                            "date": item.date.isoformat() if item.date else None,
                            "title": item.title,
                            "summary": item.summary or "",
                            "link": item.link,
                            "source_type": item.source_type,
                        }
                        for item in all_newsletter_items
                    ]
                    deduped = deduplicate_items(items_as_dicts, llm_client, model_name)
                    if len(deduped) < len(all_newsletter_items):
                        for item in all_newsletter_items:
                            repo.delete_feed_item(item.id)
                        merged = []
                        for d in deduped:
                            item_id = generate_newsletter_id(d.get("title", ""), d.get("date", ""))
                            try:
                                item_date = datetime.fromisoformat(d["date"].replace("Z", "+00:00")) if d.get("date") else datetime.now(timezone.utc)
                            except (ValueError, AttributeError):
                                item_date = datetime.now(timezone.utc)
                            if item_date.tzinfo is None:
                                item_date = item_date.replace(tzinfo=timezone.utc)
                            merged.append(FeedItem(
                                id=item_id,
                                source_type="newsletter",
                                source_id=item_id.split(":", 1)[1],
                                title=d.get("title", "Untitled"),
                                date=item_date,
                                summary=d.get("summary") or None,
                                link=d.get("link"),
                                metadata={},
                                fetched_at=datetime.now(timezone.utc),
                            ))
                        repo.save_feed_items(merged)
                        logger.info(f"Deduplication: {len(all_newsletter_items)} → {len(deduped)} items")
        except Exception as e:
            import traceback
            logger.error(f"Deduplication step failed: {e}\n{traceback.format_exc()}")

        # Step 4: Generate audio for any items missing audio files
        logger.info("Step 4: Generating audio for items")
        from src.services.audio.generate_missing_audio import generate_missing_audio_for_feed_items
        audio_result = generate_missing_audio_for_feed_items()
        logger.info(f"Generated audio for {audio_result['generated']} items (skipped {audio_result['skipped']} existing)")

        # Step 5: Fetch items from PostgreSQL and return only NEW items
        all_items = repo.get_feed_items(source_type="newsletter", limit=1000)
        new_items = [item for item in all_items if item.id not in items_before]

        logger.info(f"Returning {len(new_items)} new newsletter items (out of {len(all_items)} total)")
        return new_items
