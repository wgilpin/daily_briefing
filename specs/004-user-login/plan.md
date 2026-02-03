# Implementation Plan: User Login

**Branch**: `004-user-login` | **Date**: 2026-02-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-user-login/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement secure user authentication with dual login methods (email/password and Google OAuth) for the Daily Briefing application. This feature provides foundational authentication infrastructure for a single-user application with session management (30-day timeout), password reset capability, and account merging between authentication methods. The implementation uses Flask-Login for session management, Argon2 for password hashing, Flask-Limiter for brute force protection (5 attempts per 15 minutes), and the existing google-auth-oauthlib for Google OAuth integration.

## Technical Context

**Language/Version**: Python 3.13+ (existing project requirement)

**Primary Dependencies**:
- Flask 3.0+ (existing web framework)
- Flask-Login 0.6.3+ (session management and user authentication)
- google-auth-oauthlib 1.2.0+ (already in use for Gmail, will reuse for user OAuth)
- passlib[argon2] 1.7.4+ (password hashing with Argon2id)
- Flask-Limiter 3.5.0+ (rate limiting for brute force protection)
- psycopg2-binary (existing, database connection)
- Pydantic (existing, type-safe models)

**Storage**: Coolify PostgreSQL (DATABASE_URL env var, existing infrastructure)

**Testing**: pytest with mocked external APIs (per constitution)

**Target Platform**: Web application (Linux server via Docker/Coolify)

**Project Type**: Web application (Flask backend with templates)

**Performance Goals**:
- <10 seconds login time (per SC-002)
- <200ms authentication check for protected routes
- ~250ms password hashing time (Argon2 default)

**Constraints**:
- 30-day session timeout (FR-009)
- 5 login attempts per 15 minutes rate limiting (FR-014)
- Must use industry-standard password hashing (Argon2id via passlib)
- 100% password hashing coverage (SC-004)
- All external APIs must be mockable in tests

**Scale/Scope**:
- Single-user initially with multi-user extensibility
- 3-4 new database tables (users, sessions, password_reset_tokens, login_attempts handled by Flask-Limiter)
- 6-8 new routes (register, login, logout, OAuth callback, password reset request/confirm, account settings)
- 4 HTML templates (login, register, password reset request/confirm)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **Strong Typing (NON-NEGOTIABLE)** | ✅ PASS | All authentication models will use Pydantic. Session management will use TypedDict or Pydantic models. No plain `dict` in function signatures. |
| **Backend TDD (REQUIRED)** | ✅ PASS | Authentication service (password hashing, token generation, session validation) requires TDD. Route handlers exempt per constitution. |
| **Test Isolation (NON-NEGOTIABLE)** | ✅ PASS | Google OAuth will be mocked in tests. Email sending for password reset will be mocked. Database will use test database. Flask-Limiter will use in-memory storage for tests. |
| **Simplicity First** | ✅ PASS | Using battle-tested libraries (Flask-Login, Flask-Limiter, passlib) instead of custom implementations. Password reset tokens stored in database (simple). Reusing existing google-auth-oauthlib. |
| **Feature Discipline (NON-NEGOTIABLE)** | ✅ PASS | Implementing only what's specified: email/password, Google OAuth, sessions, password reset, brute force protection. No additional auth methods. |
| **Code Quality Gates** | ✅ PASS | All code will pass ruff and mypy before commit. |
| **Technology Stack - Database** | ✅ PASS | Using existing Coolify PostgreSQL (DATABASE_URL). No local SQLite for user data. |
| **Technology Stack - Auth** | ⚠️ NOTE | Custom user auth works alongside Coolify platform-level auth. Coolify provides infrastructure-level protection, user auth provides application-level features and multi-user support. Two-layer security model is intentional. |

**Initial Assessment**: ✅ ALL GATES PASS - Phase 0 research complete.

## Project Structure

### Documentation (this feature)

```text
specs/004-user-login/
├── plan.md              # This file
├── research.md          # ✅ Phase 0 complete
├── data-model.md        # Phase 1 output (pending)
├── quickstart.md        # Phase 1 output (pending)
├── contracts/           # Phase 1 output (pending)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── auth/                    # NEW: Authentication module
│   ├── __init__.py
│   ├── models.py           # Pydantic models for User, Session, PasswordResetToken
│   ├── service.py          # Auth business logic (TDD required)
│   ├── password.py         # Password hashing/validation (TDD required)
│   ├── session.py          # Session management (TDD required)
│   └── oauth.py            # Google OAuth integration
├── models/                  # Existing
├── services/               # Existing
├── db/                     # Existing
│   ├── migrations/
│   │   └── 002_auth.sql    # NEW: Authentication tables
│   ├── connection.py       # Existing
│   └── repository.py       # Extend for auth queries
├── web/                    # Existing Flask app
│   ├── app.py              # Update: add Flask-Login initialization, rate limiter
│   ├── auth_routes.py      # NEW: Auth endpoints
│   ├── feed_routes.py      # Update: add @login_required
│   ├── templates/
│   │   ├── auth/           # NEW: Auth templates
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   ├── reset_password.html
│   │   │   └── reset_password_confirm.html
│   │   └── [existing templates]
│   └── static/             # Existing
└── utils/                  # Existing
    └── email.py            # NEW: Email sending for password reset

tests/
├── unit/
│   └── auth/               # NEW: Auth service tests (TDD)
│       ├── test_password.py
│       ├── test_session.py
│       └── test_service.py
├── integration/
│   └── auth/               # NEW: Database integration tests
│       └── test_auth_flow.py
└── [existing tests]
```

**Structure Decision**: Using existing single-project Flask structure. Auth is added as a new module under `src/auth/` with corresponding web routes in `src/web/auth_routes.py`. Database migrations follow existing pattern in `src/db/migrations/`. Tests follow existing pytest structure with mocked external dependencies (Google OAuth, email sending). Flask-Limiter handles rate limiting storage automatically.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitutional principles satisfied.

## Phase 0: Research ✅ COMPLETE

See [research.md](research.md) for detailed research findings on:

1. ✅ Session Management: Flask-Login with server-side sessions (industry standard for Flask apps)
2. ✅ OAuth Library: google-auth-oauthlib (already in dependencies, reuse existing)
3. ✅ Password Hashing: Argon2 via passlib (2026 best practice, won Password Hashing Competition)
4. ✅ Rate Limiting: Flask-Limiter with database backend (industry standard, prevents brute force)
5. ✅ Password Reset: secrets.token_urlsafe with database storage (cryptographically secure)

**Key Research Outcomes**:
- Flask-Login chosen over JWT (best for traditional web apps per 2026 research)
- Argon2 chosen over bcrypt (strongest KDF, GPU/ASIC resistant)
- Flask-Limiter provides production-ready rate limiting
- All choices aligned with constitution's simplicity principle while following industry best practices

## Phase 1: Design & Contracts (IN PROGRESS)

Next steps:
1. Generate data-model.md with database schema
2. Create API contracts in contracts/ directory
3. Generate quickstart.md for developer setup
4. Update agent context with new technologies

## Phase 2: Task Generation Prep

Will be completed via `/speckit.tasks` command after Phase 1 is complete.
