"""Shared test fixtures for the unified feed application.

Provides mock fixtures for:
- PostgreSQL database connections
- Zotero API responses
- Gmail API responses
- Gemini LLM responses
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models.feed_item import FeedItem
from src.models.source import SourceConfig, ZoteroConfig, NewsletterConfig


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_feed_item() -> FeedItem:
    """Create a sample FeedItem for testing."""
    return FeedItem(
        id="zotero:ABC123",
        source_type="zotero",
        source_id="ABC123",
        title="Test Paper Title",
        date=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        summary="This is a test abstract for the paper.",
        link="https://example.com/paper",
        metadata={"authors": "Smith, Jones"},
        fetched_at=datetime(2026, 1, 30, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_zotero_items() -> list[dict[str, Any]]:
    """Sample Zotero API response items."""
    return [
        {
            "key": "ABC123",
            "data": {
                "title": "Machine Learning Paper",
                "abstractNote": "A paper about ML.",
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


@pytest.fixture
def sample_newsletter_items() -> list[dict[str, Any]]:
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
def sample_source_config() -> SourceConfig:
    """Create a sample SourceConfig for testing."""
    return SourceConfig(
        source_type="zotero",
        enabled=True,
        last_refresh=datetime(2026, 1, 30, 9, 0, 0, tzinfo=timezone.utc),
        last_error=None,
        settings={"library_id": "12345"},
    )


@pytest.fixture
def sample_zotero_config() -> ZoteroConfig:
    """Create a sample ZoteroConfig for testing."""
    return ZoteroConfig(
        library_id="12345",
        api_key="test_api_key",
        days_lookback=7,
        include_keywords=["machine learning", "AI"],
        exclude_keywords=["review"],
    )


@pytest.fixture
def sample_newsletter_config() -> NewsletterConfig:
    """Create a sample NewsletterConfig for testing."""
    return NewsletterConfig(
        sender_emails=["newsletter@example.com", "updates@tech.com"],
        parsing_prompt="Extract articles from this newsletter.",
        max_emails_per_refresh=20,
    )


# =============================================================================
# Database Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_db_connection():
    """Mock PostgreSQL database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


@pytest.fixture
def mock_psycopg2(mock_db_connection):
    """Patch psycopg2.connect to return mock connection."""
    mock_conn, mock_cursor = mock_db_connection
    with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
        yield mock_connect, mock_conn, mock_cursor


# =============================================================================
# Zotero API Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_pyzotero(sample_zotero_items):
    """Mock pyzotero.Zotero client."""
    mock_zotero = MagicMock()
    mock_zotero.top.return_value = sample_zotero_items
    mock_zotero.items.return_value = sample_zotero_items

    with patch("pyzotero.zotero.Zotero", return_value=mock_zotero) as mock_class:
        yield mock_class, mock_zotero


# =============================================================================
# Gmail API Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service."""
    mock_service = MagicMock()
    mock_messages = MagicMock()
    mock_service.users.return_value.messages.return_value = mock_messages

    # Mock list response
    mock_messages.list.return_value.execute.return_value = {
        "messages": [{"id": "msg1"}, {"id": "msg2"}]
    }

    # Mock get response
    mock_messages.get.return_value.execute.return_value = {
        "id": "msg1",
        "payload": {
            "headers": [
                {"name": "From", "value": "newsletter@example.com"},
                {"name": "Subject", "value": "Weekly Newsletter"},
                {"name": "Date", "value": "Mon, 15 Jan 2026 12:00:00 +0000"},
            ],
            "body": {"data": "VGVzdCBlbWFpbCBib2R5"},  # Base64 "Test email body"
        },
    }

    return mock_service


# =============================================================================
# Gemini LLM Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_gemini(sample_newsletter_items):
    """Mock Google Gemini API responses."""
    import json

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(sample_newsletter_items)
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client) as mock_class:
        yield mock_class, mock_client


# =============================================================================
# Environment Variable Fixtures
# =============================================================================


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
        "ZOTERO_LIBRARY_ID": "12345",
        "ZOTERO_API_KEY": "test_zotero_key",
        "GEMINI_API_KEY": "test_gemini_key",
        "ENCRYPTION_KEY": "test_encryption_key_32_bytes_long!",
        "GOOGLE_CLIENT_ID": "test_client_id",
        "GOOGLE_CLIENT_SECRET": "test_client_secret",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
