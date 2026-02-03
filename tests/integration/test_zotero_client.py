"""Integration tests for Zotero API client functions."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.zotero import AuthenticationError, ZoteroConnectionError
from src.zotero.client import fetch_recent_items


def test_fetch_recent_items_success():
    """Test fetch_recent_items() successfully retrieves items."""
    # Create mock client
    mock_client = MagicMock()
    
    # Calculate expected cutoff timestamp in UTC (matching implementation)
    days = 1
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Create items with dateAdded in the correct format (RFC 3339 with Z)
    now_utc = datetime.now(timezone.utc)
    item1_date = (now_utc - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    item2_date = (now_utc - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old_item_date = (cutoff - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Mock items response - include items within and outside the date range
    mock_items = [
        {
            "key": "item1",
            "data": {
                "title": "Test Item 1",
                "dateAdded": item1_date,  # Within range
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Test Item 2",
                "dateAdded": item2_date,  # Within range
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item3",
            "data": {
                "title": "Old Item",
                "dateAdded": old_item_date,  # Outside range (too old)
                "itemType": "journalArticle",
            }
        },
    ]
    
    # Mock items() to return the items
    mock_client.items.return_value = mock_items

    # Call function
    result = fetch_recent_items(mock_client, days)

    # Verify client.items was called once with correct parameters
    mock_client.items.assert_called_once()
    call_args = mock_client.items.call_args
    assert call_args.kwargs["sort"] == "dateAdded"
    assert call_args.kwargs["direction"] == "desc"
    assert call_args.kwargs["limit"] == 100

    # Verify result - should only include items within the date range
    assert len(result) == 2, "Should filter out old items"
    assert result[0]["key"] == "item1"
    assert result[1]["key"] == "item2"
    # Verify item3 (old item) is not in results
    assert "item3" not in [item["key"] for item in result]


def test_fetch_recent_items_authentication_error():
    """Test fetch_recent_items() raises AuthenticationError on invalid credentials."""
    mock_client = MagicMock()
    mock_client.items.side_effect = Exception("401 Unauthorized")
    
    with pytest.raises(AuthenticationError):
        fetch_recent_items(mock_client, 1)


def test_fetch_recent_items_connection_error():
    """Test fetch_recent_items() raises ConnectionError on network failure."""
    mock_client = MagicMock()
    mock_client.items.side_effect = Exception("Connection timeout")
    
    with pytest.raises(ZoteroConnectionError):
        fetch_recent_items(mock_client, 1)


def test_fetch_recent_items_invalid_days():
    """Test fetch_recent_items() raises ValueError for invalid days."""
    mock_client = MagicMock()
    
    with pytest.raises(ValueError, match="days must be a positive integer"):
        fetch_recent_items(mock_client, 0)
    
    with pytest.raises(ValueError, match="days must be a positive integer"):
        fetch_recent_items(mock_client, -1)


def test_fetch_recent_items_empty_result():
    """Test fetch_recent_items() handles empty results."""
    mock_client = MagicMock()
    mock_client.items.return_value = []

    result = fetch_recent_items(mock_client, 1)

    assert result == []
    # Should call once, sorted by dateAdded
    mock_client.items.assert_called_once()
    call_args = mock_client.items.call_args
    assert call_args.kwargs["sort"] == "dateAdded"

