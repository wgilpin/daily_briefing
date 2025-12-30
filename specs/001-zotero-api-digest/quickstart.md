# Quickstart: Zotero API Digest

**Date**: 2024-12-30  
**Feature**: 001-zotero-api-digest

## Prerequisites

- Python 3.13 or higher
- Zotero account with library items
- Zotero API credentials (see Setup below)

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended, if project uses uv)
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

## journalArticle

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

## Next Steps

- Integrate into daily workflow (e.g., cron job, scheduled task)
- Customize markdown formatting (edit `src/zotero/formatter.py`)
- Add additional filters or sorting options
- Extend to other sources (Gmail, Twitter) per PRD roadmap

