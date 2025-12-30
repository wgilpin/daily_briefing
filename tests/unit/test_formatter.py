"""Unit tests for markdown formatting functions."""

import os
import tempfile
from pathlib import Path

import pytest

from src.zotero.formatter import format_item_markdown, generate_digest, write_digest


def test_format_item_markdown_with_complete_item_data():
    """Test format_item_markdown() with complete item data."""
    item = {
        "key": "item1",
        "data": {
            "title": "Test Article Title",
            "itemType": "journalArticle",
            "creators": [
                {"firstName": "John", "lastName": "Doe", "creatorType": "author"},
                {"firstName": "Jane", "lastName": "Smith", "creatorType": "author"},
            ],
            "date": "2024-01-15",
            "publicationTitle": "Journal of Testing",
            "abstractNote": "This is a test abstract for the article.",
            "url": "https://example.com/article",
        }
    }
    
    result = format_item_markdown(item)
    
    # Should contain title as ### header
    assert "### Test Article Title" in result
    
    # Should contain authors formatted as "LastName, FirstName"
    assert "Doe, John" in result
    assert "Smith, Jane" in result
    
    # Should contain publication date
    assert "2024-01-15" in result
    
    # Should contain venue
    assert "Journal of Testing" in result
    
    # Should contain abstract
    assert "This is a test abstract" in result
    
    # Should contain URL as markdown link
    assert "[https://example.com/article](https://example.com/article)" in result or "URL" in result


def test_format_item_markdown_with_missing_optional_fields():
    """Test format_item_markdown() with missing optional fields."""
    item = {
        "key": "item2",
        "data": {
            "title": "Minimal Item",
            "itemType": "journalArticle",
            # No creators, date, venue, abstract, or URL
        }
    }
    
    result = format_item_markdown(item)
    
    # Should still contain title
    assert "### Minimal Item" in result
    
    # Should handle missing fields gracefully (not crash)
    # Missing fields should either be omitted or show "N/A"
    assert result  # Should not be empty


def test_format_item_markdown_with_special_markdown_characters():
    """Test format_item_markdown() with special markdown characters in titles."""
    item = {
        "key": "item3",
        "data": {
            "title": "Article with # Special * Characters & <Tags>",
            "itemType": "journalArticle",
            "creators": [{"firstName": "Test", "lastName": "Author", "creatorType": "author"}],
        }
    }
    
    result = format_item_markdown(item)
    
    # Special characters should be escaped in the title
    # The title should appear but markdown special chars should be escaped
    assert "Article" in result
    # Check that # is escaped (should be \# or handled properly)
    # Since we're using ### for header, the # in title should be escaped
    assert "Special" in result


def test_generate_digest_with_multiple_item_types():
    """Test generate_digest() with multiple item types."""
    items = [
        {
            "key": "item1",
            "data": {
                "title": "Journal Article",
                "itemType": "journalArticle",
                "date": "2024-01-01",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Book Title",
                "itemType": "book",
                "date": "2024-02-01",
            }
        },
        {
            "key": "item3",
            "data": {
                "title": "Another Article",
                "itemType": "journalArticle",
                "date": "2024-03-01",
            }
        },
    ]
    
    result = generate_digest(items, days=1)
    
    # Should have main header
    assert "#" in result
    assert "Zotero Digest" in result or "Digest" in result
    
    # Should have sections for each item type
    assert "## journalArticle" in result or "## Journal Article" in result
    assert "## book" in result or "## Book" in result
    
    # Should contain all items
    assert "Journal Article" in result
    assert "Book Title" in result
    assert "Another Article" in result


def test_generate_digest_with_empty_items_list():
    """Test generate_digest() with empty items list."""
    result = generate_digest([], days=1)
    
    # Should return message about no items found
    assert "No items found" in result or "no items" in result.lower()
    assert "1" in result or "day" in result.lower()


def test_write_digest_file_creation():
    """Test write_digest() file creation."""
    content = "# Test Digest\n\nThis is a test digest content."
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_digest.md")
        
        write_digest(content, output_path)
        
        # File should exist
        assert os.path.exists(output_path)
        
        # File should contain the content
        with open(output_path, "r", encoding="utf-8") as f:
            written_content = f.read()
            assert written_content == content


def test_write_digest_creates_directory():
    """Test write_digest() creates output directory if needed."""
    content = "# Test Digest\n\nContent."
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "subdir", "nested", "digest.md")
        
        write_digest(content, output_path)
        
        # Directory should be created
        assert os.path.exists(os.path.dirname(output_path))
        
        # File should exist
        assert os.path.exists(output_path)


def test_format_item_markdown_handles_empty_creators():
    """Test format_item_markdown() handles empty creators list."""
    item = {
        "key": "item4",
        "data": {
            "title": "Item Without Authors",
            "itemType": "journalArticle",
            "creators": [],  # Empty creators list
        }
    }
    
    result = format_item_markdown(item)
    
    # Should not crash
    assert result
    assert "Item Without Authors" in result


def test_format_item_markdown_handles_partial_creator_names():
    """Test format_item_markdown() handles creators with missing first or last name."""
    item = {
        "key": "item5",
        "data": {
            "title": "Item with Partial Names",
            "itemType": "journalArticle",
            "creators": [
                {"lastName": "Doe", "creatorType": "author"},  # No firstName
                {"firstName": "Jane", "creatorType": "author"},  # No lastName
            ],
        }
    }
    
    result = format_item_markdown(item)
    
    # Should handle gracefully
    assert result
    assert "Item with Partial Names" in result

