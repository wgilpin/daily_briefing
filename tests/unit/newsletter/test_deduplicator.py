"""Unit tests for newsletter deduplicator."""

import json
from unittest.mock import MagicMock

from src.newsletter.deduplicator import deduplicate_items, cluster_items, merge_cluster


def make_item(title, summary="", source_type="newsletter", date="2026-01-15", link=None):
    """Create a test item dict matching the format used by feed_routes."""
    return {
        "date": date,
        "title": title,
        "summary": summary,
        "link": link,
        "source_type": source_type,
    }


class TestDeduplicateItems:
    """Test the deduplicate_items orchestrator function."""

    def test_empty_list_returns_empty(self):
        """Empty list returns empty without any LLM call."""
        mock_client = MagicMock()
        result = deduplicate_items([], mock_client, "gemini-2.5-flash")

        assert result == []
        mock_client.models.generate_content.assert_not_called()

    def test_single_item_returns_unchanged(self):
        """Single item list returned as-is, no LLM call."""
        mock_client = MagicMock()
        items = [make_item("Test Article")]

        result = deduplicate_items(items, mock_client, "gemini-2.5-flash")

        assert result == items
        mock_client.models.generate_content.assert_not_called()

    def test_no_duplicates_all_singletons(self):
        """LLM clusters every item alone; output equals input."""
        mock_client = MagicMock()
        cluster_response = MagicMock()
        cluster_response.text = json.dumps({
            "clusters": [["item_0"], ["item_1"], ["item_2"]]
        })
        mock_client.models.generate_content.return_value = cluster_response

        items = [
            make_item("Story A"),
            make_item("Story B"),
            make_item("Story C"),
        ]

        result = deduplicate_items(items, mock_client, "gemini-2.5-flash")

        assert len(result) == 3
        assert result == items
        # Only clustering call, no merge calls
        assert mock_client.models.generate_content.call_count == 1

    def test_two_duplicates_merged(self):
        """Two items clustered together; merge_cluster called once; output has one fewer item."""
        mock_client = MagicMock()

        # First call: cluster_items
        cluster_response = MagicMock()
        cluster_response.text = json.dumps({
            "clusters": [["item_0", "item_1"], ["item_2"]]
        })

        # Second call: merge_cluster
        merge_response = MagicMock()
        merge_response.text = json.dumps({
            "date": "2026-01-15",
            "title": "OpenAI launches GPT-5",
            "summary": "Merged summary from both sources.",
            "link": "https://openai.com/gpt5",
            "source_type": "newsletter",
        })

        mock_client.models.generate_content.side_effect = [
            cluster_response,
            merge_response,
        ]

        items = [
            make_item("OpenAI launches GPT-5", "Source A coverage"),
            make_item("GPT-5 released by OpenAI", "Source B coverage"),
            make_item("SpaceX Starship update", "Unique story"),
        ]

        result = deduplicate_items(items, mock_client, "gemini-2.5-flash")

        assert len(result) == 2
        assert result[0]["title"] == "OpenAI launches GPT-5"
        assert result[1]["title"] == "SpaceX Starship update"
        # Cluster call + 1 merge call = 2 LLM calls total
        assert mock_client.models.generate_content.call_count == 2

    def test_mixed_clusters(self):
        """5 items: cluster of 2, cluster of 2, singleton. Output has 3 items."""
        mock_client = MagicMock()

        cluster_response = MagicMock()
        cluster_response.text = json.dumps({
            "clusters": [["item_0", "item_1"], ["item_2", "item_3"], ["item_4"]]
        })

        merge_response_1 = MagicMock()
        merge_response_1.text = json.dumps({
            "date": "2026-01-15",
            "title": "Story A merged",
            "summary": "Merged A",
            "link": None,
            "source_type": "newsletter",
        })

        merge_response_2 = MagicMock()
        merge_response_2.text = json.dumps({
            "date": "2026-01-16",
            "title": "Story B merged",
            "summary": "Merged B",
            "link": None,
            "source_type": "newsletter",
        })

        mock_client.models.generate_content.side_effect = [
            cluster_response,
            merge_response_1,
            merge_response_2,
        ]

        items = [
            make_item("Story A v1"),
            make_item("Story A v2"),
            make_item("Story B v1"),
            make_item("Story B v2"),
            make_item("Story C unique"),
        ]

        result = deduplicate_items(items, mock_client, "gemini-2.5-flash")

        assert len(result) == 3
        assert result[0]["title"] == "Story A merged"
        assert result[1]["title"] == "Story B merged"
        assert result[2]["title"] == "Story C unique"
        # 1 cluster + 2 merges = 3 calls
        assert mock_client.models.generate_content.call_count == 3

    def test_llm_failure_returns_originals(self):
        """generate_content raises exception; original items returned."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")

        items = [
            make_item("Story A"),
            make_item("Story B"),
        ]

        result = deduplicate_items(items, mock_client, "gemini-2.5-flash")

        assert result == items

    def test_output_format_matches_input_format(self):
        """Merged items have all expected keys."""
        mock_client = MagicMock()

        cluster_response = MagicMock()
        cluster_response.text = json.dumps({
            "clusters": [["item_0", "item_1"]]
        })

        merge_response = MagicMock()
        merge_response.text = json.dumps({
            "date": "2026-01-15",
            "title": "Merged Story",
            "summary": "Merged summary",
            "link": "https://example.com",
            "source_type": "newsletter",
        })

        mock_client.models.generate_content.side_effect = [
            cluster_response,
            merge_response,
        ]

        items = [
            make_item("Story v1", summary="Summary 1", link="https://link1.com"),
            make_item("Story v2", summary="Summary 2", link="https://link2.com"),
        ]

        result = deduplicate_items(items, mock_client, "gemini-2.5-flash")

        assert len(result) == 1
        merged = result[0]
        assert "date" in merged
        assert "title" in merged
        assert "summary" in merged
        assert "link" in merged
        assert "source_type" in merged


class TestClusterItems:
    """Test the cluster_items function."""

    def test_cluster_prompt_contains_items(self):
        """Verify the prompt sent to LLM contains item IDs and text."""
        mock_client = MagicMock()
        cluster_response = MagicMock()
        cluster_response.text = json.dumps({"clusters": [["item_0"], ["item_1"]]})
        mock_client.models.generate_content.return_value = cluster_response

        items = [
            make_item("Title A", summary="Summary A"),
            make_item("Title B", summary="Summary B"),
        ]

        cluster_items(items, mock_client, "gemini-2.5-flash")

        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]["contents"]

        assert "item_0" in prompt
        assert "item_1" in prompt
        assert "Title A" in prompt
        assert "Title B" in prompt

    def test_valid_cluster_response_parsed(self):
        """Mock LLM returns valid cluster JSON; parsed correctly."""
        mock_client = MagicMock()
        cluster_response = MagicMock()
        cluster_response.text = json.dumps({
            "clusters": [["item_0", "item_1"], ["item_2"]]
        })
        mock_client.models.generate_content.return_value = cluster_response

        items = [make_item("A"), make_item("B"), make_item("C")]

        result = cluster_items(items, mock_client, "gemini-2.5-flash")

        assert result == [["item_0", "item_1"], ["item_2"]]

    def test_missing_items_added_as_singletons(self):
        """LLM returns clusters missing item_2; it gets added as singleton."""
        mock_client = MagicMock()
        cluster_response = MagicMock()
        # Only item_0 and item_1 in clusters, item_2 missing
        cluster_response.text = json.dumps({
            "clusters": [["item_0", "item_1"]]
        })
        mock_client.models.generate_content.return_value = cluster_response

        items = [make_item("A"), make_item("B"), make_item("C")]

        result = cluster_items(items, mock_client, "gemini-2.5-flash")

        # Should have original cluster plus item_2 as singleton
        assert ["item_0", "item_1"] in result
        assert ["item_2"] in result
        assert len(result) == 2

    def test_invalid_json_returns_singletons(self):
        """LLM returns garbled text; all items become singletons."""
        mock_client = MagicMock()
        cluster_response = MagicMock()
        cluster_response.text = "Not valid JSON!"
        mock_client.models.generate_content.return_value = cluster_response

        items = [make_item("A"), make_item("B")]

        result = cluster_items(items, mock_client, "gemini-2.5-flash")

        assert result == [["item_0"], ["item_1"]]

    def test_uses_json_response_mode(self):
        """Verify response_mime_type='application/json' is in the config."""
        mock_client = MagicMock()
        cluster_response = MagicMock()
        cluster_response.text = json.dumps({"clusters": [["item_0"]]})
        mock_client.models.generate_content.return_value = cluster_response

        items = [make_item("A")]

        cluster_items(items, mock_client, "gemini-2.5-flash")

        call_args = mock_client.models.generate_content.call_args
        config = call_args[1]["config"]
        assert config.response_mime_type == "application/json"


class TestMergeCluster:
    """Test the merge_cluster function."""

    def test_merge_two_items(self):
        """Two items sent; merged dict returned with expected keys."""
        mock_client = MagicMock()
        merge_response = MagicMock()
        merge_response.text = json.dumps({
            "date": "2026-01-15",
            "title": "Merged Title",
            "summary": "Merged summary from both sources.",
            "link": "https://merged.com",
            "source_type": "newsletter",
        })
        mock_client.models.generate_content.return_value = merge_response

        items = [
            make_item("Title 1", "Summary 1", link="https://link1.com"),
            make_item("Title 2", "Summary 2", link="https://link2.com"),
        ]

        result = merge_cluster(items, mock_client, "gemini-2.5-flash")

        assert result["title"] == "Merged Title"
        assert result["summary"] == "Merged summary from both sources."
        assert result["link"] == "https://merged.com"
        assert result["source_type"] == "newsletter"

    def test_merge_preserves_authors_from_zotero(self):
        """If an input item has authors, verify the merge doesn't crash."""
        mock_client = MagicMock()
        merge_response = MagicMock()
        merge_response.text = json.dumps({
            "date": "2026-01-15",
            "title": "Merged",
            "summary": "Summary",
            "link": None,
            "source_type": "newsletter",
        })
        mock_client.models.generate_content.return_value = merge_response

        items = [
            {**make_item("Paper A"), "authors": "Smith, Jones"},
            {**make_item("Paper B"), "authors": "Doe"},
        ]

        # Should not crash even with extra 'authors' field
        result = merge_cluster(items, mock_client, "gemini-2.5-flash")

        assert result["title"] == "Merged"

    def test_merge_llm_failure_returns_first_item(self):
        """LLM raises exception; first item returned."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")

        items = [
            make_item("Title 1", "Summary 1"),
            make_item("Title 2", "Summary 2"),
        ]

        result = merge_cluster(items, mock_client, "gemini-2.5-flash")

        assert result == items[0]

    def test_merge_invalid_json_returns_first_item(self):
        """LLM returns invalid JSON; first item returned."""
        mock_client = MagicMock()
        merge_response = MagicMock()
        merge_response.text = "Not valid JSON"
        mock_client.models.generate_content.return_value = merge_response

        items = [
            make_item("Title 1", "Summary 1"),
            make_item("Title 2", "Summary 2"),
        ]

        result = merge_cluster(items, mock_client, "gemini-2.5-flash")

        assert result == items[0]

    def test_merge_missing_title_returns_first_item(self):
        """LLM returns JSON without title key; first item returned."""
        mock_client = MagicMock()
        merge_response = MagicMock()
        merge_response.text = json.dumps({
            "date": "2026-01-15",
            "summary": "Summary",
            # Missing 'title'
        })
        mock_client.models.generate_content.return_value = merge_response

        items = [
            make_item("Title 1", "Summary 1"),
            make_item("Title 2", "Summary 2"),
        ]

        result = merge_cluster(items, mock_client, "gemini-2.5-flash")

        assert result == items[0]
