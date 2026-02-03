# Daily Briefing

A unified web application that aggregates content from multiple sources (Zotero research papers and newsletter emails) into a single feed. Designed for deployment to Coolify or other container platforms.

## Features

- **User Authentication**: Secure password-based login to protect your personal feed
- **Unified Feed**: Single view combining items from all configured sources
- **Multiple Sources**:
  - Zotero library additions (research papers)
  - Newsletter emails from Gmail (parsed via LLM)
- **On-Demand Refresh**: Manually trigger content updates from all sources
- **Source Management**: Configure and manage multiple content sources
- **Extensible Architecture**: Easy to add new source types
- **Container-Ready**: Built for deployment to Coolify with PostgreSQL

## Prerequisites

- Python 3.13 or higher
- PostgreSQL database (for production deployment)
- Zotero account with API credentials (optional, for Zotero source)
- Gmail account with OAuth credentials (optional, for newsletter source)
- Google Gemini API key (optional, for newsletter parsing)

## Setup

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database (PostgreSQL for production, optional for local dev)
DATABASE_URL=postgresql://user:pass@localhost:5432/daily_briefing

# Zotero API (optional - only if using Zotero source)
ZOTERO_LIBRARY_ID=your_user_id_here
ZOTERO_API_KEY=your_api_key_here

# Google Gemini API (optional - only if using newsletter source)
GEMINI_API_KEY=your_gemini_api_key_here

# Gmail OAuth (optional - only if using newsletter source)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Encryption key for secure data storage
ENCRYPTION_KEY=your_32_byte_hex_key

# Flask secret key (required for user sessions)
SECRET_KEY=your_secret_key_here
```

**Security Note**: Never commit `.env` to version control.

### 3. Create Your User Account

**IMPORTANT**: Public registration is disabled for security. This is a personal app where all authenticated users share the same feed data.

Create your user account using the CLI tool:

```bash
python create_user.py
```

You'll be prompted for:

- Email address
- Name (optional)
- Password (must be 8+ characters with uppercase, lowercase, and a number)

### 4. Get API Credentials

#### Zotero API Credentials (Optional)

1. Visit [https://www.zotero.org/settings/keys](https://www.zotero.org/settings/keys)
2. Note your **User ID** (shown as "Your userID for use in API calls")
3. Click "Create new private key"
4. Give it a name (e.g., "Daily Briefing")
5. Copy the generated **API Key**

#### Gmail OAuth Credentials (Optional)

1. Follow the [Gmail Setup Guide](docs/gmail_setup.md) to create OAuth credentials
2. Place the downloaded file in `config/credentials.json`

#### Google Gemini API Key (Optional)

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your `.env` file

### 5. Configure Newsletter Senders (Optional)

If using the newsletter source, configure sender email addresses in `config/senders.json`:

```json
{
  "senders": {
    "newsletter@example.com": {
      "parsing_prompt": "Extract the top 3 most important articles...",
      "enabled": true
    }
  },
  "models": {
    "parsing": "gemini-2.5-flash",
    "consolidation": "gemini-2.5-flash"
  }
}
```

## Running Locally

### Start the Application

```bash
# Using uv
uv run flask --app src.web.app run

# Or using Python directly
uv run python -m src.web.app
```

The application will start on `http://127.0.0.1:5000`.

### First-Time Setup

1. Create your user account: `python create_user.py`
2. Open the web UI in your browser
3. Log in with your credentials
4. Navigate to Settings to configure your sources
5. Click "Refresh Feed" to fetch initial content

## Docker Deployment

### Local Development with Docker Compose

```bash
# Copy environment file and configure
cp .env.example .env
# Edit .env with your API keys

# Start services
docker compose up -d

# View logs
docker compose logs -f app

# Stop services
docker compose down
```

The app will be available at `http://localhost:5000`.

### Coolify Deployment

1. **Create a new service** in Coolify:
   - Select "Docker" as the deployment method
   - Point to your repository

2. **Configure environment variables** in Coolify's dashboard:
   - `DATABASE_URL` - PostgreSQL connection string
   - `ZOTERO_LIBRARY_ID` - Your Zotero user ID (optional)
   - `ZOTERO_API_KEY` - Your Zotero API key (optional)
   - `GEMINI_API_KEY` - Google Gemini API key (optional)
   - `ENCRYPTION_KEY` - 32-byte hex encryption key
   - `GOOGLE_CLIENT_ID` - Gmail OAuth client ID (optional)
   - `GOOGLE_CLIENT_SECRET` - Gmail OAuth secret (optional)
   - `SECRET_KEY` - Flask secret key

