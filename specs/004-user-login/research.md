# Research: User Login Implementation

**Feature**: User Login (004-user-login)
**Date**: 2026-02-02
**Phase**: Phase 0 Research

## Research Questions

Based on the Technical Context "NEEDS CLARIFICATION" items:

1. Session management approach (Flask-Login vs custom vs JWT)
2. OAuth library choice (Authlib vs google-auth-oauthlib)
3. Password hashing library and configuration
4. Rate limiting implementation pattern
5. Password reset token generation

## Decisions

### 1. Session Management: Flask-Login with Server-Side Sessions

**Decision**: Use Flask-Login with server-side session storage in PostgreSQL.

**Rationale** (based on 2026 best practices research):
- **Industry standard**: Flask-Login is the most popular authentication library for Flask applications, handling user sessions, login state, and route protection with minimal configuration
- **Simplicity**: Flask-Login eliminates the hassle of handling session cookies and user tracking manually - it manages authentication state automatically
- **Best for traditional web apps**: Session-based auth is best suited for server-side sessions, simpler setup, and built for traditional web apps with browser-based UI
- **30-day timeout**: Easily configurable with `PERMANENT_SESSION_LIFETIME`
- **Multi-user ready**: Database-backed sessions scale naturally to multiple users
- **Security**: Session-based auth is stateful - each request ties the session ID back to the associated user on the server side
- **Proven approach**: "It's a best practice to use these robust libraries instead of writing your own auth from scratch"

**Implementation approach**:
- Install Flask-Login extension
- Create `sessions` table in PostgreSQL with columns: `session_id`, `user_id`, `data`, `created_at`, `expires_at`
- Store session ID in secure HTTP-only cookie
- Implement session cleanup task for expired sessions
- Use Flask-Login's `@login_required` decorator for protected routes
- Implement `UserMixin` for user model
- Configure login manager with user_loader callback

**Alternatives considered**:
- **JWT tokens**: Stateless tokens better for APIs and microservices, but more complex configuration. "JWT is often the best choice when transitioning from Flask + Jinja2 to React, as it aligns with RESTful API principles." Not needed for this traditional web app.
- **Plain Flask sessions**: Requires manual implementation of what Flask-Login provides out of the box
- **Cookie-only sessions**: Limited to 4KB, security concerns with client-side data

