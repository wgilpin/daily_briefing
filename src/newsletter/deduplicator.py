"""LLM-based deduplication of feed items using Map-Reduce approach."""

import json
import logging

import google.genai as genai

logger = logging.getLogger(__name__)

# Clustering prompt - groups items by the exact same specific event
_CLUSTER_PROMPT = """You are a senior news editor. Your task is to identify duplicate or overlapping coverage of the same stories from a list of newsletter snippets.

**Input Data:**
A list of items, each with an `id` and `text` (title + summary).

**Instructions:**
1. Analyze the semantic meaning of each item.
2. Group items that refer to the **same underlying story, event, announcement, report, or release**, even if they cover different angles or sub-topics of it.
3. For example, if a single report spawns multiple articles (e.g., "Latin America productivity opportunity", "Latin America in the Intelligent Age", "What a new era means for Latin America"), these should be grouped as one story.
4. Do NOT group items that are genuinely about unrelated topics, even if they come from the same source.
5. Output strictly valid JSON.

**Output Format:**
{
  "clusters": [
    ["id_1", "id_2"],
    ["id_3"],
    ["id_4", "id_5"]
  ]
}"""

# Merge prompt - combines duplicate items into a single representative item
_MERGE_PROMPT = """You are a senior news editor. You are given multiple newsletter items that cover the same story from different sources.

Merge them into a single item that combines the best information from all sources.

**Rules:**
1. Write one combined title that is clear and specific.
2. Write one combined summary (2 paragraphs) that incorporates the most important details from all sources. Do not repeat information.
3. Pick the most authoritative or original link from the sources.
4. Use the earliest date among the sources.
5. Set source_type to "newsletter".
6. Output strictly valid JSON.

**Output Format:**
{
  "date": "...",
  "title": "...",
  "summary": "...",
  "link": "...",
  "source_type": "..."
}"""


def deduplicate_items(
    items: list[dict],
    llm_client: genai.Client,
    model_name: str,
) -> list[dict]:
    """Deduplicate feed items using LLM-based clustering and merging.

    Orchestrates the full Map-Reduce pipeline:
    1. Assigns temporary IDs to items
    2. Calls cluster_items() to group duplicates
    3. Calls merge_cluster() on each multi-item cluster
    4. Returns deduplicated list in same dict format as input

    Args:
        items: List of item dicts (keys: date, title, summary, link, source_type,
               optionally authors). Must be the same format used by consolidate_newsletters.
        llm_client: Google Gemini client instance.
        model_name: Gemini model name (e.g., "gemini-2.5-flash").

    Returns:
        list[dict]: Deduplicated items in same format as input. On any error,
        returns original items unchanged.
    """
    # Edge cases: 0 or 1 items, skip dedup entirely
    if len(items) <= 1:
        return items

    try:
        # Step 1: Cluster
        clusters = cluster_items(items, llm_client, model_name)
        logger.info(f"Clustering produced {len(clusters)} clusters from {len(items)} items")

        # Step 2: Merge each cluster
        deduplicated = []
        for cluster in clusters:
            cluster_dicts = []
            for item_id in cluster:
                # Parse index from "item_N"
                try:
                    idx = int(item_id.split("_")[1])
                    if 0 <= idx < len(items):
                        cluster_dicts.append(items[idx])
                except (IndexError, ValueError):
                    logger.warning(f"Invalid item ID format: {item_id}")
                    continue

            if not cluster_dicts:
                continue
            elif len(cluster_dicts) == 1:
                # Singleton cluster: no merge needed
                deduplicated.append(cluster_dicts[0])
            else:
                # Multi-item cluster: merge
                logger.info(f"Merging cluster of {len(cluster_dicts)} items")
                merged = merge_cluster(cluster_dicts, llm_client, model_name)
                deduplicated.append(merged)

        # Safety: if dedup produced nothing (should not happen), return originals
        if not deduplicated:
            logger.warning("Deduplication produced empty result, returning originals")
            return items

        logger.info(f"Deduplication reduced {len(items)} items to {len(deduplicated)} items")
        return deduplicated

    except Exception as e:
        logger.warning(f"Deduplication failed: {e}, returning original items")
        return items


