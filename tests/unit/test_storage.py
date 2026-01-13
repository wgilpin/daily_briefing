"""Unit tests for newsletter storage functions."""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.newsletter.storage import (
    apply_retention_policy,
    get_all_parsed_items,
    get_processed_message_ids,
    init_database,
    insert_newsletter_items,
    save_email,
    save_consolidated_digest,
    save_markdown,
    save_parsed_items,
    track_email_processed,
)


class TestGetProcessedMessageIds:
    """Tests for get_processed_message_ids() function."""

    def test_get_processed_message_ids_returns_empty_set_when_no_records(self):
        """Test getting processed message IDs when database is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            result = get_processed_message_ids(str(db_path))

            assert result == set()

    def test_get_processed_message_ids_returns_all_message_ids(self):
        """Test getting all processed message IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # Insert test records
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO processed_emails 
                (message_id, sender_email, collected_at, status)
                VALUES (?, ?, ?, ?)
                """,
                ("msg1", "sender1@example.com", datetime.now().isoformat(), "collected"),
            )
            cursor.execute(
                """
                INSERT INTO processed_emails 
                (message_id, sender_email, collected_at, status)
                VALUES (?, ?, ?, ?)
                """,
                ("msg2", "sender2@example.com", datetime.now().isoformat(), "collected"),
            )
            conn.commit()
            conn.close()

            result = get_processed_message_ids(str(db_path))

            assert result == {"msg1", "msg2"}

    def test_get_processed_message_ids_filters_by_sender(self):
        """Test getting processed message IDs filtered by sender emails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # Insert test records
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO processed_emails 
                (message_id, sender_email, collected_at, status)
                VALUES (?, ?, ?, ?)
                """,
                ("msg1", "sender1@example.com", datetime.now().isoformat(), "collected"),
            )
            cursor.execute(
                """
                INSERT INTO processed_emails 
                (message_id, sender_email, collected_at, status)
                VALUES (?, ?, ?, ?)
                """,
                ("msg2", "sender2@example.com", datetime.now().isoformat(), "collected"),
            )
            cursor.execute(
                """
                INSERT INTO processed_emails 
                (message_id, sender_email, collected_at, status)
                VALUES (?, ?, ?, ?)
                """,
                ("msg3", "sender1@example.com", datetime.now().isoformat(), "collected"),
            )
            conn.commit()
            conn.close()

            result = get_processed_message_ids(
                str(db_path), sender_emails=["sender1@example.com"]
            )

            assert result == {"msg1", "msg3"}
            assert "msg2" not in result

    def test_get_processed_message_ids_handles_nonexistent_database(self):
        """Test getting processed message IDs when database doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nonexistent.db"

            result = get_processed_message_ids(str(db_path))

            assert result == set()


class TestTrackEmailProcessed:
    """Tests for track_email_processed() function."""

    def test_track_email_processed_inserts_new_record(self):
        """Test tracking a new email as processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            # Verify record was inserted
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message_id, sender_email, status FROM processed_emails WHERE message_id = ?",
                ("msg1",),
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == "msg1"
            assert result[1] == "sender@example.com"
            assert result[2] == "collected"

    def test_track_email_processed_updates_existing_record(self):
        """Test tracking updates existing email record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # Insert initial record
            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            # Update status
            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="parsed",
            )

            # Verify record was updated
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status FROM processed_emails WHERE message_id = ?",
                ("msg1",),
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == "parsed"

    def test_track_email_processed_sets_collected_at_timestamp(self):
        """Test tracking sets collected_at timestamp for new records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            before = datetime.now()

            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            after = datetime.now()

            # Verify timestamp was set
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT collected_at FROM processed_emails WHERE message_id = ?",
                ("msg1",),
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            collected_at = datetime.fromisoformat(result[0])
            assert before <= collected_at <= after

    def test_track_email_processed_with_subject(self):
        """Test tracking email with subject line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
                subject="Test Subject",
            )

            # Verify subject was stored
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT subject FROM processed_emails WHERE message_id = ?",
                ("msg1",),
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == "Test Subject"


