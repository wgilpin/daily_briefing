"""Integration tests for topic exclusion routes."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.web.app import create_app
from src.newsletter.config import NewsletterConfig


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def auth(client):
    """Authentication helper for test client."""
    class AuthActions:
        def __init__(self, client):
            self._client = client

        def login(self, email="test@example.com"):
            """Login as test user."""
            # Mock authentication - bypass actual login
            with client.session_transaction() as sess:
                sess["_user_id"] = "1"
                sess["_fresh"] = True

        def logout(self):
            """Logout user."""
            with client.session_transaction() as sess:
                sess.clear()

    return AuthActions(client)


@pytest.fixture
def mock_config(tmp_path):
    """Create temporary config file for testing."""
    config_file = tmp_path / "senders.json"
    config_data = {
        "senders": {},
        "consolidation_prompt": "test prompt",
        "retention_limit": 100,
        "days_lookback": 30,
        "max_workers": 10,
        "default_parsing_prompt": "test parsing",
        "default_consolidation_prompt": "test consolidation",
        "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
        "excluded_topics": []
    }
    config_file.write_text(json.dumps(config_data), encoding="utf-8")
    return config_file


class TestExclusionRoutes:
    """Test exclusion management routes."""

    def test_add_exclusion_success(self, client, auth, mock_config):
        """POST /settings/exclusions/add adds topic and returns HTML."""
        auth.login()

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = mock_config

            response = client.post('/settings/exclusions/add', data={'topic': 'datasette'})

            assert response.status_code == 200
            assert b'datasette' in response.data
            assert b'hx-delete' in response.data

    def test_add_exclusion_empty_topic(self, client, auth, mock_config):
        """POST /settings/exclusions/add with empty topic returns error."""
        auth.login()

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = mock_config

            response = client.post('/settings/exclusions/add', data={'topic': '   '})

            assert response.status_code == 400
            assert b'empty' in response.data.lower()

    def test_add_exclusion_exceeds_100_chars(self, client, auth, mock_config):
        """POST /settings/exclusions/add with topic exceeding 100 chars returns error."""
        auth.login()

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = mock_config

            long_topic = "a" * 101
            response = client.post('/settings/exclusions/add', data={'topic': long_topic})

            assert response.status_code == 400
            assert b'100 character' in response.data

    def test_add_exclusion_at_limit(self, client, auth, tmp_path):
        """POST /settings/exclusions/add at 50-topic limit returns error."""
        auth.login()

        # Create config with 50 topics already
        config_file = tmp_path / "senders.json"
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": [f"topic{i}" for i in range(50)]
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = config_file

            response = client.post('/settings/exclusions/add', data={'topic': 'one_more'})

            assert response.status_code == 409
            assert b'50' in response.data or b'Maximum' in response.data

    def test_delete_exclusion_success(self, client, auth, tmp_path):
        """DELETE /settings/exclusions/delete/{index} removes topic."""
        auth.login()

        # Create config with topics
        config_file = tmp_path / "senders.json"
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["datasette", "SQL"]
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = config_file

            response = client.delete('/settings/exclusions/delete/0')

            assert response.status_code == 200

            # Verify topic was removed from config
            saved_data = json.loads(config_file.read_text(encoding="utf-8"))
            assert "datasette" not in saved_data["excluded_topics"]
            assert "SQL" in saved_data["excluded_topics"]

    def test_delete_exclusion_invalid_index(self, client, auth, mock_config):
        """DELETE /settings/exclusions/delete/{index} with invalid index returns error."""
        auth.login()

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = mock_config

            response = client.delete('/settings/exclusions/delete/999')

            assert response.status_code == 404
            assert b'not found' in response.data.lower() or b'invalid' in response.data.lower()

    def test_list_exclusions_with_topics(self, client, auth, tmp_path):
        """GET /settings/exclusions/list returns HTML list with topics."""
        auth.login()

        # Create config with topics
        config_file = tmp_path / "senders.json"
        config_data = {
            "senders": {},
            "consolidation_prompt": "test prompt",
            "retention_limit": 100,
            "days_lookback": 30,
            "max_workers": 10,
            "default_parsing_prompt": "test parsing",
            "default_consolidation_prompt": "test consolidation",
            "models": {"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            "excluded_topics": ["datasette", "low-level coding"]
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = config_file

            response = client.get('/settings/exclusions/list')

            assert response.status_code == 200
            assert b'datasette' in response.data
            assert b'low-level coding' in response.data

    def test_list_exclusions_empty(self, client, auth, mock_config):
        """GET /settings/exclusions/list with empty list returns placeholder."""
        auth.login()

        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = mock_config

            response = client.get('/settings/exclusions/list')

            assert response.status_code == 200
            assert b'No topics' in response.data or b'empty' in response.data.lower()

    def test_routes_require_authentication(self, client, mock_config):
        """All exclusion routes require authentication."""
        with patch('src.newsletter.config.Path') as mock_path_class:
            mock_path_class.return_value = mock_config

            # Test without authentication
            response_add = client.post('/settings/exclusions/add', data={'topic': 'test'})
            response_delete = client.delete('/settings/exclusions/delete/0')
            response_list = client.get('/settings/exclusions/list')

            # Should redirect to login or return 401
            assert response_add.status_code in [301, 302, 401]
            assert response_delete.status_code in [301, 302, 401]
            assert response_list.status_code in [301, 302, 401]
