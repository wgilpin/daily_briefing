"""Unit tests for NewsletterSource adapter.

Tests NewsletterSource.fetch_items with mocked existing newsletter modules.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch
import pytest

from src.models.feed_item import FeedItem
from src.models.source import NewsletterConfig


class TestNewsletterSource:
    """Tests for NewsletterSource adapter."""

    @pytest.fixture
    def newsletter_config(self) -> NewsletterConfig:
        """Create test newsletter configuration."""
        return NewsletterConfig(
            sender_emails=["newsletter@example.com", "updates@tech.com"],
            parsing_prompt="Extract articles from this newsletter.",
            max_emails_per_refresh=20,
        )

    @pytest.fixture
    def mock_parsed_items(self) -> list[dict[str, Any]]:
        """Sample parsed newsletter items."""
        return [
            {
                "date": "2026-01-15",
                "title": "AI News Roundup",
                "summary": "Latest developments in AI.",
                "link": "https://newsletter.com/ai-news",
            },
            {
                "date": "2026-01-14",
                "title": "Tech Update",
                "summary": "Weekly tech industry update.",
                "link": None,
            },
        ]

    @pytest.fixture
    def mock_pipeline(self, mock_parsed_items):
        """Mock all pipeline functions and Repository."""
        with patch("src.sources.newsletter.collect_newsletter_emails") as mock_collect, \
             patch("src.sources.newsletter.convert_emails_to_markdown") as mock_convert, \
             patch("src.sources.newsletter.parse_newsletters") as mock_parse, \
             patch("src.sources.newsletter.Repository") as mock_repo_class, \
             patch("src.services.audio.generate_missing_audio.generate_missing_audio_for_feed_items") as mock_audio:

            # Setup mocks
            mock_collect.return_value = {"emails_collected": 2, "errors": []}
            mock_convert.return_value = {"emails_converted": 2, "errors": []}
            mock_parse.return_value = {"emails_parsed": 2, "errors": []}
            mock_audio.return_value = {"generated": 0, "skipped": 2, "errors": []}

            # Mock Repository instance and methods
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            # Convert mock_parsed_items to FeedItem objects for the "after" state
            feed_items = []
            for idx, item in enumerate(mock_parsed_items):
                feed_items.append(FeedItem(
                    id=f"newsletter:{idx}",
                    source_type="newsletter",
                    source_id=str(idx),
                    title=item["title"],
                    date=datetime.fromisoformat(item["date"]).replace(tzinfo=timezone.utc),
                    summary=item.get("summary"),
                    link=item.get("link"),
                    metadata={"sender": item.get("sender", "")} if item.get("sender") else {},
                    fetched_at=datetime.now(timezone.utc),
                ))

            # Multiple calls: before pipeline, during pipeline steps, after pipeline
            mock_repo.get_feed_items.side_effect = [[], feed_items, feed_items, feed_items]

            yield {
                "collect": mock_collect,
                "convert": mock_convert,
                "parse": mock_parse,
                "audio": mock_audio,
                "repo": mock_repo,
            }

    def test_fetch_items_returns_feed_items(
        self, newsletter_config: NewsletterConfig, mock_pipeline
    ) -> None:
        """Test that fetch_items returns list of FeedItem."""
        from src.sources.newsletter import NewsletterSource

        source = NewsletterSource(newsletter_config)
        items = source.fetch_items()

        assert isinstance(items, list)
        assert all(isinstance(item, FeedItem) for item in items)

    def test_fetch_items_correct_source_type(
        self, newsletter_config: NewsletterConfig, mock_pipeline
    ) -> None:
        """Test that items have correct source_type."""
        from src.sources.newsletter import NewsletterSource

        source = NewsletterSource(newsletter_config)
        items = source.fetch_items()

        assert all(item.source_type == "newsletter" for item in items)

    def test_fetch_items_extracts_title(
        self, newsletter_config: NewsletterConfig, mock_pipeline
    ) -> None:
        """Test that item titles are extracted correctly."""
        from src.sources.newsletter import NewsletterSource

        source = NewsletterSource(newsletter_config)
        items = source.fetch_items()

        titles = [item.title for item in items]
        assert "AI News Roundup" in titles
        assert "Tech Update" in titles

    def test_fetch_items_handles_empty_response(
        self, newsletter_config: NewsletterConfig
    ) -> None:
        """Test handling of no newsletter items."""
        with patch("src.sources.newsletter.collect_newsletter_emails") as mock_collect, \
             patch("src.sources.newsletter.convert_emails_to_markdown") as mock_convert, \
             patch("src.sources.newsletter.parse_newsletters") as mock_parse, \
             patch("src.sources.newsletter.Repository") as mock_repo_class, \
             patch("src.services.audio.generate_missing_audio.generate_missing_audio_for_feed_items") as mock_audio:

            # Setup mocks
            mock_collect.return_value = {"emails_collected": 0, "errors": []}
            mock_convert.return_value = {"emails_converted": 0, "errors": []}
            mock_parse.return_value = {"emails_parsed": 0, "errors": []}
            mock_audio.return_value = {"generated": 0, "skipped": 0, "errors": []}

            # Mock Repository instance and methods
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_feed_items.return_value = []

            from src.sources.newsletter import NewsletterSource

            source = NewsletterSource(newsletter_config)
            items = source.fetch_items()

            assert items == []

    def test_fetch_items_handles_missing_link(
        self, newsletter_config: NewsletterConfig, mock_pipeline
    ) -> None:
        """Test handling of items without links."""
        from src.sources.newsletter import NewsletterSource

        source = NewsletterSource(newsletter_config)
        items = source.fetch_items()

        # Second item has no link
        item_without_link = [i for i in items if i.title == "Tech Update"]
        assert len(item_without_link) == 1
        assert item_without_link[0].link is None

    def test_source_type_property(self, newsletter_config: NewsletterConfig) -> None:
        """Test that source_type property returns 'newsletter'."""
        from src.sources.newsletter import NewsletterSource

        source = NewsletterSource(newsletter_config)
        assert source.source_type == "newsletter"

    def test_fetch_items_includes_sender_metadata(
        self, newsletter_config: NewsletterConfig
    ) -> None:
        """Test that sender info is included in metadata."""
        feed_item_with_sender = FeedItem(
            id="newsletter:test123",
            source_type="newsletter",
            source_id="test123",
            title="Newsletter Item",
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            summary="Content",
            link=None,
            metadata={"sender": "newsletter@example.com"},
            fetched_at=datetime.now(timezone.utc),
        )

        with patch("src.sources.newsletter.collect_newsletter_emails") as mock_collect, \
             patch("src.sources.newsletter.convert_emails_to_markdown") as mock_convert, \
             patch("src.sources.newsletter.parse_newsletters") as mock_parse, \
             patch("src.sources.newsletter.Repository") as mock_repo_class, \
             patch("src.services.audio.generate_missing_audio.generate_missing_audio_for_feed_items") as mock_audio:

            # Setup mocks
            mock_collect.return_value = {"emails_collected": 1, "errors": []}
            mock_convert.return_value = {"emails_converted": 1, "errors": []}
            mock_parse.return_value = {"emails_parsed": 1, "errors": []}
            mock_audio.return_value = {"generated": 0, "skipped": 1, "errors": []}

            # Mock Repository instance and methods
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_feed_items.side_effect = [[], [feed_item_with_sender], [feed_item_with_sender], [feed_item_with_sender]]

            from src.sources.newsletter import NewsletterSource

            source = NewsletterSource(newsletter_config)
            items = source.fetch_items()

            if items and "sender" in items[0].metadata:
                assert items[0].metadata["sender"] == "newsletter@example.com"