class TestSaveEmail:
    """Tests for save_email() function."""

    def test_save_email_creates_json_file(self):
        """Test saving email creates JSON file with correct name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "emails"
            data_dir.mkdir()

            email = {
                "message_id": "msg123",
                "sender": "sender@example.com",
                "subject": "Test Email",
                "date": "2024-12-30T10:00:00Z",
                "body_html": "<html>Test</html>",
                "body_text": "Test",
            }

            result_path = save_email(email, str(data_dir))

            # Verify file was created
            expected_path = data_dir / "msg123.json"
            assert expected_path.exists()
            assert result_path == str(expected_path)

    def test_save_email_saves_correct_content(self):
        """Test saving email saves correct JSON content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "emails"
            data_dir.mkdir()

            email = {
                "message_id": "msg123",
                "sender": "sender@example.com",
                "subject": "Test Email",
                "date": "2024-12-30T10:00:00Z",
                "body_html": "<html>Test</html>",
                "body_text": "Test",
                "headers": {"From": "sender@example.com"},
            }

            save_email(email, str(data_dir))

            # Verify content
            file_path = data_dir / "msg123.json"
            with open(file_path) as f:
                saved_data = json.load(f)

            assert saved_data == email

    def test_save_email_creates_directory_if_needed(self):
        """Test saving email creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "emails" / "subdir"

            email = {
                "message_id": "msg123",
                "sender": "sender@example.com",
                "subject": "Test",
            }

            save_email(email, str(data_dir))

            # Verify directory and file were created
            assert data_dir.exists()
            assert (data_dir / "msg123.json").exists()


class TestSaveMarkdown:
    """Tests for save_markdown() function."""

    def test_save_markdown_creates_md_file(self):
        """Test saving markdown creates .md file with correct name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "markdown"
            data_dir.mkdir()

            message_id = "msg123"
            markdown_content = "# Title\n\nThis is markdown content."

            result_path = save_markdown(message_id, markdown_content, str(data_dir))

            # Verify file was created
            expected_path = data_dir / "msg123.md"
            assert expected_path.exists()
            assert result_path == str(expected_path)

    def test_save_markdown_saves_correct_content(self):
        """Test saving markdown saves correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "markdown"
            data_dir.mkdir()

            message_id = "msg123"
            markdown_content = "# Title\n\nThis is markdown content with **bold** text."

            save_markdown(message_id, markdown_content, str(data_dir))

            # Verify content
            file_path = data_dir / "msg123.md"
            with open(file_path, encoding="utf-8") as f:
                saved_content = f.read()

            assert saved_content == markdown_content

    def test_save_markdown_creates_directory_if_needed(self):
        """Test saving markdown creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "markdown" / "subdir"

            message_id = "msg123"
            markdown_content = "# Title\n\nContent."

            save_markdown(message_id, markdown_content, str(data_dir))

            # Verify directory and file were created
            assert data_dir.exists()
            assert (data_dir / "msg123.md").exists()

    def test_save_markdown_handles_unicode_content(self):
        """Test saving markdown with unicode characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "markdown"
            data_dir.mkdir()

            message_id = "msg123"
            markdown_content = "# Title\n\nContent with émojis 🎉 and unicode: 中文"

            save_markdown(message_id, markdown_content, str(data_dir))

            # Verify content with unicode
            file_path = data_dir / "msg123.md"
            with open(file_path, encoding="utf-8") as f:
                saved_content = f.read()

            assert saved_content == markdown_content
            assert "🎉" in saved_content
            assert "中文" in saved_content


class TestSaveParsedItems:
    """Tests for save_parsed_items() function."""

    def test_save_parsed_items_creates_json_file(self):
        """Test saving parsed items creates JSON file with correct name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "parsed"
            data_dir.mkdir()

            message_id = "msg123"
            parsed_items = [
                {
                    "date": "2024-12-30",
                    "title": "Article 1",
                    "summary": "Summary 1",
                    "link": "https://example.com/1",
                }
            ]

            result_path = save_parsed_items(message_id, parsed_items, str(data_dir))

            # Verify file was created
            expected_path = data_dir / "msg123.json"
            assert expected_path.exists()
            assert result_path == str(expected_path)

    def test_save_parsed_items_saves_correct_content(self):
        """Test saving parsed items saves correct JSON content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "parsed"
            data_dir.mkdir()

            message_id = "msg123"
            parsed_items = [
                {
                    "date": "2024-12-30",
                    "title": "Article 1",
                    "summary": "Summary 1",
                    "link": "https://example.com/1",
                },
                {
                    "date": "2024-12-29",
                    "title": "Article 2",
                    "summary": "Summary 2",
                    "link": None,
                },
            ]

            save_parsed_items(message_id, parsed_items, str(data_dir))

            # Verify content
            file_path = data_dir / "msg123.json"
            with open(file_path) as f:
                saved_data = json.load(f)

            assert saved_data == parsed_items
            assert len(saved_data) == 2

    def test_save_parsed_items_creates_directory_if_needed(self):
        """Test saving parsed items creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "parsed" / "subdir"

            message_id = "msg123"
            parsed_items = [{"title": "Test", "date": "2024-12-30"}]

            save_parsed_items(message_id, parsed_items, str(data_dir))

            # Verify directory and file were created
            assert data_dir.exists()
            assert (data_dir / "msg123.json").exists()

    def test_save_parsed_items_handles_empty_list(self):
        """Test saving parsed items handles empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "parsed"
            data_dir.mkdir()

            message_id = "msg123"
            parsed_items = []

            save_parsed_items(message_id, parsed_items, str(data_dir))

            # Verify file was created with empty array
            file_path = data_dir / "msg123.json"
            with open(file_path) as f:
                saved_data = json.load(f)

            assert saved_data == []


class TestInsertNewsletterItems:
    """Tests for insert_newsletter_items() function."""

    def test_insert_newsletter_items_inserts_single_item(self):
        """Test inserting a single newsletter item into database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # First, create a processed_emails record
            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            message_id = "msg1"
            parsed_items = [
                {
                    "date": "2024-12-30",
                    "title": "Article Title",
                    "summary": "Article summary",
                    "link": "https://example.com/article",
                }
            ]

            insert_newsletter_items(str(db_path), message_id, parsed_items)

            # Verify item was inserted
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT message_id, item_index, title, date, summary, link FROM newsletter_items WHERE message_id = ?",
                (message_id,),
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == message_id
            assert result[1] == 0  # item_index
            assert result[2] == "Article Title"
            assert result[3] == "2024-12-30"
            assert result[4] == "Article summary"
            assert result[5] == "https://example.com/article"

    def test_insert_newsletter_items_inserts_multiple_items(self):
        """Test inserting multiple newsletter items with correct item_index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # First, create a processed_emails record
            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            message_id = "msg1"
            parsed_items = [
                {
                    "date": "2024-12-30",
                    "title": "Article 1",
                    "summary": "Summary 1",
                    "link": "https://example.com/1",
                },
                {
                    "date": "2024-12-29",
                    "title": "Article 2",
                    "summary": "Summary 2",
                    "link": "https://example.com/2",
                },
                {
                    "date": "2024-12-28",
                    "title": "Article 3",
                    "summary": "Summary 3",
                    "link": None,
                },
            ]

            insert_newsletter_items(str(db_path), message_id, parsed_items)

            # Verify all items were inserted with correct item_index
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT item_index, title FROM newsletter_items WHERE message_id = ? ORDER BY item_index",
                (message_id,),
            )
            results = cursor.fetchall()
            conn.close()

            assert len(results) == 3
            assert results[0][0] == 0  # item_index for first item
            assert results[0][1] == "Article 1"
            assert results[1][0] == 1  # item_index for second item
            assert results[1][1] == "Article 2"
            assert results[2][0] == 2  # item_index for third item
            assert results[2][1] == "Article 3"

    def test_insert_newsletter_items_handles_missing_optional_fields(self):
        """Test inserting items with missing optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # First, create a processed_emails record
            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            message_id = "msg1"
            parsed_items = [
                {
                    "title": "Article Without Optional Fields",
                    # date, summary, link are missing
                }
            ]

            insert_newsletter_items(str(db_path), message_id, parsed_items)

            # Verify item was inserted with NULL for optional fields
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT title, date, summary, link FROM newsletter_items WHERE message_id = ?",
                (message_id,),
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            assert result[0] == "Article Without Optional Fields"
            # Optional fields should be None/NULL
            assert result[1] is None or result[1] == ""
            assert result[2] is None or result[2] == ""
            assert result[3] is None or result[3] == ""


