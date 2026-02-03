# Authentication API Contracts

**Feature**: User Login (004-user-login)
**Date**: 2026-02-02
**Phase**: Phase 1 Design

## Overview

This document defines the HTTP API contracts for all authentication endpoints. All endpoints return JSON responses unless otherwise specified.

## Base Configuration

**Base Path**: `/auth`
**Content-Type**: `application/json` (for POST/PUT requests)
**Rate Limiting**: Applied per endpoint (see individual endpoints)

## Common Response Structures

### Success Response

```json
{
  "success": true,
  "data": {
    // Endpoint-specific data
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

### Error Codes

- `VALIDATION_ERROR`: Invalid input data
- `AUTH_FAILED`: Authentication failed (wrong credentials)
- `USER_EXISTS`: Email already registered
- `USER_NOT_FOUND`: User account not found
- `TOKEN_INVALID`: Reset token is invalid or expired
- `TOKEN_EXPIRED`: Reset token has expired
- `RATE_LIMIT_EXCEEDED`: Too many attempts
- `OAUTH_ERROR`: Google OAuth error
- `SERVER_ERROR`: Internal server error

## Endpoints

### 1. Register (Email/Password)

**Endpoint**: `POST /auth/register`
**Rate Limit**: 10 requests per hour per IP
**Authentication**: None
**Requirement**: FR-001 (user registration)

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "name": "John Doe"  // Optional
}
```

**Validation**:
- `email`: Valid email format (FR-002)
- `password`: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit (FR-003)
- `name`: Optional, max 255 characters

**Success Response** (201 Created):

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2026-02-02T10:00:00Z"
    },
    "message": "Account created successfully"
  }
}
```

**Error Responses**:

- **400 Bad Request** (validation error):

  ```json
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Password must contain at least one uppercase letter"
    }
  }
  ```

- **409 Conflict** (email exists):

  ```json
  {
    "success": false,
    "error": {
      "code": "USER_EXISTS",
      "message": "An account with this email already exists"
    }
  }
  ```

- **429 Too Many Requests** (rate limit):

  ```json
  {
    "success": false,
    "error": {
      "code": "RATE_LIMIT_EXCEEDED",
      "message": "Too many registration attempts. Please try again later."
    }
  }
  ```

**Post-Conditions**:
- User created in database
- Password hashed with Argon2
- User automatically logged in (session created)
- SC-001: Process completes in <60 seconds

---

### 2. Login (Email/Password)

**Endpoint**: `POST /auth/login`
**Rate Limit**: 5 requests per 15 minutes per email
**Authentication**: None
**Requirement**: FR-005 (email/password login)

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Success Response** (200 OK):

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe"
    },
    "message": "Login successful"
  }
}
```

**Error Responses**:

- **401 Unauthorized** (wrong credentials):

  ```json
  {
    "success": false,
    "error": {
      "code": "AUTH_FAILED",
      "message": "Invalid email or password"
    }
  }
  ```

- **429 Too Many Requests** (rate limit per FR-014):

  ```json
  {
    "success": false,
    "error": {
      "code": "RATE_LIMIT_EXCEEDED",
      "message": "Too many failed login attempts. Please try again in 15 minutes."
    }
  }
  ```

**Post-Conditions**:
- Session created with 30-day expiration
- `last_login_at` updated in database
- SC-002: Login completes in <10 seconds
- SC-003: 95% of legitimate attempts succeed on first try

---

### 3. Logout

**Endpoint**: `POST /auth/logout`
**Rate Limit**: None
**Authentication**: Required (logged-in user)
**Requirement**: FR-008 (user logout)

**Request Body**: None

**Success Response** (200 OK):

```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

**Post-Conditions**:
- Session deleted from database
- User must login again to access protected features
- SC-007: Protected features become inaccessible

---

### 4. Google OAuth - Initiate

**Endpoint**: `GET /auth/google`
**Rate Limit**: 20 requests per hour per IP
**Authentication**: None
**Requirement**: FR-006 (Google OAuth login)

**Query Parameters**: None

**Response**: HTTP 302 Redirect to Google OAuth consent screen

**Redirect URL**: `https://accounts.google.com/o/oauth2/v2/auth?...`

**State Parameter**: Cryptographically secure random string (CSRF protection)

---

### 5. Google OAuth - Callback

**Endpoint**: `GET /auth/google/callback`
**Rate Limit**: None (single-use per OAuth flow)
**Authentication**: None (OAuth flow in progress)
**Requirement**: FR-006 (Google OAuth login)

**Query Parameters**:
- `code`: Authorization code from Google
- `state`: CSRF token from initiate step

**Success Response**: HTTP 302 Redirect to application home page

**Post-Conditions**:
- If email exists: Add google_id to existing user (FR-012)
- If email new: Create new user with google_id
- Session created
- User logged in
- SC-002: Process completes in <10 seconds

