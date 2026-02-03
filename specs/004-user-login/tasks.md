# Implementation Tasks: User Login

**Feature**: User Login (004-user-login)
**Branch**: `004-user-login`
**Generated**: 2026-02-02

## Overview

This document provides a complete task breakdown for implementing user authentication with email/password and Google OAuth login. Tasks are organized by user story to enable independent implementation and testing.

**Constitution Note**: Backend TDD is REQUIRED for auth service modules (password.py, session.py, service.py). Route handlers are exempt from TDD per constitution.

## Task Summary

- **Total Tasks**: 56
- **Setup Phase**: 6 tasks
- **Foundational Phase**: 9 tasks
- **User Story 1 (P1 - Email/Password)**: 13 tasks
- **User Story 3 (P1 - Session Management)**: 6 tasks
- **User Story 2 (P2 - Google OAuth)**: 9 tasks
- **User Story 4 (P2 - Password Reset)**: 10 tasks
- **Polish Phase**: 3 tasks

## Implementation Strategy

**MVP Scope**: User Story 1 + User Story 3 (Email/Password Login + Session Management)

**Note**: Password reset (US4/FR-010) is marked as P2 priority in spec.md ("Important for recovery but not needed for initial MVP"). Users can create new accounts if locked out during MVP phase.

**Incremental Delivery**:
1. **Sprint 1 (MVP)**: Setup + Foundational + US1 + US3 → Basic auth working (registration, login, logout, sessions)
2. **Sprint 2**: US2 → Add Google OAuth (convenience feature)
3. **Sprint 3**: US4 → Add password reset (recovery feature, post-MVP)
4. **Sprint 4**: Polish → Production-ready

## Dependencies & Execution Order

```mermaid
graph TD
    Setup[Phase 1: Setup] --> Found[Phase 2: Foundational]
    Found --> US1[Phase 3: US1 - Email/Password]
    Found --> US3[Phase 4: US3 - Sessions]
    US1 --> US2[Phase 5: US2 - Google OAuth]
    US1 --> US4[Phase 6: US4 - Password Reset]
    US2 --> Polish[Phase 7: Polish]
    US4 --> Polish
    US3 --> Polish
```

**Story Completion Order**:
- US1 and US3 can be developed in parallel after Foundational
- US2 and US4 require US1 complete
- US2 and US4 can be developed in parallel

---

## Phase 1: Setup

**Goal**: Initialize project structure and install dependencies

**Tasks**:

- [ ] T001 Add authentication dependencies to pyproject.toml (flask-login>=0.6.3, passlib[argon2]>=1.7.4, flask-limiter>=3.5.0)
- [ ] T002 Run uv sync to install new dependencies
- [ ] T003 Create auth module directory structure (src/auth/, tests/unit/auth/, tests/integration/auth/)
- [ ] T004 Create auth templates directory (src/web/templates/auth/)
- [ ] T005 Create database migration file src/db/migrations/002_auth.sql
- [ ] T006 Add environment variables to .env.example (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL)

**Validation**: All directories exist, dependencies installed, migration file created

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Implement core auth infrastructure needed by all user stories

**Independent Test**: Core auth services can hash passwords, generate tokens, and validate inputs

**Tasks**:

- [ ] T007 Create Pydantic models in src/auth/models.py (UserModel, UserRegistrationRequest, UserLoginRequest, SessionModel, PasswordResetTokenModel, PasswordResetRequest, PasswordResetConfirm)
- [ ] T008 [P] Write unit tests for password module in tests/unit/auth/test_password.py (TDD required)
- [ ] T009 [P] Implement password hashing module in src/auth/password.py (hash_password, verify_password, validate_password_strength using Argon2 via passlib)
- [ ] T010 [P] Write unit tests for session module in tests/unit/auth/test_session.py (TDD required)
- [ ] T011 [P] Implement session management module in src/auth/session.py (create_session, validate_session, cleanup_expired_sessions)
- [ ] T012 Run database migration 002_auth.sql to create users, sessions, and password_reset_tokens tables
- [ ] T013 Initialize Flask-Login in src/web/app.py (LoginManager, user_loader callback)
- [ ] T014 Initialize Flask-Limiter in src/web/app.py with PostgreSQL storage backend (IMPORTANT: Configure with custom key_func for email-based rate limiting on login endpoint - use combination of IP + email from request.json to enforce FR-014: "5 attempts per email address per 15 minutes")
- [ ] T015 Create auth blueprint in src/web/auth_routes.py (empty blueprint with /auth prefix)

