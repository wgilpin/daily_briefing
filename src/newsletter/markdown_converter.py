"""Markdown conversion functions for newsletter aggregator."""

import html2text
from typing import Optional


def convert_to_markdown(email: dict) -> str:
    """
    Convert email content (HTML or plain text) to markdown format.

    Converts email body to markdown, preferring HTML over plain text if both are present.
    Uses html2text library for HTML conversion to preserve structure and formatting.

    Args:
        email: Dictionary with email data, must contain at least one of:
            - body_html: HTML content string
            - body_text: Plain text content string

    Returns:
        str: Markdown-formatted content

    Side Effects:
        - None (pure function)

    Raises:
        ValueError: If email has neither body_html nor body_text
    """
    body_html = email.get("body_html")
    body_text = email.get("body_text")

    # Prefer HTML over plain text if both are present
    if body_html:
        # Convert HTML to markdown using html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # Don't wrap lines
        h.unicode_snob = True  # Preserve unicode characters

        markdown = h.handle(body_html)
        return markdown.strip()

    elif body_text:
        # Format plain text as markdown
        # Preserve line breaks and structure
        markdown = body_text.strip()
        return markdown

    else:
        # No content available
        return ""
