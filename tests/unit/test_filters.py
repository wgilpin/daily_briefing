"""Unit tests for filtering and sorting functions."""

import pytest

from src.zotero.filters import filter_by_keywords, sort_and_limit_items


def test_sort_and_limit_items_with_more_than_10_items():
    """Test sort_and_limit_items() with >10 items - should sort by date and limit to 10."""
    # Create 15 items with different publication dates
    items = []
    for i in range(15):
        year = 2020 + i  # Dates from 2020 to 2034
        items.append({
            "key": f"item_{i}",
            "data": {
                "title": f"Item {i}",
                "date": f"{year}-01-01",
                "itemType": "journalArticle",
            }
        })
    
    # Reverse so oldest is first (to test sorting)
    items.reverse()
    
    result = sort_and_limit_items(items, limit=10)
    
    # Should return exactly 10 items
    assert len(result) == 10
    
    # Should be sorted by date descending (newest first)
    dates = [item["data"]["date"] for item in result]
    assert dates == sorted(dates, reverse=True)
    
    # Should contain the 10 most recent items (2024-2034)
    assert result[0]["data"]["date"] == "2034-01-01"
    assert result[-1]["data"]["date"] == "2025-01-01"


def test_sort_and_limit_items_with_10_or_fewer_items():
    """Test sort_and_limit_items() with <=10 items - should return all items."""
    # Create 5 items
    items = []
    for i in range(5):
        items.append({
            "key": f"item_{i}",
            "data": {
                "title": f"Item {i}",
                "date": f"2024-{i+1:02d}-01",
                "itemType": "journalArticle",
            }
        })
    
    result = sort_and_limit_items(items, limit=10)
    
    # Should return all 5 items (no limit applied)
    assert len(result) == 5
    
    # Should be sorted by date descending
    dates = [item["data"]["date"] for item in result]
    assert dates == sorted(dates, reverse=True)


