"""Unit tests for Pydantic models.

Tests FeedItem and SourceConfig model validation per TDD.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.models.feed_item import FeedItem
from src.models.source import (
    AppSettings,
    NewsletterConfig,
    SourceConfig,
    ZoteroConfig,
)


class TestFeedItem:
    """Tests for FeedItem model validation."""

    def test_valid_feed_item_creation(self) -> None:
        """Test creating a valid FeedItem."""
        item = FeedItem(
            id="zotero:ABC123",
            source_type="zotero",
            source_id="ABC123",
            title="Test Paper",
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            summary="Test abstract",
            link="https://example.com/paper",
            metadata={"authors": "Smith"},
            fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
        )
        assert item.id == "zotero:ABC123"
        assert item.source_type == "zotero"
        assert item.title == "Test Paper"

    def test_feed_item_id_format_validation(self) -> None:
        """Test that id must match source_type:source_id format."""
        # Valid format
        item = FeedItem(
            id="newsletter:MSG001",
            source_type="newsletter",
            source_id="MSG001",
            title="Newsletter Item",
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
        )
        assert item.id == "newsletter:MSG001"

    def test_feed_item_requires_title(self) -> None:
        """Test that title is required and cannot be empty."""
        with pytest.raises(ValidationError):
            FeedItem(
                id="zotero:ABC123",
                source_type="zotero",
                source_id="ABC123",
                title="",  # Empty title should fail
                date=datetime(2026, 1, 15, tzinfo=timezone.utc),
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            )

    def test_feed_item_optional_fields(self) -> None:
        """Test that summary and link are optional."""
        item = FeedItem(
            id="zotero:ABC123",
            source_type="zotero",
            source_id="ABC123",
            title="Minimal Item",
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
        )
        assert item.summary is None
        assert item.link is None
        assert item.metadata == {}

    def test_feed_item_is_immutable(self) -> None:
        """Test that FeedItem is frozen (immutable)."""
        item = FeedItem(
            id="zotero:ABC123",
            source_type="zotero",
            source_id="ABC123",
            title="Test",
            date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
        )
        with pytest.raises(ValidationError):
            item.title = "Changed"  # type: ignore[misc]


class TestSourceConfig:
    """Tests for SourceConfig model validation."""

    def test_valid_source_config(self) -> None:
        """Test creating a valid SourceConfig."""
        config = SourceConfig(
            source_type="zotero",
            enabled=True,
            last_refresh=datetime(2026, 1, 30, tzinfo=timezone.utc),
            settings={"library_id": "12345"},
        )
        assert config.source_type == "zotero"
        assert config.enabled is True
        assert config.settings["library_id"] == "12345"

    def test_source_config_defaults(self) -> None:
        """Test SourceConfig default values."""
        config = SourceConfig(source_type="newsletter")
        assert config.enabled is True
        assert config.last_refresh is None
        assert config.last_error is None
        assert config.settings == {}

    def test_source_config_with_error(self) -> None:
        """Test SourceConfig with error state."""
        config = SourceConfig(
            source_type="zotero",
            enabled=True,
            last_error="API rate limited",
        )
        assert config.last_error == "API rate limited"


class TestZoteroConfig:
    """Tests for ZoteroConfig model validation."""

    def test_valid_zotero_config(self) -> None:
        """Test creating a valid ZoteroConfig."""
        config = ZoteroConfig(
            library_id="12345",
            api_key="secret_key",
            days_lookback=7,
            include_keywords=["AI", "ML"],
            exclude_keywords=["review"],
        )
        assert config.library_id == "12345"
        assert config.days_lookback == 7
        assert "AI" in config.include_keywords

    def test_zotero_config_defaults(self) -> None:
        """Test ZoteroConfig default values."""
        config = ZoteroConfig(library_id="12345", api_key="key")
        assert config.days_lookback == 7
        assert config.include_keywords == []
        assert config.exclude_keywords == []

    def test_zotero_config_days_lookback_validation(self) -> None:
        """Test days_lookback must be between 1 and 365."""
        with pytest.raises(ValidationError):
            ZoteroConfig(library_id="12345", api_key="key", days_lookback=0)

        with pytest.raises(ValidationError):
            ZoteroConfig(library_id="12345", api_key="key", days_lookback=366)


class TestNewsletterConfig:
    """Tests for NewsletterConfig model validation."""

    def test_valid_newsletter_config(self) -> None:
        """Test creating a valid NewsletterConfig."""
        config = NewsletterConfig(
            sender_emails=["news@example.com"],
            parsing_prompt="Extract articles",
            max_emails_per_refresh=20,
        )
        assert "news@example.com" in config.sender_emails
        assert config.max_emails_per_refresh == 20

    def test_newsletter_config_defaults(self) -> None:
        """Test NewsletterConfig default values."""
        config = NewsletterConfig()
        assert config.sender_emails == []
        assert config.parsing_prompt is None
        assert config.max_emails_per_refresh == 20

    def test_newsletter_config_max_emails_validation(self) -> None:
        """Test max_emails_per_refresh must be between 1 and 100."""
        with pytest.raises(ValidationError):
            NewsletterConfig(max_emails_per_refresh=0)

        with pytest.raises(ValidationError):
            NewsletterConfig(max_emails_per_refresh=101)


class TestAppSettings:
    """Tests for AppSettings model validation."""

    def test_valid_app_settings(self) -> None:
        """Test creating valid AppSettings."""
        settings = AppSettings(
            default_days_lookback=14,
            page_size=25,
            refresh_timeout_seconds=120,
        )
        assert settings.default_days_lookback == 14
        assert settings.page_size == 25

    def test_app_settings_defaults(self) -> None:
        """Test AppSettings default values."""
        settings = AppSettings()
        assert settings.default_days_lookback == 7
        assert settings.page_size == 50
        assert settings.refresh_timeout_seconds == 60

    def test_app_settings_page_size_validation(self) -> None:
        """Test page_size must be between 10 and 100."""
        with pytest.raises(ValidationError):
            AppSettings(page_size=5)

        with pytest.raises(ValidationError):
            AppSettings(page_size=150)