def cluster_items(
    items: list[dict],
    llm_client: genai.Client,
    model_name: str,
) -> list[list[str]]:
    """Send items to LLM and return clusters of duplicate item IDs.

    Assigns temporary IDs (item_0, item_1, ...) and sends headlines/summaries
    to the LLM with the clustering prompt.

    Args:
        items: List of item dicts.
        llm_client: Google Gemini client.
        model_name: Model to use.

    Returns:
        list[list[str]]: List of clusters, where each cluster is a list of
        temporary item IDs (e.g., [["item_0", "item_2"], ["item_1"]]).
        On LLM error, returns each item in its own singleton cluster.
    """
    # Build lightweight representations for clustering
    cluster_input = []
    for i, item in enumerate(items):
        item_id = f"item_{i}"
        text = item.get("title", "")
        if item.get("summary"):
            text += " - " + item["summary"]
        cluster_input.append({"id": item_id, "text": text})

    items_json = json.dumps(cluster_input, ensure_ascii=False)
    full_prompt = f"{_CLUSTER_PROMPT}\n\n**Items to Process:**\n{items_json}"

    try:
        response = llm_client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for deterministic clustering
                response_mime_type="application/json",
            ),
        )

        result = json.loads(response.text)
        clusters = result.get("clusters", [])

        # Validate: every cluster must be a list of strings
        validated = []
        for cluster in clusters:
            if isinstance(cluster, list) and all(isinstance(x, str) for x in cluster):
                validated.append(cluster)
            else:
                logger.warning(f"Skipping invalid cluster: {cluster}")

        # Verify all items are accounted for; if any are missing, add them as singletons
        all_ids = {f"item_{i}" for i in range(len(items))}
        seen_ids = {item_id for cluster in validated for item_id in cluster}
        missing = all_ids - seen_ids
        if missing:
            logger.info(f"Adding {len(missing)} missing items as singletons")
            for item_id in sorted(missing):
                validated.append([item_id])

        return validated

    except Exception as e:
        logger.warning(f"Clustering LLM call failed: {e}, treating all items as unique")
        return [[f"item_{i}"] for i in range(len(items))]


def merge_cluster(
    cluster_items: list[dict],
    llm_client: genai.Client,
    model_name: str,
) -> dict:
    """Merge multiple duplicate items into a single representative item.

    Sends the full item dicts from a cluster to the LLM and asks it to
    produce one merged version preserving the best information from each source.

    Args:
        cluster_items: List of 2+ item dicts that cover the same story.
        llm_client: Google Gemini client.
        model_name: Model to use.

    Returns:
        dict: Single merged item dict with keys: date, title, summary, link,
        source_type. On LLM error, returns the first item from the cluster.
    """
    items_json = json.dumps(cluster_items, indent=2, ensure_ascii=False)
    full_prompt = f"{_MERGE_PROMPT}\n\n**Items to Merge:**\n{items_json}"

    try:
        response = llm_client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.2,  # Slightly higher for text generation
                response_mime_type="application/json",
            ),
        )

        merged = json.loads(response.text)

        # Validate required keys exist
        if not isinstance(merged, dict) or "title" not in merged:
            logger.warning("Merge returned invalid structure, using first item")
            return cluster_items[0]

        # Ensure all expected keys present, fill from first item as fallback
        first = cluster_items[0]
        return {
            "date": merged.get("date") or first.get("date"),
            "title": merged.get("title", first.get("title", "")),
            "summary": merged.get("summary") or first.get("summary", ""),
            "link": merged.get("link") or first.get("link"),
            "source_type": merged.get("source_type") or first.get("source_type", "newsletter"),
        }

    except Exception as e:
        logger.warning(f"Merge LLM call failed: {e}, using first item from cluster")
        return cluster_items[0]
