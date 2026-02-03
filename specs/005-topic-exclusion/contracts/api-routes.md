# API Contracts: Topic Exclusion Routes

**Feature**: 005-topic-exclusion
**Date**: 2026-02-03
**Protocol**: HTTP (Flask + HTMX)

## Overview

Flask routes for managing topic exclusions via HTMX. All routes require authentication (existing Flask-Login session).

---

## Routes

### 1. GET /settings/exclusions/list

**Purpose**: Render the current list of excluded topics as HTML partial

**Authentication**: Required (Flask-Login)

**Request**:
```http
GET /settings/exclusions/list HTTP/1.1
Host: localhost:5000
Cookie: session=...
```

**Response (200 OK)**:
```html
<ul id="exclusion-list" class="exclusion-list">
  <li class="exclusion-item" data-index="0">
    <span class="topic-text">datasette</span>
    <button
      class="btn-small btn-danger"
      hx-delete="/settings/exclusions/delete/0"
      hx-target="closest li"
      hx-swap="outerHTML"
      hx-confirm="Remove 'datasette' from exclusions?">
      Remove
    </button>
  </li>
  <li class="exclusion-item" data-index="1">
    <span class="topic-text">low-level coding</span>
    <button
      class="btn-small btn-danger"
      hx-delete="/settings/exclusions/delete/1"
      hx-target="closest li"
      hx-swap="outerHTML"
      hx-confirm="Remove 'low-level coding' from exclusions?">
      Remove
    </button>
  </li>
</ul>
```

**Response (Empty List)**:
```html
<ul id="exclusion-list" class="exclusion-list">
  <li class="no-exclusions">No topics excluded</li>
</ul>
```

**Errors**:
- `401 Unauthorized`: Not logged in
- `500 Internal Server Error`: Config load failure

---

### 2. POST /settings/exclusions/add

**Purpose**: Add a new topic to the exclusion list

**Authentication**: Required (Flask-Login)

**Request**:
```http
POST /settings/exclusions/add HTTP/1.1
Host: localhost:5000
Cookie: session=...
Content-Type: application/x-www-form-urlencoded

topic=SQL+internals
```

**Form Parameters**:
- `topic` (required): String, 1-100 characters, will be trimmed

**Response (200 OK)** - Returns HTML fragment for new list item:
```html
<li class="exclusion-item" data-index="2">
  <span class="topic-text">SQL internals</span>
  <button
    class="btn-small btn-danger"
    hx-delete="/settings/exclusions/delete/2"
    hx-target="closest li"
    hx-swap="outerHTML"
    hx-confirm="Remove 'SQL internals' from exclusions?">
    Remove
  </button>
</li>
```

**Response (400 Bad Request)** - Validation failure:
```html
<div class="alert alert-error" role="alert">
  Topic exceeds 100 character limit
</div>
```

**Response (409 Conflict)** - At topic limit:
```html
<div class="alert alert-error" role="alert">
  Maximum 50 topics allowed. Please remove some before adding more.
</div>
```

**Errors**:
- `400 Bad Request`: Invalid input (empty, too long)
- `401 Unauthorized`: Not logged in
- `409 Conflict`: Topic limit reached
- `500 Internal Server Error`: Config save failure

---

### 3. DELETE /settings/exclusions/delete/{index}

**Purpose**: Remove a topic from the exclusion list by index

**Authentication**: Required (Flask-Login)

**Request**:
```http
DELETE /settings/exclusions/delete/1 HTTP/1.1
Host: localhost:5000
Cookie: session=...
```

**Path Parameters**:
- `index` (required): Integer, 0-based list index

**Response (200 OK)** - Empty response (HTMX removes element):
```http
HTTP/1.1 200 OK
Content-Length: 0
```

**Response (404 Not Found)** - Invalid index:
```html
<div class="alert alert-error" role="alert">
  Topic not found at index 1
</div>
```

**Errors**:
- `400 Bad Request`: Invalid index format
- `401 Unauthorized`: Not logged in
- `404 Not Found`: Index out of bounds
- `500 Internal Server Error`: Config save failure

---

## Frontend Integration

### Settings Page HTML

The main settings page includes the topic exclusion section:

