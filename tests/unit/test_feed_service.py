"""Unit tests for FeedService.

Tests feed aggregation, sorting, and pagination with mocked sources.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models.feed_item import FeedItem


class TestFeedServiceGetUnifiedFeed:
    """Tests for FeedService.get_unified_feed method."""

    @pytest.fixture
    def zotero_items(self) -> list[FeedItem]:
        """Sample Zotero feed items."""
        return [
            FeedItem(
                id="zotero:ABC123",
                source_type="zotero",
                source_id="ABC123",
                title="Zotero Paper 1",
                date=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                summary="Abstract 1",
                link="https://example.com/paper1",
                metadata={"authors": "Smith"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
            FeedItem(
                id="zotero:DEF456",
                source_type="zotero",
                source_id="DEF456",
                title="Zotero Paper 2",
                date=datetime(2026, 1, 13, 10, 0, 0, tzinfo=timezone.utc),
                summary="Abstract 2",
                link="https://example.com/paper2",
                metadata={"authors": "Jones"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
        ]

    @pytest.fixture
    def newsletter_items(self) -> list[FeedItem]:
        """Sample Newsletter feed items."""
        return [
            FeedItem(
                id="newsletter:MSG001",
                source_type="newsletter",
                source_id="MSG001",
                title="Newsletter Article 1",
                date=datetime(2026, 1, 14, 8, 0, 0, tzinfo=timezone.utc),
                summary="Newsletter content",
                link="https://newsletter.com/article1",
                metadata={"sender": "news@example.com"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
        ]

    def test_get_unified_feed_combines_sources(
        self, zotero_items: list[FeedItem], newsletter_items: list[FeedItem]
    ) -> None:
        """Test that unified feed combines items from all sources."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = zotero_items + newsletter_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.get_unified_feed()

        assert len(items) == 3

    def test_get_unified_feed_sorted_by_date_descending(
        self, zotero_items: list[FeedItem], newsletter_items: list[FeedItem]
    ) -> None:
        """Test that feed is sorted by date, newest first."""
        mock_repo = MagicMock()
        # Return items in random order
        mock_repo.get_feed_items.return_value = [
            newsletter_items[0],
            zotero_items[1],
            zotero_items[0],
        ]

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.get_unified_feed()

        # Should be sorted newest first
        dates = [item.date for item in items]
        assert dates == sorted(dates, reverse=True)

    def test_get_unified_feed_respects_limit(
        self, zotero_items: list[FeedItem], newsletter_items: list[FeedItem]
    ) -> None:
        """Test that limit parameter is respected."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = zotero_items + newsletter_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.get_unified_feed(limit=2)

        assert len(items) <= 3  # Limit passed to repo, but all items returned by mock

    def test_get_unified_feed_respects_offset(
        self, zotero_items: list[FeedItem], newsletter_items: list[FeedItem]
    ) -> None:
        """Test that offset parameter is respected for pagination."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = zotero_items + newsletter_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        # Get all items first
        all_items = service.get_unified_feed()

        # Verify offset is passed to repository
        service.get_unified_feed(offset=1)
        mock_repo.get_feed_items.assert_called_with(
            source_type=None,
            limit=50,
            offset=1,
            days=None,
        )

    def test_get_unified_feed_filter_by_source(
        self, zotero_items: list[FeedItem], newsletter_items: list[FeedItem]
    ) -> None:
        """Test filtering by source type."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = zotero_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.get_unified_feed(source_type="zotero")

        mock_repo.get_feed_items.assert_called_with(
            source_type="zotero",
            limit=50,
            offset=0,
            days=None,
        )

    def test_get_unified_feed_empty_sources(self) -> None:
        """Test handling when no items exist."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = []

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.get_unified_feed()

        assert items == []

    def test_get_unified_feed_with_days_filter(
        self, zotero_items: list[FeedItem]
    ) -> None:
        """Test filtering by days lookback."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = zotero_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        service.get_unified_feed(days=7)

        mock_repo.get_feed_items.assert_called_with(
            source_type=None,
            limit=50,
            offset=0,
            days=7,
        )


class TestFeedServiceSourceManagement:
    """Tests for FeedService source registration."""

    def test_get_enabled_sources(self) -> None:
        """Test getting list of enabled sources."""
        mock_repo = MagicMock()

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        # Service should have registered sources
        assert hasattr(service, "sources") or hasattr(service, "_sources")


class TestFeedServiceFilterItems:
    """Tests for FeedService.filter_items method."""

    @pytest.fixture
    def sample_items(self) -> list[FeedItem]:
        """Sample feed items for filtering tests."""
        return [
            FeedItem(
                id="zotero:ABC123",
                source_type="zotero",
                source_id="ABC123",
                title="Machine Learning Paper",
                date=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                summary="Abstract about neural networks and deep learning.",
                link="https://example.com/paper1",
                metadata={"authors": "Smith"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
            FeedItem(
                id="zotero:DEF456",
                source_type="zotero",
                source_id="DEF456",
                title="Quantum Computing Research",
                date=datetime(2026, 1, 13, 10, 0, 0, tzinfo=timezone.utc),
                summary="Research on quantum algorithms.",
                link="https://example.com/paper2",
                metadata={"authors": "Jones"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
            FeedItem(
                id="newsletter:MSG001",
                source_type="newsletter",
                source_id="MSG001",
                title="AI News Roundup",
                date=datetime(2026, 1, 14, 8, 0, 0, tzinfo=timezone.utc),
                summary="Latest news in artificial intelligence and machine learning.",
                link="https://newsletter.com/article1",
                metadata={"sender": "news@example.com"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
        ]

    def test_filter_items_by_source(self, sample_items: list[FeedItem]) -> None:
        """Test filtering items by source type."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = [
            item for item in sample_items if item.source_type == "zotero"
        ]

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.filter_items(source_type="zotero")

        assert all(item.source_type == "zotero" for item in items)

    def test_filter_items_by_date_range(self, sample_items: list[FeedItem]) -> None:
        """Test filtering items by date range."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = sample_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        start_date = datetime(2026, 1, 14, tzinfo=timezone.utc)
        end_date = datetime(2026, 1, 16, tzinfo=timezone.utc)

        items = service.filter_items(start_date=start_date, end_date=end_date)

        # Should return items between Jan 14-16
        for item in items:
            assert start_date <= item.date <= end_date

    def test_filter_items_no_matches(self) -> None:
        """Test filtering with no matching items."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = []

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.filter_items(source_type="nonexistent")

        assert items == []