**Validation**:
- All unit tests pass (pytest tests/unit/auth/)
- Password hashing works with Argon2
- Database tables exist
- Flask-Login and Flask-Limiter initialized

---

## Phase 3: User Story 1 - Email/Password Login (P1)

**Story Goal**: Users can register with email/password, login, and logout

**Independent Test Criteria**:
1. User can create account with valid email and strong password
2. User can login with correct credentials
3. Login fails with incorrect password
4. User can logout and session is terminated
5. Duplicate email registration is rejected

**Acceptance Scenarios** (from spec.md):
- ✅ Create account with email/password → logged in
- ✅ Login with correct credentials → logged in
- ✅ Login with wrong password → error message
- ✅ Logout → session terminated, cannot access protected features

**Tasks**:

- [ ] T016 [US1] Write unit tests for authentication service in tests/unit/auth/test_service.py (user_registration, user_login, account_validation - TDD required)
- [ ] T017 [US1] Implement user registration logic in src/auth/service.py (create_user, validate_email_unique, hash_password)
- [ ] T018 [US1] Implement user login logic in src/auth/service.py (authenticate_user, verify_credentials, update_last_login)
- [ ] T019 [US1] Implement user_loader callback in src/auth/service.py (get_user_by_id for Flask-Login)
- [ ] T020 [P] [US1] Create POST /auth/register endpoint in src/web/auth_routes.py (rate limit: 10/hour)
- [ ] T021 [P] [US1] Create POST /auth/login endpoint in src/web/auth_routes.py (rate limit: 5 per 15 min)
- [ ] T022 [P] [US1] Create POST /auth/logout endpoint in src/web/auth_routes.py
- [ ] T023 [P] [US1] Create GET /auth/me endpoint in src/web/auth_routes.py (returns current user info)
- [ ] T024 [P] [US1] Create GET /auth/status endpoint in src/web/auth_routes.py (checks if authenticated)
- [ ] T025 [P] [US1] Create registration page template in src/web/templates/auth/register.html
- [ ] T026 [P] [US1] Create login page template in src/web/templates/auth/login.html
- [ ] T027 [US1] Write integration tests for registration/login/logout flow in tests/integration/auth/test_auth_flow.py
- [ ] T028 [US1] Update existing protected routes in src/web/feed_routes.py to require authentication with @login_required decorator

**Parallel Opportunities**:
- T020-T026 can run in parallel (different files)
- T016-T019 must run sequentially (same file, TDD)
- T027 must wait for T020-T022 (integration test)

**Validation**:
- All unit tests pass for auth service
- Integration tests pass for full registration → login → logout flow
- Manual test: Register, logout, login, logout works end-to-end
- Protected routes redirect to login when not authenticated
- Rate limiting triggers after 5 failed login attempts

---

## Phase 4: User Story 3 - Session Management (P1)

**Story Goal**: Users remain authenticated across page refreshes and sessions expire appropriately

**Independent Test Criteria**:
1. Session persists across page refresh
2. Session persists across browser close/reopen (within 30 days)
3. Session expires after 30 days
4. Logout terminates session immediately
5. Expired session requires re-authentication

**Acceptance Scenarios** (from spec.md):
- ✅ Refresh page → remain logged in
- ✅ Close/reopen browser → remain logged in (within timeout)
- ✅ Session expires after 30 days → must re-authenticate
- ✅ Logout → session terminated

**Tasks**:

