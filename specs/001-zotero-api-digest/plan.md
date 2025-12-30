# Implementation Plan: Zotero API Digest

**Branch**: `001-zotero-api-digest` | **Date**: 2024-12-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-zotero-api-digest/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a CLI application that retrieves recent Zotero library additions via the Zotero Web API, filters and sorts them by publication date (limiting to 10 most recent when >10 items found), and generates a markdown digest file. The application uses pyzotero for API integration, supports command-line configuration, and handles keyword filtering for inclusion/exclusion.

## Technical Context

**Language/Version**: Python 3.13+ (project already requires >=3.13)  
**Primary Dependencies**: pyzotero (Zotero API client), python-dotenv (credential management), tqdm (progress bars), argparse (stdlib CLI)  
**Storage**: N/A (stateless CLI, writes markdown files to disk)  
**Testing**: pytest (for unit tests per constitution - backend logic only)  
**Target Platform**: Cross-platform CLI (Windows, macOS, Linux)  
**Project Type**: single (CLI application)  
**Performance Goals**: Complete digest generation in <30 seconds for up to 100 items (per SC-001)  
**Constraints**: Must handle missing metadata gracefully, provide clear error messages, support configurable time windows  
**Scale/Scope**: Single-user CLI tool, processes up to 100 library items per run, outputs single markdown file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Simplicity First ✓
- **Status**: PASS
- **Rationale**: Using pyzotero (existing dependency) for API access, stdlib argparse for CLI, simple functions over classes. No unnecessary abstractions.

### II. Minimal Boilerplate ✓
- **Status**: PASS
- **Rationale**: CLI-only, no web framework, no database, no configuration files beyond .env for credentials. Direct file output.

### III. Rapid Iteration Over Perfection ✓
- **Status**: PASS
- **Rationale**: MVP scope clearly defined. Tests only for core logic (sorting, filtering, markdown generation), not API endpoints.

### IV. Focused Scope ✓
- **Status**: PASS
- **Rationale**: Single feature (Zotero digest), no group libraries, no scheduling, no LLM integration yet. Strictly MVP.

### V. Pleasing Simplicity (UI/UX) ✓
- **Status**: PASS (N/A - CLI only)
- **Rationale**: CLI interface with clear help text and error messages. No UI complexity.

### Technology Constraints ✓
- **Status**: PASS
- **Rationale**: Python 3.13+, using existing pyzotero dependency, stdlib for CLI, no forbidden patterns (ORMs, queues, microservices).

**Overall**: All gates pass. No violations detected.

**Post-Phase 1 Re-check**: After completing data model and contracts design, all gates still pass. Design maintains simplicity with function-based architecture, no unnecessary abstractions, and minimal dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
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
├── zotero/
│   ├── __init__.py
│   ├── client.py          # Zotero API client wrapper
│   ├── filters.py         # Keyword filtering logic
│   └── formatter.py       # Markdown generation
├── cli/
│   ├── __init__.py
│   └── main.py            # CLI entry point and argument parsing
└── utils/
    ├── __init__.py
    └── config.py          # Configuration loading (env vars)

tests/
├── unit/
│   ├── test_filters.py    # Keyword filtering tests
│   └── test_formatter.py  # Markdown generation tests
└── integration/
    └── test_zotero_client.py  # API client tests (mocked)
```

**Structure Decision**: Single project structure with modular organization. `src/zotero/` contains core Zotero-specific logic, `src/cli/` handles CLI interface, `src/utils/` for shared utilities. Tests mirror source structure. No web framework needed (CLI only). Library items are represented as raw `dict` structures from the Zotero API (no custom classes needed per constitution simplicity principle).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All constitution gates pass.
