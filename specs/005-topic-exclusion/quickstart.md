# Quickstart: Topic Exclusion Filter

**Feature**: 005-topic-exclusion
**Audience**: Developers implementing this feature
**Estimated Time**: 30 minutes to understand, 4-6 hours to implement

## Prerequisites

- Familiarity with Flask and HTMX
- Understanding of Pydantic models
- Knowledge of existing `config/senders.json` structure
- TDD mindset (required by constitution)

## Overview

This feature adds topic exclusion to newsletter consolidation through three main components:

1. **Configuration Layer**: Extend `NewsletterConfig` with `excluded_topics` list
2. **UI Layer**: HTMX-based settings interface for managing exclusions
3. **LLM Layer**: Inject exclusion instructions into consolidation prompt

## Architecture Diagram

```text
┌─────────────┐
│   Browser   │
│   (HTMX)    │
└──────┬──────┘
       │ POST /settings/exclusions/add
       │ DELETE /settings/exclusions/delete/{index}
       ↓
┌──────────────────────────────────────────┐
│         Flask Routes                     │
│  src/web/feed_routes.py (or new file)   │
└──────┬───────────────────────────────────┘
       │ load_config() / save_config()
       ↓
┌──────────────────────────────────────────┐
│      Configuration Service               │
│     src/newsletter/config.py             │
│  - NewsletterConfig (Pydantic)           │
│  - load_config()                         │
│  - save_config()                         │
└──────┬───────────────────────────────────┘
       │ Read/Write JSON
       ↓
┌──────────────────────────────────────────┐
│       config/senders.json                │
│  {                                       │
│    "excluded_topics": ["topic1", ...]   │
│    ...                                   │
│  }                                       │
└──────────────────────────────────────────┘

       ↓ (Used during consolidation)

┌──────────────────────────────────────────┐
│      Newsletter Consolidator             │
│   src/newsletter/consolidator.py         │
│  - consolidate_newsletters()             │
│  - inject exclusions into prompt         │
└──────────────────────────────────────────┘
```

## Implementation Order (TDD)

### Step 1: Configuration Model (TDD)

**Test First** (`tests/unit/newsletter/test_config.py`):

```python
def test_newsletter_config_with_exclusions():
    """Config loads with excluded_topics list."""
    config_data = {
        "excluded_topics": ["datasette", "SQL"],
        "consolidation_prompt": "...",
        # ... other required fields
    }
    config = NewsletterConfig(**config_data)
    assert config.excluded_topics == ["datasette", "SQL"]

def test_exclusions_max_50_topics():
    """Validator rejects > 50 topics."""
    with pytest.raises(ValueError, match="Maximum 50"):
        NewsletterConfig(
            excluded_topics=[f"topic{i}" for i in range(51)],
            # ... other required fields
        )

def test_exclusions_max_100_chars():
    """Validator rejects topics > 100 characters."""
    with pytest.raises(ValueError, match="100 character limit"):
        NewsletterConfig(
            excluded_topics=["a" * 101],
            # ... other required fields
        )
```

**Then Implement** (`src/newsletter/config.py`):

```python
from pydantic import BaseModel, Field, field_validator

class NewsletterConfig(BaseModel):
    excluded_topics: list[str] = Field(default_factory=list)

    @field_validator('excluded_topics')
    @classmethod
    def validate_exclusions(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("Maximum 50 excluded topics allowed")
        for topic in v:
            if len(topic) > 100:
                raise ValueError(f"Topic exceeds 100 character limit")
        return v

def load_config(path: Path = Path("config/senders.json")) -> NewsletterConfig:
    """Load config from JSON file."""
    with open(path) as f:
        data = json.load(f)
    return NewsletterConfig(**data)

def save_config(config: NewsletterConfig, path: Path = Path("config/senders.json")) -> None:
    """Save config to JSON file atomically."""
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(config.model_dump(), f, indent=2)
    temp_path.replace(path)  # Atomic on POSIX
```

**Run Tests**: `pytest tests/unit/newsletter/test_config.py -v`

---

### Step 2: Flask Routes (TDD)

**Test First** (`tests/integration/web/test_exclusion_routes.py`):