- [ ] T029 [US3] Configure Flask session settings in src/web/app.py (PERMANENT_SESSION_LIFETIME=30 days, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True for production)
- [ ] T030 [US3] Implement session persistence check on each request in src/web/app.py (before_request handler to update last_accessed_at)
- [ ] T031 [US3] Implement session cleanup task in src/auth/session.py (delete_expired_sessions)
- [ ] T032 [US3] Add session expiration logic to logout in src/web/auth_routes.py (invalidate all user sessions on logout)
- [ ] T033 [US3] Write integration tests for session persistence in tests/integration/auth/test_session_persistence.py
- [ ] T034 [US3] Write integration test for session expiration in tests/integration/auth/test_session_persistence.py

**Parallel Opportunities**:
- T029-T032 can run in parallel (different files/functions)
- T033-T034 can run in parallel (same file, different tests)

**Validation**:
- Session persists across page refreshes
- Session persists across browser restart
- Manual test: Login, close browser, reopen → still logged in
- Manual test: Wait for session expiration (or manipulate expires_at) → logged out

---

## Phase 5: User Story 2 - Google OAuth Login (P2)

**Story Goal**: Users can login with Google account, with account merging for existing emails

**Independent Test Criteria**:
1. New user can create account via Google OAuth
2. Returning Google user can login without re-authorization
3. User declining Google auth returns to login page
4. Google OAuth email matching existing account merges accounts (FR-012)

**Acceptance Scenarios** (from spec.md):
- ✅ New user signs in with Google → account created, logged in
- ✅ Returning Google user → logged in without re-auth
- ✅ Decline Google auth → return to login with message

**Tasks**:

- [ ] T035 [US2] Implement Google OAuth flow handler in src/auth/oauth.py (get_google_auth_url, handle_google_callback, extract_user_info)
- [ ] T036 [US2] Implement account merging logic in src/auth/service.py (merge_google_account, link_google_to_existing_user)
- [ ] T037 [US2] Write unit tests for OAuth module in tests/unit/auth/test_oauth.py (mock google-auth-oauthlib)
- [ ] T038 [US2] Write unit tests for account merging in tests/unit/auth/test_service.py
- [ ] T039 [P] [US2] Create GET /auth/google endpoint in src/web/auth_routes.py (initiates OAuth flow)
- [ ] T040 [P] [US2] Create GET /auth/google/callback endpoint in src/web/auth_routes.py (handles OAuth callback)
- [ ] T041 [P] [US2] Add "Sign in with Google" button to src/web/templates/auth/login.html
- [ ] T042 [US2] Write integration tests for Google OAuth flow in tests/integration/auth/test_oauth_flow.py (mocked Google API)
- [ ] T043 [US2] Write integration test for account merging scenario in tests/integration/auth/test_oauth_flow.py

**Parallel Opportunities**:
- T035-T038 must run sequentially (TDD for same modules)
- T039-T041 can run in parallel (different files)
- T042-T043 can run in parallel (same file, different tests)

**Validation**:
- Google OAuth flow works end-to-end (with test Google credentials)
- Account merging works when Google email matches existing account
- User can login with both email/password and Google after merging
- All tests pass with mocked Google API

---

## Phase 6: User Story 4 - Password Reset (P2)

**Story Goal**: Users can reset forgotten passwords via secure email link

**Independent Test Criteria**:
1. User can request password reset and receives email
2. User can set new password using valid reset link
3. Expired reset link shows error
4. Used reset link cannot be reused
5. User can login with new password after reset

**Acceptance Scenarios** (from spec.md):
- ✅ Request reset → receive secure link via email
- ✅ Click link, set new password → can login with new password
- ✅ Expired link → error message, can request new link

**Tasks**:

- [ ] T044 [US4] Implement email sending utility in src/utils/email.py (send_email, send_password_reset_email using SMTP)
- [ ] T045 [US4] Implement password reset token generation in src/auth/service.py (create_reset_token, validate_reset_token, mark_token_used)
- [ ] T046 [US4] Implement password reset logic in src/auth/service.py (reset_password, invalidate_all_user_sessions)
- [ ] T047 [US4] Write unit tests for email utility in tests/unit/auth/test_email.py (mock SMTP)
- [ ] T048 [US4] Write unit tests for password reset in tests/unit/auth/test_service.py
- [ ] T049 [P] [US4] Create POST /auth/password-reset endpoint in src/web/auth_routes.py (rate limit: 3/hour)
- [ ] T050 [P] [US4] Create POST /auth/password-reset/confirm endpoint in src/web/auth_routes.py
- [ ] T051 [P] [US4] Create password reset request template in src/web/templates/auth/reset_password.html
- [ ] T052 [P] [US4] Create password reset confirm template in src/web/templates/auth/reset_password_confirm.html
- [ ] T053 [US4] Write integration tests for password reset flow in tests/integration/auth/test_password_reset.py

