"""Integration tests for Gmail client functions."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials

from src.newsletter.gmail_client import authenticate_gmail, collect_emails


class TestAuthenticateGmail:
    """Tests for authenticate_gmail() function."""

    @patch("src.newsletter.gmail_client.build")
    @patch("src.newsletter.gmail_client.InstalledAppFlow")
    @patch("src.newsletter.gmail_client.Credentials")
    def test_authenticate_gmail_with_existing_valid_token(
        self, mock_credentials_class, mock_flow_class, mock_build
    ):
        """Test authentication with existing valid token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            credentials_path = Path(tmpdir) / "credentials.json"
            tokens_path = Path(tmpdir) / "tokens.json"

            # Create mock credentials file
            credentials_data = {
                "installed": {
                    "client_id": "test_client_id",
                    "client_secret": "test_secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            with open(credentials_path, "w") as f:
                json.dump(credentials_data, f)

            # Create mock tokens file
            tokens_data = {
                "token": "test_token",
                "refresh_token": "test_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            }
            with open(tokens_path, "w") as f:
                json.dump(tokens_data, f)

            # Mock valid credentials
            mock_creds = Mock(spec=Credentials)
            mock_creds.valid = True
            mock_creds.refresh.return_value = None

            mock_credentials_class.from_authorized_user_file.return_value = mock_creds

            result = authenticate_gmail(str(credentials_path), str(tokens_path))

            assert result == mock_creds
            mock_credentials_class.from_authorized_user_file.assert_called_once()

    @patch("src.newsletter.gmail_client.build")
    @patch("src.newsletter.gmail_client.InstalledAppFlow")
    @patch("src.newsletter.gmail_client.Credentials")
    def test_authenticate_gmail_with_expired_token_refreshes(
        self, mock_credentials_class, mock_flow_class, mock_build
    ):
        """Test authentication refreshes expired token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            credentials_path = Path(tmpdir) / "credentials.json"
            tokens_path = Path(tmpdir) / "tokens.json"

            # Create mock credentials file
            credentials_data = {
                "installed": {
                    "client_id": "test_client_id",
                    "client_secret": "test_secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            with open(credentials_path, "w") as f:
                json.dump(credentials_data, f)

            # Create mock tokens file
            tokens_data = {
                "token": "expired_token",
                "refresh_token": "test_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
            }
            with open(tokens_path, "w") as f:
                json.dump(tokens_data, f)

            # Mock expired credentials that refresh successfully
            mock_creds = Mock(spec=Credentials)
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "test_refresh_token"
            mock_creds.refresh.return_value = None
            mock_creds.to_json.return_value = '{"token": "refreshed_token"}'

            mock_credentials_class.from_authorized_user_file.return_value = mock_creds

            result = authenticate_gmail(str(credentials_path), str(tokens_path))

            assert result == mock_creds
            mock_creds.refresh.assert_called_once()

    @patch("src.newsletter.gmail_client.build")
    @patch("src.newsletter.gmail_client.InstalledAppFlow")
    @patch("src.newsletter.gmail_client.Credentials")
    def test_authenticate_gmail_initiates_oauth_flow_when_no_token(
        self, mock_credentials_class, mock_flow_class, mock_build
    ):
        """Test authentication initiates OAuth flow when no token exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            credentials_path = Path(tmpdir) / "credentials.json"
            tokens_path = Path(tmpdir) / "tokens.json"

            # Create mock credentials file
            credentials_data = {
                "installed": {
                    "client_id": "test_client_id",
                    "client_secret": "test_secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            with open(credentials_path, "w") as f:
                json.dump(credentials_data, f)

            # Mock flow
            mock_creds = Mock(spec=Credentials)
            mock_creds.to_json.return_value = '{"token": "new_token"}'
            mock_flow = Mock()
            mock_flow.run_local_server.return_value = mock_creds
            mock_flow_class.from_client_secrets_file.return_value = mock_flow

            result = authenticate_gmail(str(credentials_path), str(tokens_path))

            assert result is not None
            mock_flow.run_local_server.assert_called_once()


class TestCollectEmails:
    """Tests for collect_emails() function."""

    @patch("src.newsletter.gmail_client.build")
    def test_collect_emails_filters_by_sender(self, mock_build):
        """Test collect_emails filters emails by sender addresses."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock messages list
        mock_messages = MagicMock()
        mock_messages.list.return_value.execute.return_value = {
            "messages": [
                {"id": "msg1"},
                {"id": "msg2"},
            ]
        }
        mock_service.users.return_value.messages.return_value = mock_messages

        # Mock individual message gets
        def mock_get(userId, id, format):
            if id == "msg1":
                return Mock(
                    execute=Mock(
                        return_value={
                            "id": "msg1",
                            "payload": {
                                "headers": [
                                    {"name": "From", "value": "sender1@example.com"},
                                    {"name": "Subject", "value": "Test 1"},
                                ],
                                "body": {"data": ""},
                            },
                        }
                    )
                )
            elif id == "msg2":
                return Mock(
                    execute=Mock(
                        return_value={
                            "id": "msg2",
                            "payload": {
                                "headers": [
                                    {"name": "From", "value": "sender2@example.com"},
                                    {"name": "Subject", "value": "Test 2"},
                                ],
                                "body": {"data": ""},
                            },
                        }
                    )
                )

        mock_messages.get = mock_get

        # Mock credentials
        mock_creds = Mock(spec=Credentials)

        # Test filtering
        sender_emails = ["sender1@example.com"]
        processed_ids = set()

        result = collect_emails(mock_creds, sender_emails, processed_ids)

        # Should only return emails from sender1@example.com
        assert len(result) == 1
        assert result[0]["message_id"] == "msg1"
        assert result[0]["sender"] == "sender1@example.com"

    @patch("src.newsletter.gmail_client.build")
    def test_collect_emails_excludes_processed_ids(self, mock_build):
        """Test collect_emails excludes already processed message IDs."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock messages list
        mock_messages = MagicMock()
        mock_messages.list.return_value.execute.return_value = {
            "messages": [
                {"id": "msg1"},
                {"id": "msg2"},
            ]
        }
        mock_service.users.return_value.messages.return_value = mock_messages

        # Mock individual message gets
        def mock_get(userId, id, format):
            return Mock(
                execute=Mock(
                    return_value={
                        "id": id,
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "sender1@example.com"},
                                {"name": "Subject", "value": f"Test {id}"},
                            ],
                            "body": {"data": ""},
                        },
                    }
                )
            )

        mock_messages.get = mock_get

        # Mock credentials
        mock_creds = Mock(spec=Credentials)

        # Test exclusion
        sender_emails = ["sender1@example.com"]
        processed_ids = {"msg1"}  # msg1 already processed

        result = collect_emails(mock_creds, sender_emails, processed_ids)

        # Should only return msg2 (msg1 is excluded)
        assert len(result) == 1
        assert result[0]["message_id"] == "msg2"

    @patch("src.newsletter.gmail_client.build")
    def test_collect_emails_returns_empty_list_when_no_matches(self, mock_build):
        """Test collect_emails returns empty list when no emails match."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock empty messages list
        mock_messages = MagicMock()
        mock_messages.list.return_value.execute.return_value = {"messages": []}
        mock_service.users.return_value.messages.return_value = mock_messages

        # Mock credentials
        mock_creds = Mock(spec=Credentials)

        sender_emails = ["sender1@example.com"]
        processed_ids = set()

        result = collect_emails(mock_creds, sender_emails, processed_ids)

        assert result == []
