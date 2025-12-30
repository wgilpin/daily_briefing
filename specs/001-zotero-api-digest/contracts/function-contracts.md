# Function Contracts: Zotero API Digest

**Date**: 2024-12-30  
**Feature**: 001-zotero-api-digest

## Core Functions

### `fetch_recent_items(client: Zotero, days: int) -> list[dict]`

**Purpose**: Retrieve library items added within the specified time window.

**Parameters**:
- `client` (Zotero): Initialized pyzotero client instance
- `days` (int): Number of days to look back (must be > 0)

**Returns**: `list[dict]` - List of Zotero API item dictionaries

**Behavior**:
- Calculates cutoff timestamp: `datetime.now() - timedelta(days=days)`
- Calls `client.items(since=iso_timestamp)`
- Returns all items added since cutoff
- Raises `ValueError` if `days <= 0`
- Raises `ConnectionError` on network failures
- Raises `AuthenticationError` on invalid credentials

**Preconditions**:
- `client` must be initialized with valid credentials
- `days` must be positive integer

**Postconditions**:
- Returned list contains only items with `dateAdded >= cutoff`
- Items are in API response order (not sorted)

---

### `sort_and_limit_items(items: list[dict], limit: int = 10) -> list[dict]`

**Purpose**: Sort items by publication date and limit to N most recent.

**Parameters**:
- `items` (list[dict]): List of Zotero item dictionaries
- `limit` (int, optional): Maximum items to return (default: 10)

**Returns**: `list[dict]` - Sorted and limited list of items

**Behavior**:
- If `len(items) <= limit`: Returns all items (no sorting needed)
- If `len(items) > limit`:
  - Sorts by `item['data'].get('date', '')` descending (most recent first)
  - Items without publication date sorted to end
  - Returns first `limit` items
- Handles missing/invalid dates gracefully

**Preconditions**:
- `items` is a list (may be empty)
- `limit` must be positive integer

**Postconditions**:
- Returned list length <= `limit`
- Items with dates come before items without dates
- Items with dates are sorted newest to oldest

---

### `filter_by_keywords(items: list[dict], include: list[str], exclude: list[str]) -> list[dict]`

**Purpose**: Filter items by keyword matching in title, abstract, and tags.

**Parameters**:
- `items` (list[dict]): List of Zotero item dictionaries
- `include` (list[str]): Keywords that must be present (empty = no filter)
- `exclude` (list[str]): Keywords that must be absent (empty = no filter)

**Returns**: `list[dict]` - Filtered list of items

**Behavior**:
- Case-insensitive substring matching
- Searches in: `title`, `abstractNote`, and tag names
- Exclusion takes precedence: items matching exclude keywords are removed first
- Then inclusion filter applied: items must match at least one include keyword (if provided)
- Empty `include` list means include all (after exclusions)
- Empty `exclude` list means no exclusions

**Preconditions**:
- `items` is a list (may be empty)
- `include` and `exclude` are lists of strings (may be empty)

**Postconditions**:
- Returned items satisfy inclusion criteria (if any)
- Returned items do not match exclusion criteria
- Original item order preserved (filtering only, no sorting)

---

### `format_item_markdown(item: dict) -> str`

**Purpose**: Convert a Zotero item to markdown format.

**Parameters**:
- `item` (dict): Zotero API item dictionary

**Returns**: `str` - Markdown-formatted string for the item

**Behavior**:
- Formats as `###` header with title
- Includes authors as comma-separated "LastName, FirstName"
- Includes publication date, venue, abstract (if available)
- Includes URL as markdown link
- Handles missing fields gracefully (omits or shows "N/A")
- Escapes special markdown characters in content

**Preconditions**:
- `item` is a valid Zotero API item dictionary
- `item['data']` exists

**Postconditions**:
- Returned string is valid markdown
- All user-visible content is properly escaped

---

### `generate_digest(items: list[dict], days: int) -> str`

**Purpose**: Generate complete markdown digest from items.

**Parameters**:
- `items` (list[dict]): List of Zotero item dictionaries (already filtered/sorted)
- `days` (int): Time window used for filtering

**Returns**: `str` - Complete markdown document

**Behavior**:
- Creates `#` header with title and generation date
- Groups items by `itemType` into sections
- Each section uses `##` header for item type
- Items within section formatted with `format_item_markdown()`
- If no items: returns message "No items found in the last {days} day(s)."

**Preconditions**:
- `items` is a list (may be empty)
- `days` is positive integer

**Postconditions**:
- Returned string is complete, valid markdown document
- Items are organized hierarchically by type

---

### `load_configuration() -> Configuration`

**Purpose**: Load configuration from environment variables and CLI arguments.

**Parameters**: None (reads from environment and sys.argv)

**Returns**: `Configuration` object (see data-model.md)

**Behavior**:
- Loads `.env` file if present (via python-dotenv)
- Reads `ZOTERO_LIBRARY_ID` and `ZOTERO_API_KEY` from environment
- Parses CLI arguments: `--output`, `--days`, `--include`, `--exclude`, `--help`
- Validates required fields (library_id, api_key)
- Raises `ValueError` with helpful message if credentials missing

**Preconditions**:
- `.env` file exists or environment variables are set
- CLI arguments are valid (argparse handles validation)

**Postconditions**:
- Returned Configuration has all required fields populated
- Optional fields have defaults or None

---

### `write_digest(content: str, output_path: str) -> None`

**Purpose**: Write digest content to markdown file.

**Parameters**:
- `content` (str): Markdown content to write
- `output_path` (str): File path (may include directory)

**Returns**: `None`

**Behavior**:
- Creates output directory if it doesn't exist
- Writes content to file (overwrites if exists)
- Uses UTF-8 encoding
- Raises `IOError` if file cannot be written

**Preconditions**:
- `content` is a string (may be empty)
- `output_path` is a valid file path string

**Postconditions**:
- File exists at `output_path` with `content`
- Directory structure created if needed

---

## Error Handling Contracts

### `AuthenticationError`
- **Raised by**: `fetch_recent_items()` when API key is invalid
- **Message**: "Invalid Zotero API credentials. Check your ZOTERO_LIBRARY_ID and ZOTERO_API_KEY."
- **Recovery**: User must update credentials and retry

### `ConnectionError`
- **Raised by**: `fetch_recent_items()` when network request fails
- **Message**: "Failed to connect to Zotero API. Check your internet connection and try again."
- **Recovery**: User can retry after network issue resolved

### `ValueError`
- **Raised by**: Various functions for invalid input
- **Message**: Descriptive message explaining what's wrong and how to fix
- **Recovery**: User corrects input and retries

### `IOError`
- **Raised by**: `write_digest()` when file cannot be written
- **Message**: "Failed to write digest file: {error details}"
- **Recovery**: User checks file permissions and path validity