```html
<!-- src/web/templates/settings.html -->

<div class="settings-section">
    <h3>Topic Exclusions</h3>
    <p class="section-description">
        Exclude topics from your consolidated newsletters. Items matching these topics
        will be filtered out during generation. Maximum 50 topics, 100 characters each.
    </p>

    <!-- Add form -->
    <form
      hx-post="/settings/exclusions/add"
      hx-target="#exclusion-list"
      hx-swap="beforeend"
      class="exclusion-add-form">
        <div class="form-group">
            <label for="topic-input">Add Topic to Exclude</label>
            <input
              type="text"
              id="topic-input"
              name="topic"
              maxlength="100"
              placeholder="e.g., datasette, SQL internals"
              required
              class="form-control">
            <span class="form-hint">
                Topics are matched semantically by the LLM
            </span>
        </div>
        <button type="submit" class="btn btn-primary">Add Topic</button>
    </form>

    <!-- List container (loaded via HTMX) -->
    <div
      hx-get="/settings/exclusions/list"
      hx-trigger="load"
      hx-target="this"
      hx-swap="innerHTML">
        Loading exclusions...
    </div>
</div>
```

### HTMX Behavior

1. **Page Load**: `hx-get="/settings/exclusions/list"` loads current topics
2. **Add Topic**: Form submit → POST → append new `<li>` to list
3. **Delete Topic**: Button click → DELETE → remove `<li>` from DOM
4. **Confirmation**: `hx-confirm` shows browser confirm dialog before delete

---

## Error Response Format

All error responses use consistent HTML format for display:

```html
<div class="alert alert-{type}" role="alert">
  {error_message}
</div>
```

Where `{type}` is:
- `error`: Validation or operational errors
- `warning`: Non-critical issues
- `info`: Informational messages

---

## Backend Implementation Notes

### Route Organization

Add routes to existing `src/web/feed_routes.py` (or create new `exclusion_routes.py`):

```python
from flask import Blueprint, request, render_template_string
from flask_login import login_required

exclusions_bp = Blueprint('exclusions', __name__, url_prefix='/settings/exclusions')

@exclusions_bp.route('/list', methods=['GET'])
@login_required
def list_exclusions():
    """Render current exclusion list."""
    ...

@exclusions_bp.route('/add', methods=['POST'])
@login_required
def add_exclusion():
    """Add new exclusion topic."""
    ...

@exclusions_bp.route('/delete/<int:index>', methods=['DELETE'])
@login_required
def delete_exclusion(index: int):
    """Delete exclusion by index."""
    ...
```

### Template Rendering

Use `render_template_string` for small HTML fragments or create partial templates:

```python
# Option 1: Inline template string
return render_template_string('''
<li class="exclusion-item" data-index="{{ index }}">
  <span class="topic-text">{{ topic }}</span>
  <button ...>Remove</button>
</li>
''', index=index, topic=topic)

# Option 2: Partial template file
return render_template('partials/exclusion_item.html', index=index, topic=topic)
```

---

## Testing Contracts

### Integration Test Examples

```python
def test_add_exclusion_success(client, auth):
    """POST /settings/exclusions/add returns new list item."""
    auth.login()
    response = client.post('/settings/exclusions/add', data={'topic': 'test topic'})

    assert response.status_code == 200
    assert b'test topic' in response.data
    assert b'hx-delete' in response.data

def test_add_exclusion_at_limit(client, auth):
    """Adding 51st topic returns 409 Conflict."""
    auth.login()

    # Add 50 topics
    for i in range(50):
        client.post('/settings/exclusions/add', data={'topic': f'topic{i}'})

    # Try to add 51st
    response = client.post('/settings/exclusions/add', data={'topic': 'topic51'})

    assert response.status_code == 409
    assert b'Maximum 50 topics' in response.data

def test_delete_exclusion(client, auth):
    """DELETE /settings/exclusions/delete/{index} removes topic."""
    auth.login()

    # Add topic
    client.post('/settings/exclusions/add', data={'topic': 'test'})

    # Delete it
    response = client.delete('/settings/exclusions/delete/0')

    assert response.status_code == 200

    # Verify removed
    list_response = client.get('/settings/exclusions/list')
    assert b'test' not in list_response.data
```

---

## Security Considerations

1. **Authentication**: All routes require `@login_required`
2. **CSRF Protection**: Flask-WTF or Flask session cookies handle CSRF
3. **Input Validation**: Server-side validation of topic length/count
4. **Index Bounds**: Validate index before array access
5. **XSS Prevention**: Use Jinja2 auto-escaping for topic text

---

## References

- Spec: [spec.md](spec.md) - FR-003 through FR-007, FR-016
- Research: [research.md](research.md) - Section 1 (HTMX patterns)
- Data Model: [data-model.md](data-model.md) - NewsletterConfig
