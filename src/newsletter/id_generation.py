"""Stable ID generation for newsletter items using SHA-256.

This module provides deterministic, collision-resistant ID generation
for newsletter items. IDs remain stable across application restarts.
"""

import hashlib
import unicodedata
from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for consistent hashing.

    Performs the following transformations:
    1. Handles None/empty by returning empty string
    2. Strips leading/trailing whitespace
    3. Converts to lowercase
    4. Normalizes Unicode to NFC (canonical composition)
    5. Collapses multiple spaces to single space

    Args:
        text: Input text (may be None or empty)

    Returns:
        Normalized text (empty string if None/empty)

    Examples:
        >>> normalize_text("  AI News  ")
        'ai news'
        >>> normalize_text("Breaking  News")
        'breaking news'
        >>> normalize_text(None)
        ''
    """
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()
    if not text:
        return ""

    # Lowercase for case-insensitive matching
    text = text.lower()

    # Normalize Unicode characters (NFC)
    # This ensures "ř" is always represented the same way
    text = unicodedata.normalize('NFC', text)

    # Collapse multiple spaces to single space
    text = ' '.join(text.split())

    return text


def generate_newsletter_id(title: str, date: str) -> str:
    """Generate stable, deterministic ID for newsletter item.

    Uses SHA-256 hashing with input normalization to ensure:
    - Same content always generates same ID
    - IDs stable across application restarts
    - Collision probability ~0 for practical scale (1000s of items)
    - Human-readable hex format for debugging

    Format: "newsletter:{16-char-hash}"

    NOTE: This function does not validate inputs. Empty title/date will
    generate valid IDs. Validation should happen at Pydantic model layer.

    Args:
        title: Newsletter item title (should not be empty)
        date: Publication date string (may be empty)

    Returns:
        Stable ID in format "newsletter:{16-char-hash}"

    Examples:
        >>> generate_newsletter_id("AI News", "2026-02-04")
        'newsletter:a1b2c3d4e5f6g7h8'
        >>> generate_newsletter_id("  AI News  ", "2026-02-04")
        'newsletter:a1b2c3d4e5f6g7h8'  # Same as above (normalized)
        >>> generate_newsletter_id("AI News", "")
        'newsletter:x1y2z3a4b5c6d7e8'
    """
    # Normalize both inputs for consistent hashing
    norm_title = normalize_text(title)
    norm_date = normalize_text(date)

    # Combine with colon separator (matches current implementation format)
    hash_input = f"{norm_title}:{norm_date}"

    # Generate SHA-256 hash with UTF-8 encoding
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8'))
    hash_hex = hash_bytes.hexdigest()  # 64-character hex string

    # Truncate to 16 characters (64 bits of entropy)
    # Provides 2^64 collision space (sufficient for billions of items)
    hash_truncated = hash_hex[:16]

    return f"newsletter:{hash_truncated}"