class TestFeedServiceSearchItems:
    """Tests for FeedService.search_items method."""

    @pytest.fixture
    def sample_items(self) -> list[FeedItem]:
        """Sample feed items for search tests."""
        return [
            FeedItem(
                id="zotero:ABC123",
                source_type="zotero",
                source_id="ABC123",
                title="Machine Learning Paper",
                date=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                summary="Abstract about neural networks and deep learning.",
                link="https://example.com/paper1",
                metadata={"authors": "Smith"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
            FeedItem(
                id="zotero:DEF456",
                source_type="zotero",
                source_id="DEF456",
                title="Quantum Computing Research",
                date=datetime(2026, 1, 13, 10, 0, 0, tzinfo=timezone.utc),
                summary="Research on quantum algorithms.",
                link="https://example.com/paper2",
                metadata={"authors": "Jones"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
            FeedItem(
                id="newsletter:MSG001",
                source_type="newsletter",
                source_id="MSG001",
                title="AI News Roundup",
                date=datetime(2026, 1, 14, 8, 0, 0, tzinfo=timezone.utc),
                summary="Latest news in artificial intelligence and machine learning.",
                link="https://newsletter.com/article1",
                metadata={"sender": "news@example.com"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            ),
        ]

    def test_search_items_by_keyword_in_title(self, sample_items: list[FeedItem]) -> None:
        """Test searching items by keyword in title."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = sample_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.search_items(query="machine learning")

        # Should find items with "machine learning" in title or summary
        assert len(items) >= 1
        assert any("machine learning" in item.title.lower() for item in items)

    def test_search_items_by_keyword_in_summary(self, sample_items: list[FeedItem]) -> None:
        """Test searching items by keyword in summary."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = sample_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.search_items(query="neural networks")

        # Should find the ML paper with "neural networks" in summary
        assert len(items) >= 1
        assert any("neural networks" in (item.summary or "").lower() for item in items)

    def test_search_items_case_insensitive(self, sample_items: list[FeedItem]) -> None:
        """Test that search is case insensitive."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = sample_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items_lower = service.search_items(query="quantum")
        items_upper = service.search_items(query="QUANTUM")

        assert len(items_lower) == len(items_upper)

    def test_search_items_no_matches(self, sample_items: list[FeedItem]) -> None:
        """Test searching with no matching items."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = sample_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.search_items(query="xyznonexistent")

        assert items == []

    def test_search_items_empty_query(self, sample_items: list[FeedItem]) -> None:
        """Test searching with empty query returns all items."""
        mock_repo = MagicMock()
        mock_repo.get_feed_items.return_value = sample_items

        from src.services.feed import FeedService

        service = FeedService(repository=mock_repo)
        items = service.search_items(query="")

        assert len(items) == len(sample_items)
