"""Unit tests for repository CRUD operations.

Tests Repository class with mocked database connection.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.models.feed_item import FeedItem
from src.models.source import SourceConfig


class TestRepositoryFeedItems:
    """Tests for FeedItem CRUD operations."""

    def test_save_feed_item(self, mock_db_connection) -> None:
        """Test saving a feed item to database."""
        mock_conn, mock_cursor = mock_db_connection

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            item = FeedItem(
                id="zotero:ABC123",
                source_type="zotero",
                source_id="ABC123",
                title="Test Paper",
                date=datetime(2026, 1, 15, tzinfo=timezone.utc),
                summary="Abstract",
                link="https://example.com",
                metadata={"authors": "Smith"},
                fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
            )

            repo.save_feed_item(item)

            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()

    def test_get_feed_items(self, mock_db_connection) -> None:
        """Test retrieving feed items from database."""
        mock_conn, mock_cursor = mock_db_connection

        # Mock database response
        mock_cursor.fetchall.return_value = [
            (
                "zotero:ABC123",
                "zotero",
                "ABC123",
                "Test Paper",
                datetime(2026, 1, 15, tzinfo=timezone.utc),
                "Abstract",
                "https://example.com",
                {"authors": "Smith"},
                datetime(2026, 1, 30, tzinfo=timezone.utc),
            )
        ]

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            items = repo.get_feed_items(limit=50)

            assert len(items) == 1
            assert items[0].id == "zotero:ABC123"
            assert items[0].title == "Test Paper"

    def test_get_feed_items_by_source(self, mock_db_connection) -> None:
        """Test filtering feed items by source type."""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            repo.get_feed_items(source_type="zotero")

            # Verify query includes source filter
            call_args = mock_cursor.execute.call_args
            assert "source_type" in str(call_args)

    def test_delete_feed_item(self, mock_db_connection) -> None:
        """Test deleting a feed item."""
        mock_conn, mock_cursor = mock_db_connection

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            repo.delete_feed_item("zotero:ABC123")

            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()

    def test_get_feed_items_pagination(self, mock_db_connection) -> None:
        """Test feed items pagination with offset."""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            repo.get_feed_items(limit=10, offset=20)

            call_args = mock_cursor.execute.call_args
            assert "LIMIT" in str(call_args)
            assert "OFFSET" in str(call_args)


class TestRepositorySourceConfig:
    """Tests for SourceConfig CRUD operations."""

    def test_save_source_config(self, mock_db_connection) -> None:
        """Test saving source configuration."""
        mock_conn, mock_cursor = mock_db_connection

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            config = SourceConfig(
                source_type="zotero",
                enabled=True,
                settings={"library_id": "12345"},
            )

            repo.save_source_config(config)

            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()

    def test_get_source_config(self, mock_db_connection) -> None:
        """Test retrieving source configuration."""
        mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchone.return_value = (
            "zotero",
            True,
            datetime(2026, 1, 30, tzinfo=timezone.utc),
            None,
            {"library_id": "12345"},
        )

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            config = repo.get_source_config("zotero")

            assert config is not None
            assert config.source_type == "zotero"
            assert config.enabled is True

    def test_get_source_config_not_found(self, mock_db_connection) -> None:
        """Test retrieving non-existent source configuration."""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            config = repo.get_source_config("nonexistent")

            assert config is None

    def test_get_all_source_configs(self, mock_db_connection) -> None:
        """Test retrieving all source configurations."""
        mock_conn, mock_cursor = mock_db_connection

        mock_cursor.fetchall.return_value = [
            ("zotero", True, None, None, {}),
            ("newsletter", True, None, None, {}),
        ]

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            configs = repo.get_all_source_configs()

            assert len(configs) == 2


class TestRepositoryBulkOperations:
    """Tests for bulk database operations."""

    def test_save_feed_items_batch(self, mock_db_connection) -> None:
        """Test saving multiple feed items in a batch."""
        mock_conn, mock_cursor = mock_db_connection

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            items = [
                FeedItem(
                    id=f"zotero:ITEM{i}",
                    source_type="zotero",
                    source_id=f"ITEM{i}",
                    title=f"Paper {i}",
                    date=datetime(2026, 1, 15, tzinfo=timezone.utc),
                    fetched_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
                )
                for i in range(3)
            ]

            repo.save_feed_items(items)

            # Should use batch insert
            mock_conn.commit.assert_called()

    def test_delete_old_feed_items(self, mock_db_connection) -> None:
        """Test deleting old feed items for retention."""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.rowcount = 5

        with patch("src.db.repository.get_connection", return_value=mock_conn):
            from src.db.repository import Repository

            repo = Repository()
            deleted = repo.delete_old_feed_items(source_type="zotero", keep_count=100)

            assert deleted == 5
            mock_conn.commit.assert_called()
