"""Parse newsletter markdown files for text-to-speech conversion."""

import re
from pathlib import Path

from src.models.audio_models import NewsletterItem


def strip_markdown_formatting(text: str) -> str:
    """
    Remove markdown formatting from text for clean TTS.

    Removes:
    - Bold: **text** or __text__
    - Italic: *text* or _text_
    - Code: `text`
    - Links: [text](url) -> text

    Args:
        text: Text with markdown formatting

    Returns:
        Clean text without markdown formatting
    """
    # Remove bold (** or __)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Remove italic (* or _) - but be careful not to match bold
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'\1', text)

    # Remove inline code
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    return text


def parse_newsletter_items(markdown_path: Path | str) -> list[NewsletterItem]:
    """
    Parse newsletter markdown file and extract items for TTS conversion.

    Supports two formats:
    1. ### Title headers with content below
    2. **Bold Title** paragraphs with content below

    Args:
        markdown_path: Path to markdown file or markdown content string

    Returns:
        List of NewsletterItem objects with title and content
    """
    # Handle both Path and string inputs
    if isinstance(markdown_path, Path):
        content = markdown_path.read_text(encoding="utf-8")
    else:
        content = markdown_path

    items = []
    item_number = 0

    # Split by ### headers (category or article titles)
    sections = content.split("\n###")

    for section in sections[1:]:  # Skip first section before first ###
        lines = section.strip().split("\n")
        if not lines or not lines[0].strip():
            continue

        section_title = lines[0].strip()

        # Check if this section contains **Bold** article titles
        # (new format where ### is a category and ** marks article titles)
        bold_pattern = re.compile(r'^\*\*(.+?)\*\*\s*$')
        link_pattern = re.compile(r'\[Read More\]\(([^\)]+)\)')
        current_item_title = None
        current_item_lines = []
        current_item_link = None

        for line in lines[1:]:
            stripped = line.strip()

            # Extract link if present (for cache stability)
            link_match = link_pattern.search(stripped)
            if link_match:
                current_item_link = link_match.group(1)
                continue  # Skip this line

            # Skip empty lines, metadata, separators
            if not stripped or stripped.startswith("*Date:"):
                continue
            if stripped == "---" or stripped.startswith("##"):
                continue

            # Check if this line is a bold title (new article starts)
            bold_match = bold_pattern.match(stripped)
            if bold_match:
                # Save previous item if exists
                if current_item_title and current_item_lines:
                    content_text = "\n".join(current_item_lines).strip()
                    if content_text:
                        clean_content = strip_markdown_formatting(content_text)
                        clean_title = strip_markdown_formatting(current_item_title)
                        item_number += 1
                        items.append(
                            NewsletterItem(
                                title=clean_title,
                                content=clean_content,
                                item_number=item_number,
                                link=current_item_link,
                            )
                        )

                # Start new item
                current_item_title = bold_match.group(1)
                current_item_lines = []
                current_item_link = None
            else:
                # Add content to current item
                current_item_lines.append(line)

        # Save the last item in this section
        if current_item_title and current_item_lines:
            content_text = "\n".join(current_item_lines).strip()
            if content_text:
                clean_content = strip_markdown_formatting(content_text)
                clean_title = strip_markdown_formatting(current_item_title)
                item_number += 1
                items.append(
                    NewsletterItem(
                        title=clean_title,
                        content=clean_content,
                        item_number=item_number,
                        link=current_item_link,
                    )
                )

        # If no bold titles found, treat the whole section as one item (old format)
        if not any(bold_pattern.match(line.strip()) for line in lines[1:]):
            content_lines = []
            item_link = None
            for line in lines[1:]:
                stripped = line.strip()

                # Extract link if present
                link_match = link_pattern.search(stripped)
                if link_match:
                    item_link = link_match.group(1)
                    continue

                if stripped.startswith("*Date:"):
                    continue
                if stripped == "---" or stripped.startswith("##"):
                    continue
                content_lines.append(line)

            content_text = "\n".join(content_lines).strip()
            if content_text:
                clean_content = strip_markdown_formatting(content_text)
                clean_title = strip_markdown_formatting(section_title)
                item_number += 1
                items.append(
                    NewsletterItem(
                        title=clean_title,
                        content=clean_content,
                        item_number=item_number,
                        link=item_link,
                    )
                )

    return items