**Sources**:
- [Flask Security Best Practices 2025](https://hub.corgea.com/articles/flask-security-best-practices-2025)
- [Session-based Auth with Flask for Single Page Apps](https://testdriven.io/blog/flask-spa-auth/)
- [Understanding Authentication: Session-Based vs. Token-Based](https://dev.to/usooldatascience/understanding-authentication-session-based-vs-token-based-and-beyond-1bnd)

### 2. OAuth Library: google-auth-oauthlib (Existing Dependency)

**Decision**: Use `google-auth-oauthlib` which is already in project dependencies.

**Rationale** (based on 2026 best practices research):
- **Already installed**: Listed in pyproject.toml, used for Gmail API integration
- **Official Google library**: First-party support, well-maintained by Google
- **Simplicity**: No need to add another dependency (Authlib would be redundant)
- **Proven in codebase**: Already working for Gmail authentication
- **Mockable**: Easy to mock for tests (constitution requirement)
- **Both are viable**: Research shows "there's no special reason to use Authlib instead of google-auth" for Google-only OAuth

**Implementation approach**:
- Reuse OAuth flow patterns from existing Gmail integration
- Store OAuth tokens in existing `oauth_tokens` table (already has encrypted_token column)
- Use `google.oauth2.credentials` for token management

**Alternatives considered**:
- **Authlib**: The successor to Flask-OAuthlib, handles both OAuth 1 and OAuth 2 services, supports multiple providers. "Flask-OAuthlib is deprecated in favor of Authlib." However, for Google-only authentication with an existing google-auth-oauthlib setup, adding Authlib would be over-engineering.
- **Custom OAuth**: Violates simplicity principle, reinventing the wheel

**Sources**:
- [Authlib Documentation](https://docs.authlib.org/en/latest/client/flask.html)
- [Migrate OAuth Client from Flask-OAuthlib to Authlib](https://blog.authlib.org/2018/migrate-flask-oauthlib-client-to-authlib)

### 3. Password Hashing: Argon2 via passlib (with bcrypt fallback)

**Decision**: Use `passlib` library with `argon2` as primary algorithm and `bcrypt` for backward compatibility.

**Rationale** (based on 2026 best practices research):
- **Modern standard**: "Argon2 is generally considered the strongest and most flexible key derivation function (KDF) today, having won the Password Hashing Competition in 2015"
- **Superior protection**: "Argon2 is a modern ASIC-resistant and GPU-resistant secure key derivation algorithm with even better password cracking resistance than pbkdf2, bcrypt and scrypt"
- **Argon2id recommended**: "Argon2id is the recommended variant, as it combines the benefits of both Argon2d and Argon2i"
- **Configurable**: Adjustable for memory, time, and parallelism, resisting both GPU and custom hardware attacks
- **Migration path**: Passlib allows graceful migration from bcrypt to Argon2
- **Python 3.13 compatible**: Well-supported through argon2_cffi library
- **Constitution compliance**: Industry-standard hashing (FR-004)

**Configuration**:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)

# Hash new passwords with Argon2
hashed = pwd_context.hash(password)

# Verify passwords (works with both argon2 and bcrypt)
is_valid = pwd_context.verify(password, hashed)

# Automatically migrates bcrypt to argon2 on login
if pwd_context.needs_update(hashed):
    hashed = pwd_context.hash(password)
```

**Implementation approach**:
- Install `passlib[argon2]` (includes argon2_cffi support library)
- New passwords hashed with Argon2id
- Existing bcrypt passwords still verify
- Automatic migration to Argon2 when users log in

**Alternatives considered**:
- **bcrypt only**: Time-tested and secure, but "the balance is currently in favor of bcrypt over pbkdf2, though pbkdf2 can be cracked somewhat more efficiently." Argon2 is more resistant to modern attacks.
- **scrypt**: Good but less common than bcrypt or argon2, harder to configure correctly
- **Python hashlib**: Too low-level, would need to implement salting manually

**Sources**:
- [Passlib Argon2 Documentation](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.argon2.html)
- [Argon2 - Practical Cryptography for Developers](https://cryptobook.nakov.com/mac-and-key-derivation/argon2)
- [New Application Quickstart Guide - Passlib](https://passlib.readthedocs.io/en/stable/narr/quickstart.html)

### 4. Rate Limiting: Flask-Limiter with Database Backend

**Decision**: Use Flask-Limiter extension with database (SQLAlchemy) storage backend for rate limiting.

**Rationale** (based on 2026 best practices research):
- **Industry standard**: "Flask-Limiter is the primary tool for adding rate limiting to Flask applications"
- **Login protection**: "Login routes are typically limited to 5 requests per minute, which is particularly useful for preventing brute-force attacks on login endpoints"
- **Security benefit**: "Rate limiting is fundamental for preventing malicious activities like brute-force attacks, denial-of-service (DoS) attempts, and general API abuse"
- **Flexible backends**: Supports various storage backends including SQLAlchemy (matches our PostgreSQL database)
- **Simple integration**: "Flask-Limiter can be combined with bcrypt for password hashing to protect authentication endpoints from brute force attacks"
- **Production ready**: Can use in-memory for development, PostgreSQL for production

**Implementation approach**:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="postgresql://...",  # Use DATABASE_URL
    default_limits=["200 per day", "50 per hour"]
)

# Apply strict limits to auth endpoints
@app.route("/login", methods=["POST"])
@limiter.limit("5 per 15 minutes")
def login():
    ...
```

**Configuration**:
- Login endpoint: 5 requests per 15 minutes (per spec FR-014)
- Password reset: 3 requests per hour (prevent abuse)
- Registration: 10 requests per hour
- Storage: PostgreSQL via SQLAlchemy backend
- Key function: IP address + email combination for login attempts

**Alternatives considered**:
- **Custom database solution**: More work, reinventing the wheel, Flask-Limiter already provides this
- **Redis backend**: Requires additional infrastructure; PostgreSQL backend sufficient for single-server deployment
- **In-memory storage**: Lost on restart, not suitable for security feature in production
- **No rate limiting**: Violates requirement FR-014

**Sources**:
- [Flask-Limiter Documentation](https://flask-limiter.readthedocs.io/)
- [Improve Flask API Security: Implement Rate Limiting](https://medium.com/@alfininfo/improve-flask-api-security-implement-rate-limiting-b82104032647)
- [Flask Security Best Practices 2025](https://hub.corgea.com/articles/flask-security-best-practices-2025)

### 5. Password Reset Tokens: UUID4 with Database Storage

**Decision**: Generate tokens using Python's `secrets.token_urlsafe(32)`, store in `password_reset_tokens` table.

**Rationale**:
- **Cryptographically secure**: `secrets` module designed for security tokens
- **URL-safe**: Can be used in email links without encoding issues
- **Simple**: Built-in Python library, no dependencies
- **Database storage**: Consistent with other security data (sessions, login attempts)
- **Easy revocation**: Can mark as used or delete from database

**Implementation approach**:
```python
import secrets
from datetime import datetime, timedelta

# Generate token
token = secrets.token_urlsafe(32)  # 256 bits of randomness
expires_at = datetime.utcnow() + timedelta(hours=1)

# Store in database
INSERT INTO password_reset_tokens (token, user_id, expires_at, used)
```

**Token lifetime**: 1 hour (spec requires expiration)

**Schema**:
```sql
CREATE TABLE password_reset_tokens (
    token VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE
);
```

**Alternatives considered**:
- **UUID4**: Also secure, but `secrets.token_urlsafe` is more explicit about cryptographic use
- **JWT tokens**: Stateless but harder to revoke if user requests multiple resets
- **Signed URLs**: More complex, requires key management

## Additional Technical Decisions

### Email Sending for Password Reset

**Decision**: Use Python's `smtplib` with environment variable configuration.

**Rationale**:
- **Built-in**: No additional dependencies
- **Flexible**: Works with any SMTP provider (Gmail, SendGrid, etc.)
- **Mockable**: Easy to mock in tests (constitution requirement)
- **Simple**: Sufficient for low-volume password resets

**Configuration via environment variables**:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `FROM_EMAIL`

### Account Merging Strategy

**Decision**: Link accounts by email address in `users` table with nullable `password_hash` and `google_id` columns.

**Rationale**:
- **Spec requirement**: FR-012 requires account merging
- **Simple schema**: Single users table, multiple auth methods per user
- **Flexible**: User can authenticate with either method once linked

**Schema approach**:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL if only Google auth
    google_id VARCHAR(255),      -- NULL if only email/password
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);
```

**Merge logic**:
- When Google OAuth login occurs, check if email exists in users table
- If exists: Add google_id to existing user record
- If not: Create new user with google_id
- User can then use either authentication method

## Dependencies to Add

Based on research decisions:

```toml
# Add to pyproject.toml dependencies
"flask-login>=0.6.3",       # Session management and user authentication
"passlib[argon2]>=1.7.4",   # Password hashing (includes argon2_cffi)
"flask-limiter>=3.5.0",     # Rate limiting for brute force protection
```

Note: `google-auth-oauthlib` already present in dependencies.

## Testing Strategy

Per constitution requirements:

1. **Mock external APIs**:
   - Google OAuth: Mock `google.oauth2` credentials flow
   - Email sending: Mock `smtplib.SMTP`
   - Database: Use test database (DATABASE_URL_TEST)

2. **TDD Required** (per constitution):
   - `src/auth/password.py` - password hashing/verification
   - `src/auth/session.py` - session management logic
   - `src/auth/rate_limit.py` - rate limiting logic
   - `src/auth/service.py` - authentication business logic

3. **TDD Not Required** (per constitution):
   - Route handlers in `src/web/auth_routes.py`
   - HTML templates

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Session table grows unbounded | Implement cleanup job for expired sessions |
| Login attempts table grows unbounded | Cleanup job for old attempts (>24 hours) |
| SMTP credentials in environment | Document in setup guide, consider secrets management |
| Google OAuth credentials exposure | Store client secret in environment variable, not in code |
| Coolify platform auth conflicts | Document two-layer auth model in quickstart |

## Next Steps (Phase 1)

1. Generate detailed data model (data-model.md)
2. Design API contracts for auth routes (contracts/)
3. Create quickstart guide for setup (quickstart.md)
4. Update agent context with new dependencies
