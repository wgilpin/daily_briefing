"""Integration tests for topic exclusion routes."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.web.app import create_app
from src.newsletter.config import NewsletterConfig


@pytest.fixture
def app():
    """Create Flask app for testing."""
    from flask_login import UserMixin

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
    app.config["LOGIN_DISABLED"] = True  # Disable Flask-Login for tests

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

        def login(self, email="test@example.com", user_id="1"):
            """Login as test user by setting session."""
            # Flask-Login reads _user_id from session
            with self._client.session_transaction() as sess:
                sess["_user_id"] = user_id
                sess["_fresh"] = True

        def logout(self):
            """Logout user."""
            with self._client.session_transaction() as sess:
                sess.clear()

    return AuthActions(client)


@pytest.fixture
def base_config():
    """Base configuration for testing."""
    return NewsletterConfig(
        senders={},
        consolidation_prompt="test prompt",
        retention_limit=100,
        days_lookback=30,
        max_workers=10,
        default_parsing_prompt="test parsing",
        default_consolidation_prompt="test consolidation",
        models={"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
        excluded_topics=[]
    )


class TestExclusionRoutes:
    """Test exclusion management routes."""

    def test_add_exclusion_success(self, client, auth, base_config):
        """POST /settings/exclusions/add adds topic and returns HTML."""
        auth.login()

        with patch('src.newsletter.config.load_config') as mock_load, \
             patch('src.newsletter.config.save_config') as mock_save:

            mock_load.return_value = base_config

            response = client.post('/settings/exclusions/add', data={'topic': 'datasette'})

            assert response.status_code == 200
            assert b'datasette' in response.data
            assert b'hx-delete' in response.data

            # Verify save was called with updated config
            mock_save.assert_called_once()
            saved_config = mock_save.call_args[0][0]
            assert 'datasette' in saved_config.excluded_topics

    def test_add_exclusion_empty_topic(self, client, auth, base_config):
        """POST /settings/exclusions/add with empty topic returns error."""
        auth.login()

        with patch('src.newsletter.config.load_config') as mock_load, \
             patch('src.newsletter.config.save_config') as mock_save:

            mock_load.return_value = base_config

            response = client.post('/settings/exclusions/add', data={'topic': '   '})

            assert response.status_code == 400
            assert b'empty' in response.data.lower()
            mock_save.assert_not_called()

    def test_add_exclusion_exceeds_100_chars(self, client, auth, base_config):
        """POST /settings/exclusions/add with topic exceeding 100 chars returns error."""
        auth.login()

        with patch('src.newsletter.config.load_config') as mock_load, \
             patch('src.newsletter.config.save_config') as mock_save:

            mock_load.return_value = base_config

            long_topic = 'a' * 101
            response = client.post('/settings/exclusions/add', data={'topic': long_topic})

            assert response.status_code == 400
            assert b'100 character' in response.data
            mock_save.assert_not_called()

    def test_add_exclusion_at_limit(self, client, auth, base_config):
        """POST /settings/exclusions/add at 50-topic limit returns error."""
        auth.login()

        # Create config at limit
        config_at_limit = NewsletterConfig(
            senders={},
            consolidation_prompt="test prompt",
            retention_limit=100,
            days_lookback=30,
            max_workers=10,
            default_parsing_prompt="test parsing",
            default_consolidation_prompt="test consolidation",
            models={"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            excluded_topics=[f"topic{i}" for i in range(50)]
        )

        with patch('src.newsletter.config.load_config') as mock_load, \
             patch('src.newsletter.config.save_config') as mock_save:

            mock_load.return_value = config_at_limit

            response = client.post('/settings/exclusions/add', data={'topic': 'new_topic'})

            assert response.status_code == 409
            assert b'50 topics' in response.data.lower()
            mock_save.assert_not_called()

    def test_delete_exclusion_success(self, client, auth, base_config):
        """DELETE /settings/exclusions/delete/<index> removes topic."""
        auth.login()

        # Config with topics
        config_with_topics = NewsletterConfig(
            senders={},
            consolidation_prompt="test prompt",
            retention_limit=100,
            days_lookback=30,
            max_workers=10,
            default_parsing_prompt="test parsing",
            default_consolidation_prompt="test consolidation",
            models={"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            excluded_topics=["topic1", "topic2", "topic3"]
        )

        with patch('src.newsletter.config.load_config') as mock_load, \
             patch('src.newsletter.config.save_config') as mock_save:

            mock_load.return_value = config_with_topics

            response = client.delete('/settings/exclusions/delete/1')

            assert response.status_code == 200
            mock_save.assert_called_once()
            saved_config = mock_save.call_args[0][0]
            assert saved_config.excluded_topics == ["topic1", "topic3"]

    def test_delete_exclusion_invalid_index(self, client, auth, base_config):
        """DELETE /settings/exclusions/delete/<index> with invalid index returns error."""
        auth.login()

        config_with_topics = NewsletterConfig(
            senders={},
            consolidation_prompt="test prompt",
            retention_limit=100,
            days_lookback=30,
            max_workers=10,
            default_parsing_prompt="test parsing",
            default_consolidation_prompt="test consolidation",
            models={"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            excluded_topics=["topic1", "topic2"]
        )

        with patch('src.newsletter.config.load_config') as mock_load, \
             patch('src.newsletter.config.save_config') as mock_save:

            mock_load.return_value = config_with_topics

            response = client.delete('/settings/exclusions/delete/5')

            assert response.status_code in (400, 404)  # Either bad request or not found
            assert b'invalid' in response.data.lower() or b'not found' in response.data.lower()
            mock_save.assert_not_called()

    def test_list_exclusions_with_topics(self, client, auth, base_config):
        """GET /settings/exclusions/list returns HTML with topics."""
        auth.login()

        config_with_topics = NewsletterConfig(
            senders={},
            consolidation_prompt="test prompt",
            retention_limit=100,
            days_lookback=30,
            max_workers=10,
            default_parsing_prompt="test parsing",
            default_consolidation_prompt="test consolidation",
            models={"parsing": "gemini-2.5-flash", "consolidation": "gemini-2.5-flash"},
            excluded_topics=["datasette", "SQL internals"]
        )

        with patch('src.newsletter.config.load_config') as mock_load:
            mock_load.return_value = config_with_topics

            response = client.get('/settings/exclusions/list')

            assert response.status_code == 200
            assert b'datasette' in response.data
            assert b'SQL internals' in response.data
            assert b'exclusion-item' in response.data

    def test_list_exclusions_empty(self, client, auth, base_config):
        """GET /settings/exclusions/list with no topics shows empty state."""
        auth.login()

        with patch('src.newsletter.config.load_config') as mock_load:
            mock_load.return_value = base_config

            response = client.get('/settings/exclusions/list')

            assert response.status_code == 200
            assert b'no-exclusions' in response.data.lower() or b'no topics' in response.data.lower()

    def test_routes_require_authentication(self):
        """All exclusion routes require authentication."""
        # Create app WITHOUT LOGIN_DISABLED
        app = create_app()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        # Do NOT set LOGIN_DISABLED here
        client = app.test_client()

        # Test without login - should redirect or return 401
        response_add = client.post('/settings/exclusions/add', data={'topic': 'test'})
        assert response_add.status_code in (302, 401)  # Redirect to login or unauthorized

        response_delete = client.delete('/settings/exclusions/delete/0')
        assert response_delete.status_code in (302, 401)

        response_list = client.get('/settings/exclusions/list')
        assert response_list.status_code in (302, 401)
