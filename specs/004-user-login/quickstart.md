# Quickstart Guide: User Login Implementation

**Feature**: User Login (004-user-login)
**Date**: 2026-02-02
**Phase**: Phase 1 Design

## Overview

This guide provides step-by-step instructions for implementing the user authentication feature, following the project's constitution and TDD requirements.

## Prerequisites

- Python 3.13+
- uv package manager
- PostgreSQL database (Coolify)
- Google OAuth credentials
- SMTP credentials (for password reset emails)

## Environment Setup

### 1. Install Dependencies

Add new dependencies to `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "flask-login>=0.6.3",       # Session management
    "passlib[argon2]>=1.7.4",   # Password hashing
    "flask-limiter>=3.5.0",     # Rate limiting
]
```

Install:

```bash
uv sync
```

### 2. Environment Variables

Add to `.env`:

```bash
# Existing
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key-here

# New for authentication
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

### 3. Database Migration

Run the authentication migration:

```bash
# The migration will run automatically on app startup
# Or manually via psql:
psql $DATABASE_URL < src/db/migrations/002_auth.sql
```

## Implementation Order (TDD Required)

Follow this order to maintain TDD discipline per constitution:

### Phase A: Core Authentication Logic (TDD Required)

1. **Password Hashing** (`src/auth/password.py`)
   - Write tests first in `tests/unit/auth/test_password.py`
   - Test password hashing with Argon2
   - Test password verification
   - Test password strength validation
   - Implement

2. **Session Management** (`src/auth/session.py`)
   - Write tests first in `tests/unit/auth/test_session.py`
   - Test session creation
   - Test session validation
   - Test session expiration
   - Implement

3. **Authentication Service** (`src/auth/service.py`)
   - Write tests first in `tests/unit/auth/test_service.py`
   - Test user registration
   - Test user login
   - Test account merging (Google + email/password)
   - Test password reset token generation
   - Implement

### Phase B: Flask Integration (No TDD Required)

4. **Flask App Configuration** (`src/web/app.py`)
   - Initialize Flask-Login
   - Configure Flask-Limiter
   - Set session configuration
   - Add user_loader callback

5. **Auth Routes** (`src/web/auth_routes.py`)
   - Implement registration endpoint
   - Implement login endpoint
   - Implement logout endpoint
   - Implement Google OAuth flow
   - Implement password reset endpoints
   - Apply rate limiting decorators

6. **Templates** (`src/web/templates/auth/`)
   - Create login.html
   - Create register.html
   - Create reset_password.html
   - Create reset_password_confirm.html

### Phase C: Integration Testing

7. **Integration Tests** (`tests/integration/auth/test_auth_flow.py`)
   - Test full registration → login → logout flow
   - Test password reset flow
   - Test Google OAuth flow (mocked)
   - Test rate limiting enforcement
   - Test session persistence

## Detailed Implementation Steps

### Step 1: Create Auth Module Structure

```bash
mkdir -p src/auth
mkdir -p src/web/templates/auth
mkdir -p tests/unit/auth
mkdir -p tests/integration/auth
```

Create empty files:

```bash
touch src/auth/__init__.py
touch src/auth/models.py
touch src/auth/password.py
touch src/auth/session.py
touch src/auth/service.py
touch src/auth/oauth.py
```

### Step 2: Define Pydantic Models

In `src/auth/models.py`, create all models from [data-model.md](data-model.md):
- `UserModel`
- `UserRegistrationRequest`
- `UserLoginRequest`
- `SessionModel`
- `PasswordResetTokenModel`
- `PasswordResetRequest`
- `PasswordResetConfirm`

### Step 3: Implement Password Module (TDD)

**Write tests first** in `tests/unit/auth/test_password.py`:

```python
import pytest
from src.auth.password import hash_password, verify_password, validate_password_strength

def test_hash_password_returns_different_hash():
    """Test that hashing same password twice returns different hashes."""
    password = "SecurePass123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2  # Different salts

def test_verify_password_with_correct_password():
    """Test that verification succeeds with correct password."""
    password = "SecurePass123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_with_wrong_password():
    """Test that verification fails with wrong password."""
    password = "SecurePass123"
    hashed = hash_password(password)
    assert verify_password("WrongPass456", hashed) is False

def test_validate_password_strength_rejects_weak_passwords():
    """Test that weak passwords are rejected."""
    with pytest.raises(ValueError, match="at least 8 characters"):
        validate_password_strength("short")

    with pytest.raises(ValueError, match="uppercase letter"):
        validate_password_strength("nouppercase123")

    with pytest.raises(ValueError, match="lowercase letter"):
        validate_password_strength("NOLOWERCASE123")

    with pytest.raises(ValueError, match="digit"):
        validate_password_strength("NoDigitsHere")

def test_validate_password_strength_accepts_strong_passwords():
    """Test that strong passwords are accepted."""
    validate_password_strength("SecurePass123")  # Should not raise
```

**Run tests** (should fail):

```bash
pytest tests/unit/auth/test_password.py
```

**Implement** in `src/auth/password.py`:

```python
from passlib.context import CryptContext

