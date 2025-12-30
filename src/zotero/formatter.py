"""Markdown formatting functions for Zotero items."""

import os
import re
from datetime import datetime

from src.zotero.types import Creator, ZoteroItem


def escape_markdown(text: str) -> str:
    """
    Escape special markdown characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for markdown
    """
    if not text:
        return ""
    
    # Escape markdown special characters
    # Note: We don't escape # in headers since we control those
    # But we do escape them in regular text
    special_chars = ["#", "*", "_", "[", "]", "(", ")", "`", "!", "\\"]
    escaped = text
    for char in special_chars:
        escaped = escaped.replace(char, "\\" + char)
    
    return escaped


def format_authors(creators: list[Creator]) -> str:
    """
    Format creators as "LastName, FirstName" comma-separated list.
    
    Args:
        creators: List of creator dictionaries from Zotero
        
    Returns:
        Formatted author string, or "N/A" if no authors
    """
    authors = []
    for creator in creators:
        if creator.get("creatorType") != "author":
            continue
        
        last_name = creator.get("lastName", "").strip()
        first_name = creator.get("firstName", "").strip()
        
        if last_name and first_name:
            authors.append(f"{last_name}, {first_name}")
        elif last_name:
            authors.append(last_name)
        elif first_name:
            authors.append(first_name)
    
    if not authors:
        return "N/A"
    
    return ", ".join(authors)


def format_item_markdown(item: ZoteroItem) -> str:
    """
    Convert a Zotero item to markdown format.
    
    Args:
        item: Zotero API item dictionary
        
    Returns:
        Markdown-formatted string for the item
    """
    data = item.get("data", {})
    title = data.get("title", "Untitled")
    
    # Escape title for markdown (but keep ### header)
    escaped_title = escape_markdown(title)
    
    # Build markdown
    lines = [f"### {escaped_title}", ""]
    
    # Authors
    creators = data.get("creators", [])
    authors = format_authors(creators)
    lines.append(f"**Authors**: {authors}")
    lines.append("")
    
    # Publication date
    date = data.get("date", "")
    if date:
        lines.append(f"**Published**: {date}")
        lines.append("")
    
    # Venue (publication title)
    venue = data.get("publicationTitle", "")
    if venue:
        escaped_venue = escape_markdown(venue)
        lines.append(f"**Venue**: {escaped_venue}")
        lines.append("")
    
    # Abstract
    abstract = data.get("abstractNote", "")
    if abstract:
        escaped_abstract = escape_markdown(abstract)
        lines.append(f"**Abstract**: {escaped_abstract}")
        lines.append("")
    
    # URL
    url = data.get("url", "")
    if url:
        lines.append(f"**URL**: [{url}]({url})")
        lines.append("")
    
    return "\n".join(lines)


def generate_digest(items: list[ZoteroItem], days: int) -> str:
    """
    Generate complete markdown digest from items.
    
    Args:
        items: List of Zotero item dictionaries (already filtered/sorted)
        days: Time window used for filtering
        
    Returns:
        Complete markdown document
    """
    # Header
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    lines = [
        f"# Zotero Digest - {date_str}",
        "",
        f"Generated: {date_str} {time_str}",
        f"Time Range: Last {days} day(s)",
        f"Items Found: {len(items)}",
        "",
    ]
    
    # If no items, return message
    if not items:
        lines.append(f"No items found in the last {days} day(s).")
        return "\n".join(lines)
    
    # Group items by itemType
    items_by_type = {}
    for item in items:
        item_type = item.get("data", {}).get("itemType", "unknown")
        if item_type not in items_by_type:
            items_by_type[item_type] = []
        items_by_type[item_type].append(item)
    
    # Format each type section
    for item_type, type_items in sorted(items_by_type.items()):
        # Section header
        # Convert camelCase to Title Case for display
        # Insert space before capital letters and title case
        type_display = re.sub(r"([a-z])([A-Z])", r"\1 \2", item_type)
        type_display = type_display.replace("_", " ").title()
        lines.append(f"## {type_display}")
        lines.append("")
        
        # Format each item
        for item in type_items:
            item_markdown = format_item_markdown(item)
            lines.append(item_markdown)
            lines.append("")  # Extra blank line between items
    
    return "\n".join(lines)


def write_digest(content: str, output_path: str) -> None:
    """
    Write digest content to markdown file.
    
    Args:
        content: Markdown content to write
        output_path: File path (may include directory)
        
    Raises:
        IOError: If file cannot be written
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Failed to write digest file: {e}") from e

