# Quickstart: Unified Feed App

**Date**: 2026-01-30
**Feature**: 003-unified-feed-app

## Local Development

### Prerequisites

- Python 3.13+
- uv (package manager)
- PostgreSQL (local or Docker)
- Zotero account with API key
- Gmail OAuth credentials
- Gemini API key

### 1. Environment Setup

```bash
# Clone and setup
cd daily-briefing
uv sync

# Create .env file
cp .env.example .env
```

Edit `.env`:
```bash
DATABASE_URL=postgresql://localhost:5432/daily_briefing
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
GEMINI_API_KEY=your_gemini_key
ENCRYPTION_KEY=your_32_byte_encryption_key
GOOGLE_CLIENT_ID=your_oauth_client_id
GOOGLE_CLIENT_SECRET=your_oauth_client_secret
```

### 2. Database Setup

```bash
# Start PostgreSQL (if using Docker)
docker run -d --name pg-briefing \
  -e POSTGRES_DB=daily_briefing \
  -e POSTGRES_PASSWORD=dev \
  -p 5432:5432 \
  postgres:16

# Run migrations
uv run python -m src.db.migrate
```

### 3. Run Application

```bash
# Development server
uv run flask --app src.web.app run --debug

# Open http://127.0.0.1:5000
```

### 4. First-time Setup

1. Navigate to Settings page
2. Verify Zotero credentials (from environment)
3. Add newsletter sender emails
4. Click "Refresh Feed" to fetch initial items

## Integration Scenarios

### Scenario 1: View Unified Feed

**Steps**:
1. Open http://localhost:5000
2. View combined feed from Zotero and newsletters
3. Verify source badges on each item

**Expected**:
- Items sorted by date (newest first)
- Clear source indicators (Zotero/Newsletter)
- Title, date, summary visible

### Scenario 2: On-Demand Refresh

**Steps**:
1. Click "Refresh Feed" button
2. Observe loading indicator
3. Wait for completion

**Expected**:
- Loading spinner during refresh
- Status message showing items fetched
- Feed updates with new items

### Scenario 3: Filter by Source

**Steps**:
1. Click "Zotero" filter button
2. Observe feed updates
3. Click "Newsletters" filter
4. Click "All" to reset

**Expected**:
- Feed shows only selected source
- Filter state visible in UI

### Scenario 4: Configure Zotero

**Steps**:
1. Go to Settings
2. Adjust days lookback
3. Add include/exclude keywords
4. Save settings
5. Refresh feed

**Expected**:
- Settings saved successfully
- Next refresh uses new settings

### Scenario 5: Add Newsletter Sender

**Steps**:
1. Go to Settings > Newsletters
2. Enter new sender email
3. Save
4. Refresh feed

**Expected**:
- Sender added to list
- Next refresh includes emails from new sender

### Scenario 6: Partial Failure Recovery

**Steps**:
1. Configure invalid Zotero API key (simulate failure)
2. Click Refresh Feed
3. Observe partial success

**Expected**:
- Newsletter items still load
- Error message for Zotero
- Feed shows available items

## Coolify Deployment

### 1. Create Coolify Application

1. New Application > Docker Compose
2. Connect GitHub repository
3. Set build context to repository root

### 2. Configure Environment

In Coolify dashboard, add environment variables:
- `DATABASE_URL` (from Coolify PostgreSQL)
- `ZOTERO_LIBRARY_ID`
- `ZOTERO_API_KEY`
- `GEMINI_API_KEY`
- `ENCRYPTION_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

### 3. Configure Coolify Auth

1. Enable "Protected" in Coolify settings
2. Configure allowed users/emails
3. App is now protected by platform auth

### 4. Deploy

```bash
git push origin main
# Coolify auto-deploys on push
```

### 5. Verify

1. Access app URL (requires Coolify login)
2. Check /api/health returns healthy
3. Verify feed loads

## Troubleshooting

### Database Connection Failed

```
Error: Connection refused to PostgreSQL
```

**Solution**: Check DATABASE_URL, ensure PostgreSQL is running

### Zotero API Error

```
Error: Invalid Zotero credentials
```

**Solution**: Verify ZOTERO_LIBRARY_ID and ZOTERO_API_KEY in environment

### Gmail OAuth Failed

```
Error: Gmail authentication failed
```

**Solution**: Re-authenticate via Settings page, check OAuth credentials

### Rate Limited

```
Error: 429 RESOURCE_EXHAUSTED
```

**Solution**: Wait for retry (automatic exponential backoff). If persistent, reduce newsletter sender count or increase refresh interval.
