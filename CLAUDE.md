# daily_briefing Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-02

## Active Technologies
- Python 3.13+ + Flask, HTMX, Google Gemini (google-genai), Pydantic (005-topic-exclusion)
- PostgreSQL (Coolify) + config/senders.json (file-based configuration) (005-topic-exclusion)

- Python 3.13+ (existing project requirement) (004-user-login)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.13+ (existing project requirement): Follow standard conventions

## Recent Changes
- 005-topic-exclusion: Added Python 3.13+ + Flask, HTMX, Google Gemini (google-genai), Pydantic

- 004-user-login: Added Python 3.13+ (existing project requirement)

<!-- MANUAL ADDITIONS START -->

## Dependency Management

- Use `uv add <package>` for adding dependencies instead of directly editing pyproject.toml
- Only edit pyproject.toml directly when pinning is required for compatibility, security, or explicit user requirements
- Let uv handle version resolution and lock file management

## Simplicity Over Generalization (NON-NEGOTIABLE)

Never use a library when a short point solution will do. Never over-generalize the solution beyond the specified scope.

**Core Principles:**

- Prefer <20 lines of direct code over adding a new library dependency
- Only add dependencies that provide significant complexity reduction for the CURRENT scope
- No premature abstraction or engineering beyond requirements
- Every dependency is a liability (maintenance, security, breaking changes)

**Examples:**

❌ **Bad: Over-engineering**

```python
# Adding Flask-Limiter for rate limiting in a personal single-user app
from flask_limiter import Limiter
limiter = Limiter(app, storage_uri="memory://", ...)
@limiter.limit("5 per minute")
```

✅ **Good: Simple point solution**

```python
# Simple 5-second delay for brute-force protection
import time
if not authenticate_user(...):
    time.sleep(5)
    return error_response()
```

**When to use libraries:**

- Complex algorithms (cryptography, parsing, protocols)
- Well-established frameworks (Flask, pytest, SQLAlchemy)
- Proven tools for specific domains (argon2 for password hashing)

**When NOT to use libraries:**

- Simple utilities that can be written in <20 lines
- Single-use helpers or wrappers
- Configuration or glue code
- Features only needed for one specific use case

<!-- MANUAL ADDITIONS END -->