class TestGetAllParsedItems:
    """Tests for get_all_parsed_items() function."""

    def test_get_all_parsed_items_returns_empty_list_when_no_items(self):
        """Test getting all parsed items returns empty list when no items exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            result = get_all_parsed_items(str(db_path))

            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_all_parsed_items_returns_all_items(self):
        """Test getting all parsed items returns all items from database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # Create processed_emails records
            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )
            track_email_processed(
                str(db_path),
                message_id="msg2",
                sender_email="sender@example.com",
                status="collected",
            )

            # Insert items
            insert_newsletter_items(
                str(db_path),
                "msg1",
                [
                    {
                        "date": "2024-12-30",
                        "title": "Article 1",
                        "summary": "Summary 1",
                        "link": "https://example.com/1",
                    }
                ],
            )
            insert_newsletter_items(
                str(db_path),
                "msg2",
                [
                    {
                        "date": "2024-12-29",
                        "title": "Article 2",
                        "summary": "Summary 2",
                        "link": "https://example.com/2",
                    },
                    {
                        "date": "2024-12-28",
                        "title": "Article 3",
                        "summary": "Summary 3",
                        "link": None,
                    },
                ],
            )

            result = get_all_parsed_items(str(db_path))

            assert isinstance(result, list)
            assert len(result) == 3
            # Verify items have expected structure
            assert all("title" in item for item in result)
            assert all("date" in item for item in result)
            assert all("summary" in item for item in result)
            assert all("link" in item for item in result)

    def test_get_all_parsed_items_returns_list_of_dicts(self):
        """Test that get_all_parsed_items returns list of dictionaries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            insert_newsletter_items(
                str(db_path),
                "msg1",
                [
                    {
                        "title": "Test Article",
                        "date": "2024-12-30",
                        "summary": "Test summary",
                        "link": "https://example.com",
                    }
                ],
            )

            result = get_all_parsed_items(str(db_path))

            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], dict)
            assert result[0]["title"] == "Test Article"


class TestSaveConsolidatedDigest:
    """Tests for save_consolidated_digest() function."""

    def test_save_consolidated_digest_creates_timestamped_file(self):
        """Test saving consolidated digest creates file with timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            markdown_content = "# Consolidated Newsletter\n\nContent here."

            result_path = save_consolidated_digest(markdown_content, str(output_dir))

            # Verify file was created with timestamp pattern
            assert result_path is not None
            assert Path(result_path).exists()
            assert "digest_" in Path(result_path).name
            assert Path(result_path).name.endswith(".md")

    def test_save_consolidated_digest_saves_correct_content(self):
        """Test saving consolidated digest saves correct markdown content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            markdown_content = "# Consolidated Newsletter\n\n## Article 1\n\nContent here."

            result_path = save_consolidated_digest(markdown_content, str(output_dir))

            # Verify content
            with open(result_path, "r", encoding="utf-8") as f:
                saved_content = f.read()

            assert saved_content == markdown_content
            assert "# Consolidated Newsletter" in saved_content

    def test_save_consolidated_digest_creates_directory_if_needed(self):
        """Test saving consolidated digest creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output" / "subdir"

            markdown_content = "# Newsletter\n\nContent."

            save_consolidated_digest(markdown_content, str(output_dir))

            # Verify directory and file were created
            assert output_dir.exists()
            # Check that at least one digest file exists
            digest_files = list(output_dir.glob("digest_*.md"))
            assert len(digest_files) > 0

    def test_save_consolidated_digest_uses_unique_timestamps(self):
        """Test that multiple saves create files with different timestamps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            content1 = "# Newsletter 1"
            content2 = "# Newsletter 2"

            import time

            path1 = save_consolidated_digest(content1, str(output_dir))
            time.sleep(1.1)  # Sleep for more than 1 second to ensure different timestamp
            path2 = save_consolidated_digest(content2, str(output_dir))

            # Verify both files exist and have different names
            assert Path(path1).exists()
            assert Path(path2).exists()
            assert path1 != path2

    def test_insert_newsletter_items_stores_raw_data(self):
        """Test that raw_data JSON is stored for reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            init_database(str(db_path))

            # First, create a processed_emails record
            track_email_processed(
                str(db_path),
                message_id="msg1",
                sender_email="sender@example.com",
                status="collected",
            )

            message_id = "msg1"
            parsed_items = [
                {
                    "date": "2024-12-30",
                    "title": "Article Title",
                    "summary": "Summary",
                    "link": "https://example.com",
                    "extra_field": "extra_value",  # Extra field that might not be in schema
                }
            ]

            insert_newsletter_items(str(db_path), message_id, parsed_items)

            # Verify raw_data contains full JSON
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT raw_data FROM newsletter_items WHERE message_id = ?",
                (message_id,),
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None
            raw_data = json.loads(result[0])
            assert raw_data == parsed_items[0]
            assert "extra_field" in raw_data


