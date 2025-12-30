"""Integration tests for Zotero API client functions."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.zotero import AuthenticationError, ZoteroConnectionError
from src.zotero.client import fetch_recent_items


def test_fetch_recent_items_success():
    """Test fetch_recent_items() successfully retrieves items."""
    # Create mock client
    mock_client = MagicMock()
    
    # Calculate expected cutoff timestamp
    days = 1
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()
    
    # Mock items response
    mock_items = [
        {
            "key": "item1",
            "data": {
                "title": "Test Item 1",
                "dateAdded": (datetime.now() - timedelta(hours=12)).isoformat(),
                "itemType": "journalArticle",
            }
        },
        {
            "key": "item2",
            "data": {
                "title": "Test Item 2",
                "dateAdded": (datetime.now() - timedelta(hours=6)).isoformat(),
                "itemType": "journalArticle",
            }
        },
    ]
    
    mock_client.items.return_value = mock_items
    
    # Call function
    result = fetch_recent_items(mock_client, days)
    
    # Verify client.items was called with correct since parameter
    mock_client.items.assert_called_once()
    call_args = mock_client.items.call_args
    assert "since" in call_args.kwargs
    since_value = call_args.kwargs["since"]
    # Since value should be close to our cutoff (within a few seconds)
    # Handle timezone-aware and naive datetime comparison
    since_dt = datetime.fromisoformat(since_value.replace("Z", "+00:00"))
    if since_dt.tzinfo is not None:
        # Convert to naive for comparison
        since_dt = since_dt.replace(tzinfo=None)
    assert abs((since_dt - cutoff).total_seconds()) < 5
    
    # Verify result
    assert len(result) == 2
    assert result[0]["key"] == "item1"
    assert result[1]["key"] == "item2"


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
    mock_client.items.assert_called_once()

