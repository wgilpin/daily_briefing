# API Contract: Unified Feed App

**Date**: 2026-01-30
**Feature**: 003-unified-feed-app

## Overview

REST API served by Flask. Uses HTMX for partial page updates. All endpoints return HTML fragments unless otherwise specified.

**Base URL**: `/`

## Page Routes

### GET /

**Description**: Unified feed homepage

**Response**: HTML page with:
- Unified feed (sorted by date, newest first)
- Source filter controls
- Refresh button
- Status indicators per source

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| source | string | all | Filter: `all`, `zotero`, `newsletter` |
| page | int | 1 | Pagination |
| q | string | | Search query |
| days | int | 7 | Date range filter |

### GET /settings

**Description**: Configuration page

**Response**: HTML page with:
- Zotero credentials form
- Newsletter sender configuration
- Global settings (days lookback, page size)

## API Endpoints (HTMX)

### POST /api/refresh

**Description**: Trigger on-demand refresh of all enabled sources

**Response**: HTMX fragment with refresh status

```html
<div id="refresh-status" class="status success">
  <p>Refreshed 12 Zotero items, 8 newsletter items</p>
</div>
```

**Error Response**:
```html
<div id="refresh-status" class="status partial">
  <p>Zotero: 12 items. Newsletter: Failed (rate limited, retrying...)</p>
</div>
```

### GET /api/feed

**Description**: Get feed items (HTMX partial)

**Query Parameters**: Same as GET /

**Response**: HTML fragment with feed items

```html
<div id="feed-items">
  <article class="feed-item" data-source="zotero">
    <span class="source-badge zotero">Zotero</span>
    <h3><a href="...">Paper Title</a></h3>
    <time>2026-01-30</time>
    <p class="summary">Abstract text...</p>
    <p class="metadata">Authors: Smith, Jones</p>
  </article>
  <!-- more items -->
</div>
```

### GET /api/sources

**Description**: Get source status (HTMX partial)

**Response**: HTML fragment with source cards

```html
<div id="source-status">
  <div class="source-card zotero enabled">
    <h4>Zotero</h4>
    <p>Last refresh: 5 min ago</p>
    <p>Items: 42</p>
  </div>
  <div class="source-card newsletter enabled">
    <h4>Newsletters</h4>
    <p>Last refresh: 5 min ago</p>
    <p>Items: 28</p>
  </div>
</div>
```

### POST /api/settings/zotero

**Description**: Update Zotero configuration

**Request Body**: Form data
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| library_id | string | Yes | Zotero library ID |
| days_lookback | int | No | Days to look back (default: 7) |
| include_keywords | string | No | Comma-separated keywords |
| exclude_keywords | string | No | Comma-separated keywords |

**Note**: API key comes from environment variable, not form

**Response**: HTMX fragment with success/error status

### POST /api/settings/newsletter

**Description**: Update newsletter configuration

**Request Body**: Form data
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sender_emails | string | Yes | Comma-separated sender emails |
| parsing_prompt | string | No | Custom LLM prompt |

**Response**: HTMX fragment with success/error status

### POST /api/settings/newsletter/senders

**Description**: Add a newsletter sender

**Request Body**: Form data
| Field | Type | Required |
|-------|------|----------|
| email | string | Yes |
| parsing_prompt | string | No |
| enabled | bool | No |

**Response**: HTMX fragment with updated sender list

### DELETE /api/settings/newsletter/senders/{email}

**Description**: Remove a newsletter sender

**Response**: HTMX fragment with updated sender list

### GET /api/health

**Description**: Health check endpoint for container orchestration

**Response**: JSON
```json
{
  "status": "healthy",
  "database": "connected",
  "sources": {
    "zotero": "configured",
    "newsletter": "configured"
  }
}
```

**Error Response** (HTTP 503):
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Connection refused"
}
```

## Authentication

**None required at application level**. Access control is handled by Coolify platform authentication.

## Error Handling

All API errors return HTML fragments with error status:

```html
<div class="status error">
  <p>Error: {message}</p>
</div>
```

HTTP status codes:
- 200: Success
- 400: Bad request (validation error)
- 500: Internal server error
- 503: Service unavailable (health check failure)

## Rate Limiting

No application-level rate limiting. External API rate limits (Zotero, Gmail, Gemini) handled with exponential backoff per FR-011a.
