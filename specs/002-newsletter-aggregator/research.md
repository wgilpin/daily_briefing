# Research: Newsletter Aggregator

**Date**: 2024-12-30  
**Feature**: Newsletter Aggregator  
**Purpose**: Document technical decisions and research findings for implementation

## Technology Choices

### Web Framework: Flask

**Decision**: Use Flask for the web application framework.

**Rationale**: 
- Simple, lightweight Python web framework
- Minimal boilerplate compared to Django
- Easy to set up local dev server
- Good integration with HTMX
- Aligns with constitution's simplicity principle

**Alternatives Considered**:
- FastAPI: More modern, async support, but adds complexity with async/await patterns throughout
- Django: Too much boilerplate and structure for a simple single-user app
- Bottle: Too minimal, lacks ecosystem support

### Frontend Interactivity: HTMX

**Decision**: Use HTMX for all interactive UI elements.

**Rationale**:
- Enables dynamic updates without writing JavaScript
- Server-side rendering with partial page updates
- Simple form submissions and content swapping
- Minimal JavaScript needed (only for edge cases HTMX can't handle)
- Aligns with constitution's "no complex frameworks" principle

**Alternatives Considered**:
- React/Vue: Too heavy, violates constitution constraints
- Alpine.js: Could work but HTMX is simpler for form-based interactions
- Vanilla JS: Would require more code, HTMX reduces boilerplate

### Email to Markdown Conversion

**Decision**: Use `html2text` library for HTML email conversion, with fallback to plain text handling.

**Rationale**:
- Handles HTML emails (common in newsletters) reliably
- Preserves structure (headings, links, lists)
- Lightweight Python library
- Can handle plain text emails as well

**Alternatives Considered**:
- `markdownify`: Similar functionality, `html2text` has better maintenance
- Manual HTML parsing: Too complex, reinventing the wheel
- `beautifulsoup4` + custom conversion: More flexible but more code

### LLM Integration for Parsing

**Decision**: Use OpenAI API (or compatible API) for prompt-based parsing.

**Rationale**:
- Standard REST API, easy to integrate
- Good prompt engineering support
- Can extract structured data (JSON) from prompts
- Local alternatives (Ollama) can be swapped in if needed

**Alternatives Considered**:
- LangChain: Adds unnecessary abstraction layer (violates constitution)
- Local LLM (Ollama): Could work but requires local model setup
- Custom regex parsing: Too brittle for varied newsletter formats

### Data Storage

**Decision**: 
- SQLite database for tracking processed emails (message IDs, timestamps)
- JSON files for configuration (senders, prompts, retention settings)
- File system for emails, markdown files, parsed data

**Rationale**:
- SQLite is simple, file-based, no server needed
- Perfect for single-user local app
- JSON files are human-readable for configuration
- File system storage is straightforward for emails/markdown
- No ORM needed (raw SQL is simple enough)

**Alternatives Considered**:
- PostgreSQL: Overkill for single-user local app
- All JSON files: Would work but SQLite better for querying processed emails
- ORM (SQLAlchemy): Adds complexity, violates minimal boilerplate principle

### Gmail API Integration

**Decision**: Use `google-api-python-client` and `google-auth` libraries.

**Rationale**:
- Official Google libraries
- Handles OAuth 2.0 flow automatically
- Token refresh built-in
- Well-documented and maintained

**Alternatives Considered**:
- Custom OAuth implementation: Too complex, security risk
- Other email providers: Out of scope for MVP

## Architecture Patterns

### Function-Based Over Classes

**Decision**: Prefer functions over classes unless stateful behavior is needed.

**Rationale**: Aligns with constitution's simplicity principle. Classes only for:
- Gmail client (needs to maintain OAuth tokens)
- Storage manager (needs database connection)

**Example**: `parse_newsletter(markdown_content, prompt)` as function, not `NewsletterParser` class.

### Server-Side Rendering

**Decision**: All HTML rendered server-side with Jinja2 templates, HTMX for updates.

**Rationale**:
- Simpler than client-side rendering
- Better for SEO (not needed but simpler)
- HTMX handles dynamic updates without JS framework

### Error Handling

**Decision**: Log errors, display user-friendly messages, continue processing where possible.

**Rationale**:
- Per spec requirements (FR-014)
- Graceful degradation (skip failed emails, continue with others)
- Logging for debugging without exposing technical details to users

## Implementation Details

### Email Tracking

**Decision**: Use SQLite table with columns: `message_id` (unique), `sender_email`, `processed_at`, `status`.

**Rationale**: 
- Fast lookups to avoid duplicate processing
- Simple schema, no complex relationships
- SQLite handles this easily

### Prompt Storage

**Decision**: Store prompts in JSON config file, one per sender email address.

**Rationale**:
- Human-readable and editable
- Simple structure: `{"sender@example.com": {"parsing_prompt": "..."}, ...}`
- No database needed for config

### Retention Policy

**Decision**: Implement retention as cleanup job that runs after processing, removing oldest records by `processed_at` timestamp.

**Rationale**:
- Simple to implement (SQL DELETE with ORDER BY and LIMIT)
- Runs automatically, no manual intervention
- Applies to all data types (emails, markdown, parsed items)

### LLM Prompt Structure

**Decision**: Use structured prompts that request JSON output for parsed items.

**Rationale**:
- Easier to parse and validate
- Consistent format: `{date, title, summary, link}`
- Can handle multiple items per newsletter in array format

## Open Questions Resolved

1. **How to handle multiple items per newsletter?**
   - LLM prompt will extract array of items, each with {date, title, summary, link}
   - Stored as array in parsed data

2. **How to track processed emails across runs?**
   - SQLite table with message_id (Gmail message ID is unique and stable)
   - Query before collection to filter already-processed emails

3. **Where to store OAuth tokens?**
   - Local file `data/tokens.json` (git-ignored)
   - Refresh handled automatically by google-auth library

4. **How to handle LLM API failures?**
   - Log error, mark newsletter for manual review
   - Continue processing other newsletters
   - Display error in UI with retry option

## Dependencies Summary

```python
# Core web framework
flask>=3.0.0

# Gmail API
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1

# Email to markdown
html2text>=2024.2.26

# LLM API (OpenAI compatible)
openai>=1.0.0  # or anthropic, groq, etc.

# Database
# SQLite included in Python stdlib

# Testing
pytest>=7.4.0
```

## Next Steps

1. Set up Flask application structure
2. Implement Gmail OAuth flow
3. Create email collection logic
4. Implement markdown conversion
5. Build LLM parsing integration
6. Create consolidation logic
7. Build HTMX UI
8. Implement retention policy

