"""OAuth token encryption utilities.

Uses Fernet symmetric encryption for secure token storage.
"""

import json
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


def _get_fernet() -> Fernet:
    """Get Fernet cipher using ENCRYPTION_KEY from environment.

    Returns:
        Fernet cipher instance

    Raises:
        ValueError: If ENCRYPTION_KEY is not set
    """
    encryption_key = os.environ.get("ENCRYPTION_KEY")
    if not encryption_key:
        raise ValueError("ENCRYPTION_KEY environment variable is required")

    # Derive a proper 32-byte key using PBKDF2
    # Using a static salt since we need deterministic key derivation
    # The ENCRYPTION_KEY provides the entropy
    salt = b"daily_briefing_oauth_token_salt"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
    return Fernet(key)


def encrypt_token(token_data: dict[str, Any]) -> bytes:
    """Encrypt OAuth token data.

    Args:
        token_data: Dictionary containing OAuth token information

    Returns:
        Encrypted token as bytes

    Raises:
        ValueError: If ENCRYPTION_KEY is not set
    """
    fernet = _get_fernet()
    json_bytes = json.dumps(token_data).encode("utf-8")
    return fernet.encrypt(json_bytes)


def decrypt_token(encrypted_data: bytes) -> dict[str, Any]:
    """Decrypt OAuth token data.

    Args:
        encrypted_data: Encrypted token bytes

    Returns:
        Decrypted token dictionary

    Raises:
        ValueError: If ENCRYPTION_KEY is not set
        cryptography.fernet.InvalidToken: If decryption fails
    """
    fernet = _get_fernet()
    decrypted = fernet.decrypt(encrypted_data)
    return json.loads(decrypted.decode("utf-8"))