```python
def test_add_exclusion_success(client, auth):
    """POST /settings/exclusions/add adds topic and returns HTML."""
    auth.login()
    response = client.post('/settings/exclusions/add', data={'topic': 'datasette'})

    assert response.status_code == 200
    assert b'datasette' in response.data

def test_delete_exclusion(client, auth):
    """DELETE /settings/exclusions/delete/{index} removes topic."""
    auth.login()
    # Add first
    client.post('/settings/exclusions/add', data={'topic': 'test'})
    # Then delete
    response = client.delete('/settings/exclusions/delete/0')
    assert response.status_code == 200
```

**Then Implement** (`src/web/feed_routes.py` or new file):

```python
from flask import Blueprint, request, render_template_string
from flask_login import login_required
from src.newsletter.config import load_config, save_config

exclusions_bp = Blueprint('exclusions', __name__, url_prefix='/settings/exclusions')

@exclusions_bp.route('/add', methods=['POST'])
@login_required
def add_exclusion():
    topic = request.form.get('topic', '').strip()

    if not topic:
        return '<div class="alert alert-error">Topic cannot be empty</div>', 400

    if len(topic) > 100:
        return '<div class="alert alert-error">Topic exceeds 100 characters</div>', 400

    config = load_config()

    if len(config.excluded_topics) >= 50:
        return '<div class="alert alert-error">Maximum 50 topics allowed</div>', 409

    config.excluded_topics.append(topic)
    save_config(config)

    index = len(config.excluded_topics) - 1
    return render_template_string('''
    <li class="exclusion-item" data-index="{{ index }}">
      <span class="topic-text">{{ topic }}</span>
      <button hx-delete="/settings/exclusions/delete/{{ index }}"
              hx-target="closest li" hx-swap="outerHTML">Remove</button>
    </li>
    ''', index=index, topic=topic)

@exclusions_bp.route('/delete/<int:index>', methods=['DELETE'])
@login_required
def delete_exclusion(index: int):
    config = load_config()

    if index < 0 or index >= len(config.excluded_topics):
        return '<div class="alert alert-error">Topic not found</div>', 404

    config.excluded_topics.pop(index)
    save_config(config)

    return '', 200  # HTMX removes element
```

**Run Tests**: `pytest tests/integration/web/test_exclusion_routes.py -v`

---

### Step 3: UI Templates

**Create Partial** (`src/web/templates/partials/topic_exclusion_config.html`):

```html
<div class="source-config-form">
    <h4>Topic Exclusions</h4>

    <p class="section-description">
        Topics to exclude from consolidated newsletters (max 50, 100 chars each)
    </p>

    <form hx-post="/settings/exclusions/add"
          hx-target="#exclusion-list"
          hx-swap="beforeend"
          class="config-form">
        <div class="form-group">
            <label for="exclusion-topic">Add Topic</label>
            <input type="text"
                   id="exclusion-topic"
                   name="topic"
                   maxlength="100"
                   placeholder="e.g., datasette"
                   required>
            <span class="form-hint">
                Topics matched semantically by LLM
            </span>
        </div>
        <button type="submit" class="btn btn-primary">Add</button>
    </form>

    <div hx-get="/settings/exclusions/list"
         hx-trigger="load"
         hx-target="this"
         hx-swap="innerHTML">
        Loading...
    </div>
</div>
```

**Update Settings Page** (`src/web/templates/settings.html`):

```html
<div class="source-configs">
    {% include "partials/zotero_config.html" %}
    {% include "partials/newsletter_config.html" %}
    {% include "partials/topic_exclusion_config.html" %}  <!-- NEW -->
</div>
```

---

### Step 4: LLM Integration (TDD)

**Test First** (`tests/unit/newsletter/test_consolidator.py`):

```python
def test_consolidate_with_exclusions(mock_llm_client):
    """Exclusions are injected into prompt."""
    items = [{"title": "Datasette article", ...}]
    exclusions = ["datasette"]

    result = consolidate_newsletters(
        items, "prompt", mock_llm_client, "model", exclusions
    )

    # Verify prompt included exclusion instructions
    call_args = mock_llm_client.models.generate_content.call_args
    prompt = call_args[1]['contents']

    assert "CRITICAL INSTRUCTION" in prompt
    assert "datasette" in prompt
```

**Then Implement** (`src/newsletter/consolidator.py`):