class TestApplyRetentionPolicy:
    """Tests for apply_retention_policy() function."""

    def test_apply_retention_policy_deletes_oldest_records(self):
        """Test that retention policy deletes oldest records beyond limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            emails_dir = Path(tmpdir) / "emails"
            markdown_dir = Path(tmpdir) / "markdown"
            parsed_dir = Path(tmpdir) / "parsed"
            
            emails_dir.mkdir()
            markdown_dir.mkdir()
            parsed_dir.mkdir()
            
            init_database(str(db_path))

            # Create 5 records with different processed_at times
            for i in range(5):
                message_id = f"msg{i}"
                # Track as processed with different timestamps
                track_email_processed(
                    str(db_path),
                    message_id=message_id,
                    sender_email="sender@example.com",
                    status="parsed",
                    subject=f"Subject {i}",
                )
                # Update processed_at to create ordering
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                # Use ISO format timestamps with different times
                processed_time = datetime.now().isoformat().replace("T", " ").split(".")[0]
                cursor.execute(
                    "UPDATE processed_emails SET processed_at = datetime(?, '+' || ? || ' seconds') WHERE message_id = ?",
                    (processed_time, i, message_id),
                )
                conn.commit()
                conn.close()
                
                # Create files for each message
                save_email({"message_id": message_id, "subject": f"Subject {i}"}, str(emails_dir))
                save_markdown(message_id, f"# Markdown {i}", str(markdown_dir))
                save_parsed_items(message_id, [{"title": f"Article {i}"}], str(parsed_dir))
                
                # Add newsletter items
                insert_newsletter_items(str(db_path), message_id, [{"title": f"Article {i}"}])

            # Apply retention policy with limit of 3
            deleted_count = apply_retention_policy(
                str(db_path),
                [str(emails_dir), str(markdown_dir), str(parsed_dir)],
                retention_limit=3,
            )

            # Should delete 2 oldest records (5 total - 3 limit = 2 deleted)
            assert deleted_count == 2

            # Verify only 3 records remain
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_emails")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 3

            # Verify files for deleted messages are gone
            # Oldest 2 should be deleted (msg0 and msg1)
            assert not (emails_dir / "msg0.json").exists()
            assert not (emails_dir / "msg1.json").exists()
            assert (emails_dir / "msg2.json").exists()
            assert (emails_dir / "msg3.json").exists()
            assert (emails_dir / "msg4.json").exists()

            assert not (markdown_dir / "msg0.md").exists()
            assert not (markdown_dir / "msg1.md").exists()
            assert (markdown_dir / "msg2.md").exists()

            assert not (parsed_dir / "msg0.json").exists()
            assert not (parsed_dir / "msg1.json").exists()
            assert (parsed_dir / "msg2.json").exists()

            # Verify newsletter_items for deleted messages are gone
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM newsletter_items WHERE message_id IN ('msg0', 'msg1')")
            deleted_items_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM newsletter_items")
            total_items_count = cursor.fetchone()[0]
            conn.close()
            assert deleted_items_count == 0
            assert total_items_count == 3  # Only items for msg2, msg3, msg4 remain

    def test_apply_retention_policy_no_deletion_when_under_limit(self):
        """Test that retention policy doesn't delete when under limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            emails_dir = Path(tmpdir) / "emails"
            markdown_dir = Path(tmpdir) / "markdown"
            parsed_dir = Path(tmpdir) / "parsed"
            
            emails_dir.mkdir()
            markdown_dir.mkdir()
            parsed_dir.mkdir()
            
            init_database(str(db_path))

            # Create 2 records
            for i in range(2):
                message_id = f"msg{i}"
                track_email_processed(
                    str(db_path),
                    message_id=message_id,
                    sender_email="sender@example.com",
                    status="parsed",
                )
                save_email({"message_id": message_id}, str(emails_dir))
                save_markdown(message_id, f"# Markdown {i}", str(markdown_dir))
                save_parsed_items(message_id, [{"title": f"Article {i}"}], str(parsed_dir))
                insert_newsletter_items(str(db_path), message_id, [{"title": f"Article {i}"}])

            # Apply retention policy with limit of 5 (more than we have)
            deleted_count = apply_retention_policy(
                str(db_path),
                [str(emails_dir), str(markdown_dir), str(parsed_dir)],
                retention_limit=5,
            )

            # Should delete nothing
            assert deleted_count == 0

            # Verify all records still exist
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processed_emails")
            count = cursor.fetchone()[0]
            conn.close()
            assert count == 2

            # Verify all files still exist
            assert (emails_dir / "msg0.json").exists()
            assert (emails_dir / "msg1.json").exists()

    def test_apply_retention_policy_handles_missing_files_gracefully(self):
        """Test that retention policy handles missing files without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            emails_dir = Path(tmpdir) / "emails"
            markdown_dir = Path(tmpdir) / "markdown"
            parsed_dir = Path(tmpdir) / "parsed"
            
            emails_dir.mkdir()
            markdown_dir.mkdir()
            parsed_dir.mkdir()
            
            init_database(str(db_path))

            # Create 3 records with processed_at timestamps
            base_time = datetime.now()
            for i in range(3):
                message_id = f"msg{i}"
                track_email_processed(
                    str(db_path),
                    message_id=message_id,
                    sender_email="sender@example.com",
                    status="parsed",
                )
                # Set processed_at explicitly
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                from datetime import timedelta
                processed_time = (base_time - timedelta(seconds=10-i)).isoformat().replace("T", " ").split(".")[0]
                cursor.execute(
                    "UPDATE processed_emails SET processed_at = ? WHERE message_id = ?",
                    (processed_time, message_id),
                )
                conn.commit()
                conn.close()
                
                # Only create some files (simulate missing files)
                if i < 2:
                    save_email({"message_id": message_id}, str(emails_dir))
                save_markdown(message_id, f"# Markdown {i}", str(markdown_dir))
                insert_newsletter_items(str(db_path), message_id, [{"title": f"Article {i}"}])

            # Apply retention policy with limit of 1
            # Should not raise error even if some files are missing
            deleted_count = apply_retention_policy(
                str(db_path),
                [str(emails_dir), str(markdown_dir), str(parsed_dir)],
                retention_limit=1,
            )

            # Should delete 2 records
            assert deleted_count == 2

    def test_apply_retention_policy_orders_by_processed_at(self):
        """Test that retention policy orders by processed_at timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            emails_dir = Path(tmpdir) / "emails"
            markdown_dir = Path(tmpdir) / "markdown"
            parsed_dir = Path(tmpdir) / "parsed"
            
            emails_dir.mkdir()
            markdown_dir.mkdir()
            parsed_dir.mkdir()
            
            init_database(str(db_path))

            # Create records with explicit processed_at times (oldest first)
            base_time = datetime.now()
            for i in range(4):
                message_id = f"msg{i}"
                track_email_processed(
                    str(db_path),
                    message_id=message_id,
                    sender_email="sender@example.com",
                    status="parsed",
                )
                # Set processed_at explicitly (older records have earlier times)
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                # Use datetime arithmetic to create ordering
                from datetime import timedelta
                processed_time = (base_time - timedelta(seconds=10-i)).isoformat().replace("T", " ").split(".")[0]
                cursor.execute(
                    "UPDATE processed_emails SET processed_at = ? WHERE message_id = ?",
                    (processed_time, message_id),
                )
                conn.commit()
                conn.close()
                
                save_email({"message_id": message_id}, str(emails_dir))
                save_markdown(message_id, f"# Markdown {i}", str(markdown_dir))
                save_parsed_items(message_id, [{"title": f"Article {i}"}], str(parsed_dir))
                insert_newsletter_items(str(db_path), message_id, [{"title": f"Article {i}"}])

            # Apply retention policy with limit of 2
            deleted_count = apply_retention_policy(
                str(db_path),
                [str(emails_dir), str(markdown_dir), str(parsed_dir)],
                retention_limit=2,
            )

            # Should delete 2 oldest (msg0 and msg1)
            assert deleted_count == 2

            # Verify oldest are deleted, newest remain
            assert not (emails_dir / "msg0.json").exists()
            assert not (emails_dir / "msg1.json").exists()
            assert (emails_dir / "msg2.json").exists()
            assert (emails_dir / "msg3.json").exists()
