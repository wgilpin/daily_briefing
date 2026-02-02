# Data Model: User Login

**Feature**: User Login (004-user-login)
**Date**: 2026-02-02
**Phase**: Phase 1 Design

## Overview

This document defines the database schema and data models for the user authentication system. The design supports both email/password and Google OAuth authentication methods, with account merging capability, session management, password reset functionality, and rate limiting.

## Database Schema

### 1. users

Stores user account information with support for multiple authentication methods.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),              -- NULL if only Google OAuth
    google_id VARCHAR(255) UNIQUE,           -- NULL if only email/password
    name VARCHAR(255),                       -- From OAuth or registration
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id) WHERE google_id IS NOT NULL;
```

**Key Features**:
- Single user can have both password_hash and google_id (account merging per FR-012)
- Email is always required and unique (primary identifier)
- password_hash is nullable (Google-only users)
- google_id is nullable (email/password-only users)
- is_active allows account deactivation without deletion

### 2. sessions

Stores active user sessions for Flask-Login server-side session management.

```sql
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,     -- Flask session ID
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data JSONB DEFAULT '{}',                 -- Session data
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,           -- 30 days from creation
    last_accessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),                  -- For security logging
    user_agent TEXT                          -- For security logging
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

**Key Features**:
- 30-day expiration (per FR-009)
- Cascading delete when user is deleted
- Tracks IP and user agent for security
- last_accessed_at for session activity tracking

### 3. password_reset_tokens

Stores temporary tokens for password reset functionality.

```sql
CREATE TABLE password_reset_tokens (
    token VARCHAR(255) PRIMARY KEY,          -- Cryptographically secure token
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,           -- 1 hour expiration
    used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMP
);

CREATE INDEX idx_password_reset_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_expires_at ON password_reset_tokens(expires_at);
```

**Key Features**:
- 1-hour expiration for security
- Marks as used (one-time use per FR-010)
- Cascading delete when user is deleted
- Token generated using secrets.token_urlsafe(32)

### 4. Flask-Limiter Storage

Flask-Limiter automatically manages rate limiting storage. No explicit table creation needed - it uses the configured storage backend (PostgreSQL via SQLAlchemy).

**Configuration**:
- Login endpoint: 5 attempts per 15 minutes (per FR-014)
- Password reset request: 3 attempts per hour
- Registration: 10 attempts per hour

## Pydantic Models

### UserModel

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserModel(BaseModel):
    """User account model."""
    id: Optional[int] = None
    email: EmailStr
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True  # For ORM compatibility
```

### UserRegistrationRequest

```python
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserRegistrationRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: Optional[str] = Field(None, max_length=255)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements (FR-003)."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

### UserLoginRequest

```python
from pydantic import BaseModel, EmailStr

class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str
```

### SessionModel

```python
from datetime import datetime, timedelta
from typing import Optional, Any
from pydantic import BaseModel, Field

class SessionModel(BaseModel):
    """User session model."""
    session_id: str
    user_id: int
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=30)
    )
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True
```

### PasswordResetTokenModel

```python
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
import secrets

class PasswordResetTokenModel(BaseModel):
    """Password reset token model."""
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    user_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=1)
    )
    used: bool = False
    used_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### PasswordResetRequest

```python
from pydantic import BaseModel, EmailStr

class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr
```

### PasswordResetConfirm

```python
from pydantic import BaseModel, Field

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation with new password."""
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements (FR-003)."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

## Entity Relationships

```text
users (1) ----< (N) sessions
  |
  +----< (N) password_reset_tokens
```

**Relationship Details**:
1. **User → Sessions**: One-to-many. A user can have multiple active sessions across different devices.
2. **User → Password Reset Tokens**: One-to-many. A user can request multiple password resets (though only the latest should be valid).

## Data Validation Rules

### Email Validation (FR-002)
- Must be valid email format (enforced by Pydantic EmailStr)
- Must be unique in users table
- Case-insensitive comparison for duplicate checking

### Password Requirements (FR-003)
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Maximum 128 characters (reasonable upper bound)

### Password Hashing (FR-004)
- Algorithm: Argon2id via passlib
- Never store plain text passwords
- Hash generated on registration and password change
- Verification done via passlib.verify()

### Session Management (FR-007, FR-009)
- 30-day default expiration
- Can be extended on activity
- Automatic cleanup of expired sessions

### Rate Limiting (FR-014)
- Login: 5 attempts per 15 minutes per email
- Tracked automatically by Flask-Limiter
- Key: combination of IP address and email

## State Transitions

### User Account States

```text
[None] --register--> [Active, email/password only]
[Active, email/password] --add Google--> [Active, both methods]
[None] --Google OAuth--> [Active, Google only]
[Active, Google only] --set password--> [Active, both methods]
[Active] --deactivate--> [Inactive]
```

### Password Reset Flow

```text
[User forgets password]
  --> [Request reset, token created, email sent]
  --> [Token unused, not expired]
  --> [User clicks link, sets new password]
  --> [Token marked used]
```

### Session Lifecycle

```text
[User logs in]
  --> [Session created, expires_at = now + 30 days]
  --> [User activity updates last_accessed_at]
  --> [Either: User logs out (session deleted) OR expires_at reached (session expired)]
```

## Migration Script

The database migration will be created as `src/db/migrations/002_auth.sql`:

```sql
-- Migration 002: User Authentication
-- Created: 2026-02-02

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    google_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id) WHERE google_id IS NOT NULL;

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMP
);

CREATE INDEX idx_password_reset_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_expires_at ON password_reset_tokens(expires_at);
```

## Cleanup Tasks

To prevent unbounded table growth:

1. **Expired Sessions**: Delete sessions where `expires_at < NOW()`
   - Run daily via cron or application startup

2. **Used/Expired Reset Tokens**: Delete tokens where `used = TRUE OR expires_at < NOW()`
   - Run daily via cron or application startup

3. **Old Login Attempts**: Flask-Limiter handles cleanup automatically

Sample cleanup SQL:

```sql
-- Clean expired sessions
DELETE FROM sessions WHERE expires_at < NOW();

-- Clean used or expired password reset tokens
DELETE FROM password_reset_tokens WHERE used = TRUE OR expires_at < NOW();
```

## Security Considerations

1. **Password Storage**: Never log or expose password_hash values
2. **Session IDs**: Generated by Flask, cryptographically secure
3. **Reset Tokens**: Generated using secrets.token_urlsafe(32) - 256 bits of entropy
4. **Email Uniqueness**: Enforced at database level with UNIQUE constraint
5. **Cascading Deletes**: Sessions and tokens are automatically deleted when user is deleted
6. **Rate Limiting**: Prevents brute force attacks on login and password reset endpoints

## Testing Requirements

Per constitution TDD requirements:

1. **Unit Tests** (src/auth/password.py, service.py):
   - Password hashing and verification
   - Session creation and validation
   - Token generation and expiration
   - User creation with email/password
   - User creation with Google OAuth
   - Account merging logic

2. **Integration Tests** (auth flow):
   - Full registration → login → logout flow
   - Password reset flow
   - Google OAuth flow (mocked)
   - Session persistence across requests
   - Rate limiting enforcement

All database queries should use test database (DATABASE_URL_TEST environment variable).
