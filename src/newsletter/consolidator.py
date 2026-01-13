"""Newsletter consolidation functions for newsletter aggregator."""

import json

import google.genai as genai


def consolidate_newsletters(
    parsed_items: list[dict], prompt: str, llm_client: genai.Client, model_name: str
) -> str:
    """
    Generate consolidated newsletter from parsed items using LLM.

    Calls LLM API with the provided prompt and parsed items to generate
    a consolidated newsletter in markdown format.

    Args:
        parsed_items: List of parsed newsletter items (from multiple sources)
        prompt: Consolidation prompt template
        llm_client: LLM API client (Gemini Client)
        model_name: Gemini model to use (e.g., "gemini-2.5-flash")

    Returns:
        str: Consolidated newsletter in markdown format

    Side Effects:
        - Makes LLM API call
        - May raise API errors if LLM call fails

    Raises:
        ValueError: If prompt is empty
        Exception: If LLM API call fails

    Postconditions:
        - Returns markdown string suitable for reading
        - Content is well-formatted with headings and sections
        - All items from input are represented in output (or fallback format if LLM fails)
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be non-empty")

    # If no items, return empty newsletter
    if not parsed_items:
        return "# Newsletter\n\nNo items to consolidate."

    # Format items as JSON for LLM
    items_json = json.dumps(parsed_items, indent=2, ensure_ascii=False)

    # Build the full prompt with items
    full_prompt = f"{prompt}\n\nItems to consolidate:\n\n{items_json}\n\nGenerate a well-formatted markdown newsletter that consolidates all these items."

    try:
        # Call Gemini API using the new google.genai package
        system_instruction = "You are a helpful assistant that creates well-formatted newsletter digests. Always return valid markdown with clear headings and sections."
        
        response = llm_client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.7,  # Slightly higher for more creative consolidation
                system_instruction=system_instruction,
            ),
        )

        # Extract response content
        content = response.text

        # Validate that we got markdown content
        if not content or not content.strip():
            # Fallback: return structured list format
            return _generate_fallback_digest(parsed_items)

        return content

    except Exception as e:
        # On error, return fallback format with raw structured lists
        # This provides partial data as per edge case spec (FR-014, FR-015)
        return _generate_fallback_digest(parsed_items)


def _generate_fallback_digest(parsed_items: list[dict]) -> str:
    """
    Generate fallback digest format when LLM fails.

    Creates a simple markdown format with structured lists of items.
    This ensures users always get some output even if LLM fails.

    Args:
        parsed_items: List of parsed newsletter items

    Returns:
        str: Fallback markdown digest
    """
    lines = ["# Newsletter Digest\n"]
    lines.append(f"*Generated from {len(parsed_items)} items*\n\n")

    for i, item in enumerate(parsed_items, 1):
        lines.append(f"## {i}. {item.get('title', 'Untitled')}\n")
        
        if item.get("date"):
            lines.append(f"**Date:** {item['date']}\n")
        
        if item.get("summary"):
            lines.append(f"{item['summary']}\n")
        
        if item.get("link"):
            lines.append(f"[Read more]({item['link']})\n")
        
        lines.append("\n")

    return "".join(lines)
