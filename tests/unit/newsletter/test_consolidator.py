"""Unit tests for newsletter consolidator with topic exclusions."""

import json
import pytest
from unittest.mock import MagicMock

from src.newsletter.consolidator import consolidate_newsletters


class TestConsolidatorWithExclusions:
    """Test consolidate_newsletters function with exclusion support."""

    def test_consolidate_with_no_exclusions(self):
        """Consolidator works without exclusions parameter."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "# Newsletter\n\nConsolidated content"
        mock_client.models.generate_content.return_value = mock_response

        items = [{"title": "Test Article", "summary": "Summary"}]
        result = consolidate_newsletters(
            items, "consolidate prompt", mock_client, "gemini-2.5-flash"
        )

        assert result == "# Newsletter\n\nConsolidated content"
        mock_client.models.generate_content.assert_called_once()

    def test_consolidate_with_exclusions_parameter(self):
        """Consolidator accepts excluded_topics parameter."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "# Newsletter\n\nFiltered content"
        mock_client.models.generate_content.return_value = mock_response

        items = [{"title": "Test Article", "summary": "Summary"}]
        exclusions = ["datasette", "SQL"]

        result = consolidate_newsletters(
            items, "consolidate prompt", mock_client, "gemini-2.5-flash", exclusions
        )

        assert result == "# Newsletter\n\nFiltered content"
        mock_client.models.generate_content.assert_called_once()

    def test_exclusions_injected_into_prompt(self):
        """Exclusion instructions are added to the LLM prompt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "# Newsletter\n\nContent"
        mock_client.models.generate_content.return_value = mock_response

        items = [{"title": "Article", "summary": "Summary"}]
        exclusions = ["datasette", "low-level coding"]

        consolidate_newsletters(
            items, "consolidate prompt", mock_client, "gemini-2.5-flash", exclusions
        )

        # Get the prompt that was passed to LLM
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        # Verify exclusion instructions are in prompt
        assert "CRITICAL INSTRUCTION" in prompt
        assert "datasette" in prompt
        assert "low-level coding" in prompt
        assert "exclude" in prompt.lower() or "skip" in prompt.lower()

    def test_empty_exclusions_list_no_instructions(self):
        """Empty exclusions list doesn't add instructions to prompt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "# Newsletter\n\nContent"
        mock_client.models.generate_content.return_value = mock_response

        items = [{"title": "Article", "summary": "Summary"}]
        exclusions = []

        consolidate_newsletters(
            items, "consolidate prompt", mock_client, "gemini-2.5-flash", exclusions
        )

        # Get the prompt
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        # Verify NO exclusion instructions when list is empty
        assert "CRITICAL INSTRUCTION" not in prompt
        assert "exclude" not in prompt.lower()

    def test_prompt_format_with_multiple_exclusions(self):
        """Prompt correctly formats multiple exclusion topics."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "# Newsletter\n\nContent"
        mock_client.models.generate_content.return_value = mock_response

        items = [{"title": "Article", "summary": "Summary"}]
        exclusions = ["topic1", "topic2", "topic3"]

        consolidate_newsletters(
            items, "consolidate prompt", mock_client, "gemini-2.5-flash", exclusions
        )

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        # Verify all topics appear in prompt
        assert "topic1" in prompt
        assert "topic2" in prompt
        assert "topic3" in prompt

    def test_exclusions_none_behaves_like_empty(self):
        """Passing None for exclusions behaves like empty list."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "# Newsletter\n\nContent"
        mock_client.models.generate_content.return_value = mock_response

        items = [{"title": "Article", "summary": "Summary"}]

        consolidate_newsletters(
            items, "consolidate prompt", mock_client, "gemini-2.5-flash", None
        )

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        # Verify no exclusion instructions
        assert "CRITICAL INSTRUCTION" not in prompt
