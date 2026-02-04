"""LLM-based newsletter parser for newsletter aggregator."""

import base64
import json
import os
from typing import Optional
from urllib.parse import urlparse

import google.genai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def decode_tracking_url(url: str) -> str:
    """
    Decode email tracking redirect URLs to extract the real destination.

    Handles common tracking services like customeriomail.com that embed
    the real URL in base64-encoded JSON.

    Args:
        url: Tracking URL (e.g., from customeriomail.com)

    Returns:
        str: Real destination URL, or original URL if decoding fails
    """
    if not url:
        return url

    try:
        parsed = urlparse(url)

        # Handle customeriomail.com tracking URLs
        # Format: https://e.customeriomail.com/e/c/BASE64_JSON/hash
        if 'customeriomail.com' in parsed.netloc and '/e/c/' in parsed.path:
            # Extract base64 part (between /e/c/ and next /)
            path_parts = parsed.path.split('/e/c/')
            if len(path_parts) > 1:
                base64_part = path_parts[1].split('/')[0]

                # Decode using URL-safe base64 (handles - and _ characters)
                # Add padding if needed
                padding = len(base64_part) % 4
                if padding:
                    base64_part += '=' * (4 - padding)

                decoded_bytes = base64.urlsafe_b64decode(base64_part)
                decoded_str = decoded_bytes.decode('utf-8', errors='ignore')

                # Parse as JSON
                tracking_data = json.loads(decoded_str)

                # Extract href field
                if 'href' in tracking_data:
                    return tracking_data['href']

    except Exception:
        # If any decoding fails, return original URL
        pass

    return url


def create_llm_client(api_key: Optional[str] = None) -> genai.Client:
    """
    Create Gemini LLM client.

    Creates a client for making LLM API calls using Google's Gemini API.

    Args:
        api_key: Optional API key. If not provided, reads from GEMINI_API_KEY environment variable.

    Returns:
        GenerativeModel: Configured Gemini model instance

    Raises:
        ValueError: If API key is not provided and not found in environment
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key not found. "
            "Set GEMINI_API_KEY environment variable or pass api_key parameter."
        )

    # Create client with API key
    client = genai.Client(api_key=api_key)
    return client


def parse_newsletter(
    markdown_content: str, prompt: str, llm_client: genai.Client, model_name: str
) -> list[dict]:
    """
    Parse newsletter markdown using LLM with configurable prompt.

    Calls LLM API with the provided prompt and markdown content to extract
    structured newsletter items (articles, links, summaries, etc.).

    Args:
        markdown_content: Markdown text of newsletter
        prompt: Prompt template for LLM (includes instructions for extraction)
        llm_client: LLM API client (Gemini Client)
        model_name: Gemini model to use (e.g., "gemini-2.5-flash")

    Returns:
        list[dict]: List of parsed items, each with keys: `date`, `title`, `summary`, `link` (link optional)

    Side Effects:
        - Makes LLM API call
        - May raise API errors if LLM call fails

    Raises:
        ValueError: If markdown_content or prompt is empty
        Exception: If LLM API call fails or returns invalid JSON

    Postconditions:
        - Returns list (may be empty if no items found, or multiple if newsletter has multiple articles)
        - Each item has at least `title` field
        - `date`, `summary`, `link` may be None/empty if not found
    """
    if not markdown_content or not markdown_content.strip():
        raise ValueError("markdown_content must be non-empty")

    if not prompt or not prompt.strip():
        raise ValueError("prompt must be non-empty")

    # Build the full prompt with content
    # Request JSON object with "items" array
    system_instruction = "You are a helpful assistant that extracts structured information from newsletters. Always return valid JSON with an 'items' array."
    full_prompt = f"{prompt}\n\nNewsletter content:\n\n{markdown_content}\n\nReturn a JSON object with an 'items' array. Each item should have: date, title, summary, link (optional)."

    try:
        # Call Gemini API using the new google.genai package
        response = llm_client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
                system_instruction=system_instruction,
            ),
        )

        # Extract response content
        if not hasattr(response, 'text') or not response.text:
            raise ValueError("LLM returned empty or invalid response. Check API key and model availability.")
        
        content = response.text

        # Parse JSON response
        # Gemini JSON mode returns a JSON object, we expect {"items": [...]}
        try:
            parsed = json.loads(content)
            
            # Extract items array from response
            if isinstance(parsed, dict):
                # Look for items array in common keys
                if "items" in parsed:
                    items = parsed["items"]
                elif "articles" in parsed:
                    items = parsed["articles"]
                elif len(parsed) == 1:
                    # Single key, use its value if it's a list
                    value = list(parsed.values())[0]
                    if isinstance(value, list):
                        items = value
                    else:
                        raise ValueError("Expected items array in JSON response")
                else:
                    # Try to find array value
                    items = next(
                        (v for v in parsed.values() if isinstance(v, list)), None
                    )
                    if items is None:
                        raise ValueError("Could not find items array in LLM response")
            elif isinstance(parsed, list):
                # Direct array (fallback for non-JSON mode responses)
                items = parsed
            else:
                raise ValueError(f"Unexpected response type: {type(parsed)}")

            # Ensure items is a list
            if not isinstance(items, list):
                raise ValueError(f"Expected list, got {type(items)}")

            # Validate and clean items
            validated_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                # Ensure title exists (required field)
                if "title" not in item or not item["title"]:
                    continue

                # Get link and decode if it's a tracking URL
                raw_link = item.get("link")
                decoded_link = decode_tracking_url(raw_link) if raw_link else None

                # Build validated item with required and optional fields
                validated_item = {
                    "title": str(item.get("title", "")).strip(),
                    "date": item.get("date") if item.get("date") else None,
                    "summary": item.get("summary") if item.get("summary") else None,
                    "link": decoded_link if decoded_link else None,
                }

                validated_items.append(validated_item)

            return validated_items

        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}") from e

    except ValueError:
        # Re-raise ValueError as-is
        raise
    except Exception as e:
        # Wrap other exceptions
        raise ValueError(f"Failed to parse newsletter with LLM: {str(e)}") from e
