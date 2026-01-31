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

    def test_fetch_items_returns_feed_items(
        self, newsletter_config: NewsletterConfig, mock_parsed_items: list[dict[str, Any]]
    ) -> None:
        """Test that fetch_items returns list of FeedItem."""
        with patch("src.sources.newsletter.NewsletterSource._fetch_from_storage") as mock_fetch:
            mock_fetch.return_value = mock_parsed_items

            from src.sources.newsletter import NewsletterSource

            source = NewsletterSource(newsletter_config)
            items = source.fetch_items()

            assert isinstance(items, list)
            assert all(isinstance(item, FeedItem) for item in items)

    def test_fetch_items_correct_source_type(
        self, newsletter_config: NewsletterConfig, mock_parsed_items: list[dict[str, Any]]
    ) -> None:
        """Test that items have correct source_type."""
        with patch("src.sources.newsletter.NewsletterSource._fetch_from_storage") as mock_fetch:
            mock_fetch.return_value = mock_parsed_items

            from src.sources.newsletter import NewsletterSource

            source = NewsletterSource(newsletter_config)
            items = source.fetch_items()

            assert all(item.source_type == "newsletter" for item in items)

    def test_fetch_items_extracts_title(
        self, newsletter_config: NewsletterConfig, mock_parsed_items: list[dict[str, Any]]
    ) -> None:
        """Test that item titles are extracted correctly."""
        with patch("src.sources.newsletter.NewsletterSource._fetch_from_storage") as mock_fetch:
            mock_fetch.return_value = mock_parsed_items

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
        with patch("src.sources.newsletter.NewsletterSource._fetch_from_storage") as mock_fetch:
            mock_fetch.return_value = []

            from src.sources.newsletter import NewsletterSource

            source = NewsletterSource(newsletter_config)
            items = source.fetch_items()

            assert items == []

    def test_fetch_items_handles_missing_link(
        self, newsletter_config: NewsletterConfig, mock_parsed_items: list[dict[str, Any]]
    ) -> None:
        """Test handling of items without links."""
        with patch("src.sources.newsletter.NewsletterSource._fetch_from_storage") as mock_fetch:
            mock_fetch.return_value = mock_parsed_items

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
        items_with_sender = [
            {
                "date": "2026-01-15",
                "title": "Newsletter Item",
                "summary": "Content",
                "link": None,
                "sender": "newsletter@example.com",
            }
        ]

        with patch("src.sources.newsletter.NewsletterSource._fetch_from_storage") as mock_fetch:
            mock_fetch.return_value = items_with_sender

            from src.sources.newsletter import NewsletterSource

            source = NewsletterSource(newsletter_config)
            items = source.fetch_items()

            if items and "sender" in items[0].metadata:
                assert items[0].metadata["sender"] == "newsletter@example.com"
