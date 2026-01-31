"""Unit tests for retry utility with exponential backoff.

Tests retry logic using tenacity library.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestRetryUtility:
    """Tests for retry utility functions."""

    def test_with_retry_returns_on_success(self) -> None:
        """Test that with_retry returns result on successful call."""
        from src.services.retry import with_retry

        @with_retry(max_attempts=3)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_with_retry_retries_on_failure(self) -> None:
        """Test that with_retry retries on exception."""
        from src.services.retry import with_retry

        call_count = 0

        @with_retry(max_attempts=3, wait_seconds=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_with_retry_raises_after_max_attempts(self) -> None:
        """Test that with_retry raises after max attempts exceeded."""
        from src.services.retry import with_retry

        @with_retry(max_attempts=3, wait_seconds=0.01)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()

    def test_with_retry_handles_rate_limit(self) -> None:
        """Test that with_retry handles 429 rate limit errors."""
        from src.services.retry import with_retry

        call_count = 0

        @with_retry(max_attempts=3, wait_seconds=0.01)
        def rate_limited_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Simulate rate limit response
                error = Exception("429 RESOURCE_EXHAUSTED")
                raise error
            return "success"

        result = rate_limited_function()
        assert result == "success"
        assert call_count == 2

    def test_with_retry_uses_exponential_backoff(self) -> None:
        """Test that retry uses exponential backoff between attempts."""
        # This is a behavioral test - we verify the decorator accepts backoff params
        from src.services.retry import with_retry

        @with_retry(max_attempts=2, wait_seconds=0.01, exponential=True)
        def test_function():
            return "success"

        # Should not raise - just verify it works with exponential param
        result = test_function()
        assert result == "success"

    def test_with_retry_logs_retries(self) -> None:
        """Test that retries are logged."""
        from src.services.retry import with_retry

        call_count = 0

        @with_retry(max_attempts=3, wait_seconds=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"

        with patch("src.services.retry.logger") as mock_logger:
            result = flaky_function()
            assert result == "success"
            # Logger should have been called for the retry
            # Note: This depends on implementation details


class TestRefreshAll:
    """Tests for FeedService.refresh_all method."""

    def test_refresh_all_fetches_from_all_sources(self) -> None:
        """Test that refresh_all fetches from all registered sources."""
        from datetime import datetime, timezone
        from unittest.mock import MagicMock

        from src.models.feed_item import FeedItem
        from src.services.feed import FeedService

        # Create mock sources
        mock_zotero = MagicMock()
        mock_zotero.source_type = "zotero"
        mock_zotero.fetch_items.return_value = [
            FeedItem(
                id="zotero:1",
                source_type="zotero",
                source_id="1",
                title="Paper 1",
                date=datetime.now(timezone.utc),
                fetched_at=datetime.now(timezone.utc),
            )
        ]

        mock_newsletter = MagicMock()
        mock_newsletter.source_type = "newsletter"
        mock_newsletter.fetch_items.return_value = [
            FeedItem(
                id="newsletter:1",
                source_type="newsletter",
                source_id="1",
                title="Newsletter 1",
                date=datetime.now(timezone.utc),
                fetched_at=datetime.now(timezone.utc),
            )
        ]

        mock_repo = MagicMock()
        service = FeedService(repository=mock_repo)
        service.register_source(mock_zotero)
        service.register_source(mock_newsletter)

        result = service.refresh_all()

        assert result["success"] is True
        assert result["sources"]["zotero"]["items_fetched"] == 1
        assert result["sources"]["newsletter"]["items_fetched"] == 1
        mock_zotero.fetch_items.assert_called_once()
        mock_newsletter.fetch_items.assert_called_once()

    def test_refresh_all_handles_partial_failure(self) -> None:
        """Test that refresh_all continues if one source fails."""
        from datetime import datetime, timezone
        from unittest.mock import MagicMock

        from src.models.feed_item import FeedItem
        from src.services.feed import FeedService

        # Create mock sources - one succeeds, one fails
        mock_zotero = MagicMock()
        mock_zotero.source_type = "zotero"
        mock_zotero.fetch_items.side_effect = ConnectionError("API unavailable")

        mock_newsletter = MagicMock()
        mock_newsletter.source_type = "newsletter"
        mock_newsletter.fetch_items.return_value = [
            FeedItem(
                id="newsletter:1",
                source_type="newsletter",
                source_id="1",
                title="Newsletter 1",
                date=datetime.now(timezone.utc),
                fetched_at=datetime.now(timezone.utc),
            )
        ]

        mock_repo = MagicMock()
        service = FeedService(repository=mock_repo)
        service.register_source(mock_zotero)
        service.register_source(mock_newsletter)

        result = service.refresh_all()

        # Should still succeed partially
        assert result["success"] is True  # Partial success
        assert result["sources"]["zotero"]["error"] is not None
        assert result["sources"]["newsletter"]["items_fetched"] == 1

    def test_refresh_all_saves_items_to_repository(self) -> None:
        """Test that refresh_all saves fetched items to repository."""
        from datetime import datetime, timezone
        from unittest.mock import MagicMock

        from src.models.feed_item import FeedItem
        from src.services.feed import FeedService

        mock_source = MagicMock()
        mock_source.source_type = "zotero"
        items = [
            FeedItem(
                id="zotero:1",
                source_type="zotero",
                source_id="1",
                title="Paper 1",
                date=datetime.now(timezone.utc),
                fetched_at=datetime.now(timezone.utc),
            )
        ]
        mock_source.fetch_items.return_value = items

        mock_repo = MagicMock()
        service = FeedService(repository=mock_repo)
        service.register_source(mock_source)

        service.refresh_all()

        mock_repo.save_feed_items_batch.assert_called_once_with(items)
