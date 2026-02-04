"""Pydantic models for user authentication."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import secrets
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Simple email regex - no DNS lookups or complex validation needed
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class UserModel(BaseModel):
    """User account model."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    email: str
    password_hash: Optional[str] = None
    google_id: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Simple email format validation."""
        if not EMAIL_REGEX.match(v):
            raise ValueError("Please enter a valid email address")
        return v.lower()


class UserRegistrationRequest(BaseModel):
    """User registration request."""

    email: str
    password: str = Field(min_length=8, max_length=128)
    name: Optional[str] = Field(None, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Simple email format validation."""
        if not EMAIL_REGEX.match(v):
            raise ValueError("Please enter a valid email address")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements (FR-003)."""
        if len(v) < 8:
            raise ValueError("Your password needs to be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Please include at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Please include at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Please include at least one number")
        return v


class UserLoginRequest(BaseModel):
    """User login request."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Simple email format validation."""
        if not EMAIL_REGEX.match(v):
            raise ValueError("Please enter a valid email address")
        return v.lower()


class SessionModel(BaseModel):
    """User session model."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str
    user_id: int
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class PasswordResetTokenModel(BaseModel):
    """Password reset token model."""

    model_config = ConfigDict(from_attributes=True)

    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    user_id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1)
    )
    used: bool = False
    used_at: Optional[datetime] = None


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Simple email format validation."""
        if not EMAIL_REGEX.match(v):
            raise ValueError("Please enter a valid email address")
        return v.lower()


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation with new password."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements (FR-003)."""
        if len(v) < 8:
            raise ValueError("Your password needs to be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Please include at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Please include at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Please include at least one number")
        return v