**Parallel Opportunities**:
- T044-T048 must run sequentially (TDD for service layer)
- T049-T052 can run in parallel (different files)

**Validation**:
- Password reset email is sent (verify in logs/mock)
- Valid reset link allows password change
- Expired link shows error
- Used link cannot be reused
- Can login with new password after reset
- All user sessions invalidated after password reset

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Production readiness, code quality, documentation

**Tasks**:

- [ ] T054 [P] Run ruff check --fix on all auth code (src/auth/, src/web/auth_routes.py, tests/)
- [ ] T055 [P] Run mypy on all auth code to verify type safety
- [ ] T056 Verify all success criteria from spec.md are met (SC-001 through SC-007)

**Validation**:
- All linting passes
- All type checks pass
- All tests pass
- Manual testing checklist complete
- All success criteria validated

---

## Testing Checklist

Before marking feature complete, verify:

### Unit Tests
- [ ] pytest tests/unit/auth/test_password.py passes
- [ ] pytest tests/unit/auth/test_session.py passes
- [ ] pytest tests/unit/auth/test_service.py passes
- [ ] pytest tests/unit/auth/test_oauth.py passes
- [ ] pytest tests/unit/auth/test_email.py passes

### Integration Tests
- [ ] pytest tests/integration/auth/test_auth_flow.py passes
- [ ] pytest tests/integration/auth/test_session_persistence.py passes
- [ ] pytest tests/integration/auth/test_oauth_flow.py passes
- [ ] pytest tests/integration/auth/test_password_reset.py passes

### Code Quality
- [ ] ruff check src/ tests/ passes
- [ ] mypy src/ passes

### Manual Testing
- [ ] Register new account with email/password
- [ ] Login with email/password
- [ ] Logout
- [ ] Login with Google OAuth (new account)
- [ ] Login with Google OAuth (existing account - account merging)
- [ ] Request password reset
- [ ] Complete password reset
- [ ] Verify rate limiting triggers (5 failed logins)
- [ ] Verify session persists across page refresh
- [ ] Verify session persists across browser restart
- [ ] Verify logout clears session
- [ ] Verify protected routes require authentication

### Success Criteria (from spec.md)
- [ ] SC-001: Account registration completes in <60 seconds
- [ ] SC-002: Login completes in <10 seconds
- [ ] SC-003: 95% of legitimate logins succeed first try
- [ ] SC-004: Zero plain-text passwords (all Argon2 hashed)
- [ ] SC-005: Session persists across browser restart
- [ ] SC-006: Password reset completes in <3 minutes
- [ ] SC-007: Protected features inaccessible without auth

---

## Parallel Execution Examples

### Sprint 1 (MVP) - Parallel Work Streams

**Stream A - Auth Core**:
```bash
# One developer/agent works on:
T008 → T009  # Password module (TDD)
T010 → T011  # Session module (TDD)
T016 → T017 → T018 → T019  # Auth service (TDD)
```

**Stream B - Infrastructure**:
```bash
# Another developer/agent works on:
T012  # Database migration
T013  # Flask-Login setup
T014  # Flask-Limiter setup
T015  # Auth blueprint
```

**Stream C - Routes & Templates** (after Stream A+B complete):
```bash
# Can all run in parallel:
T020  # Register endpoint
T021  # Login endpoint
T022  # Logout endpoint
T023  # /me endpoint
T024  # /status endpoint
T025  # Register template
T026  # Login template
```

### Sprint 2 (Google OAuth) - Parallel Work Streams

**Stream A - OAuth Logic**:
```bash
T035 → T036 → T037 → T038  # OAuth module + account merging (TDD)
```

