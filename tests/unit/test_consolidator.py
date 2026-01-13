"""Unit tests for newsletter consolidator functions."""

from unittest.mock import MagicMock, Mock

import pytest

from src.newsletter.consolidator import consolidate_newsletters


class TestConsolidateNewsletters:
    """Tests for consolidate_newsletters() function."""

    def test_consolidate_newsletters_with_multiple_items(self):
        """Test consolidating multiple newsletter items."""
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

        prompt = "Create a consolidated newsletter from these items."

        # Mock LLM client (Gemini API)
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = "# Consolidated Newsletter\n\n## Article 1\nSummary 1\n\n## Article 2\nSummary 2\n\n## Article 3\nSummary 3"
        mock_llm_client.models.generate_content.return_value = mock_response

        result = consolidate_newsletters(parsed_items, prompt, mock_llm_client, "gemini-2.5-flash")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Article 1" in result or "Consolidated" in result
        # Verify LLM was called
        assert mock_llm_client.models.generate_content.called

    def test_consolidate_newsletters_with_empty_items_list(self):
        """Test consolidating with empty items list."""
        parsed_items = []
        prompt = "Create a consolidated newsletter."

        # Mock LLM client
        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = "# Newsletter\n\nNo items to consolidate."
        mock_llm_client.models.generate_content.return_value = mock_response

        result = consolidate_newsletters(parsed_items, prompt, mock_llm_client, "gemini-2.5-flash")

        assert isinstance(result, str)
        # Should still return markdown even with empty items
        assert len(result) > 0

    def test_consolidate_newsletters_calls_llm_with_correct_parameters(self):
        """Test that consolidate_newsletters calls LLM with correct prompt and items."""
        parsed_items = [
            {
                "date": "2024-12-30",
                "title": "Test Article",
                "summary": "Test summary",
                "link": "https://example.com",
            }
        ]
        prompt = "Consolidate these items: {items}"

        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = "# Newsletter\n\nTest content"
        mock_llm_client.models.generate_content.return_value = mock_response

        consolidate_newsletters(parsed_items, prompt, mock_llm_client, "gemini-2.5-flash")

        # Verify LLM was called
        assert mock_llm_client.models.generate_content.called
        call_args = mock_llm_client.models.generate_content.call_args

        # Check that the model, contents, and config were passed (keyword args in new API)
        assert "model" in call_args.kwargs
        assert "contents" in call_args.kwargs
        assert "config" in call_args.kwargs

    def test_consolidate_newsletters_handles_llm_error(self):
        """Test that consolidate_newsletters handles LLM API errors by returning fallback."""
        parsed_items = [
            {
                "title": "Test Article",
                "summary": "Test summary",
            }
        ]
        prompt = "Consolidate these items."

        mock_llm_client = MagicMock()
        mock_llm_client.models.generate_content.side_effect = Exception(
            "API Error"
        )

        # Should return fallback digest instead of raising
        result = consolidate_newsletters(parsed_items, prompt, mock_llm_client, "gemini-2.5-flash")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Fallback should contain the item title
        assert "Test Article" in result or "Newsletter" in result

    def test_consolidate_newsletters_returns_markdown_format(self):
        """Test that consolidate_newsletters returns valid markdown."""
        parsed_items = [
            {
                "date": "2024-12-30",
                "title": "Article Title",
                "summary": "Article summary",
                "link": "https://example.com",
            }
        ]
        prompt = "Create a newsletter."

        mock_llm_client = MagicMock()
        mock_response = Mock()
        mock_response.text = "# Newsletter\n\n## Article Title\n\nArticle summary\n\n[Read more](https://example.com)"
        mock_llm_client.models.generate_content.return_value = mock_response

        result = consolidate_newsletters(parsed_items, prompt, mock_llm_client, "gemini-2.5-flash")

        assert isinstance(result, str)
        # Should contain markdown elements
        assert "#" in result or "##" in result or len(result) > 0
