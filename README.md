# Daily Briefing - Zotero API Digest

A CLI application that generates markdown digests of recent Zotero library additions, helping you stay up-to-date with your research collection.

## Features

- **Recent Items**: Retrieve items added to your Zotero library within a configurable time window
- **Smart Sorting**: Automatically sorts by publication date and limits to 10 most recent when >10 items found
- **Keyword Filtering**: Include or exclude items based on keywords in titles, abstracts, or tags
- **Markdown Output**: Generates clean, readable markdown files for easy integration into your workflow

## Prerequisites

- Python 3.13 or higher
- Zotero account with library items
- Zotero API credentials (see Setup below)

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 2. Get Zotero API Credentials

1. Visit https://www.zotero.org/settings/keys
2. Note your **User ID** (shown as "Your userID for use in API calls")
3. Click "Create new private key"
4. Give it a name (e.g., "Daily Briefing")
5. Copy the generated **API Key** (you'll only see it once)

### 3. Configure Credentials

Create a `.env` file in the project root:

```bash
ZOTERO_LIBRARY_ID=your_user_id_here
ZOTERO_API_KEY=your_api_key_here
```

**Security Note**: Never commit `.env` to version control. It should already be in `.gitignore`.

Alternatively, you can copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### Basic Usage

Generate a digest of items added in the last 24 hours:

```bash
python -m src.cli.main
```

This creates `digest.md` in the current directory.

### Custom Time Range

Generate digest for items added in the last 7 days:

```bash
python -m src.cli.main --days 7
```

### Custom Output Path

Save digest to a specific location:

```bash
python -m src.cli.main --output ~/Documents/zotero-digest.md
```

### Keyword Filtering

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

### Help

View all available options:

```bash
python -m src.cli.main --help
```

## Output Format

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

## Behavior

### Item Selection

- **Default**: Items added in the last 24 hours
- **If ≤10 items**: All items included
- **If >10 items**: Sorted by publication date, only 10 most recently published included
- **Missing dates**: Items without publication dates sorted to end

### Filtering

- **Include keywords**: Case-insensitive, matches in title, abstract, or tags
- **Exclude keywords**: Takes precedence over include filters
- **Empty filters**: No filtering applied (all items included)

## Troubleshooting

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

## Success Criteria Validation Checklist

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
├── cli/           # Command-line interface
├── zotero/        # Zotero API integration
│   ├── client.py  # API client wrapper
│   ├── filters.py # Filtering and sorting logic
│   ├── formatter.py # Markdown generation
│   └── types.py   # Type definitions
└── utils/         # Configuration management
```

## Next Steps

- Integrate into daily workflow (e.g., cron job, scheduled task)
- Customize markdown formatting (edit `src/zotero/formatter.py`)
- Add additional filters or sorting options
- Extend to other sources (Gmail, Twitter) per PRD roadmap

## License

[Add your license here]