3. **Add PostgreSQL service**:
   - Create a new PostgreSQL database in Coolify
   - Link it to your application
   - Database migrations run automatically on startup

4. **Deploy**: Coolify will build and deploy the container

## Usage

### Authentication

- All routes require authentication to access your personal feed
- Public registration is disabled for security
- To create additional user accounts, use: `python create_user.py`
- Sessions last 30 days with "Remember Me" enabled

### Viewing the Feed

- Log in to access the web UI
- The main page shows a unified feed of all items from configured sources
- Items are sorted chronologically (most recent first)
- Each item shows its source type, title, date, and summary

### Refreshing Content

- Click the "Refresh Feed" button to fetch latest content from all sources
- The app will:
  - Fetch recent Zotero additions (if configured)
  - Collect and parse new newsletter emails (if configured)
  - Update the feed with new items

### Managing Sources

- Navigate to Settings to:
  - Configure Zotero credentials
  - Add/remove newsletter sender addresses
  - Customize parsing prompts per sender
  - Enable/disable specific sources

### Filtering (Future)

Future versions will support:

- Filter by source type (Zotero only, newsletters only, etc.)
- Search by keyword
- Date range filtering

## API Endpoints

### Authentication Routes

- `GET /auth/login` - Login page
- `POST /auth/login` - Handle login (with brute-force protection)
- `POST /auth/logout` - Logout user
- `GET /auth/register` - Shows "Registration Disabled" message

### Feed Routes (Protected)

- `GET /` - Main feed page (requires login)
- `GET /feed` - Feed view (requires login)
- `GET /api/feed/items` - Get feed items (requires login)
- `POST /api/refresh` - Trigger feed refresh (requires login)
- `GET /api/health` - Health check for monitoring
- `POST /api/settings/zotero` - Configure Zotero source (requires login)
- `POST /api/settings/newsletter` - Configure newsletter source (requires login)

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Project Structure

```text
src/
├── auth/            # User authentication (password hashing, sessions, models)
├── db/              # Database migrations and connection
├── models/          # Data models (FeedItem, etc.)
├── newsletter/      # Newsletter collection and parsing
├── services/        # Business logic (FeedService)
├── sources/         # Source implementations (Zotero, Newsletter)
├── utils/           # Shared utilities
├── web/             # Flask application and routes
└── zotero/          # Zotero API integration

config/              # Configuration files (OAuth credentials, senders)
data/                # Local data storage (SQLite for newsletters)
tests/
├── unit/            # Unit tests
│   └── auth/        # Authentication tests (24 tests)
└── integration/     # Integration tests

create_user.py       # CLI tool to create user accounts
```

### Adding New Sources

To add a new source type:

1. Create a new file in `src/sources/` implementing the `FeedSource` protocol
2. Implement `fetch_items()` method returning `List[FeedItem]`
3. Register the source in `src/services/feed_service.py`

See [specs/003-unified-feed-app/](specs/003-unified-feed-app/) for detailed architecture.

## Troubleshooting

### Authentication Issues

- **Cannot create account via web**: Public registration is disabled. Use `python create_user.py`
- **Login fails**: Check password requirements (8+ chars, uppercase, lowercase, number)
- **Brute-force protection**: Failed logins trigger a 5-second delay
- **Session expired**: Sessions last 30 days. Log in again if expired

### Database Connection Issues

- Verify `DATABASE_URL` is correctly formatted
- Ensure PostgreSQL is running and accessible
- Check database migrations ran successfully (check logs)
- Database includes users, sessions, and password_reset_tokens tables

### Zotero Source Not Working

- Verify `ZOTERO_LIBRARY_ID` and `ZOTERO_API_KEY` are set
- Test credentials at [https://www.zotero.org/settings/keys](https://www.zotero.org/settings/keys)
- Check network connectivity to Zotero API

### Newsletter Source Not Working

- Ensure `GEMINI_API_KEY` is set in environment
- Verify `config/credentials.json` exists for Gmail OAuth
- Check `config/senders.json` has at least one enabled sender
- Monitor Gemini API quota limits

### "No items found"

- Ensure at least one source is configured
- Try clicking "Refresh Feed" to fetch new content
- Check that sources have recent content available

## Specifications

See the `specs/` directory for detailed feature specifications:

- [001-zotero-digest](specs/001-zotero-digest/) - Original Zotero CLI tool (deprecated)
- [002-newsletter-aggregator](specs/002-newsletter-aggregator/) - Newsletter collection (integrated)
- [003-unified-feed-app](specs/003-unified-feed-app/) - Current unified application

## License

[Add your license here]
