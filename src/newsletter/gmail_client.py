"""Gmail API client for newsletter aggregator."""

import base64
import json
import logging
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authenticate_gmail(
    credentials_path: str, tokens_path: str = "data/tokens.json"
) -> Credentials:
    """
    Authenticate with Gmail API using OAuth 2.0.

    Handles OAuth 2.0 flow, token storage, and automatic token refresh.
    If tokens exist and are valid, uses them. Otherwise, initiates OAuth flow.

    Args:
        credentials_path: Path to credentials.json file containing OAuth client credentials
        tokens_path: Path to tokens.json file for storing user tokens (default: data/tokens.json)

    Returns:
        Credentials: Google auth credentials object (from google-auth library)

    Side Effects:
        - Opens browser for OAuth flow if tokens don't exist
        - Creates/updates tokens_path with refresh token
        - May raise RefreshError if authentication fails

    Raises:
        FileNotFoundError: If credentials_path doesn't exist
        RefreshError: If token refresh fails and re-authentication is needed
    """
    tokens_path_obj = Path(tokens_path)
    credentials_path_obj = Path(credentials_path)

    if not credentials_path_obj.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_path}\n"
            "Please download credentials.json from Google Cloud Console and place it in config/ directory."
        )

    creds = None

    # Load existing tokens if available
    if tokens_path_obj.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(tokens_path_obj), SCOPES)
        except (ValueError, json.JSONDecodeError):
            # Invalid token file, will need to re-authenticate
            creds = None

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Try to refresh the token
            try:
                creds.refresh(Request())
            except RefreshError:
                # Refresh failed, need to re-authenticate
                creds = None

        if not creds:
            # Start OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path_obj), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        tokens_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(tokens_path_obj, "w") as token:
            token.write(creds.to_json())

    return creds


def collect_emails(
    credentials: Credentials,
    sender_emails: list[str],
    processed_ids: set[str],
    days_lookback: int = 30,
    max_per_sender: int = 1,
) -> list[dict]:
    """
    Collect emails from Gmail for specified senders.

    Queries Gmail API for emails from specified senders, excluding already processed emails.
    Limits collection to most recent N emails per sender to reduce LLM processing costs.

    Args:
        credentials: Authenticated Gmail credentials
        sender_emails: List of sender email addresses to collect from
        processed_ids: Set of message IDs already processed (to avoid duplicates)
        days_lookback: Number of days to look back for emails (default: 30)
        max_per_sender: Maximum emails to collect per sender (default: 1)

    Returns:
        list[dict]: List of email dictionaries with keys:
            - message_id: Gmail message ID
            - sender: Sender email address
            - subject: Email subject line
            - date: Email date (ISO format)
            - body_html: HTML body content (if available)
            - body_text: Plain text body content (if available)
            - headers: Dictionary of email headers

    Side Effects:
        - Makes Gmail API calls
        - No file writes (caller handles storage)

    Raises:
        Exception: If Gmail API calls fail
    """
    if not sender_emails:
        return []

    # Build Gmail service
    service = build("gmail", "v1", credentials=credentials)

    # Calculate date for lookback filter
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days_lookback)
    date_filter = cutoff_date.strftime("%Y/%m/%d")

    # Collect emails per sender to enforce max_per_sender limit
    all_emails = []
    sender_counts = {email.lower(): 0 for email in sender_emails}

    # Query each sender separately to get most recent emails per sender
    for sender_email in sender_emails:
        query = f"from:{sender_email} after:{date_filter}"

        # Get list of messages for this sender
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_per_sender)
            .execute()
        )

        messages = results.get("messages", [])

        for msg in messages:
            message_id = msg["id"]

            # Skip if already processed
            if message_id in processed_ids:
                continue

            try:
                # Get full message
                message = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message_id, format="full")
                    .execute()
                )

                # Extract headers
                headers = {}
                payload = message.get("payload", {})
                for header in payload.get("headers", []):
                    headers[header["name"].lower()] = header["value"]

                # Extract sender from headers
                from_header = headers.get("from", "")

                # Extract email from "Name <email@example.com>" format or plain email
                actual_sender = from_header
                if "<" in from_header:
                    # Extract email from "Name <email@example.com>"
                    actual_sender = from_header.split("<")[1].split(">")[0].strip()
                else:
                    # Plain email address
                    actual_sender = from_header.strip()

                # Extract body content
                body_html = None
                body_text = None

                # Handle multipart messages
                if "parts" in payload:
                    for part in payload["parts"]:
                        mime_type = part.get("mimeType", "")
                        body_data = part.get("body", {}).get("data", "")

                        if mime_type == "text/html" and body_data:
                            body_html = base64.urlsafe_b64decode(body_data).decode("utf-8")
                        elif mime_type == "text/plain" and body_data:
                            body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")
                else:
                    # Single part message
                    mime_type = payload.get("mimeType", "")
                    body_data = payload.get("body", {}).get("data", "")
                    if mime_type == "text/html" and body_data:
                        body_html = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    elif mime_type == "text/plain" and body_data:
                        body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")

                # Build email dict
                email_dict = {
                    "message_id": message_id,
                    "sender": actual_sender,
                    "subject": headers.get("subject", ""),
                    "date": headers.get("date", ""),
                    "body_html": body_html,
                    "body_text": body_text,
                    "headers": headers,
                }

                all_emails.append(email_dict)

            except Exception as e:
                # Log error but continue with other emails
                logger.error(f"Error processing message {message_id}: {e}")
                continue

    return all_emails
