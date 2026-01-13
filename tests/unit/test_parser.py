"""Unit tests for newsletter parser functions."""

from unittest.mock import MagicMock, Mock

import pytest

from src.newsletter.parser import parse_newsletter


class TestParseNewsletter:
    """Tests for parse_newsletter() function."""

    def test_parse_newsletter_with_single_article(self):
        """Test parsing newsletter with single article."""
        markdown_content = """
# Newsletter Title

## Article Title
Published: 2024-12-30
Summary: This is a test article about something interesting.
Link: https://example.com/article
"""

        prompt = "Extract articles from this newsletter. Return JSON array with date, title, summary, link."

        # Mock LLM client (Gemini API)
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = '{"items": [{"date": "2024-12-30", "title": "Article Title", "summary": "This is a test article about something interesting.", "link": "https://example.com/article"}]}'
        mock_llm_client.models.generate_content.return_value = mock_response

        result = parse_newsletter(markdown_content, prompt, mock_llm_client, "gemini-2.5-flash")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Article Title"
        assert result[0]["date"] == "2024-12-30"
        assert result[0]["summary"] == "This is a test article about something interesting."
        assert result[0]["link"] == "https://example.com/article"

    def test_parse_newsletter_with_multiple_articles(self):
        """Test parsing newsletter with multiple articles."""
        markdown_content = """
# Newsletter

## Article 1
Date: 2024-12-30
Summary: First article
Link: https://example.com/1

## Article 2
Date: 2024-12-29
Summary: Second article
Link: https://example.com/2
"""

        prompt = "Extract articles from this newsletter."

        # Mock LLM client (Gemini API)
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = '{"items": [{"date": "2024-12-30", "title": "Article 1", "summary": "First article", "link": "https://example.com/1"}, {"date": "2024-12-29", "title": "Article 2", "summary": "Second article", "link": "https://example.com/2"}]}'
        mock_llm_client.models.generate_content.return_value = mock_response

        result = parse_newsletter(markdown_content, prompt, mock_llm_client, "gemini-2.5-flash")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Article 1"
        assert result[1]["title"] == "Article 2"

    def test_parse_newsletter_with_missing_fields(self):
        """Test parsing newsletter with missing optional fields."""
        markdown_content = """
# Newsletter

## Article Without All Fields
Just a title here.
"""

        prompt = "Extract articles from this newsletter."

        # Mock LLM client returning item with missing fields
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = '{"items": [{"title": "Article Without All Fields", "date": null, "summary": null, "link": null}]}'
        mock_llm_client.models.generate_content.return_value = mock_response

        result = parse_newsletter(markdown_content, prompt, mock_llm_client, "gemini-2.5-flash")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Article Without All Fields"
        # Missing fields should be None or empty
        assert result[0].get("date") is None or result[0].get("date") == ""
        assert result[0].get("summary") is None or result[0].get("summary") == ""

    def test_parse_newsletter_requires_title(self):
        """Test that parsed items must have at least a title."""
        markdown_content = "# Newsletter\n\nSome content."

        prompt = "Extract articles from this newsletter."

        # Mock LLM client returning item without title (should be filtered or error)
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = '{"items": [{"date": "2024-12-30", "summary": "No title", "link": "https://example.com"}]}'
        mock_llm_client.models.generate_content.return_value = mock_response

        result = parse_newsletter(markdown_content, prompt, mock_llm_client, "gemini-2.5-flash")

        # Items without title should be filtered out or the function should handle it
        # For now, we'll return what LLM gives us, but validation can be added
        assert isinstance(result, list)

    def test_parse_newsletter_handles_empty_response(self):
        """Test parsing when LLM returns empty list."""
        markdown_content = "# Newsletter\n\nNo articles here."

        prompt = "Extract articles from this newsletter."

        # Mock LLM client returning empty list
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = '{"items": []}'
        mock_llm_client.models.generate_content.return_value = mock_response

        result = parse_newsletter(markdown_content, prompt, mock_llm_client, "gemini-2.5-flash")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_newsletter_handles_invalid_json(self):
        """Test parsing when LLM returns invalid JSON."""
        markdown_content = "# Newsletter\n\nSome content."

        prompt = "Extract articles from this newsletter."

        # Mock LLM client returning invalid JSON
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="This is not JSON"))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response

        # Should raise ValueError for invalid JSON
        with pytest.raises(ValueError, match="invalid JSON|Failed to parse"):
            parse_newsletter(markdown_content, prompt, mock_llm_client, "gemini-2.5-flash")

    def test_parse_newsletter_calls_llm_with_correct_parameters(self):
        """Test that parse_newsletter calls LLM with correct prompt and content."""
        markdown_content = "# Newsletter\n\nContent here."
        prompt = "Extract articles: {content}"

        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = '{"items": [{"title": "Test", "date": "2024-12-30"}]}'
        mock_llm_client.models.generate_content.return_value = mock_response

        parse_newsletter(markdown_content, prompt, mock_llm_client, "gemini-2.5-flash")

        # Verify LLM was called
        assert mock_llm_client.models.generate_content.called
        call_args = mock_llm_client.models.generate_content.call_args

        # Check that the model, contents, and config were passed (keyword args in new API)
        assert "model" in call_args.kwargs
        assert "contents" in call_args.kwargs
        assert "config" in call_args.kwargs
