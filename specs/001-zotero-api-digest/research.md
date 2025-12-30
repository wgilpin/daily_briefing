# Research: Zotero API Digest

**Date**: 2024-12-30  
**Feature**: 001-zotero-api-digest

## Research Questions

### 1. Zotero API Authentication & Access Patterns

**Question**: How to authenticate and retrieve recent items from Zotero API?

**Decision**: Use pyzotero library with API key and user ID from environment variables.

**Rationale**:
- pyzotero is already a project dependency (pyproject.toml)
- Provides clean Python interface to Zotero Web API
- Handles rate limiting and pagination automatically
- Supports filtering by date using `since` parameter

**Alternatives Considered**:
- Direct HTTP requests to Zotero API: More boilerplate, manual rate limiting
- OAuth flow: Unnecessary complexity for personal library access (API key sufficient)

**Implementation Notes**:
- Initialize client: `zotero.Zotero(library_id, 'user', api_key)`
- Fetch recent items: `zot.items(since=iso_timestamp)`
- Library type is 'user' for personal libraries (group libraries out of scope)

---

### 2. Date Filtering and Sorting Logic

**Question**: How to filter by addition date and sort by publication date?

**Decision**: 
- Filter items by `dateAdded` field (when item was added to library)
- Sort filtered results by `date` field (publication date) descending
- Items without publication date sorted to end

**Rationale**:
- Zotero API items include both `dateAdded` (when added) and `date` (publication date)
- Filtering by addition date ensures we only process recent additions
- Sorting by publication date prioritizes latest research when batch imports occur
- Missing dates handled gracefully by sorting to end

**Alternatives Considered**:
- Sort by addition date only: Doesn't prioritize recent publications in batch imports
- Require publication date: Too restrictive, many items may lack dates

**Implementation Notes**:
- Use `item['data'].get('dateAdded', '')` for filtering
- Use `item['data'].get('date', '')` for sorting
- Parse dates as ISO strings, handle missing dates by placing at end of sorted list

---

### 3. Markdown Formatting Structure

**Question**: What markdown structure best organizes bibliographic items?

**Decision**: Hierarchical organization by item type, with consistent metadata fields.

**Rationale**:
- Grouping by type (journalArticle, book, conferencePaper, etc.) provides logical organization
- Consistent field order (title, authors, date, venue, abstract, URL) improves readability
- Markdown headers (#, ##) create clear hierarchy
- Compatible with standard markdown viewers (GitHub, VS Code, Obsidian)

**Alternatives Considered**:
- Chronological only: Less useful for researchers who think in terms of publication types
- Flat list: Loses organizational benefits
- HTML output: More complex, markdown sufficient per PRD

**Implementation Notes**:
- Use `#` for main title, `##` for item type sections, `###` for individual items
- Format authors as "LastName, FirstName" comma-separated list
- Include abstract if available, otherwise omit field
- Use markdown links for URLs: `[text](url)`

---

### 4. Keyword Filtering Implementation

**Question**: How to implement include/exclude keyword filtering efficiently?

**Decision**: Case-insensitive substring matching across title, abstract, and tags fields.

**Rationale**:
- Simple substring matching sufficient for MVP (no complex NLP needed)
- Case-insensitive improves usability
- Searching multiple fields (title, abstract, tags) provides comprehensive coverage
- Exclusion takes precedence over inclusion (per spec acceptance scenario)

**Alternatives Considered**:
- Regex matching: More powerful but adds complexity, not needed for MVP
- Full-text search with ranking: Overkill for simple keyword filtering
- Tag-only filtering: Too restrictive, users may want to filter by content

**Implementation Notes**:
- Normalize all text to lowercase for comparison
- Search in: `item['data'].get('title', '')`, `item['data'].get('abstractNote', '')`, and tag names
- Apply exclusion filters first, then inclusion filters
- Empty filter lists mean no filtering (include all)

---

### 5. Error Handling Patterns

**Question**: How to handle API errors and missing data gracefully?

**Decision**: Provide clear, actionable error messages with guidance for common issues.

**Rationale**:
- Users need to self-diagnose issues per SC-005
- Common issues: missing credentials, network errors, invalid API keys
- Graceful degradation: continue processing other items if one fails

**Alternatives Considered**:
- Silent failures: Poor UX, users can't diagnose issues
- Generic error messages: Not actionable
- Retry logic: Adds complexity, not needed for MVP (users can re-run)

**Implementation Notes**:
- Validate credentials at startup with clear instructions if missing
- Catch network exceptions and suggest retry
- Handle missing metadata fields by omitting or showing "N/A"
- Log errors but don't crash on individual item failures

---

### 6. Command-Line Interface Design

**Question**: What CLI argument structure best supports the requirements?

**Decision**: Use argparse with positional/optional arguments for configuration.

**Rationale**:
- stdlib argparse sufficient (no external dependencies)
- Supports both required (credentials) and optional (filters, output path) arguments
- `--help` flag provides built-in documentation
- Follows Unix CLI conventions

**Alternatives Considered**:
- Click library: More features but adds dependency, not needed
- Config file: Adds complexity, CLI args sufficient for MVP
- Environment-only config: Less flexible, users may want per-run customization

**Implementation Notes**:
- Required: API credentials (from env vars, not CLI args for security)
- Optional: `--output <path>`, `--days <N>`, `--include <keywords>`, `--exclude <keywords>`, `--help`
- Defaults: output to `digest.md`, days=1 (24 hours), no filters

---

## Technology Decisions Summary

| Component | Choice | Rationale |
|-----------|--------|-----------|
| API Client | pyzotero | Existing dependency, clean interface |
| CLI Framework | argparse (stdlib) | No dependencies, sufficient for needs |
| Date Handling | ISO string parsing | Zotero API uses ISO format |
| Markdown | Manual formatting | Simple, no dependencies needed |
| Config | Environment variables + CLI args | Secure (creds in env), flexible (args) |
| Error Handling | Try/except with clear messages | Simple, actionable |

## Dependencies

- **pyzotero**: Already in pyproject.toml (>=1.7.6)
- **python-dotenv**: Already in pyproject.toml (>=1.0.0)
- **tqdm**: Already in pyproject.toml (>=4.66.0) - for progress bars if needed
- **argparse**: Python stdlib (no installation needed)
- **pytest**: For unit tests (add to dev dependencies)

## Open Questions Resolved

All technical questions resolved. No NEEDS CLARIFICATION markers remain.

