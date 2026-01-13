# Daily Briefing

A collection of tools for generating personalized daily briefings from multiple sources.

## Features

### 1. Zotero API Digest

A CLI application that generates markdown digests of recent Zotero library additions, helping you stay up-to-date with your research collection.

### 2. Newsletter Aggregator (In Development)

A web application that collects newsletter emails from Gmail, converts them to markdown, parses them using configurable LLM prompts, and generates a consolidated newsletter digest. All data is stored locally.

## Features

- **Recent Items**: Retrieve items added to your Zotero library within a configurable time window
- **Smart Sorting**: Automatically sorts by publication date and limits to 10 most recent when >10 items found
- **Keyword Filtering**: Include or exclude items based on keywords in titles, abstracts, or tags
- **Markdown Output**: Generates clean, readable markdown files for easy integration into your workflow

## Prerequisites

- Python 3.13 or higher
- For Zotero Digest: Zotero account with library items and API credentials
- For Newsletter Aggregator: Gmail account with OAuth credentials, Google Gemini API key (GEMINI_API_KEY environment variable)

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 2. Zotero Digest Setup

#### Get Zotero API Credentials

1. Visit https://www.zotero.org/settings/keys
2. Note your **User ID** (shown as "Your userID for use in API calls")
3. Click "Create new private key"
4. Give it a name (e.g., "Daily Briefing")
5. Copy the generated **API Key** (you'll only see it once)

#### Configure Credentials

Create a `.env` file in the project root:

```bash
ZOTERO_LIBRARY_ID=your_user_id_here
ZOTERO_API_KEY=your_api_key_here
```

**Security Note**: Never commit `.env` to version control. It should already be in `.gitignore`.

### 3. Newsletter Aggregator Setup

#### Gmail OAuth Credentials

1. Follow the [Gmail Setup Guide](docs/gmail_setup.md) to create and download OAuth credentials
2. Place the downloaded file in `config/credentials.json`:
   ```bash
   # If you downloaded a file with a different name, rename it:
   mv config/client_secret_*.json config/credentials.json
   ```

#### Google Gemini API Key

The Newsletter Aggregator uses Google Gemini for LLM-based parsing and consolidation.

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your `.env` file:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

#### Starting the Application

Start the Flask web server:

```bash
# Using the startup script (recommended)
./start_emails.sh

# Or using uv directly
uv run flask --app src.web.app run

# Or using Python directly
uv run python -m src.web.app
```

The application will start on `http://127.0.0.1:5000`. Open this URL in your browser.

**First-time authentication**: When you first try to collect emails, the app will open your browser for Gmail OAuth authentication. Sign in and grant permissions to allow the app to read your emails.

#### Initial Configuration

1. **Configure Newsletter Senders**:
   - Navigate to the "Configuration" page in the web UI
   - Add sender email addresses (e.g., `newsletter@example.com`)
   - Optionally customize parsing prompts per sender
   - Set retention limit (default: 100 records)

2. **Configure Models** (if needed):
   - Edit `config/senders.json` to change default models:
     ```json
     {
       "models": {
         "parsing": "gemini-2.5-flash",
         "consolidation": "gemini-2.5-flash"
       }
     }
     ```

See `specs/002-newsletter-aggregator/` for detailed specifications.

## Usage

### Zotero Digest

### Basic Usage

Generate a digest of items added in the last 24 hours:

```bash
python -m src.cli.main
```

This creates `digest.md` in the current directory.

#### Custom Time Range

Generate digest for items added in the last 7 days:

```bash
python -m src.cli.main --days 7
```

#### Custom Output Path

Save digest to a specific location:

```bash
python -m src.cli.main --output ~/Documents/zotero-digest.md
```

#### Keyword Filtering

Include only items matching keywords:

```bash
python -m src.cli.main --include "machine learning" "neural networks"
```

Exclude items matching keywords:

```bash
python -m src.cli.main --exclude "review" "survey"
```

Combine filters:

```bash
python -m src.cli.main --include "AI" --exclude "review" --days 3
```

#### Help

View all available options:

```bash
python -m src.cli.main --help
```

### Newsletter Aggregator

The Newsletter Aggregator provides a complete workflow for processing newsletters:

1. **Collect Emails**: Retrieves newsletters from Gmail based on configured sender addresses
2. **Convert to Markdown**: Converts email content (HTML/text) to standardized markdown format
3. **Parse Newsletters**: Uses LLM (Gemini) to extract structured items (title, date, summary, link) from newsletters
4. **Consolidate**: Generates a single consolidated newsletter digest from all parsed items

#### Workflow

1. **Configure Senders**: Add newsletter sender email addresses in the Configuration page
2. **Collect Emails**: Click "Collect Emails" to retrieve newsletters from Gmail
3. **Process Emails**: Click "Process Emails" to convert and parse newsletters
4. **Consolidate**: Click "Consolidate Newsletter" to generate the final digest

#### Features

- **Parallel Processing**: Processes multiple newsletters concurrently for faster parsing
- **Configurable Prompts**: Customize parsing prompts per sender for better extraction
- **Retention Policy**: Automatically cleans up old records based on configurable limit
- **Status Indicators**: Dashboard shows counts of processed emails, parsed items, and more
- **Error Handling**: Graceful error handling with clear user feedback

#### Troubleshooting

**"Failed to create LLM client"**: Ensure `GEMINI_API_KEY` is set in your `.env` file

**"No senders configured"**: Add at least one sender email address in the Configuration page

**"Gmail authentication failed"**: Check that `config/credentials.json` exists and is valid. Re-authenticate if needed.

**"429 RESOURCE_EXHAUSTED"**: You've hit Gemini API rate limits. The app uses `gemini-2.5-flash` by default for higher quotas. You can adjust `max_workers` in `config/senders.json` to reduce parallel requests.

## Zotero Digest Output Format

The generated markdown file contains:

1. **Header**: Title with generation date and time range
2. **Sections**: Items organized by type (journal articles, books, etc.)
3. **Item Details**: For each item:
   - Title (as header)
   - Authors
   - Publication date
   - Venue (journal/conference name)
   - Abstract (if available)
   - URL (if available)

### Example Output

```markdown
# Zotero Digest - 2024-12-30

Generated: 2024-12-30 14:30:00  
Time Range: Last 1 day(s)  
Items Found: 5

## Journal Article

### Deep Learning for Natural Language Processing
**Authors**: Smith, John; Doe, Jane  
**Published**: 2024-12-15  
**Venue**: Journal of AI Research  
**Abstract**: This paper presents...  
**URL**: https://example.com/paper

...
```

## Zotero Digest Behavior

### Item Selection

- **Default**: Items added in the last 24 hours
- **If ≤10 items**: All items included
- **If >10 items**: Sorted by publication date, only 10 most recently published included
- **Missing dates**: Items without publication dates sorted to end

### Filtering

- **Include keywords**: Case-insensitive, matches in title, abstract, or tags
- **Exclude keywords**: Takes precedence over include filters
- **Empty filters**: No filtering applied (all items included)

## Zotero Digest Troubleshooting

### "Missing required environment variables"

**Problem**: Credentials not found in `.env` or environment.

**Solution**: 
1. Check `.env` file exists in project root
2. Verify `ZOTERO_LIBRARY_ID` and `ZOTERO_API_KEY` are set
3. Ensure no extra spaces or quotes around values

### "Invalid Zotero API credentials"

**Problem**: API key or library ID is incorrect.

**Solution**:
1. Verify credentials at https://www.zotero.org/settings/keys
2. Regenerate API key if needed
3. Ensure you're using your personal library ID (not a group ID)

### "Failed to connect to Zotero API"

**Problem**: Network issue or Zotero API is down.

**Solution**:
1. Check internet connection
2. Visit https://www.zotero.org to verify service status
3. Retry after a few minutes

### "No items found"

**Problem**: No items were added in the specified time range.

**Solution**:
- Try increasing `--days` value
- Verify items exist in your Zotero library
- Check that items have `dateAdded` timestamps

## Success Criteria Validation

The following success criteria are validated as part of the implementation:

- **SC-001 (Performance)**: Digest generation completes in <30 seconds for up to 100 items (validated via manual timing)
- **SC-002 (Setup Time)**: Initial setup takes <5 minutes (validated via user testing)
- **SC-003 (Markdown Rendering)**: Generated markdown renders correctly in common viewers (validated via visual inspection)
- **SC-004 (Item Count)**: Correct item count displayed in digest header (validated via automated tests)
- **SC-005 (Error Messages)**: Clear error messages for common failure scenarios (validated via manual testing)

See the [Success Criteria Validation Checklist](#success-criteria-validation-checklist) below for detailed validation steps.

## Zotero Digest Success Criteria Validation Checklist

Use this checklist to verify all success criteria are met:

### SC-001: Performance
- [ ] Run digest generation with 100 items
- [ ] Verify completion time is <30 seconds
- [ ] Document timing results

### SC-002: Setup Time
- [ ] Follow setup instructions from scratch
- [ ] Verify total setup time is <5 minutes
- [ ] Document any blockers or delays

### SC-003: Markdown Rendering
- [ ] Generate a sample digest
- [ ] Open in GitHub/GitLab viewer
- [ ] Open in VS Code markdown preview
- [ ] Verify all formatting renders correctly
- [ ] Check special characters are escaped properly

### SC-004: Item Count
- [ ] Run with known number of items
- [ ] Verify count in header matches actual items
- [ ] Run automated tests: `uv run pytest tests/`

### SC-005: Error Messages
- [ ] Test with missing `.env` file
- [ ] Test with invalid API credentials
- [ ] Test with network disconnected
- [ ] Verify all error messages are clear and actionable

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Project Structure

```
src/
├── cli/           # Command-line interface (Zotero digest)
├── newsletter/    # Newsletter aggregator core logic (in development)
├── web/           # Flask web application (in development)
├── zotero/        # Zotero API integration
│   ├── client.py  # API client wrapper
│   ├── filters.py # Filtering and sorting logic
│   ├── formatter.py # Markdown generation
│   └── types.py   # Type definitions
└── utils/         # Shared utilities and configuration

data/              # Local data storage (newsletter aggregator)
config/            # Configuration files (OAuth credentials, etc.)
tests/
├── unit/          # Unit tests
└── integration/   # Integration tests
```

## Next Steps

- Complete Newsletter Aggregator implementation (see `specs/002-newsletter-aggregator/`)
- Integrate into daily workflow (e.g., cron job, scheduled task)
- Customize markdown formatting (edit `src/zotero/formatter.py`)
- Add additional filters or sorting options

## License

[Add your license here]





