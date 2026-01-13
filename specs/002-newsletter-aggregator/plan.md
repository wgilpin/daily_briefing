# Implementation Plan: Newsletter Aggregator

**Branch**: `002-newsletter-aggregator` | **Date**: 2024-12-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-newsletter-aggregator/spec.md`
**Tech Stack**: Flask, HTMX, minimal JavaScript, local dev server

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a web application that collects newsletter emails from Gmail, converts them to markdown, parses them using configurable prompts (LLM-based), and generates a consolidated newsletter digest. The application runs as a local Flask server with HTMX for interactivity, storing all data locally. Users configure newsletter senders, customize parsing prompts per sender, and generate consolidated outputs suitable for reading or audio conversion.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: Flask, HTMX, google-api-python-client, google-auth libraries, markdown conversion library (html2text or similar), LLM client library (OpenAI API or similar)  
**Storage**: Local file system (JSON files for configuration, SQLite for processed email tracking, file system for emails/markdown/parsed data)  
**Testing**: pytest for unit tests (backend logic only, not UI/API endpoints per constitution)  
**Target Platform**: Local development server (Flask dev server)  
**Project Type**: Web application (single Flask app with HTMX frontend)  
**Performance Goals**: Process 10 newsletter senders in under 5 minutes, generate consolidated newsletter in under 30 seconds for 50 items  
**Constraints**: All data stored locally, single-user app, no cloud processing (LLM API calls allowed), OAuth 2.0 for Gmail access  
**Scale/Scope**: Up to 10 configured senders, up to 50 newsletter items per consolidation, configurable retention limit (N records)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Simplicity First ✓
- **Status**: PASS
- **Rationale**: Flask is simple web framework, HTMX provides interactivity without complex JS, function-based architecture preferred over classes where possible. Direct file system storage with SQLite for tracking (simple, no ORM needed).

### II. Minimal Boilerplate ✓
- **Status**: PASS
- **Rationale**: Single Flask app, no separate frontend/backend projects, minimal configuration files (just credentials.json for OAuth). No infrastructure code until deployment needed.

### III. Rapid Iteration Over Perfection ✓
- **Status**: PASS
- **Rationale**: MVP scope clearly defined. Tests only for backend logic (parsing, validation, data transformations), not UI components or API endpoints per constitution testing policy.

### IV. Focused Scope ✓
- **Status**: PASS
- **Rationale**: Single feature (newsletter aggregation), no multi-user support, no scheduling, no deployment infrastructure. Strictly MVP for local use.

### V. Pleasing Simplicity (UI/UX) ✓
- **Status**: PASS
- **Rationale**: HTMX provides clean interactions without heavy JS frameworks. Semantic HTML + minimal CSS. Simple forms for configuration, clear status messages.

### Technology Constraints ✓
- **Status**: PASS
- **Rationale**: Python 3.13+, Flask (simple web framework), HTMX for interactivity (no React/Vue), SQLite for tracking (no Postgres needed for single-user), JSON files for config. No ORMs, no background queues (async/await for LLM calls), no microservices.

**Overall**: All gates pass. No violations detected.

**Post-Phase 1 Re-check**: After completing data model and contracts design, all gates still pass. Design maintains simplicity with function-based architecture, no unnecessary abstractions, and minimal dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/002-newsletter-aggregator/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── newsletter/
│   ├── __init__.py
│   ├── gmail_client.py      # Gmail API client and OAuth handling
│   ├── email_collector.py   # Email collection logic
│   ├── markdown_converter.py # HTML/plain text to markdown conversion
│   ├── parser.py            # LLM-based parsing with configurable prompts
│   ├── consolidator.py      # Final consolidation prompt processing
│   └── storage.py           # Local file storage and SQLite tracking
├── web/
│   ├── __init__.py
│   ├── app.py               # Flask application
│   ├── routes.py            # Route handlers
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── config.html
│   │   └── digest.html
│   └── static/              # CSS and minimal JS
│       ├── style.css
│       └── app.js           # Minimal JS for HTMX enhancements
└── utils/
    ├── __init__.py
    └── config.py            # Configuration loading

data/
├── emails/                 # Raw email storage
├── markdown/               # Converted markdown files
├── parsed/                 # Parsed newsletter items (JSON)
└── newsletter_aggregator.db # SQLite database for tracking

config/
└── credentials.json        # Gmail OAuth credentials (git-ignored)

tests/
├── unit/
│   ├── test_markdown_converter.py
│   ├── test_parser.py
│   ├── test_consolidator.py
│   └── test_storage.py
└── integration/
    └── test_gmail_client.py  # Mocked Gmail API calls
```

**Structure Decision**: Single Flask application with modular organization. `src/newsletter/` contains core business logic (Gmail, parsing, consolidation), `src/web/` handles Flask routes and templates (adds to existing directory), `src/utils/` for shared utilities (adds newsletter config functions to existing config.py). Data stored in `data/` directory with SQLite for tracking processed emails. HTMX used for all interactive UI elements, minimal JavaScript only for enhancements not possible with HTMX alone.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All constitution gates pass.
