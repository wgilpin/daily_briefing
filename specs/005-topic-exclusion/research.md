# Research: Topic Exclusion Filter

**Feature**: 005-topic-exclusion
**Date**: 2026-02-03
**Status**: Phase 0 - Complete

## Research Questions

1. How to implement dynamic list management (add/delete items) using HTMX?
2. Best practices for Flask + HTMX form handling with JSON configuration
3. Prompt engineering patterns for LLM content filtering
4. Configuration validation patterns with Pydantic for JSON files

---

## 1. HTMX Dynamic List Management

### Decision

Use HTMX with `hx-post`, `hx-target`, and `hx-swap` to handle add/delete operations without full page reload. Each list item is a partial template returned by Flask.

### Rationale

- HTMX is already in use in the application (evident from existing partials structure)
- Provides minimal JavaScript, server-side rendering approach (aligns with Flask architecture)
- Simple pattern: POST to add item → return new list item HTML fragment
- DELETE to remove item → return empty response or updated list

### Implementation Pattern

```html
<!-- Add form -->
<form hx-post="/settings/exclusions/add" hx-target="#exclusion-list" hx-swap="beforeend">
  <input type="text" name="topic" maxlength="100" required>
  <button type="submit">Add Topic</button>
</form>

<!-- List container -->
<ul id="exclusion-list">
  <!-- Items loaded here -->
</ul>

<!-- Item template (returned by Flask) -->
<li>
  <span class="topic-text">datasette</span>
  <button hx-delete="/settings/exclusions/delete/0"
          hx-target="closest li"
          hx-swap="outerHTML">
    Remove
  </button>
</li>
```

### Alternatives Considered

- **Full JavaScript SPA**: Rejected - over-engineering for simple list management
- **Traditional form with full page reload**: Rejected - poor UX, not using existing HTMX patterns

---

## 2. Flask + JSON Configuration Handling

### Decision

Create a dedicated configuration module (`src/newsletter/config.py`) with:
- Pydantic models for type-safe config structure
- Load/save functions with file locking for concurrent access
- Validation of exclusion constraints (max 50 topics, 100 chars each)

### Rationale

- Constitution requires strong typing (Pydantic models)
- JSON file is already used for senders.json (existing pattern)
- File-based config is simpler than database for this use case
- Validation ensures constraints before LLM processing

### Implementation Pattern

```python
from pydantic import BaseModel, Field, field_validator

class NewsletterConfig(BaseModel):
    excluded_topics: list[str] = Field(default_factory=list, max_length=50)
    consolidation_prompt: str
    # ... other existing fields

    @field_validator('excluded_topics')
    @classmethod
    def validate_topics(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("Maximum 50 topics allowed")
        for topic in v:
            if len(topic) > 100:
                raise ValueError("Topic must be <= 100 characters")
        return v

def load_config() -> NewsletterConfig:
    """Load config with file locking."""
    ...

def save_config(config: NewsletterConfig) -> None:
    """Save config with atomic write."""
    ...
```

### Alternatives Considered

- **Database storage**: Rejected - over-engineering, adds complexity for simple list
- **Environment variables**: Rejected - not suitable for user-editable lists
- **Separate exclusions.json**: Rejected - clarification confirmed single file (senders.json)

---

## 3. LLM Prompt Engineering for Content Filtering

### Decision

Inject exclusion instructions at the beginning of the consolidation prompt with explicit, high-priority language:

```text
CRITICAL INSTRUCTION - HIGHEST PRIORITY:
You MUST exclude any content related to the following topics:
- datasette
- low-level coding
- SQL internals

Do NOT include these topics in your consolidated output. Skip items that match these topics entirely.

[Original consolidation prompt continues...]
```

### Rationale

- Prompt positioning matters: instructions at start get higher attention
- Explicit language ("CRITICAL", "MUST", "Do NOT") improves compliance
- List format is clear and easy for LLM to parse
- Tested pattern: similar instructions work well in other LLM filtering tasks

### Best Practices Applied

1. **Clarity over subtlety**: Explicit instructions ("exclude", "skip") vs. vague ("avoid")
2. **Repetition**: State exclusion requirement multiple times in different phrasings
3. **Positioning**: Place at prompt start for maximum attention weight
4. **Formatting**: Use caps and formatting to emphasize critical instructions

### Alternatives Considered

- **Post-processing filter**: Rejected - requires separate classification model (out of scope)
- **System message only**: Rejected - less reliable than in-prompt instructions
- **Subtle phrasing**: Rejected - LLMs respond better to explicit directives

---

## 4. Configuration Validation with Pydantic

### Decision

Use Pydantic v2 with `field_validator` decorators and `Field` constraints for comprehensive validation:

```python
from pydantic import BaseModel, Field, field_validator

class NewsletterConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    excluded_topics: list[str] = Field(
        default_factory=list,
        description="Topics to exclude from newsletters"
    )

    @field_validator('excluded_topics')
    @classmethod
    def validate_exclusions(cls, v: list[str]) -> list[str]:
        # Max 50 topics
        if len(v) > 50:
            raise ValueError("Maximum 50 excluded topics allowed")

        # Each topic <= 100 chars
        for i, topic in enumerate(v):
            if not topic.strip():
                raise ValueError(f"Topic at index {i} cannot be empty")
            if len(topic) > 100:
                raise ValueError(f"Topic '{topic}' exceeds 100 character limit")

        return v
```

### Rationale

- Pydantic v2 is already in dependencies (pyproject.toml)
- Type safety required by constitution
- Validation happens automatically on model instantiation
- Clear error messages for constraint violations
- No need for manual dict validation

### Pattern Benefits

- **Type safety**: Mypy catches usage errors at dev time
- **Runtime validation**: Catches malformed JSON at load time
- **Self-documenting**: Field descriptions and constraints are explicit
- **Composable**: Can nest models if config grows

### Alternatives Considered

- **Manual dict validation**: Rejected - error-prone, no type safety
- **JSON Schema**: Rejected - less Pythonic, separate validation layer
- **Dataclasses**: Rejected - no built-in validation, requires custom code

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| UI Framework | HTMX dynamic partials | Existing pattern, minimal JS |
| Config Storage | Pydantic + JSON file | Strong typing, simple persistence |
| Prompt Engineering | Explicit high-priority instructions | Better LLM compliance |
| Validation | Pydantic field validators | Type-safe, automatic validation |

## Dependencies Added

None - all required libraries already in project:
- Flask (existing)
- Pydantic v2 (existing)
- google-genai (existing)

## Next Steps

Proceed to Phase 1:
- Design data model (Pydantic config schema)
- Create API contracts (Flask routes for HTMX)
- Write quickstart guide
