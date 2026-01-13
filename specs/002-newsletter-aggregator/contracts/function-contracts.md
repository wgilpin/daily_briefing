# Function Contracts: Newsletter Aggregator

**Date**: 2024-12-30  
**Feature**: Newsletter Aggregator

## Overview

This document defines the contracts (signatures, inputs, outputs, side effects) for core functions in the newsletter aggregator application. These contracts guide implementation and testing.

## Gmail Client Functions

### `authenticate_gmail(credentials_path: str) -> Credentials`

Authenticate with Gmail API using OAuth 2.0.

**Inputs**:
- `credentials_path`: Path to `credentials.json` file containing OAuth client credentials

**Outputs**:
- `Credentials`: Google auth credentials object (from google-auth library)

**Side Effects**:
- Opens browser for OAuth flow if tokens don't exist
- Creates/updates `data/tokens.json` with refresh token
- May raise `google.auth.exceptions.RefreshError` if authentication fails

**Preconditions**:
- `credentials.json` file exists and is valid
- User has network access to Google OAuth servers

**Postconditions**:
- Valid credentials returned (can be used for Gmail API calls)
- Tokens stored locally for future use

---

### `collect_emails(credentials: Credentials, sender_emails: list[str], processed_ids: set[str]) -> list[dict]`

Collect emails from Gmail for specified senders.

**Inputs**:
- `credentials`: Authenticated Gmail credentials
- `sender_emails`: List of sender email addresses to collect from
- `processed_ids`: Set of message IDs already processed (to avoid duplicates)

**Outputs**:
- `list[dict]`: List of email dictionaries with keys: `message_id`, `sender`, `subject`, `date`, `body_html`, `body_text`, `headers`

**Side Effects**:
- Makes Gmail API calls
- No file writes (caller handles storage)

**Preconditions**:
- `credentials` is valid and authenticated
- `sender_emails` is non-empty list
- Network access to Gmail API

**Postconditions**:
- Returns only emails from specified senders
- Returns only emails not in `processed_ids`
- All returned emails have required fields populated

---

## Email Processing Functions

### `convert_to_markdown(email: dict) -> str`

Convert email content (HTML or plain text) to markdown format.

**Inputs**:
- `email`: Dictionary with `body_html` and/or `body_text` keys

**Outputs**:
- `str`: Markdown-formatted content

**Side Effects**:
- None (pure function)

**Preconditions**:
- `email` contains at least one of `body_html` or `body_text`
- If `body_html` present, it's valid HTML

**Postconditions**:
- Output is valid markdown
- Links, headings, lists preserved from HTML
- Plain text formatted with appropriate line breaks

---

### `parse_newsletter(markdown_content: str, prompt: str, llm_client) -> list[dict]`

Parse newsletter markdown using LLM with configurable prompt.

**Inputs**:
- `markdown_content`: Markdown text of newsletter
- `prompt`: Prompt template for LLM (includes instructions for extraction)
- `llm_client`: LLM API client (OpenAI-compatible interface)

**Outputs**:
- `list[dict]`: List of parsed items, each with keys: `date`, `title`, `summary`, `link` (link optional)

**Side Effects**:
- Makes LLM API call
- May raise API errors if LLM call fails

**Preconditions**:
- `markdown_content` is non-empty string
- `prompt` is non-empty string
- `llm_client` is configured with API key
- Network access to LLM API

**Postconditions**:
- Returns list (may be empty if no items found, or multiple if newsletter has multiple articles)
- Each item has at least `title` field
- `date`, `summary`, `link` may be None/empty if not found

---

### `consolidate_newsletters(parsed_items: list[dict], prompt: str, llm_client) -> str`

Generate consolidated newsletter from parsed items using LLM.

**Inputs**:
- `parsed_items`: List of parsed newsletter items (from multiple sources)
- `prompt`: Consolidation prompt template
- `llm_client`: LLM API client

**Outputs**:
- `str`: Consolidated newsletter in markdown format

**Side Effects**:
- Makes LLM API call
- May raise API errors if LLM call fails

**Preconditions**:
- `parsed_items` is non-empty list
- `prompt` is non-empty string
- `llm_client` is configured

**Postconditions**:
- Returns markdown string suitable for reading
- Content is well-formatted with headings and sections
- All items from input are represented in output

---

## Storage Functions

### `save_email(email: dict, data_dir: str) -> str`

Save email to file system.

**Inputs**:
- `email`: Email dictionary (from `collect_emails`)
- `data_dir`: Base data directory path (e.g., `data/emails`)

**Outputs**:
- `str`: Path to saved file

**Side Effects**:
- Creates file `{data_dir}/{message_id}.json`
- Writes email as JSON

**Preconditions**:
- `email` has `message_id` key
- `data_dir` directory exists or can be created
- Write permissions on `data_dir`

**Postconditions**:
- File created with email data as JSON
- File path returned

---

### `track_email_processed(db_path: str, message_id: str, sender_email: str, status: str) -> None`

Record email in database as processed.

**Inputs**:
- `db_path`: Path to SQLite database
- `message_id`: Gmail message ID
- `sender_email`: Sender email address
- `status`: Processing status ('collected', 'converted', 'parsed', 'failed')

**Outputs**:
- `None`

**Side Effects**:
- Inserts or updates record in `processed_emails` table
- Creates database/table if doesn't exist