```python
def consolidate_newsletters(
    parsed_items: list[dict],
    prompt: str,
    llm_client: genai.Client,
    model_name: str,
    excluded_topics: list[str] | None = None  # NEW parameter
) -> str:
    """Generate consolidated newsletter with optional topic exclusions."""

    # Build exclusion instructions if provided
    exclusion_instructions = ""
    if excluded_topics:
        topics_formatted = "\n".join(f"- {topic}" for topic in excluded_topics)
        exclusion_instructions = f"""
CRITICAL INSTRUCTION - HIGHEST PRIORITY:
You MUST exclude any content related to the following topics:
{topics_formatted}

Do NOT include these topics in your consolidated output. Skip items matching these topics entirely.

"""

    # Prepend exclusions to prompt
    full_prompt = f"{exclusion_instructions}{prompt}\n\nItems:\n{items_json}"

    # ... rest of existing consolidation logic
```

**Run Tests**: `pytest tests/unit/newsletter/test_consolidator.py -v`

---

### Step 5: Integration

Wire everything together in the consolidation workflow:

```python
# In the code that calls consolidate_newsletters:
config = load_config()
result = consolidate_newsletters(
    parsed_items=items,
    prompt=config.consolidation_prompt,
    llm_client=client,
    model_name=config.models.consolidation,
    excluded_topics=config.excluded_topics  # Pass exclusions
)
```

---

## Testing Checklist

### Unit Tests

- [ ] Config model loads with exclusions
- [ ] Config model validates max 50 topics
- [ ] Config model validates max 100 chars per topic
- [ ] Config model allows duplicates
- [ ] Config save is atomic
- [ ] Consolidator injects exclusions into prompt

### Integration Tests

- [ ] Add topic via POST returns HTML
- [ ] Add topic at limit returns 409
- [ ] Delete topic via DELETE succeeds
- [ ] Delete invalid index returns 404
- [ ] List endpoint returns all topics

### Manual Testing

- [ ] Settings page loads
- [ ] Can add topic via UI
- [ ] Can delete topic via UI
- [ ] Topics persist after browser refresh
- [ ] Validation errors display correctly
- [ ] Consolidated newsletter excludes specified topics

---

## Common Pitfalls

### 1. Forgetting to Mock LLM in Tests

```python
# ❌ WRONG - calls real API
def test_consolidate():
    result = consolidate_newsletters(...)

# ✅ CORRECT - mock the client
def test_consolidate(mocker):
    mock_client = mocker.Mock()
    mock_client.models.generate_content.return_value.text = "result"
    result = consolidate_newsletters(..., mock_client, ...)
```

### 2. Not Using Strong Typing

```python
# ❌ WRONG - plain dict
def save_config(config: dict) -> None:
    ...

# ✅ CORRECT - Pydantic model
def save_config(config: NewsletterConfig) -> None:
    ...
```

### 3. Hardcoding Config Path

```python
# ❌ WRONG - hardcoded
with open("config/senders.json") as f:
    ...

# ✅ CORRECT - parameterized
def load_config(path: Path = Path("config/senders.json")) -> NewsletterConfig:
    ...
```

---

## Debugging Tips

### Check Config File

```bash
# Verify JSON is valid
python -m json.tool config/senders.json

# Check excluded_topics
cat config/senders.json | jq '.excluded_topics'
```

### Test HTMX Requests

```bash
# Add topic
curl -X POST http://localhost:5000/settings/exclusions/add \
  -H "Cookie: session=..." \
  -d "topic=test"

# Delete topic
curl -X DELETE http://localhost:5000/settings/exclusions/delete/0 \
  -H "Cookie: session=..."
```

### Verify LLM Prompt

Add debug logging to see the final prompt:

```python
logger.debug(f"Consolidation prompt with exclusions: {full_prompt}")
```

---

## Performance Notes

- Config file I/O is fast (<1ms for typical JSON size)
- No database queries needed
- HTMX updates are near-instant (no full page reload)
- LLM call time unchanged (prompt length increase is negligible)

---

## Next Steps

After implementation:

1. Run full test suite: `pytest`
2. Check type safety: `mypy src/`
3. Lint code: `ruff check .`
4. Manual test in browser
5. Create pull request with `/commit` command

---

## References

- [spec.md](spec.md) - Feature requirements
- [research.md](research.md) - Design decisions
- [data-model.md](data-model.md) - Pydantic models
- [contracts/api-routes.md](contracts/api-routes.md) - API details
- Constitution: `.specify/memory/constitution.md`
