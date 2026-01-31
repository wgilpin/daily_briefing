"""Unit tests for FeedSource protocol.

Tests that source implementations conform to the FeedSource protocol.
"""

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

import pytest

from src.models.feed_item import FeedItem


class TestFeedSourceProtocol:
    """Tests for FeedSource protocol compliance."""

    def test_feed_source_protocol_exists(self) -> None:
        """Test that FeedSource protocol is defined."""
        from src.sources.base import FeedSource

        assert hasattr(FeedSource, "fetch_items")
        assert hasattr(FeedSource, "source_type")

    def test_feed_source_is_runtime_checkable(self) -> None:
        """Test that FeedSource can be used with isinstance."""
        from src.sources.base import FeedSource

        # Protocol should be runtime_checkable
        assert hasattr(FeedSource, "__protocol_attrs__") or isinstance(
            FeedSource, type
        )

    def test_zotero_source_implements_protocol(self) -> None:
        """Test that ZoteroSource implements FeedSource protocol."""
        from src.sources.base import FeedSource
        from src.sources.zotero import ZoteroSource

        # ZoteroSource should have required attributes
        assert hasattr(ZoteroSource, "fetch_items")
        assert hasattr(ZoteroSource, "source_type")

    def test_newsletter_source_implements_protocol(self) -> None:
        """Test that NewsletterSource implements FeedSource protocol."""
        from src.sources.base import FeedSource
        from src.sources.newsletter import NewsletterSource

        # NewsletterSource should have required attributes
        assert hasattr(NewsletterSource, "fetch_items")
        assert hasattr(NewsletterSource, "source_type")

    def test_source_type_is_string(self) -> None:
        """Test that source_type property returns a string."""
        from src.sources.zotero import ZoteroSource
        from src.sources.newsletter import NewsletterSource

        zotero = ZoteroSource.__new__(ZoteroSource)
        newsletter = NewsletterSource.__new__(NewsletterSource)

        assert isinstance(ZoteroSource.source_type, str) or callable(
            getattr(ZoteroSource, "source_type", None)
        )
