# Feature Specification: Unified Feed App

**Feature Branch**: `003-unified-feed-app`
**Created**: 2026-01-20
**Status**: Ready
**Input**: User description: "join the two apps together into a single web-based app. The zotero app and the newsletter app. There should be a single app, single UI, and on demand it reads zotero and the newsletters to produce a single feed. Integrate into a minimal single app, allowing for the fact additional source types will be added later. The app will be deployed to a Coolify instance."

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

### User Story 5 - Extensible Source Architecture (Priority: P2)

The system is designed so that new content source types can be added in the future without requiring changes to the core feed display, filtering, or configuration UI logic.

**Why this priority**: Extensibility is a stated requirement to allow future source types. Building this into the architecture from the start avoids costly refactoring later.

**Independent Test**: Can be verified by reviewing architecture documentation to confirm new sources can be added by implementing a defined interface, without modifying core feed rendering or filtering code.

**Acceptance Scenarios**:

1. **Given** the system architecture, **When** a developer wants to add a new source type, **Then** they can do so by implementing a standard source interface without modifying existing source implementations
2. **Given** a new source type is added, **When** items are fetched from the new source, **Then** they appear in the unified feed alongside existing sources with consistent formatting
3. **Given** a new source type is configured, **When** user views settings, **Then** the new source appears in the configuration UI with its specific settings

---

### User Story 6 - Container Deployment (Priority: P2)

The application can be deployed to a Coolify instance (or similar container platform) with configuration managed through environment variables.

**Why this priority**: Deployment to Coolify is a stated requirement. The app must be containerized and configurable via environment for production use.

**Independent Test**: Can be verified by building a container image and deploying to Coolify, confirming the app starts and functions correctly with environment-based configuration.

**Acceptance Scenarios**:

1. **Given** the application codebase, **When** a container image is built, **Then** the image contains all dependencies and can run the application
2. **Given** a deployed container, **When** environment variables are set for credentials and configuration, **Then** the application uses those values without requiring file-based configuration
3. **Given** the application is running on Coolify, **When** user accesses the web UI, **Then** all features work as expected (feed viewing, refresh, configuration)

---

### Edge Cases

- What happens when Zotero API credentials are invalid but Gmail OAuth is valid? (Show partial feed with newsletter items only, display error message for Zotero)
- What happens when no items are available from either source? (Display empty state message: "No items found. Try refreshing or adjusting your time range.")
- What happens when feed refresh times out due to slow API responses? (Display timeout error, show last successfully loaded feed with timestamp)
- What happens when user has many items (100+) from both sources? (Apply pagination with configurable page size, default 50 items per page)
- What happens when newsletter parsing fails for some emails? (Show successfully parsed items, log failed emails with error details accessible via status page)
- What happens when a new source type fails during refresh but others succeed? (Apply same partial failure handling - show items from successful sources, display error for failed source)
- What happens when required environment variables are missing at startup? (Application fails to start with clear error message indicating which variables are missing)
- What happens when container storage is ephemeral? (All data persisted in PostgreSQL; container can be fully stateless)
- What happens when API rate limits are hit? (System retries with exponential backoff; after max retries, shows partial results with rate limit warning)
- What happens when PostgreSQL connection fails? (Application fails to start with clear error; health check reports unhealthy)

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
- **FR-011a**: System MUST implement automatic retry with exponential backoff when encountering API rate limits (429 errors)
- **FR-012**: System MUST persist all data (feed items, OAuth tokens, configuration) in PostgreSQL database
- **FR-013**: Users MUST be able to navigate between unified feed view and settings/configuration pages
- **FR-014**: System MUST provide visual feedback during refresh operations (loading indicators, progress updates)
- **FR-015**: System MUST support filtering feed by source type (Zotero only, newsletters only, or both)

#### Extensibility Requirements

- **FR-016**: System MUST define a standard interface for content sources that new source types can implement
- **FR-017**: System MUST allow new source types to be added without modifying core feed display, sorting, or filtering logic
- **FR-018**: System MUST support source-specific configuration options that integrate into the unified settings interface
- **FR-019**: System MUST normalize items from all source types into a common feed item format for consistent display

#### Deployment Requirements

- **FR-020**: System MUST be deployable as a container image compatible with Coolify and similar platforms
- **FR-021**: System MUST support configuration via environment variables for all credentials and key settings (Zotero API key, Gmail OAuth, Gemini API key, PostgreSQL connection string)
- **FR-022**: System MUST connect to Coolify-managed PostgreSQL instance for all persistent storage (no local SQLite or file-based storage)
- **FR-023**: System MUST provide health check endpoint for container orchestration
- **FR-024**: System MUST fail fast with clear error messages when required configuration is missing

#### Observability Requirements

- **FR-025**: System MUST output structured logs to stdout for container-native log aggregation
- **FR-026**: Logs MUST include timestamp, level, source, and contextual message for debugging

#### Access Model

- **FR-027**: System is designed as a single-user personal tool; no in-app user accounts, login screens, or multi-tenancy required (access control handled at platform level by Coolify)

### Key Entities

- **Unified Feed Item**: Represents a single entry in the consolidated feed, with attributes: title, date, summary, source type identifier, item ID, link (optional), and source-specific metadata (e.g., authors for Zotero, sender for newsletters)
- **Feed Source**: Abstract entity representing any content source, with attributes: source type identifier, display name, enabled status, last refresh timestamp, error status, source-specific configuration
- **Source Configuration**: Per-source settings (e.g., Zotero: Library ID, API Key, keyword filters; Newsletter: sender addresses, parsing prompts; Future sources: their specific settings)
- **Application Settings**: Central configuration containing global settings (time window defaults, pagination), deployment configuration (from environment variables), and references to configured sources

## Out of Scope

The following features are explicitly excluded from this version:

- **Sharing/Collaboration**: No ability to share feeds or items with other users
- **Data Export**: No export functionality (CSV, PDF, etc.) for feed items
- **Mobile App**: Web-only; no native mobile application
- **Scheduled Refresh**: No automatic/background refresh; on-demand only
- **AI Feed Summarization**: No LLM-generated summaries of the overall feed (newsletter parsing remains)

## Clarifications

### Session 2026-01-30

- Q: Is this single-user or multi-user? → A: Single-user only (personal tool, no user accounts)
- Q: What observability strategy? → A: Structured logs to stdout only (container-native)
- Q: How to handle API rate limits? → A: Automatic retry with exponential backoff
- Q: How to handle Zotero item caching/persistence? → A: Use Coolify PostgreSQL for all persistence (Zotero items, newsletter items, OAuth tokens, configuration)
- Q: What is explicitly out of scope? → A: Sharing/collaboration, data export, mobile app, scheduled/automatic refresh, AI summarization of feed
- Q: How is access control handled? → A: Coolify platform-level authentication (no in-app user management)

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

#### Extensibility Outcomes

- **SC-010**: A new source type can be added by implementing a defined interface without modifying existing source code
- **SC-011**: Items from any source type display consistently in the unified feed with source identification
- **SC-012**: Source-specific configuration integrates into the settings UI without custom UI code per source

#### Deployment Outcomes

- **SC-013**: Application successfully deploys to Coolify from a single container image
- **SC-014**: All credentials and configuration can be set via environment variables (no manual file editing required post-deployment)
- **SC-015**: Application starts within 30 seconds and responds to health checks
- **SC-016**: Data persists across container restarts via PostgreSQL (container is fully stateless)
