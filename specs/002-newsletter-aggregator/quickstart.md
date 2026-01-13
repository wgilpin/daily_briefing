# Quickstart: Newsletter Aggregator

**Date**: 2024-12-30  
**Feature**: Newsletter Aggregator

## Prerequisites

- Python 3.13+
- Gmail account with newsletter subscriptions
- Google Cloud Project with Gmail API enabled
- OAuth 2.0 credentials (Desktop application type)
- Google Gemini API key (GEMINI_API_KEY)

## Initial Setup

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask>=3.0.0
pip install google-api-python-client>=2.100.0
pip install google-auth>=2.23.0
pip install google-auth-oauthlib>=1.1.0
pip install google-auth-httplib2>=0.1.1
pip install html2text>=2024.2.26
pip install google-genai>=0.2.0  # Google Gemini API client
```

Or use `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Set Up Gmail OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Desktop application" as application type
6. Download credentials as `credentials.json`
7. Place `credentials.json` in `config/` directory

### 3. Configure Google Gemini API

Set environment variable for Gemini API key:

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a `.env` file in the project root:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

Or export as environment variable:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 4. Create Directory Structure

```bash
mkdir -p data/emails data/markdown data/parsed data/output
mkdir -p config
mkdir -p src/newsletter src/web/templates src/web/static src/utils
mkdir -p tests/unit tests/integration
```

### 5. Initialize Database

The database will be created automatically on first run, but you can verify structure:

```python
# Run once to create schema
from src.newsletter.storage import init_database
init_database('data/newsletter_aggregator.db')
```

## Running the Application

### Start Development Server

```bash
# From project root
export FLASK_APP=src/web/app.py
export FLASK_ENV=development
flask run

# Or with Python
python -m src.web.app
```

The application will be available at `http://localhost:5000`

### First-Time Authentication

1. Open `http://localhost:5000` in browser
2. Click "Connect Gmail" or similar button
3. Browser will open for OAuth flow
4. Sign in with Google account
5. Grant Gmail API permissions
6. Redirected back to application
7. Tokens saved in `data/tokens.json` (git-ignored)

## Basic Usage

### 1. Configure Newsletter Senders

1. Go to Configuration page (`/config`)
2. Add sender email address (e.g., `newsletter@example.com`)
3. Add parsing prompt for that sender:
   ```
   Extract articles from this newsletter. For each article, provide:
   - Date (if available)
   - Title
   - Summary (2-3 sentences)
   - Link (if available)
   
   Return as JSON array of objects.
   ```
4. Save configuration

### 2. Collect Emails

1. Go to main dashboard (`/`)
2. Click "Collect Emails" button
3. Application will:
   - Authenticate with Gmail (if needed)
   - Query Gmail API for emails from configured senders
   - Download emails not previously processed
   - Save to `data/emails/`
   - Update database tracking

### 3. Process Newsletters

1. Click "Process Newsletters" button
2. Application will:
   - Convert emails to markdown (save to `data/markdown/`)
   - Parse each newsletter using configured prompts
   - Extract structured items (date, title, summary, link)
   - Save parsed items to `data/parsed/` and database

### 4. Generate Consolidated Newsletter

1. Click "Generate Digest" button
2. Application will:
   - Load all parsed items
   - Apply consolidation prompt
   - Generate markdown newsletter
   - Save to `data/output/digest_{timestamp}.md`
   - Display in browser or provide download link

## Configuration

### Default Configuration

Create `config/senders.json`:

```json
{
  "senders": {},
  "consolidation_prompt": "Create a well-formatted newsletter digest from these items. Organize by date, include clear headings, and make it readable.",
  "retention_limit": 100
}
```

### Adding a Sender

Via UI (recommended):
1. Go to `/config`
2. Fill in sender email and parsing prompt
3. Save

Or edit `config/senders.json` directly:
```json
{
  "senders": {
    "newsletter@example.com": {
      "parsing_prompt": "Extract articles...",
      "enabled": true,
      "created_at": "2024-12-30T10:00:00Z"
    }
  }
}
```

## Troubleshooting

### OAuth Authentication Fails

- Verify `credentials.json` is in `config/` directory
- Check that Gmail API is enabled in Google Cloud Console
- Ensure OAuth consent screen is configured
- Delete `data/tokens.json` and re-authenticate

### LLM API Errors

- Verify API key is set in environment variable
- Check API key has sufficient credits/quota
- Verify network connectivity
- Check LLM API status page

### No Emails Collected

- Verify sender email addresses are correct
- Check emails exist in Gmail (not in spam/trash)
- Verify Gmail API permissions granted
- Check database for already-processed emails

### Parsing Fails

- Review parsing prompt (may need adjustment for newsletter format)
- Check markdown conversion quality (view `data/markdown/` files)
- Verify LLM API is responding correctly
- Check logs for error messages

## Development Tips

### Viewing Data

```bash
# View processed emails
sqlite3 data/newsletter_aggregator.db "SELECT * FROM processed_emails;"

# View parsed items
sqlite3 data/newsletter_aggregator.db "SELECT * FROM newsletter_items;"

# View markdown files
cat data/markdown/*.md

# View parsed JSON
cat data/parsed/*.json | jq
```

### Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (with mocked APIs)
pytest tests/integration/

# Run all tests
pytest
```

### Debugging

Enable Flask debug mode:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run
```

View application logs in console output.

## Next Steps

- Customize parsing prompts for your newsletter formats
- Adjust consolidation prompt for desired output style
- Set retention limit based on storage needs
- Schedule regular collection (cron job or similar)

## File Locations

- **Configuration**: `config/senders.json`
- **OAuth Credentials**: `config/credentials.json` (git-ignored)
- **OAuth Tokens**: `data/tokens.json` (git-ignored)
- **Database**: `data/newsletter_aggregator.db`
- **Emails**: `data/emails/*.json`
- **Markdown**: `data/markdown/*.md`
- **Parsed Items**: `data/parsed/*.json`
- **Output**: `data/output/digest_*.md`

