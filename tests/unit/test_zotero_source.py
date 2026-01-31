"""Unit tests for ZoteroSource adapter.

Tests ZoteroSource.fetch_items with mocked pyzotero.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models.feed_item import FeedItem
from src.models.source import ZoteroConfig


class TestZoteroSource:
    """Tests for ZoteroSource adapter."""

    @pytest.fixture
    def zotero_config(self) -> ZoteroConfig:
        """Create test Zotero configuration."""
        return ZoteroConfig(
            library_id="12345",
            api_key="test_api_key",
            days_lookback=7,
            include_keywords=[],
            exclude_keywords=[],
        )

    @pytest.fixture
    def mock_zotero_items(self) -> list[dict[str, Any]]:
        """Sample Zotero API response."""
        return [
            {
                "key": "ABC123",
                "data": {
                    "title": "Machine Learning Paper",
                    "abstractNote": "A paper about ML techniques.",
                    "url": "https://example.com/ml-paper",
                    "dateAdded": "2026-01-15T12:00:00Z",
                    "creators": [
                        {"firstName": "John", "lastName": "Smith"},
                        {"firstName": "Jane", "lastName": "Doe"},
                    ],
                },
            },
            {
                "key": "DEF456",
                "data": {
                    "title": "Deep Learning Paper",
                    "abstractNote": "A paper about DL.",
                    "url": "https://example.com/dl-paper",
                    "dateAdded": "2026-01-14T10:00:00Z",
                    "creators": [{"firstName": "Bob", "lastName": "Jones"}],
                },
            },
        ]

    def test_fetch_items_returns_feed_items(
        self, zotero_config: ZoteroConfig, mock_zotero_items: list[dict[str, Any]]
    ) -> None:
        """Test that fetch_items returns list of FeedItem."""
        with patch("src.sources.zotero.create_zotero_client") as mock_create:
            with patch("src.sources.zotero.fetch_recent_items", return_value=mock_zotero_items):
                from src.sources.zotero import ZoteroSource

                source = ZoteroSource(zotero_config)
                items = source.fetch_items()

                assert isinstance(items, list)
                assert len(items) == 2
                assert all(isinstance(item, FeedItem) for item in items)

    def test_fetch_items_correct_source_type(
        self, zotero_config: ZoteroConfig, mock_zotero_items: list[dict[str, Any]]
    ) -> None:
        """Test that items have correct source_type."""
        with patch("src.sources.zotero.create_zotero_client"):
            with patch("src.sources.zotero.fetch_recent_items", return_value=mock_zotero_items):
                from src.sources.zotero import ZoteroSource

                source = ZoteroSource(zotero_config)
                items = source.fetch_items()

                assert all(item.source_type == "zotero" for item in items)

    def test_fetch_items_extracts_title(
        self, zotero_config: ZoteroConfig, mock_zotero_items: list[dict[str, Any]]
    ) -> None:
        """Test that item titles are extracted correctly."""
        with patch("src.sources.zotero.create_zotero_client"):
            with patch("src.sources.zotero.fetch_recent_items", return_value=mock_zotero_items):
                from src.sources.zotero import ZoteroSource

                source = ZoteroSource(zotero_config)
                items = source.fetch_items()

                assert items[0].title == "Machine Learning Paper"
                assert items[1].title == "Deep Learning Paper"

    def test_fetch_items_extracts_authors(
        self, zotero_config: ZoteroConfig, mock_zotero_items: list[dict[str, Any]]
    ) -> None:
        """Test that authors are extracted to metadata."""
        with patch("src.sources.zotero.create_zotero_client"):
            with patch("src.sources.zotero.fetch_recent_items", return_value=mock_zotero_items):
                from src.sources.zotero import ZoteroSource

                source = ZoteroSource(zotero_config)
                items = source.fetch_items()

                assert "authors" in items[0].metadata
                assert "Smith" in items[0].metadata["authors"]

    def test_fetch_items_handles_empty_response(
        self, zotero_config: ZoteroConfig
    ) -> None:
        """Test handling of empty Zotero response."""
        with patch("src.sources.zotero.create_zotero_client"):
            with patch("src.sources.zotero.fetch_recent_items", return_value=[]):
                from src.sources.zotero import ZoteroSource

                source = ZoteroSource(zotero_config)
                items = source.fetch_items()

                assert items == []

    def test_fetch_items_uses_days_lookback(
        self, zotero_config: ZoteroConfig, mock_zotero_items: list[dict[str, Any]]
    ) -> None:
        """Test that days_lookback is used in API call."""
        with patch("src.sources.zotero.create_zotero_client"):
            with patch("src.sources.zotero.fetch_recent_items", return_value=mock_zotero_items) as mock_fetch:
                from src.sources.zotero import ZoteroSource

                config = ZoteroConfig(
                    library_id="12345",
                    api_key="test_key",
                    days_lookback=14,
                )
                source = ZoteroSource(config)
                source.fetch_items()

                # Verify the fetch was called with correct days_lookback
                mock_fetch.assert_called_once()
                call_args = mock_fetch.call_args
                assert call_args[0][1] == 14  # Second positional arg is days

    def test_source_type_property(self, zotero_config: ZoteroConfig) -> None:
        """Test that source_type property returns 'zotero'."""
        with patch("src.sources.zotero.create_zotero_client"):
            from src.sources.zotero import ZoteroSource

            source = ZoteroSource(zotero_config)
            assert source.source_type == "zotero"
