"""Unit tests for feed_routes.py sender route handlers.

T010: Route handlers call Repository methods, not file-based config functions.
Tests use Flask test client with mocked Repository.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.newsletter_models import SenderRecord


@pytest.fixture
def app():
    """Create Flask test app."""
    with patch("src.db.connection.initialize_pool"):
        from src.web.app import create_app
        flask_app = create_app()
        flask_app.config["TESTING"] = True
        return flask_app


def _mock_login(mock_user_fn):
    user = MagicMock()
    user.is_authenticated = True
    user.is_active = True
    user.get_id.return_value = "1"
    mock_user_fn.return_value = user


class TestApiSettingsNewsletterSender:
    """POST /api/settings/newsletter/senders — should call Repository.add_sender."""

    def test_add_sender_calls_repository(self, app):
        with patch("src.db.repository.Repository.sender_exists", return_value=False), \
             patch("src.db.repository.Repository.add_sender") as mock_add, \
             patch("flask_login.utils._get_user") as mu:
            _mock_login(mu)
            with app.test_request_context(
                "/api/settings/newsletter/senders",
                method="POST",
                data={"email": "test@example.com", "display_name": "Test"},
            ):
                from src.web.feed_routes import api_settings_newsletter_sender
                api_settings_newsletter_sender()
            mock_add.assert_called_once()

    def test_returns_error_for_duplicate_sender(self, app):
        with patch("src.db.repository.Repository.sender_exists", return_value=True), \
             patch("src.db.repository.Repository.add_sender") as mock_add, \
             patch("flask_login.utils._get_user") as mu:
            _mock_login(mu)
            with app.test_request_context(
                "/api/settings/newsletter/senders",
                method="POST",
                data={"email": "existing@example.com"},
            ):
                from src.web.feed_routes import api_settings_newsletter_sender
                response = api_settings_newsletter_sender()
            body = response if isinstance(response, str) else (response[0] if isinstance(response, tuple) else "")
            assert "already" in body.lower() or "error" in body.lower()
            mock_add.assert_not_called()


class TestApiSettingsUpdateDisplayName:
    """POST /api/settings/newsletter/display-name — calls Repository.update_sender_display_name."""

    def test_update_display_name_calls_repository(self, app):
        sender = SenderRecord(email="a@example.com")
        with patch("src.db.repository.Repository.get_sender", return_value=sender), \
             patch("src.db.repository.Repository.update_sender_display_name") as mock_update, \
             patch("flask_login.utils._get_user") as mu:
            _mock_login(mu)
            with app.test_request_context(
                "/api/settings/newsletter/display-name",
                method="POST",
                data={"email": "a@example.com", "display_name": "New Name"},
            ):
                from src.web.feed_routes import api_settings_update_display_name
                api_settings_update_display_name()
            mock_update.assert_called_once_with("a@example.com", "New Name")

    def test_returns_error_when_sender_not_found(self, app):
        with patch("src.db.repository.Repository.get_sender", return_value=None), \
             patch("src.db.repository.Repository.update_sender_display_name") as mock_update, \
             patch("flask_login.utils._get_user") as mu:
            _mock_login(mu)
            with app.test_request_context(
                "/api/settings/newsletter/display-name",
                method="POST",
                data={"email": "missing@example.com", "display_name": "X"},
            ):
                from src.web.feed_routes import api_settings_update_display_name
                response = api_settings_update_display_name()
            body = response if isinstance(response, str) else (response[0] if isinstance(response, tuple) else "")
            assert "not found" in body.lower() or "error" in body.lower()
            mock_update.assert_not_called()


class TestApiSettingsDeleteSender:
    """DELETE /api/settings/newsletter/senders/<email> — calls Repository.delete_sender."""

    def test_delete_sender_calls_repository(self, app):
        with patch("src.db.repository.Repository.sender_exists", return_value=True), \
             patch("src.db.repository.Repository.delete_sender") as mock_delete, \
             patch("flask_login.utils._get_user") as mu:
            _mock_login(mu)
            with app.test_request_context(
                "/api/settings/newsletter/senders/a@example.com",
                method="DELETE",
            ):
                from src.web.feed_routes import api_settings_delete_sender
                api_settings_delete_sender("a@example.com")
            mock_delete.assert_called_once_with("a@example.com")

    def test_returns_error_when_sender_not_found(self, app):
        with patch("src.db.repository.Repository.sender_exists", return_value=False), \
             patch("src.db.repository.Repository.delete_sender") as mock_delete, \
             patch("flask_login.utils._get_user") as mu:
            _mock_login(mu)
            with app.test_request_context(
                "/api/settings/newsletter/senders/missing@example.com",
                method="DELETE",
            ):
                from src.web.feed_routes import api_settings_delete_sender
                response = api_settings_delete_sender("missing@example.com")
            body = response if isinstance(response, str) else (response[0] if isinstance(response, tuple) else "")
            assert "not found" in body.lower() or "error" in body.lower()
            mock_delete.assert_not_called()
