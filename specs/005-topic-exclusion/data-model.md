# Data Model: Topic Exclusion Filter

**Feature**: 005-topic-exclusion
**Date**: 2026-02-03
**Status**: Phase 1 - Design

## Overview

This feature extends the existing configuration model with an `excluded_topics` list. No new database tables are required - all data is stored in the existing `config/senders.json` file.

## Configuration Model

### NewsletterConfig (Pydantic Model)

Extended configuration model for newsletter processing with topic exclusions.

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict

class NewsletterConfig(BaseModel):
    """Newsletter configuration including exclusions.

    Stored in config/senders.json at root level.
    """
    model_config = ConfigDict(strict=True)

    # Existing fields (already in senders.json)
    senders: dict[str, SenderConfig]
    consolidation_prompt: str
    retention_limit: int
    days_lookback: int
    max_workers: int
    default_parsing_prompt: str
    default_consolidation_prompt: str
    models: ModelConfig

    # NEW: Topic exclusions
    excluded_topics: list[str] = Field(
        default_factory=list,
        description="List of topics to exclude from consolidated newsletters",
        max_length=50
    )

    @field_validator('excluded_topics')
    @classmethod
    def validate_exclusions(cls, v: list[str]) -> list[str]:
        """Validate exclusion list constraints.

        Rules:
        - Maximum 50 topics
        - Each topic maximum 100 characters
        - No empty strings
        - Duplicates allowed (per spec clarifications)
        """
        if len(v) > 50:
            raise ValueError("Maximum 50 excluded topics allowed")

        for i, topic in enumerate(v):
            topic_stripped = topic.strip()
            if not topic_stripped:
                raise ValueError(f"Topic at index {i} cannot be empty or whitespace")
            if len(topic) > 100:
                raise ValueError(
                    f"Topic '{topic[:50]}...' exceeds 100 character limit "
                    f"({len(topic)} characters)"
                )

        return v


class SenderConfig(BaseModel):
    """Configuration for a newsletter sender (existing)."""
    parsing_prompt: str
    enabled: bool
    created_at: str


class ModelConfig(BaseModel):
    """LLM model configuration (existing)."""
    parsing: str
    consolidation: str
```

### JSON Structure

The `config/senders.json` file structure after modification:

```json
{
  "senders": {
    "simonw@substack.com": {
      "parsing_prompt": "...",
      "enabled": true,
      "created_at": "2026-01-09T12:06:48.461296Z"
    }
  },
  "consolidation_prompt": "...",
  "retention_limit": 100,
  "days_lookback": 30,
  "max_workers": 10,
  "default_parsing_prompt": "...",
  "default_consolidation_prompt": "...",
  "models": {
    "parsing": "gemini-2.5-flash",
    "consolidation": "gemini-2.5-flash"
  },
  "excluded_topics": [
    "datasette",
    "low-level coding",
    "SQL internals"
  ]
}
```

## State Transitions

### Configuration Lifecycle

```text
[Empty Config]
    ↓ (Initial load)
[Config with excluded_topics = []]
    ↓ (User adds topic via UI)
[Config with excluded_topics = ["topic1"]]
    ↓ (Save to file)
[Persisted Config]
    ↓ (Next consolidation run)
[Exclusions applied in LLM prompt]
    ↓ (User deletes topic via UI)
[Config with excluded_topics = []]
    ↓ (Save to file)
[Persisted Config]
```

### Validation Points

1. **Load Time**: When reading `senders.json`
   - Pydantic validates structure
   - Catches malformed JSON
   - Validates constraints (max 50, max 100 chars)

2. **Add Topic (UI)**: Before adding to list
   - Check count < 50
   - Check length <= 100
   - Trim whitespace
   - Return validation error if fails

3. **Save Time**: Before writing to file
   - Re-validate entire config
   - Atomic write (write to temp file, then rename)
   - Rollback on error

## Relationships

No new relationships - this extends existing configuration model.

```text
NewsletterConfig
├── senders (existing relationship)
│   └── SenderConfig[]
├── models (existing relationship)
│   └── ModelConfig
└── excluded_topics (NEW - simple list)
    └── str[]
```

## Constraints

| Constraint | Rule | Validation Point |
|------------|------|------------------|
| Max topics | 50 topics | Pydantic validator + UI |
| Topic length | 100 characters | Pydantic validator + HTML |
| Topic content | Non-empty after trim | Pydantic validator |
| Duplicates | Allowed | No validation (per spec) |
| File format | Valid JSON | JSON parser + Pydantic |

## Migration Strategy

### Backward Compatibility

Existing `senders.json` files without `excluded_topics` will work seamlessly:

```python
# Pydantic handles missing field with default value
excluded_topics: list[str] = Field(default_factory=list)
```

If `excluded_topics` is missing:
- Loads as empty list `[]`
- No filtering applied (backward compatible)
- First save will add empty array to JSON

### Forward Compatibility

New `senders.json` with `excluded_topics` is forward-compatible:
- Older versions ignore unknown fields (JSON parsing)
- Exclusions simply won't be applied
- No data corruption risk

## Implementation Notes

### File Locking

While not strictly required for single-user MVP, implement basic file locking for safety:

```python
import fcntl  # Unix
import msvcrt  # Windows

def save_config_atomic(config: NewsletterConfig, path: Path) -> None:
    """Save config with atomic write and file locking."""
    temp_path = path.with_suffix('.tmp')

    # Write to temp file
    with open(temp_path, 'w', encoding='utf-8') as f:
        # Lock file (platform-specific)
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Unix
        except AttributeError:
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)  # Windows

        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

        # Unlock happens automatically when file closes

    # Atomic rename
    temp_path.replace(path)
```

### Error Handling

```python
class ConfigValidationError(ValueError):
    """Raised when config validation fails."""
    pass

class ConfigLoadError(Exception):
    """Raised when config file cannot be loaded."""
    pass
```

## Testing Strategy

### Unit Tests (TDD Required)

```python
# tests/unit/newsletter/test_config.py

def test_load_config_without_exclusions():
    """Existing config without excluded_topics loads with empty list."""
    ...

def test_load_config_with_exclusions():
    """Config with excluded_topics loads correctly."""
    ...

def test_exclusions_max_50_topics():
    """Validator rejects > 50 topics."""
    ...

def test_exclusions_max_100_chars():
    """Validator rejects topics > 100 characters."""
    ...

def test_exclusions_allow_duplicates():
    """Duplicates are allowed per spec."""
    ...

def test_save_config_atomic():
    """Config save is atomic (temp file + rename)."""
    ...
```

### Integration Tests

```python
# tests/integration/web/test_exclusion_routes.py

def test_add_topic_success():
    """POST /settings/exclusions/add returns new list item."""
    ...

def test_add_topic_at_limit():
    """Adding 51st topic returns error."""
    ...

def test_delete_topic():
    """DELETE /settings/exclusions/delete/{index} removes topic."""
    ...
```

## References

- Spec: [spec.md](spec.md) - FR-001 through FR-016
- Research: [research.md](research.md) - Section 4 (Pydantic validation)
- Existing code: `src/newsletter/config.py` (to be created/modified)
