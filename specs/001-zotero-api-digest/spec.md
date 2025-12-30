# Feature Specification: Zotero API Digest

**Feature Branch**: `001-zotero-api-digest`  
**Created**: 2024-12-30  
**Status**: Draft  
**Input**: User description: "Build skeleton app for Zotero API integration outputting markdown digest"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fetch Recent Zotero Library Additions (Priority: P1)

As a researcher, I want to retrieve my recent Zotero library additions so that I can see what new papers and resources have been added to my collection in a consolidated view.

**Why this priority**: This is the core functionality - without fetching data from Zotero, no digest can be generated. This represents the minimum viable product.

**Independent Test**: Can be fully tested by running the application with valid Zotero credentials and verifying that library items are retrieved and displayed.

**Acceptance Scenarios**:

1. **Given** valid Zotero API credentials are configured, **When** I run the application, **Then** I see a list of my recent library additions from the past 24 hours
2. **Given** valid Zotero API credentials are configured, **When** I specify a custom time range (e.g., last 7 days), **Then** I see library additions from that specified period
3. **Given** no new items exist in the specified time range, **When** I run the application, **Then** I receive a message indicating no new items were found
4. **Given** more than 10 items were added in the time range, **When** the application processes them, **Then** items are sorted by publication date (most recent first) and only the 10 most recently published items are included in the digest
5. **Given** 10 or fewer items were added in the time range, **When** the application processes them, **Then** all items are included in the digest regardless of publication date

---

### User Story 2 - Generate Markdown Digest Output (Priority: P1)

As a researcher, I want my Zotero library additions formatted as a readable markdown file so that I can review them in my preferred markdown viewer or editor.

**Why this priority**: Markdown output is the specified delivery format and essential for the digest to be usable. Without it, the fetched data has no consumable format.

**Independent Test**: Can be fully tested by running the application and verifying a properly formatted markdown file is generated in the specified output location.

**Acceptance Scenarios**:

1. **Given** library items have been fetched, **When** the digest is generated, **Then** a markdown file is created with hierarchical organization by item type (articles, books, etc.)
2. **Given** library items have been fetched, **When** the digest is generated, **Then** each item includes title, authors, publication date, and abstract (if available)
3. **Given** the output file already exists, **When** a new digest is generated, **Then** the file is overwritten with fresh content

---

### User Story 3 - Configure Application via Command Line (Priority: P2)

As a user, I want to configure the application through command-line arguments so that I can customize the digest without editing configuration files.

**Why this priority**: Command-line configuration enables flexible usage and scripting, but the application can function with sensible defaults without this.

**Independent Test**: Can be fully tested by running the application with various command-line arguments and verifying behavior changes accordingly.

**Acceptance Scenarios**:

1. **Given** I run the application with `--output <path>`, **When** the digest is generated, **Then** the markdown file is saved to the specified path
2. **Given** I run the application with `--days <number>`, **When** fetching items, **Then** only items from the last N days are included
3. **Given** I run the application with `--help`, **When** executed, **Then** I see a list of all available options and their descriptions

---

### User Story 4 - Filter Content by Keywords (Priority: P3)

As a researcher, I want to filter my digest by keywords so that I can focus on topics relevant to my current interests.

**Why this priority**: Filtering enhances usability but is not required for basic functionality. The digest is still valuable without filtering.

**Independent Test**: Can be fully tested by running the application with keyword filters and verifying only matching items appear in the output.

**Acceptance Scenarios**:

1. **Given** I specify include keywords via `--include <keywords>`, **When** the digest is generated, **Then** only items containing those keywords in title, abstract, or tags are included
2. **Given** I specify exclude keywords via `--exclude <keywords>`, **When** the digest is generated, **Then** items containing those keywords are omitted
3. **Given** both include and exclude keywords are specified, **When** the digest is generated, **Then** exclusions take precedence over inclusions

---

### Edge Cases

- What happens when Zotero API credentials are missing or invalid?
  - System displays a clear error message with instructions on how to configure credentials
- What happens when the Zotero API is unreachable (network issues)?
  - System displays a connection error with retry suggestion
- What happens when a library item has missing metadata (no abstract, no authors)?
  - System gracefully handles missing fields, displaying "N/A" or omitting the field
- What happens when library items lack publication dates?
  - Items without publication dates are sorted to the end (after items with dates) when applying the 10-item limit
- What happens when the output directory doesn't exist?
  - System creates the directory or displays an error with guidance

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate with the Zotero API using user-provided API key and user ID
- **FR-002**: System MUST retrieve library items added within a configurable time window (default: 24 hours), and if more than 10 items are found, MUST sort them by publication date and process only the 10 most recently published items
- **FR-003**: System MUST sort items by publication date (most recent first) when applying the 10-item limit, with items lacking publication dates sorted to the end
- **FR-004**: System MUST support fetching items from user's personal library
- **FR-005**: System MUST generate a markdown file containing fetched library items
- **FR-006**: System MUST organize digest content hierarchically by item type (journal articles, books, conference papers, etc.)
- **FR-007**: System MUST display item metadata including: title, authors, publication date, publication venue, abstract (when available), and item URL
- **FR-008**: System MUST accept configuration via command-line arguments for: output path, time range, and keyword filters
- **FR-009**: System MUST support keyword-based filtering for both inclusion and exclusion
- **FR-010**: System MUST provide meaningful error messages for authentication failures, network errors, and configuration issues
- **FR-011**: System MUST handle items with incomplete metadata gracefully without crashing

### Key Entities

- **Library Item**: A bibliographic entry in the user's Zotero library (title, authors, abstract, publication date, item type, tags, URL)
- **Digest**: The generated markdown document containing formatted library items organized by type
- **Configuration**: User settings including API credentials, time range, output path, and filter keywords

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a complete digest of their recent Zotero additions in under 30 seconds for libraries with up to 100 items
- **SC-002**: Users can configure and run the application successfully within 5 minutes of initial setup
- **SC-003**: Generated markdown files render correctly in standard markdown viewers (GitHub, VS Code, Obsidian)
- **SC-004**: When 10 or fewer items are found, 100% appear in the digest; when more than 10 items are found, the 10 most recently published items appear (prioritizing recency over addition order)
- **SC-005**: Error messages enable users to self-diagnose and resolve common issues (missing credentials, network errors) without external documentation

## Assumptions

- User has an existing Zotero account with library items
- User can obtain their Zotero API key and user ID from zotero.org/settings/keys
- User has network access to the Zotero API (api.zotero.org)
- The application runs on-demand rather than as a scheduled service (scheduling is out of scope for MVP)
- Group libraries are out of scope for MVP; only personal libraries are supported
- Credential storage follows environment variable or configuration file patterns (not embedded in code)
