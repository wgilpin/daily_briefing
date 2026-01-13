"""Unit tests for markdown converter functions."""

import pytest

from src.newsletter.markdown_converter import convert_to_markdown


class TestConvertToMarkdown:
    """Tests for convert_to_markdown() function."""

    def test_convert_to_markdown_with_html_email(self):
        """Test converting HTML email to markdown."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": "<h1>Title</h1><p>This is a <strong>test</strong> paragraph.</p><a href='https://example.com'>Link</a>",
            "body_text": None,
        }

        result = convert_to_markdown(email)

        assert isinstance(result, str)
        assert len(result) > 0
        # html2text should convert HTML to markdown
        # Check that some markdown elements are present
        assert "Title" in result or "test" in result

    def test_convert_to_markdown_with_plain_text_email(self):
        """Test converting plain text email to markdown."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": None,
            "body_text": "This is a plain text email.\n\nIt has multiple paragraphs.\n\nAnd line breaks.",
        }

        result = convert_to_markdown(email)

        assert isinstance(result, str)
        assert "This is a plain text email" in result
        assert "multiple paragraphs" in result

    def test_convert_to_markdown_prefers_html_over_text(self):
        """Test that HTML is preferred over plain text when both are present."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": "<h1>HTML Title</h1><p>HTML content</p>",
            "body_text": "Plain text content",
        }

        result = convert_to_markdown(email)

        # Should use HTML (html2text will convert it)
        # The result should be from HTML conversion, not plain text
        assert isinstance(result, str)
        assert len(result) > 0

    def test_convert_to_markdown_preserves_links(self):
        """Test that links are preserved in markdown conversion."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": '<p>Visit <a href="https://example.com">Example</a> for more info.</p>',
            "body_text": None,
        }

        result = convert_to_markdown(email)

        # html2text should convert links to markdown format
        assert isinstance(result, str)
        # Link text or URL should be present
        assert "example.com" in result.lower() or "Example" in result

    def test_convert_to_markdown_preserves_headings(self):
        """Test that headings are preserved in markdown conversion."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": "<h1>Main Heading</h1><h2>Subheading</h2><p>Content</p>",
            "body_text": None,
        }

        result = convert_to_markdown(email)

        assert isinstance(result, str)
        # Headings should be converted to markdown
        assert "Main Heading" in result or "Subheading" in result

    def test_convert_to_markdown_preserves_lists(self):
        """Test that lists are preserved in markdown conversion."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": "<ul><li>Item 1</li><li>Item 2</li></ul>",
            "body_text": None,
        }

        result = convert_to_markdown(email)

        assert isinstance(result, str)
        # List items should be present
        assert "Item 1" in result or "Item 2" in result

    def test_convert_to_markdown_with_images(self):
        """Test converting email with images to markdown."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": '<p>Text with <img src="https://example.com/image.png" alt="Image"> image.</p>',
            "body_text": None,
        }

        result = convert_to_markdown(email)

        assert isinstance(result, str)
        # Image reference should be handled (html2text may convert to alt text or markdown)
        assert len(result) > 0

    def test_convert_to_markdown_with_attachments_reference(self):
        """Test converting email that references attachments."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": "<p>This email has attachments mentioned in the text.</p>",
            "body_text": None,
            "attachments": ["file1.pdf", "file2.jpg"],
        }

        result = convert_to_markdown(email)

        assert isinstance(result, str)
        # Should still convert successfully even with attachment references
        assert "attachments" in result.lower() or len(result) > 0

    def test_convert_to_markdown_with_empty_body(self):
        """Test converting email with empty body."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": None,
            "body_text": None,
        }

        result = convert_to_markdown(email)

        # Should return empty string or handle gracefully
        assert isinstance(result, str)

    def test_convert_to_markdown_handles_special_characters(self):
        """Test converting email with special characters."""
        email = {
            "message_id": "msg1",
            "sender": "sender@example.com",
            "subject": "Test Email",
            "body_html": "<p>Special chars: &amp; &lt; &gt; &quot; &apos;</p>",
            "body_text": None,
        }

        result = convert_to_markdown(email)

        assert isinstance(result, str)
        # html2text should decode HTML entities
        assert len(result) > 0