**Preconditions**:
- `message_id` is non-empty
- `status` is valid status string
- Write permissions on `db_path` directory

**Postconditions**:
- Record exists in database with given values
- `collected_at` timestamp set if new record

---

### `get_processed_message_ids(db_path: str, sender_emails: list[str] = None) -> set[str]`

Get set of already-processed message IDs.

**Inputs**:
- `db_path`: Path to SQLite database
- `sender_emails`: Optional list to filter by sender

**Outputs**:
- `set[str]`: Set of message IDs

**Side Effects**:
- Queries database (read-only)

**Preconditions**:
- Database exists (or returns empty set if doesn't exist)

**Postconditions**:
- Returns set of message IDs (empty if none found)
- Filtered by sender if `sender_emails` provided

---

### `apply_retention_policy(db_path: str, data_dirs: list[str], retention_limit: int) -> int`

Remove oldest records to maintain retention limit.

**Inputs**:
- `db_path`: Path to SQLite database
- `data_dirs`: List of data directories to clean (`['data/emails', 'data/markdown', 'data/parsed']`)
- `retention_limit`: Maximum number of records to keep

**Outputs**:
- `int`: Number of records deleted

**Side Effects**:
- Deletes database records
- Deletes files from `data_dirs`
- Updates database

**Preconditions**:
- `retention_limit` > 0
- Write permissions on database and data directories

**Postconditions**:
- Only `retention_limit` most recent records remain
- Corresponding files deleted
- Returns count of deleted records

---

## Configuration Functions

### `load_config(config_path: str) -> dict`

Load configuration from JSON file.

**Inputs**:
- `config_path`: Path to `config/senders.json`

**Outputs**:
- `dict`: Configuration dictionary with keys: `senders`, `consolidation_prompt`, `retention_limit`

**Side Effects**:
- Reads file (may raise `FileNotFoundError` or `JSONDecodeError`)

**Preconditions**:
- File exists and is valid JSON

**Postconditions**:
- Returns configuration dict with expected structure
- Defaults applied if keys missing (e.g., `retention_limit` defaults to 100)

---

### `save_config(config_path: str, config: dict) -> None`

Save configuration to JSON file.

**Inputs**:
- `config_path`: Path to config file
- `config`: Configuration dictionary

**Outputs**:
- `None`

**Side Effects**:
- Writes/overwrites config file
- Creates directory if needed

**Preconditions**:
- `config` has valid structure
- Write permissions on config directory

**Postconditions**:
- File written with pretty-printed JSON
- All existing configuration preserved (merge behavior)

---

## Flask Route Handlers

### `GET /`

Display main dashboard.

**Inputs**: None (HTTP request)

**Outputs**: HTML page (Jinja2 template)

**Side Effects**: None

**Template**: `templates/index.html`

---

### `POST /collect`

Trigger email collection from Gmail.

**Inputs**: HTTP POST request (no body needed, uses config)

**Outputs**: HTMX response (partial HTML update with status)

**Side Effects**:
- Calls `collect_emails()`
- Saves emails to file system
- Updates database
- May trigger OAuth flow if not authenticated

**Template Update**: Status message in dashboard

---

### `GET /config`

Display configuration page.

**Inputs**: HTTP GET request

**Outputs**: HTML page with current configuration

**Side Effects**: None

**Template**: `templates/config.html`

---

### `POST /config/senders`

Add or update newsletter sender configuration.

**Inputs**: HTTP POST with form data: `sender_email`, `parsing_prompt`

**Outputs**: HTMX response (updated config list)

**Side Effects**:
- Updates `config/senders.json`
- Saves configuration

**Template Update**: Sender list in config page

---

### `POST /config/consolidation`

Update consolidation prompt.

**Inputs**: HTTP POST with form data: `consolidation_prompt`

**Outputs**: HTMX response (success message)

**Side Effects**:
- Updates `config/senders.json`

---

### `POST /process`

Process collected emails (convert + parse).

**Inputs**: HTTP POST request

**Outputs**: HTMX response (status update)

**Side Effects**:
- Converts emails to markdown
- Parses newsletters using configured prompts
- Saves parsed items
- Updates database status

---

### `POST /consolidate`

Generate consolidated newsletter.

**Inputs**: HTTP POST request

**Outputs**: HTMX response (consolidated newsletter content or download link)

**Side Effects**:
- Calls `consolidate_newsletters()`
- Saves output to `data/output/digest_{timestamp}.md`

**Template Update**: Displays consolidated newsletter or download link

---

### `GET /digest/{timestamp}`

Download consolidated newsletter file.

**Inputs**: HTTP GET with timestamp parameter

**Outputs**: Markdown file download

**Side Effects**: None (file read)

---

## Error Handling

All functions should:
- Log errors with appropriate level (ERROR for failures, WARNING for recoverable issues)
- Return meaningful error messages to callers
- Not crash the application (catch and handle exceptions)
- Continue processing other items when one fails (where applicable)

## Testing Contracts

Unit tests should verify:
- Function signatures match contracts
- Preconditions enforced (raise errors if violated)
- Postconditions satisfied (outputs valid, side effects occur)
- Error handling works (exceptions caught and logged)

Integration tests should verify:
- End-to-end flows work (collect → convert → parse → consolidate)
- Database operations succeed
- File system operations succeed
- LLM API calls work (with mocked responses)