**Error Response**: HTTP 302 Redirect to login page with error message

**Error Query Parameters**:
- `error=oauth_failed&message=Authorization+declined`

---

### 6. Request Password Reset

**Endpoint**: `POST /auth/password-reset`
**Rate Limit**: 3 requests per hour per email
**Authentication**: None
**Requirement**: FR-010 (password reset)

**Request Body**:

```json
{
  "email": "user@example.com"
}
```

**Success Response** (200 OK):

```json
{
  "success": true,
  "data": {
    "message": "If an account exists with this email, a password reset link has been sent."
  }
}
```

**Note**: Always returns success to prevent email enumeration attacks, even if email doesn't exist.

**Post-Conditions**:
- Token created with 1-hour expiration
- Email sent with reset link
- SC-006: Email delivery initiated within 10 seconds

---

### 7. Confirm Password Reset

**Endpoint**: `POST /auth/password-reset/confirm`
**Rate Limit**: 10 requests per hour per IP
**Authentication**: None (token-based)
**Requirement**: FR-010 (password reset)

**Request Body**:

```json
{
  "token": "abc123...xyz",
  "new_password": "NewSecurePass456"
}
```

**Validation**:
- `new_password`: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit (FR-003)

**Success Response** (200 OK):

```json
{
  "success": true,
  "data": {
    "message": "Password reset successful. You can now log in with your new password."
  }
}
```

**Error Responses**:

- **400 Bad Request** (invalid token):

  ```json
  {
    "success": false,
    "error": {
      "code": "TOKEN_INVALID",
      "message": "Invalid or expired reset token"
    }
  }
  ```

- **400 Bad Request** (weak password):

  ```json
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Password must contain at least one digit"
    }
  }
  ```

**Post-Conditions**:
- Password updated with new hash
- Token marked as used
- All existing sessions for user invalidated (force re-login)
- SC-006: Full reset process completes in <3 minutes

---

### 8. Get Current User

**Endpoint**: `GET /auth/me`
**Rate Limit**: None
**Authentication**: Required (logged-in user)
**Requirement**: Session management (FR-007)

**Request Body**: None

**Success Response** (200 OK):

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "has_password": true,
      "has_google": true,
      "created_at": "2026-02-02T10:00:00Z",
      "last_login_at": "2026-02-02T14:30:00Z"
    }
  }
}
```

**Error Response**:

- **401 Unauthorized** (not logged in):

  ```json
  {
    "success": false,
    "error": {
      "code": "AUTH_REQUIRED",
      "message": "Authentication required"
    }
  }
  ```

---

### 9. Check Authentication Status

**Endpoint**: `GET /auth/status`
**Rate Limit**: None
**Authentication**: None
**Requirement**: Frontend session check

**Request Body**: None

**Success Response** (200 OK):

```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
}
```

**Or** (not authenticated):

```json
{
  "success": true,
  "data": {
    "authenticated": false
  }
}
```

**Performance**: <200ms response time (per Technical Context)

---

## Session Management

### Session Cookie

**Name**: `session`
**Type**: HTTP-only, Secure (HTTPS only in production)
**SameSite**: `Lax`
**Max-Age**: 30 days (2,592,000 seconds per FR-009)

### Session Validation

All endpoints marked "Authentication: Required" must:
1. Check for valid session cookie
2. Verify session exists in database and not expired
3. Update `last_accessed_at` timestamp
4. Return 401 if session invalid or expired

### Session Expiration

Per FR-009:
- Sessions expire after 30 days of inactivity
- Explicit logout immediately invalidates session
- Password reset invalidates all sessions

---

## Rate Limiting Details

Rate limiting is enforced using Flask-Limiter per FR-014:

| Endpoint | Limit | Window | Key |
|----------|-------|--------|-----|
| `/auth/register` | 10 | 1 hour | IP address |
| `/auth/login` | 5 | 15 minutes | Email address |
| `/auth/google` | 20 | 1 hour | IP address |
| `/auth/password-reset` | 3 | 1 hour | Email address |
| `/auth/password-reset/confirm` | 10 | 1 hour | IP address |

**Rate Limit Headers** (included in all responses):

```text
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1643814000
```

---

## Security Headers

All responses include:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

---

## CORS Configuration

For development:
- `Access-Control-Allow-Origin: http://localhost:5000`
- `Access-Control-Allow-Credentials: true`

For production:
- `Access-Control-Allow-Origin: https://your-domain.com`
- `Access-Control-Allow-Credentials: true`

---

## Testing Notes

Per constitution test isolation requirements:
- Google OAuth responses must be mocked
- Email sending must be mocked
- Rate limiting uses in-memory storage in tests
- Database uses test database (DATABASE_URL_TEST)
