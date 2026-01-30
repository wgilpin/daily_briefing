# Feature Specification: Unified Feed App

**Feature Branch**: `003-unified-feed-app`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "join the two apps together into a single web-based app. The zotero app and the newsletter app. There should be a single app, single UI, and on demand it reads zotero and the newsleteers to produce a single feed"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Unified Feed (Priority: P1)

A user opens the web application and sees a consolidated feed that combines recent items from both Zotero library additions and parsed newsletter content, sorted chronologically, displayed in a clean readable format.

**Why this priority**: This is the core value proposition - providing a single view of content from multiple sources. Without this, there's no unified app.

**Independent Test**: Can be fully tested by opening the web UI after setting up credentials for both Zotero and Gmail, then verifying that items from both sources appear in a single feed.

**Acceptance Scenarios**:

1. **Given** user has configured Zotero credentials and Gmail OAuth, **When** user visits the home page, **Then** they see a unified feed showing items from both Zotero (recent papers) and newsletters (parsed articles)
2. **Given** the unified feed is displayed, **When** user reviews the items, **Then** each item shows source indicator (Zotero or Newsletter), title, date, and summary
3. **Given** multiple items exist from both sources, **When** feed is rendered, **Then** items are sorted by date (most recent first) regardless of source

---

### User Story 2 - Refresh Feed On-Demand (Priority: P1)

A user can manually trigger a refresh to fetch the latest content from both Zotero and newsletters without restarting the application or navigating away.

**Why this priority**: On-demand updates are explicitly requested and essential for getting current data without background scheduling complexity.

**Independent Test**: Can be tested by clicking a "Refresh" button and observing that the feed updates with newly added Zotero items or recently collected newsletters.

**Acceptance Scenarios**:

1. **Given** user is viewing the unified feed, **When** user clicks "Refresh Feed" button, **Then** system fetches latest items from Zotero API and processes any new newsletters from Gmail
2. **Given** refresh is triggered, **When** new items are found in either source, **Then** feed updates to display the new items without page reload
3. **Given** refresh is in progress, **When** user is waiting, **Then** system shows loading indicator and completion status

---

### User Story 3 - Configure Data Sources (Priority: P2)

A user can configure connection settings for both Zotero and Gmail/newsletter sources through a single settings interface, managing API credentials and filtering preferences in one place.

**Why this priority**: Centralized configuration improves user experience, but basic feed viewing is more critical for MVP.

**Independent Test**: Can be tested by accessing settings page, entering credentials for both services, saving, and verifying that feed can subsequently fetch data from configured sources.

**Acceptance Scenarios**:

1. **Given** user navigates to Settings page, **When** viewing configuration options, **Then** user sees sections for both Zotero credentials (Library ID, API Key) and Gmail OAuth setup
2. **Given** user enters Zotero credentials, **When** credentials are saved, **Then** system validates credentials and confirms successful connection
3. **Given** user configures newsletter sender addresses, **When** settings are saved, **Then** those senders are used for filtering emails during feed refresh

---

### User Story 4 - Filter and Search Feed (Priority: P3)

A user can filter the unified feed by source (Zotero only, Newsletters only, or both), search by keyword, and apply date range filters to narrow down content.

**Why this priority**: Filtering enhances usability but isn't required for basic functionality. Users can still get value from unfiltered feed.

**Independent Test**: Can be tested by applying various filters (source, keyword, date) and verifying feed updates to show only matching items.

**Acceptance Scenarios**:

1. **Given** unified feed is displayed, **When** user selects "Zotero only" filter, **Then** feed shows only items from Zotero library
2. **Given** feed contains items with various keywords, **When** user enters search term, **Then** feed filters to show only items with matching titles or summaries
3. **Given** user applies date range filter, **When** filter is set to "Last 7 days", **Then** feed shows only items from past week

---

### Edge Cases

- What happens when Zotero API credentials are invalid but Gmail OAuth is valid? (Show partial feed with newsletter items only, display error message for Zotero)
- What happens when no items are available from either source? (Display empty state message: "No items found. Try refreshing or adjusting your time range.")
- What happens when feed refresh times out due to slow API responses? (Display timeout error, show last successfully loaded feed with timestamp)
- What happens when user has many items (100+) from both sources? (Apply pagination with configurable page size, default 50 items per page)
- What happens when newsletter parsing fails for some emails? (Show successfully parsed items, log failed emails with error details accessible via status page)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a unified feed combining Zotero library items and parsed newsletter content in a single chronological view
- **FR-002**: System MUST provide on-demand refresh capability that fetches latest data from both Zotero API and Gmail without automatic background scheduling
- **FR-003**: System MUST indicate the source (Zotero or Newsletter) for each item in the unified feed
- **FR-004**: System MUST retrieve Zotero items added within a configurable time window (default: last 7 days)
- **FR-005**: System MUST use existing newsletter aggregator workflow (collect emails → convert to markdown → parse with LLM → extract items)
- **FR-006**: System MUST sort unified feed items by date in descending order (newest first)
- **FR-007**: System MUST preserve existing Zotero keyword filtering capabilities (include/exclude keywords)
- **FR-008**: System MUST preserve existing newsletter sender configuration and parsing prompt customization
- **FR-009**: System MUST handle authentication for both services (Zotero API key, Gmail OAuth) through unified settings interface
- **FR-010**: System MUST display item details including: title, date, summary/abstract, source identifier, and link (when available)
- **FR-011**: System MUST handle partial failures gracefully (e.g., if Zotero API fails, still show newsletter items)
- **FR-012**: System MUST persist newsletter data locally as per existing storage implementation
- **FR-013**: Users MUST be able to navigate between unified feed view and settings/configuration pages
- **FR-014**: System MUST provide visual feedback during refresh operations (loading indicators, progress updates)
- **FR-015**: System MUST support filtering feed by source type (Zotero only, newsletters only, or both)

### Key Entities

- **Unified Feed Item**: Represents a single entry in the consolidated feed, with attributes: title, date, summary, source type (Zotero/Newsletter), item ID, link (optional), authors (Zotero items), sender (newsletter items)
- **Feed Source**: Configuration entity representing either Zotero or Newsletter source, with attributes: source type, enabled status, last refresh timestamp, error status
- **Application Settings**: Central configuration containing Zotero credentials (Library ID, API Key), newsletter sender addresses, time window for Zotero items, keyword filters, retention policies

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view a unified feed combining both Zotero and newsletter items within 3 seconds of page load
- **SC-002**: Feed refresh completes within 60 seconds for up to 50 Zotero items and 20 newsletters
- **SC-003**: Users can successfully configure both data sources through a single settings interface in under 5 minutes
- **SC-004**: System successfully handles partial failures, displaying available content when one source is unavailable
- **SC-005**: 90% of feed refresh operations complete without errors when credentials are valid and services are available
- **SC-006**: Users can identify the source of each feed item at a glance (clear visual indicators)
- **SC-007**: Feed displays correctly on standard web browsers (Chrome, Firefox, Safari, Edge) without layout issues
- **SC-008**: All existing Zotero digest features remain functional (keyword filtering, date ranges, item sorting)
- **SC-009**: All existing newsletter aggregator features remain functional (sender configuration, custom prompts, parallel processing)
