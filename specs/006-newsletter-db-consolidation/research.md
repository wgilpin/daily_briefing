# Research: SHA-256 Based ID Generation Best Practices

**Feature**: Newsletter Database Consolidation
**Branch**: `006-newsletter-db-consolidation`
**Date**: 2026-02-04
**Context**: Replace non-deterministic Python `hash()` with SHA-256 for stable newsletter item IDs

## Executive Summary

**Recommendation**: Use SHA-256 with UTF-8 encoding and hexdigest() truncated to 16 characters for PostgreSQL VARCHAR primary keys.

**Key Findings**:
- SHA-256 hexdigest is deterministic across all platforms and Python versions
- Full 64-character hex output is excessive for ~1000 items
- 16-character truncation provides 2^64 collision space (sufficient for millions of items)
- UTF-8 encoding with Unicode normalization ensures consistent hashing
- Input normalization (lowercase, whitespace stripping) prevents duplicate IDs from formatting differences
- PostgreSQL VARCHAR is acceptable for primary keys when using short, fixed-length hashes

## Research Questions Answered

### 1. How to properly use hashlib.sha256 for deterministic hashing?

**Answer**: Use `hashlib.sha256(input_bytes).hexdigest()` for deterministic, platform-independent hashing.

**Code Pattern**:
```python
import hashlib

def generate_stable_hash(input_string: str) -> str:
    """Generate deterministic SHA-256 hash from input string.

    Args:
        input_string: String to hash

    Returns:
        Hex digest of SHA-256 hash
    """
    hash_bytes = hashlib.sha256(input_string.encode('utf-8'))
    return hash_bytes.hexdigest()  # Returns 64-character hex string
```

**Why hexdigest()**:
- Returns lowercase hex string (always 64 characters for SHA-256)
- Human-readable and PostgreSQL-compatible
- No binary escaping issues
- Consistent across all platforms and Python versions

**Alternative - digest()**:
- Returns raw 32 bytes (bytea in PostgreSQL)
- More storage-efficient (32 bytes vs 64 characters)
- Not recommended for this use case due to reduced readability and debugging difficulty

