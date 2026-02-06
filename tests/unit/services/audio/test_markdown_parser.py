"""Unit tests for markdown parser."""

import pytest
from src.services.audio.markdown_parser import parse_newsletter_items


def test_parse_newsletter_items():
    """Test parsing markdown into structured items."""
    markdown = """
# Newsletter Digest - 2026-02-05

## Technology

### First Article
*Date: 2026-02-05*
Content for first article.
This is the body text.
[Read More](https://example.com/first)

### Second Article
*Date: 2026-02-05*
Content for second article.
Multi-line content here.
[Read More](https://example.com/second)
"""

    items = parse_newsletter_items(markdown)

    assert len(items) == 2
    assert items[0].title == "First Article"
    assert items[0].item_number == 1
    assert items[0].voice_gender == "male"  # Odd
    assert "Content for first article" in items[0].content
    assert "Read More" not in items[0].content  # Metadata excluded
    assert "Date:" not in items[0].content

    assert items[1].title == "Second Article"
    assert items[1].item_number == 2
    assert items[1].voice_gender == "female"  # Even
    assert "Content for second article" in items[1].content


def test_parse_empty_newsletter():
    """Test parsing empty or whitespace-only markdown."""
    markdown = """
# Newsletter Digest

## Technology

"""
    items = parse_newsletter_items(markdown)
    assert len(items) == 0


def test_parse_newsletter_excludes_metadata():
    """Test that metadata lines are excluded from content."""
    markdown = """
### Test Article
*Date: 2026-02-05*
Article content here.
More content.
[Read More](https://example.com)
"""

    items = parse_newsletter_items(markdown)
    assert len(items) == 1
    assert "Read More" not in items[0].content
    assert "Date:" not in items[0].content
    assert "Article content here" in items[0].content
    assert "More content" in items[0].content