**Stream B - OAuth UI** (can start in parallel):
```bash
T039  # Google auth initiate endpoint
T040  # Google callback endpoint
T041  # Add Google button to login page
```

**Stream C - OAuth Tests** (after Stream A complete):
```bash
T042  # OAuth flow integration test
T043  # Account merging integration test
```

---

## Environment Setup

### Required Environment Variables

Add to `.env`:

```bash
# Existing
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key-here

# New for Authentication
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# Email (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com
```

### Development Commands

```bash
# Install dependencies
uv sync

# Run migrations
# (automatic on app startup, or manually:)
psql $DATABASE_URL < src/db/migrations/002_auth.sql

# Run tests
pytest tests/unit/auth/           # Unit tests
pytest tests/integration/auth/    # Integration tests
pytest                             # All tests

# Code quality
ruff check --fix src/ tests/      # Linting
mypy src/                          # Type checking

# Run development server
python src/web/app.py
```

---

## File Reference

### New Files Created

**Auth Module**:
- `src/auth/__init__.py`
- `src/auth/models.py` - Pydantic models (T007)
- `src/auth/password.py` - Password hashing (T009)
- `src/auth/session.py` - Session management (T011)
- `src/auth/service.py` - Auth business logic (T017, T018, T019, T036, T045, T046)
- `src/auth/oauth.py` - Google OAuth (T035)

**Web Layer**:
- `src/web/auth_routes.py` - Auth endpoints (T015, T020-T024, T039-T040, T049-T050)
- `src/web/templates/auth/login.html` - Login page (T026, T041)
- `src/web/templates/auth/register.html` - Registration page (T025)
- `src/web/templates/auth/reset_password.html` - Reset request (T051)
- `src/web/templates/auth/reset_password_confirm.html` - Reset confirm (T052)

**Utilities**:
- `src/utils/email.py` - Email sending (T044)

**Database**:
- `src/db/migrations/002_auth.sql` - Auth tables (T005, T012)

**Tests**:
- `tests/unit/auth/test_password.py` - Password tests (T008)
- `tests/unit/auth/test_session.py` - Session tests (T010)
- `tests/unit/auth/test_service.py` - Service tests (T016, T038, T048)
- `tests/unit/auth/test_oauth.py` - OAuth tests (T037)
- `tests/unit/auth/test_email.py` - Email tests (T047)
- `tests/integration/auth/test_auth_flow.py` - Auth flow tests (T027)
- `tests/integration/auth/test_session_persistence.py` - Session tests (T033, T034)
- `tests/integration/auth/test_oauth_flow.py` - OAuth flow tests (T042, T043)
- `tests/integration/auth/test_password_reset.py` - Password reset tests (T053)

### Modified Files

- `pyproject.toml` - Add dependencies (T001)
- `.env.example` - Add auth env vars (T006)
- `src/web/app.py` - Initialize Flask-Login, Flask-Limiter (T013, T014, T029, T030)
- `src/web/feed_routes.py` - Add @login_required (T028)

---

## Notes

- **TDD Required**: Tasks T008-T011, T016-T019, T037-T038, T047-T048 must follow red-green-refactor
- **Constitution Compliance**: All code must pass ruff and mypy before commit
- **Mocking Required**: Google OAuth and SMTP must be mocked in all tests
- **Database**: Use test database (DATABASE_URL_TEST) for all tests
- **Rate Limiting**: Use in-memory storage for Flask-Limiter in tests

---

## Next Steps

1. Start with Phase 1 (Setup) - complete all 6 tasks
2. Move to Phase 2 (Foundational) - build core infrastructure
3. Implement MVP (US1 + US3) - basic email/password auth working
4. Add Google OAuth (US2)
5. Add password reset (US4)
6. Polish and deploy

**Estimated Effort**:
- Sprint 1 (MVP): ~8-12 hours
- Sprint 2 (OAuth): ~4-6 hours
- Sprint 3 (Password Reset): ~4-6 hours
- Sprint 4 (Polish): ~2-3 hours

**Total**: ~18-27 hours of focused development time