**Source**: [Python hashlib documentation](https://docs.python.org/3/library/hashlib.html)

---

### 2. What encoding should be used for the input string (UTF-8)?

**Answer**: UTF-8 with Unicode normalization (NFC) for international character consistency.

**Code Pattern**:
```python
import hashlib
import unicodedata

def normalize_and_encode(text: str) -> bytes:
    """Normalize Unicode and encode to UTF-8 for consistent hashing.

    Args:
        text: Input text that may contain international characters

    Returns:
        UTF-8 encoded bytes ready for hashing
    """
    # Normalize Unicode to canonical composition form (NFC)
    normalized = unicodedata.normalize('NFC', text)
    return normalized.encode('utf-8')

# Usage
input_text = "Résumé"  # Contains accented character
hash_input = normalize_and_encode(input_text)
hash_value = hashlib.sha256(hash_input).hexdigest()
```

**Why UTF-8**:
- Universal standard for text encoding
- Compatible with all systems and platforms
- Handles international characters correctly
- PostgreSQL default encoding

**Why Unicode Normalization**:
- "ř" can be represented as single character (U+0159) OR "r" + combining caron (U+0072 + U+030C)
- Without normalization, these produce different hashes despite appearing identical
- NFC (Canonical Composition) is the standard form for text storage

**Source**: [Handling Encoding Issues With Unicode Normalisation In Python](https://xebia.com/blog/handling-encoding-issues-with-unicode-normalisation-in-python/)

---

### 3. Should we use hexdigest() or other output format?

**Answer**: Use `hexdigest()` for VARCHAR primary keys. Use `digest()` only if choosing BYTEA type.

**Comparison**:

| Format | Size | PostgreSQL Type | Pros | Cons |
|--------|------|-----------------|------|------|
| hexdigest() | 64 chars | VARCHAR(64) | Human-readable, debuggable, URL-safe | Larger storage (64 bytes) |
| digest() | 32 bytes | BYTEA | Storage efficient (32 bytes) | Binary data, harder to debug |

**Recommendation for this project**: `hexdigest()` with VARCHAR

**Reasons**:
1. Newsletter IDs appear in URLs and web interface
2. Debugging is easier with readable IDs
3. Storage difference is negligible (~1000 items = 32KB difference)
4. Consistent with existing `FeedItem.id` string type

**Source**: [PostgreSQL pgcrypto — Secure Data Without Leaving SQL](https://medium.com/@nishith.explorer/postgresql-pgcrypto-secure-data-without-leaving-sql-22eac1ae1251)

---

### 4. How long should the final ID string be (full hash vs truncated)?

**Answer**: Truncate to 16 characters (64 bits) for format `newsletter:{16-char-hash}`.

**Collision Probability Analysis**:

| Hash Length | Bits | 50% Collision Probability | Suitable For |
|-------------|------|---------------------------|--------------|
| 8 chars | 32 bits | ~77,000 items | Too small |
| 12 chars | 48 bits | ~16 million items | Small scale |
| 16 chars | 64 bits | ~4.3 billion items | Recommended |
| 20 chars | 80 bits | ~1.2 × 10^12 items | Overkill |
| 64 chars (full) | 256 bits | Astronomically high | Excessive |

**Code Pattern**:
```python
def generate_newsletter_id(title: str, date: str) -> str:
    """Generate stable newsletter item ID using SHA-256.

    Args:
        title: Newsletter item title
        date: Publication date string

    Returns:
        ID in format "newsletter:{16-char-hash}"

    Example:
        >>> generate_newsletter_id("AI News", "2026-02-04")
        'newsletter:a1b2c3d4e5f6g7h8'
    """
    # Normalize input (see question 6)
    normalized_input = f"{title.strip().lower()}:{date.strip()}"

    # Generate hash
    hash_bytes = hashlib.sha256(normalized_input.encode('utf-8'))
    hash_hex = hash_bytes.hexdigest()

    # Truncate to 16 characters (64 bits)
    hash_truncated = hash_hex[:16]

    return f"newsletter:{hash_truncated}"
```

**Why 16 characters**:
- Provides 2^64 = 18 quintillion possible values
- 50% collision probability at ~4.3 billion items (far beyond project scale)
- Balances ID length with collision safety
- Total ID length: `newsletter:` (11) + hash (16) = 27 characters

**Birthday Paradox Formula**:
```
P(collision) ≈ 1 - e^(-n²/2m)
where n = number of items, m = hash space size (2^64)

For 1000 items:
P ≈ 1 - e^(-(1000²)/(2×2^64)) ≈ 2.7 × 10^-14 (0.0000000000027%)
```

**Source**: [Hash Collision Probabilities](https://preshing.com/20110504/hash-collision-probabilities/)

---

### 5. What's the collision probability with SHA-256 for ~1000 newsletter items?

**Answer**: Effectively zero (2.7 × 10^-14 or 0.0000000000027%) even with 16-character truncation.

**Detailed Analysis**:

**Full SHA-256 (256 bits)**:
- Hash space: 2^256 ≈ 1.15 × 10^77
- For 1000 items: P(collision) ≈ 4.3 × 10^-72
- **Result**: Astronomically unlikely

**Truncated to 16 chars (64 bits)**:
- Hash space: 2^64 ≈ 1.84 × 10^19
- For 1000 items: P(collision) ≈ 2.7 × 10^-14
- For 1 million items: P(collision) ≈ 2.7 × 10^-8 (0.0000027%)
- **Result**: Negligible for practical purposes

**Truncated to 12 chars (48 bits)**:
- Hash space: 2^48 ≈ 2.81 × 10^14
- For 1000 items: P(collision) ≈ 1.8 × 10^-9
- For 100,000 items: P(collision) ≈ 0.018% (starts becoming non-negligible)
- **Result**: Adequate but less safe margin

**Recommendation**: 16 characters provides excellent safety margin with reasonable ID length.

**Real-world comparison**:
- Git uses 40-character SHA-1 hashes (160 bits) for repository with millions of commits
- UUIDs provide 122 bits of randomness
- Our 64-bit hash is comparable to UUID variant 4

**Source**: [SHA-2 - Wikipedia](https://en.wikipedia.org/wiki/SHA-2), [Birthday attack probability](https://www.johndcook.com/blog/2017/01/10/probability-of-secure-hash-collisions/)

---

### 6. Should we include normalization (lowercase, strip whitespace) in the input?

**Answer**: YES - Always normalize input before hashing to prevent duplicates from formatting variations.

**Code Pattern**:
```python
import hashlib
import unicodedata
from typing import Optional

def normalize_text(text: Optional[str]) -> str:
    """Normalize text for consistent hashing.

    Args:
        text: Input text (may be None or empty)

    Returns:
        Normalized text (empty string if None/empty)
    """
    if not text:
        return ""

    # 1. Strip leading/trailing whitespace
    text = text.strip()

    # 2. Convert to lowercase
    text = text.lower()

    # 3. Normalize Unicode characters (NFC)
    text = unicodedata.normalize('NFC', text)

    # 4. Collapse multiple spaces to single space
    text = ' '.join(text.split())

    return text

def generate_newsletter_id(title: str, date: str) -> str:
    """Generate stable newsletter item ID with input normalization.

    Args:
        title: Newsletter item title
        date: Publication date string

    Returns:
        ID in format "newsletter:{16-char-hash}"
    """
    # Normalize both inputs
    norm_title = normalize_text(title)
    norm_date = normalize_text(date)

    # Combine with colon separator (matching current implementation)
    hash_input = f"{norm_title}:{norm_date}"

    # Generate and truncate hash
    hash_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    return f"newsletter:{hash_hex[:16]}"
```

**Why normalization is critical**:

Without normalization, these would generate DIFFERENT IDs:
```python
# Same semantic content, different hashes
hash("Breaking News")          # Different
hash("breaking news")          # Different
hash("  Breaking News  ")      # Different
hash("Breaking  News")         # Different (double space)
```

With normalization, these generate IDENTICAL IDs:
```python
# All normalize to "breaking news" -> same hash
normalize("Breaking News")      # "breaking news"
normalize("  Breaking News  ")  # "breaking news"
normalize("BREAKING NEWS")      # "breaking news"
```

**Normalization steps explained**:
1. **Strip whitespace**: Remove accidental spaces from copy-paste or parsing
2. **Lowercase**: "AI News" = "ai news" (case-insensitive matching)
3. **Unicode NFC**: "résumé" always uses same character representation
4. **Collapse spaces**: "Breaking  News" = "Breaking News" (handles HTML/markdown spacing)

**Trade-offs**:
- **Pro**: Prevents duplicate items from formatting variations
- **Pro**: Makes deduplication more reliable
- **Con**: "AI News" and "ai news" are treated as identical (acceptable for newsletters)
- **Con**: Slight performance overhead (negligible for ~1000 items)

**Source**: [Deterministic hashing of Python data objects](https://death.andgravity.com/stable-hashing)

---

### 7. How to handle empty/None values in title or date fields?

**Answer**: Treat empty/None as empty string, but VALIDATE at business logic layer to prevent invalid IDs.

**Code Pattern**:
```python
import hashlib
import unicodedata
from typing import Optional
from pydantic import BaseModel, Field, field_validator

def normalize_text(text: Optional[str]) -> str:
    """Normalize text for hashing, treating None/empty as empty string.

    Args:
        text: Input text (may be None or empty)

    Returns:
        Normalized text (empty string if None/empty)
    """
    if not text:
        return ""

    text = text.strip()
    if not text:
        return ""

    text = text.lower()
    text = unicodedata.normalize('NFC', text)
    text = ' '.join(text.split())

    return text

def generate_newsletter_id(title: str, date: str) -> str:
    """Generate stable newsletter item ID.

    NOTE: This function DOES NOT validate inputs. Empty title/date will
    generate IDs like "newsletter:abc123..." from hash(":")

    Validation should happen at the Pydantic model layer.

    Args:
        title: Newsletter item title (should not be empty)
        date: Publication date string (may be empty for current date)

    Returns:
        ID in format "newsletter:{16-char-hash}"
    """
    norm_title = normalize_text(title)
    norm_date = normalize_text(date)

    hash_input = f"{norm_title}:{norm_date}"
    hash_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    return f"newsletter:{hash_hex[:16]}"

# Business logic validation at Pydantic layer
class NewsletterItemInput(BaseModel):
    """Input model for newsletter item with validation."""

    title: str = Field(min_length=1, description="Item title (required)")
    date: str = Field(default="", description="Publication date (optional)")
    summary: Optional[str] = None
    link: Optional[str] = None
    sender: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that title is not empty or whitespace."""
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v

# Usage in existing code (src/sources/newsletter.py)
def _to_feed_item(
    self, newsletter_item: dict[str, Any], index: int
) -> Optional[FeedItem]:
    """Convert newsletter item to FeedItem.

    Args:
        newsletter_item: Raw newsletter item dictionary
        index: Item index (unused with SHA-256 approach)

    Returns:
        FeedItem with stable ID, or None if title is empty
    """
    # Extract and validate title (existing pattern)
    title = newsletter_item.get("title", "").strip()
    if not title:
        return None  # Skip items without title

    # Extract date (may be empty string)
    date_str = newsletter_item.get("date", "")

    # Generate stable ID using SHA-256
    item_id = generate_newsletter_id(title, date_str)

    # Parse date for FeedItem model
    date = self._parse_date(date_str)

    # ... rest of conversion
```

**Edge Cases Handling**:

| Input | Normalized | Hash Input | Result |
|-------|-----------|------------|--------|
| title="", date="" | "", "" | ":" | Valid ID, but should be rejected by validation |
| title="AI News", date="" | "ai news", "" | "ai news:" | Valid ID (date defaults to empty) |
| title="  ", date="2026-02-04" | "", "2026-02-04" | ":2026-02-04" | Should be rejected (empty title) |
| title=None, date=None | "", "" | ":" | Should be rejected at validation layer |
| title="AI News", date=None | "ai news", "" | "ai news:" | Valid ID |

**Design Decision**:
- **Hash function**: Permissive (accepts any input, even empty)
- **Validation**: Strict at Pydantic model layer (rejects empty titles)
- **Rationale**: Separation of concerns - hash generation is pure function, validation is business logic

**Existing validation in `FeedItem` model**:
```python
# From src/models/feed_item.py
@field_validator("title")
@classmethod
def title_not_empty(cls, v: str) -> str:
    """Validate that title is not empty or whitespace."""
    if not v.strip():
        raise ValueError("title cannot be empty or whitespace")
    return v
```

This existing validation ALREADY prevents empty titles from reaching the database.

**Source**: [Python TypeError: Strings must be encoded before hashing](https://bobbyhadz.com/blog/python-typeerror-strings-must-be-encoded-before-hashing)

---

## Production-Ready Implementation

### Complete Type-Safe Implementation

```python
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


# Integration example for src/sources/newsletter.py
def _to_feed_item_example(
    newsletter_item: dict, index: int
) -> Optional[object]:  # FeedItem
    """Example integration with existing code.

    This shows how to replace the current hash() implementation.
    """
    # Extract title (required) - EXISTING CODE
    title = newsletter_item.get("title", "").strip()
    if not title:
        return None

    # Extract date - EXISTING CODE
    date_str = newsletter_item.get("date", "")

    # REPLACE THIS (non-deterministic):
    # item_hash = hash(f"{title}:{date_str}")
    # item_id = f"newsletter:{abs(item_hash)}"

    # WITH THIS (deterministic SHA-256):
    item_id = generate_newsletter_id(title, date_str)
    source_id = item_id.split(":", 1)[1]  # Extract hash portion for source_id

    # ... rest of existing conversion code
    return {"id": item_id, "source_id": source_id}
```

### Unit Tests

```python
"""Tests for newsletter ID generation."""

import pytest
from src.newsletter.id_generation import (
    normalize_text,
    generate_newsletter_id,
)


class TestNormalizeText:
    """Test text normalization for hashing."""

    def test_strips_whitespace(self):
        """Should strip leading and trailing whitespace."""
        assert normalize_text("  AI News  ") == "ai news"

    def test_converts_to_lowercase(self):
        """Should convert to lowercase."""
        assert normalize_text("Breaking NEWS") == "breaking news"

    def test_collapses_spaces(self):
        """Should collapse multiple spaces to single space."""
        assert normalize_text("AI  News") == "ai news"
        assert normalize_text("AI   News") == "ai news"

    def test_handles_none(self):
        """Should return empty string for None."""
        assert normalize_text(None) == ""

    def test_handles_empty_string(self):
        """Should return empty string for empty input."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_normalizes_unicode(self):
        """Should normalize Unicode to NFC form."""
        # These should produce the same normalized result
        # (though actual bytes may differ before normalization)
        text1 = "résumé"  # Using precomposed characters
        text2 = "résumé"  # Could be decomposed form
        assert normalize_text(text1) == normalize_text(text2)


class TestGenerateNewsletterID:
    """Test newsletter ID generation."""

    def test_generates_consistent_id(self):
        """Should generate same ID for same input."""
        id1 = generate_newsletter_id("AI News", "2026-02-04")
        id2 = generate_newsletter_id("AI News", "2026-02-04")
        assert id1 == id2

    def test_format_is_correct(self):
        """Should generate ID in correct format."""
        item_id = generate_newsletter_id("AI News", "2026-02-04")
        assert item_id.startswith("newsletter:")
        hash_part = item_id.split(":", 1)[1]
        assert len(hash_part) == 16
        assert all(c in "0123456789abcdef" for c in hash_part)

    def test_normalized_inputs_produce_same_id(self):
        """Should generate same ID for semantically identical inputs."""
        id1 = generate_newsletter_id("AI News", "2026-02-04")
        id2 = generate_newsletter_id("  AI News  ", "2026-02-04")
        id3 = generate_newsletter_id("ai news", "2026-02-04")
        id4 = generate_newsletter_id("AI  News", "2026-02-04")  # Double space

        assert id1 == id2 == id3 == id4

    def test_different_titles_produce_different_ids(self):
        """Should generate different IDs for different titles."""
        id1 = generate_newsletter_id("AI News", "2026-02-04")
        id2 = generate_newsletter_id("Tech Update", "2026-02-04")
        assert id1 != id2

    def test_different_dates_produce_different_ids(self):
        """Should generate different IDs for different dates."""
        id1 = generate_newsletter_id("AI News", "2026-02-04")
        id2 = generate_newsletter_id("AI News", "2026-02-05")
        assert id1 != id2

    def test_handles_empty_date(self):
        """Should handle empty date gracefully."""
        id1 = generate_newsletter_id("AI News", "")
        id2 = generate_newsletter_id("AI News", "")
        assert id1 == id2
        assert id1.startswith("newsletter:")

    def test_stability_across_runs(self):
        """Should generate identical IDs across multiple runs (determinism test)."""
        # This tests that hash is deterministic (not like Python's hash())
        ids = [generate_newsletter_id("Test", "2026-01-01") for _ in range(100)]
        assert len(set(ids)) == 1  # All IDs identical

    def test_collision_resistance(self):
        """Should generate unique IDs for different inputs."""
        # Generate IDs for 1000 different titles
        ids = [
            generate_newsletter_id(f"Title {i}", "2026-02-04")
            for i in range(1000)
        ]
        # All should be unique (no collisions)
        assert len(ids) == len(set(ids))
```

### PostgreSQL Schema Considerations

```sql
-- Recommended schema for newsletter items in feed_items table
-- ID format: VARCHAR(27) to accommodate "newsletter:" (11) + hash (16)

-- Existing feed_items table (from spec)
-- No changes needed - existing VARCHAR(255) id column is sufficient

-- Example query to verify ID format
SELECT
    id,
    source_type,
    source_id,
    LENGTH(id) as id_length,
    LENGTH(source_id) as source_id_length
FROM feed_items
WHERE source_type = 'newsletter';

-- Expected results:
-- id: "newsletter:a1b2c3d4e5f6g7h8" (27 characters)
-- source_id: "a1b2c3d4e5f6g7h8" (16 characters)
-- id_length: 27
-- source_id_length: 16
```

## Performance Considerations

**SHA-256 Performance Benchmarks**:
- Modern CPUs: ~500 MB/s hashing throughput
- For newsletter items (typical input ~100 bytes):
  - Single hash: ~0.0002 ms (0.2 microseconds)
  - 1000 items: ~0.2 ms total
  - Negligible overhead compared to LLM parsing (~1-5 seconds per item)

**Database Index Performance**:
- VARCHAR(27) primary key: Fast B-tree lookups
- 16-character hex hash: More efficient than 64-character full hash
- Compared to UUID (36 characters): 25% smaller
- Compared to full SHA-256 hex (64 characters): 58% smaller

**Source**: [Multiple-Column Indexes and Hashing: The Ultimate Guide to Boosting Database Performance](https://medium.com/@lordNeic/multiple-column-indexes-and-hashing-the-ultimate-guide-to-boosting-database-performance-89e2a06c8a75)

## Migration Considerations

**Migrating from hash() to SHA-256**:
1. Existing items in database will have old hash-based IDs
2. After migration, same newsletter content will generate DIFFERENT IDs
3. This will create duplicates temporarily

**Recommended Migration Strategy**:
```python
# Option 1: Regenerate all IDs during migration (RECOMMENDED)
# - More complex migration
# - Clean slate with stable IDs
# - No duplicates

# Option 2: Keep old IDs, use SHA-256 only for new items
# - Simpler migration
# - Mixed ID formats (hash vs SHA-256)
# - Old items retain instability until re-processed

# From spec: "Migration script MUST import existing newsletter_items
# data from SQLite to PostgreSQL"
# Recommendation: Regenerate IDs during migration using SHA-256
```

**Migration SQL Example**:
```sql
-- Regenerate IDs during migration from SQLite to PostgreSQL
INSERT INTO feed_items (id, source_type, source_id, title, date, summary, link, metadata, fetched_at)
SELECT
    'newsletter:' || SUBSTRING(encode(digest(LOWER(TRIM(title)) || ':' || COALESCE(date, ''), 'sha256'), 'hex'), 1, 16) as id,
    'newsletter' as source_type,
    SUBSTRING(encode(digest(LOWER(TRIM(title)) || ':' || COALESCE(date, ''), 'sha256'), 'hex'), 1, 16) as source_id,
    title,
    date,
    summary,
    link,
    metadata,
    fetched_at
FROM legacy_newsletter_items
ON CONFLICT (source_type, source_id) DO NOTHING;  -- Skip duplicates
```

## Summary of Recommendations

### Implementation Checklist

- [x] **Use SHA-256 with hexdigest()** for deterministic hashing
- [x] **Encode with UTF-8** for international character support
- [x] **Normalize Unicode to NFC** before hashing
- [x] **Normalize input**: lowercase + strip whitespace + collapse spaces
- [x] **Truncate to 16 characters** (64 bits of entropy)
- [x] **Format**: `newsletter:{16-char-hash}`
- [x] **Validate at Pydantic layer** (reject empty titles)
- [x] **Type hints everywhere** for production reliability
- [x] **Unit tests** for normalization and ID stability

### Code Integration Points

**File**: `c:\Users\wgilp\projects\daily_briefing\src\sources\newsletter.py`

**Current Implementation** (lines 156-159):
```python
# Generate unique ID
# Use a hash of title and date for uniqueness
item_hash = hash(f"{title}:{newsletter_item.get('date', '')}")
item_id = f"newsletter:{abs(item_hash)}"
```

**Replacement**:
```python
# Generate stable, deterministic ID using SHA-256
item_id = generate_newsletter_id(title, newsletter_item.get("date", ""))
source_id = item_id.split(":", 1)[1]  # Extract hash for source_id
```

**New Module**: `c:\Users\wgilp\projects\daily_briefing\src\newsletter\id_generation.py`
- Contains `normalize_text()` and `generate_newsletter_id()`
- Fully typed with Pydantic validation support
- Comprehensive docstrings and examples

## References

### Primary Sources
- [Python hashlib documentation](https://docs.python.org/3/library/hashlib.html) - Official SHA-256 implementation
- [Hash Collision Probabilities](https://preshing.com/20110504/hash-collision-probabilities/) - Birthday paradox analysis
- [Handling Encoding Issues With Unicode Normalisation In Python](https://xebia.com/blog/handling-encoding-issues-with-unicode-normalisation-in-python/) - NFC normalization
- [Deterministic hashing of Python data objects](https://death.andgravity.com/stable-hashing) - Stable hashing patterns
- [PostgreSQL pgcrypto documentation](https://www.postgresql.org/docs/current/pgcrypto.html) - Database hashing functions

### Additional Reading
- [SHA-2 - Wikipedia](https://en.wikipedia.org/wiki/SHA-2) - SHA-256 algorithm details
- [Multiple-Column Indexes and Hashing: Database Performance](https://medium.com/@lordNeic/multiple-column-indexes-and-hashing-the-ultimate-guide-to-boosting-database-performance-89e2a06c8a75) - Index optimization
- [Birthday attack probability](https://www.johndcook.com/blog/2017/01/10/probability-of-secure-hash-collisions/) - Collision math

---

**Next Steps**:
1. Create `src/newsletter/id_generation.py` with implementation
2. Add unit tests in `tests/unit/test_sha256_ids.py`
3. Update `src/sources/newsletter.py` to use new ID generation
4. Run full test suite to verify no regressions
5. Update migration script to regenerate IDs using SHA-256
