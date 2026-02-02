"""Unit tests for password hashing and validation module."""

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


def test_validate_password_strength_rejects_too_short():
    """Test that passwords under 8 characters are rejected."""
    with pytest.raises(ValueError, match="at least 8 characters"):
        validate_password_strength("short")


def test_validate_password_strength_rejects_no_uppercase():
    """Test that passwords without uppercase letters are rejected."""
    with pytest.raises(ValueError, match="uppercase letter"):
        validate_password_strength("nouppercase123")


def test_validate_password_strength_rejects_no_lowercase():
    """Test that passwords without lowercase letters are rejected."""
    with pytest.raises(ValueError, match="lowercase letter"):
        validate_password_strength("NOLOWERCASE123")


def test_validate_password_strength_rejects_no_digit():
    """Test that passwords without digits are rejected."""
    with pytest.raises(ValueError, match="digit"):
        validate_password_strength("NoDigitsHere")


def test_validate_password_strength_accepts_strong_passwords():
    """Test that strong passwords are accepted."""
    validate_password_strength("SecurePass123")  # Should not raise


def test_hash_password_uses_argon2():
    """Test that password hashes use Argon2 algorithm."""
    password = "SecurePass123"
    hashed = hash_password(password)
    # Argon2 hashes start with $argon2
    assert hashed.startswith("$argon2")
