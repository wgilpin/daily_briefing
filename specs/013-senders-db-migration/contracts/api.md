# API Contracts: Senders Database Migration

**Branch**: `013-senders-db-migration` | **Date**: 2026-02-11

## Overview

No new API endpoints are introduced. All existing Flask routes in `src/web/feed_routes.py` retain their URLs, HTTP methods, and response shapes. Only the storage backend changes (file → DB).

---

## Existing Routes (unchanged interface, updated implementation)

### POST /api/settings/newsletter/senders

**Function**: `api_settings_newsletter_sender()`
**Change**: Calls `Repository.add_sender()` instead of `save_senders_config()`

**Request** (form data):
- `email` (required): sender email address
- `display_name` (optional): friendly display name

**Response**: HTMX partial HTML — sender list updated
**Error cases**: duplicate email → 409 with error message

---

### POST /api/settings/newsletter/display-name

**Function**: `api_settings_update_display_name()`
**Change**: Calls `Repository.update_sender_display_name()` instead of file save

**Request** (form data):
- `email` (required): sender email
- `display_name` (required, may be empty string): new display name; empty removes it

**Response**: HTMX partial HTML — sender row updated

---

### DELETE /api/settings/newsletter/senders/\<email\>

**Function**: `api_settings_delete_sender(email)`
**Change**: Calls `Repository.delete_sender()` instead of file save

**Response**: HTMX partial — sender row removed
**Error cases**: email not found → 404

---

## Internal Repository Contracts

New methods on `Repository` class (`src/db/repository.py`):

### Sender CRUD

```python
def get_all_senders(self) -> list[SenderRecord]: ...
def get_sender(self, email: str) -> SenderRecord | None: ...
def add_sender(self, sender: SenderRecord) -> None: ...
def update_sender(self, sender: SenderRecord) -> None: ...
def update_sender_display_name(self, email: str, display_name: str | None) -> None: ...
def delete_sender(self, email: str) -> None: ...
```

### Newsletter Config

```python
def get_newsletter_config(self) -> NewsletterConfigValues: ...  # typed TypedDict, not plain dict
def get_config_value(self, key: str) -> str | None: ...
def set_config_value(self, key: str, value: str) -> None: ...
def set_config_values(self, values: dict[str, str]) -> None: ...
```

### Migration Helper

```python
def sender_exists(self, email: str) -> bool: ...
def config_key_exists(self, key: str) -> bool: ...
```

---

## Migration Module Contract

`src/newsletter/migration.py`

```python
def migrate_senders_if_needed(config_path: Path) -> None:
    """
    If config_path (senders.json) exists:
      - Parse JSON; raise RuntimeError on malformed JSON (aborts startup)
      - Insert senders not already in DB (DB wins on conflict)
      - Insert config keys not already in newsletter_config (DB wins)
      - Rename config_path to config_path.with_suffix('.json.bak')
    If config_path does not exist: no-op.
    """
```