# Configure password hashing with Argon2 (primary) and bcrypt (fallback)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def validate_password_strength(password: str) -> None:
    """Validate password meets strength requirements. Raises ValueError if invalid."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit")
```

**Run tests again** (should pass):

```bash
pytest tests/unit/auth/test_password.py
```

### Step 4: Implement Session Module (TDD)

Follow same TDD pattern:
1. Write tests in `tests/unit/auth/test_session.py`
2. Run tests (should fail)
3. Implement in `src/auth/session.py`
4. Run tests (should pass)

### Step 5: Implement Authentication Service (TDD)

Follow same TDD pattern:
1. Write tests in `tests/unit/auth/test_service.py`
2. Mock database calls
3. Run tests (should fail)
4. Implement in `src/auth/service.py`
5. Run tests (should pass)

### Step 6: Configure Flask App

In `src/web/app.py`, add initialization:

```python
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def create_app() -> Flask:
    app = Flask(__name__)

    # Existing configuration...

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from src.auth.service import get_user_by_id
        return get_user_by_id(int(user_id))

    # Flask-Limiter setup
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        storage_uri=os.environ.get("DATABASE_URL"),
        default_limits=["200 per day", "50 per hour"]
    )

    # Register auth blueprint
    from src.web.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp)

    return app
```

### Step 7: Implement Auth Routes

Create `src/web/auth_routes.py`:

```python
from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Get limiter from app
limiter = None  # Will be set by app.py

@bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    """Handle user registration."""
    # Implementation per API contract
    pass

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def login():
    """Handle user login."""
    # Implementation per API contract
    pass

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return jsonify({"success": True, "data": {"message": "Logged out successfully"}})

# ... other endpoints per API contract
```

### Step 8: Create HTML Templates

Create minimal templates in `src/web/templates/auth/`:
- `login.html`: Login form with email/password and Google OAuth button
- `register.html`: Registration form
- `reset_password.html`: Request password reset form
- `reset_password_confirm.html`: Set new password form

### Step 9: Protect Existing Routes

In `src/web/feed_routes.py`, add authentication:

```python
from flask_login import login_required

@bp.route('/')
@login_required
def index():
    """Home page (now requires authentication)."""
    # Existing implementation
    pass
```

### Step 10: Integration Testing

Create `tests/integration/auth/test_auth_flow.py`:

```python
import pytest
from src.web.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_register_login_logout_flow(client):
    """Test complete authentication flow."""
    # Register
    response = client.post('/auth/register', json={
        "email": "test@example.com",
        "password": "SecurePass123",
        "name": "Test User"
    })
    assert response.status_code == 201

    # Logout
    response = client.post('/auth/logout')
    assert response.status_code == 200

    # Login
    response = client.post('/auth/login', json={
        "email": "test@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 200
```

## Code Quality Checks

Before committing, run:

```bash
# Format check
ruff check --fix src/ tests/

# Type check
mypy src/

# Run all tests
pytest

# Specific test suites
pytest tests/unit/auth/
pytest tests/integration/auth/
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:5000/auth/google/callback`
6. Copy Client ID and Client Secret to `.env`

## SMTP Setup (Gmail Example)

1. Enable 2-factor authentication on Gmail account
2. Generate App Password: Account Settings → Security → App Passwords
3. Add credentials to `.env`:
   - `SMTP_USER`: your Gmail address
   - `SMTP_PASSWORD`: generated app password

## Common Issues

### Issue: Argon2 import error

**Solution**: Ensure argon2_cffi is installed:

```bash
uv pip install passlib[argon2]
```

### Issue: Database connection error

**Solution**: Verify DATABASE_URL is correct:

```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Issue: Rate limiting not working in tests

**Solution**: Use in-memory storage for tests:

```python
# In test configuration
app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
```

### Issue: Google OAuth redirect mismatch

**Solution**: Ensure redirect URI in Google Console exactly matches GOOGLE_REDIRECT_URI in `.env`

## Testing Checklist

Before marking feature complete:

- [ ] All unit tests pass (`pytest tests/unit/auth/`)
- [ ] All integration tests pass (`pytest tests/integration/auth/`)
- [ ] ruff linting passes (`ruff check src/ tests/`)
- [ ] mypy type checking passes (`mypy src/`)
- [ ] Manual testing completed:
  - [ ] Register new account
  - [ ] Login with email/password
  - [ ] Login with Google OAuth
  - [ ] Request password reset
  - [ ] Complete password reset
  - [ ] Account merging (OAuth with existing email)
  - [ ] Rate limiting triggers correctly
  - [ ] Session persists across page refreshes
  - [ ] Logout clears session
  - [ ] Protected routes redirect to login

## Next Steps

After implementation:
1. Run `/speckit.tasks` to generate detailed task breakdown
2. Follow tasks in dependency order
3. Mark tasks complete as you go
4. Create PR when all tasks complete

## Reference Documentation

- [Feature Spec](spec.md)
- [Implementation Plan](plan.md)
- [Research Findings](research.md)
- [Data Model](data-model.md)
- [API Contracts](contracts/auth-api.md)