def test_sort_and_limit_items_with_missing_publication_dates():
    """Test sort_and_limit_items() with missing publication dates - items without dates sorted to end."""
    items = [
        {
            "key": "item_1",
            "data": {
                "title": "Item with date 2024",
                "date": "2024-01-01",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item_2",
            "data": {
                "title": "Item without date",
                "itemType": "journalArticle",
                # No date field
            }
        },
        {
            "key": "item_3",
            "data": {
                "title": "Item with date 2023",
                "date": "2023-01-01",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item_4",
            "data": {
                "title": "Item with empty date",
                "date": "",
                "itemType": "journalArticle",
            }
        },
    ]
    
    result = sort_and_limit_items(items, limit=10)
    
    # Should return all 4 items
    assert len(result) == 4
    
    # Items with dates should come first, sorted by date descending
    assert result[0]["key"] == "item_1"  # 2024-01-01 (newest)
    assert result[1]["key"] == "item_3"  # 2023-01-01
    
    # Items without dates should come last
    assert result[2]["key"] == "item_2"  # No date
    assert result[3]["key"] == "item_4"  # Empty date


def test_sort_and_limit_items_with_empty_list():
    """Test sort_and_limit_items() with empty list."""
    result = sort_and_limit_items([], limit=10)
    assert result == []


def test_sort_and_limit_items_with_custom_limit():
    """Test sort_and_limit_items() with custom limit."""
    items = []
    for i in range(20):
        # Use valid months (1-12) by cycling
        month = (i % 12) + 1
        items.append({
            "key": f"item_{i}",
            "data": {
                "title": f"Item {i}",
                "date": f"2024-{month:02d}-01",
                "itemType": "journalArticle",
            }
        })
    
    result = sort_and_limit_items(items, limit=5)
    
    # Should return exactly 5 items
    assert len(result) == 5
    
    # Should be sorted by date descending (newest first)
    dates = [item["data"]["date"] for item in result]
    assert dates == sorted(dates, reverse=True)


def test_filter_by_keywords_with_include_keywords():
    """Test filter_by_keywords() with include keywords."""
    items = [
        {
            "key": "item1",
            "data": {
                "title": "Machine Learning in Python",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Introduction to Statistics",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item3",
            "data": {
                "title": "Deep Learning Applications",
                "itemType": "journalArticle",
            }
        },
    ]
    
    result = filter_by_keywords(items, include=["machine learning", "deep learning"], exclude=[])
    
    # Should return only items matching include keywords
    assert len(result) == 2
    assert result[0]["key"] == "item1"  # "Machine Learning"
    assert result[1]["key"] == "item3"  # "Deep Learning"


def test_filter_by_keywords_with_exclude_keywords():
    """Test filter_by_keywords() with exclude keywords."""
    items = [
        {
            "key": "item1",
            "data": {
                "title": "A Review of Machine Learning",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Introduction to Statistics",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item3",
            "data": {
                "title": "Survey of Deep Learning",
                "itemType": "journalArticle",
            }
        },
    ]
    
    result = filter_by_keywords(items, include=[], exclude=["review", "survey"])
    
    # Should exclude items with "review" or "survey"
    assert len(result) == 1
    assert result[0]["key"] == "item2"


def test_filter_by_keywords_with_both_include_and_exclude():
    """Test filter_by_keywords() with both include and exclude (exclusion takes precedence)."""
    items = [
        {
            "key": "item1",
            "data": {
                "title": "A Review of Machine Learning",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Machine Learning Applications",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item3",
            "data": {
                "title": "Deep Learning Survey",
                "itemType": "journalArticle",
            }
        },
    ]
    
    result = filter_by_keywords(
        items,
        include=["machine learning", "deep learning"],
        exclude=["review", "survey"]
    )
    
    # Should include ML/DL items but exclude those with review/survey
    # item1 matches include but has "review" - should be excluded
    # item2 matches include and no exclude - should be included
    # item3 matches include but has "survey" - should be excluded
    assert len(result) == 1
    assert result[0]["key"] == "item2"


def test_filter_by_keywords_with_empty_filters():
    """Test filter_by_keywords() with empty filters (no filtering)."""
    items = [
        {
            "key": "item1",
            "data": {
                "title": "Item 1",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Item 2",
                "itemType": "journalArticle",
            }
        },
    ]
    
    result = filter_by_keywords(items, include=[], exclude=[])
    
    # Should return all items unchanged
    assert len(result) == 2
    assert result == items


def test_filter_by_keywords_case_insensitive_matching():
    """Test filter_by_keywords() case-insensitive matching."""
    items = [
        {
            "key": "item1",
            "data": {
                "title": "Machine Learning Basics",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "MACHINE LEARNING Advanced",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item3",
            "data": {
                "title": "machine learning applications",
                "itemType": "journalArticle",
            }
        },
    ]
    
    result = filter_by_keywords(items, include=["MACHINE LEARNING"], exclude=[])
    
    # Should match all items regardless of case
    assert len(result) == 3


def test_filter_by_keywords_searching_in_title_abstract_and_tags():
    """Test filter_by_keywords() searching in title, abstract, and tags."""
    items = [
        {
            "key": "item1",
            "data": {
                "title": "Some Article",
                "abstractNote": "This is about machine learning",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Machine Learning Paper",
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item3",
            "data": {
                "title": "Another Article",
                "tags": [{"tag": "machine-learning"}],
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item4",
            "data": {
                "title": "Unrelated Article",
                "itemType": "journalArticle",
            }
        },
    ]
    
    result = filter_by_keywords(items, include=["machine learning"], exclude=[])
    
    # Should find items with keyword in title, abstract, or tags
    assert len(result) == 3
    assert "item1" in [item["key"] for item in result]  # In abstract
    assert "item2" in [item["key"] for item in result]  # In title
    assert "item3" in [item["key"] for item in result]  # In tag
    assert "item4" not in [item["key"] for item in result]  # No match

