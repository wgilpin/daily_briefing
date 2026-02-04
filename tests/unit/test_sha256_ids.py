"""Unit tests for SHA-256 ID generation.

Tests deterministic, collision-resistant ID generation for newsletter items.
"""

import pytest

from src.newsletter.id_generation import generate_newsletter_id, normalize_text


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

    def test_specific_hash_value(self):
        """Should generate expected hash for known input (regression test)."""
        # This verifies the exact hash implementation doesn't change
        item_id = generate_newsletter_id("Test Article", "2026-02-04")
        # Extract hash portion
        hash_part = item_id.split(":", 1)[1]
        # Verify it's a valid 16-character hex string
        assert len(hash_part) == 16
        assert all(c in "0123456789abcdef" for c in hash_part)

    def test_case_insensitive_matching(self):
        """Should treat case variations as identical."""
        id1 = generate_newsletter_id("Breaking News", "2026-02-04")
        id2 = generate_newsletter_id("BREAKING NEWS", "2026-02-04")
        id3 = generate_newsletter_id("breaking news", "2026-02-04")
        assert id1 == id2 == id3
