"""Configuration management for the unified feed application.

Provides environment variable loading and validation for:
- Zotero API credentials
- Newsletter/Gmail configuration
- PostgreSQL database connection
- Encryption keys for OAuth token storage
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


# =============================================================================
# Unified Feed App Environment Configuration
# =============================================================================


def get_database_url() -> str:
    """Get PostgreSQL database URL from environment.

    Returns:
        str: DATABASE_URL connection string

    Raises:
        ValueError: If DATABASE_URL is not set
    """
    load_dotenv()
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise ValueError(
            "Missing required environment variable: DATABASE_URL\n"
            "Please set DATABASE_URL to your PostgreSQL connection string.\n"
            "Example: postgresql://user:password@localhost:5432/daily_briefing"
        )
    return url


def get_encryption_key() -> str:
    """Get encryption key for OAuth token storage.

    Returns:
        str: ENCRYPTION_KEY for Fernet encryption (32 bytes, base64-encoded)

    Raises:
        ValueError: If ENCRYPTION_KEY is not set
    """
    load_dotenv()
    key = os.getenv("ENCRYPTION_KEY", "").strip()
    if not key:
        raise ValueError(
            "Missing required environment variable: ENCRYPTION_KEY\n"
            "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return key


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment.

    Returns:
        str: GEMINI_API_KEY

    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "Missing required environment variable: GEMINI_API_KEY\n"
            "Get your API key from: https://aistudio.google.com/apikey"
        )
    return key


def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an optional environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        str or None: The environment variable value or default
    """
    load_dotenv()
    value = os.getenv(key, "").strip()
    return value if value else default


# =============================================================================
# Legacy Zotero Configuration (preserved for backwards compatibility)
# =============================================================================


@dataclass
class Configuration:
    """Application configuration loaded from environment variables and CLI arguments."""

    library_id: str
    api_key: str
    output_path: str = "digest.md"
    days: int = 1
    include_keywords: list[str] = None
    exclude_keywords: list[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.library_id or not self.library_id.strip():
            raise ValueError(
                "ZOTERO_LIBRARY_ID is required. "
                "Set it in your .env file or environment variables."
            )
        if not self.api_key or not self.api_key.strip():
            raise ValueError(
                "ZOTERO_API_KEY is required. "
                "Set it in your .env file or environment variables."
            )
        if self.days <= 0:
            raise ValueError("days must be a positive integer")
        if self.include_keywords is None:
            self.include_keywords = []
        if self.exclude_keywords is None:
            self.exclude_keywords = []


def load_configuration() -> Configuration:
    """
    Load configuration from environment variables and CLI arguments.

    Loads .env file if present, reads ZOTERO_LIBRARY_ID and ZOTERO_API_KEY
    from environment, and merges with CLI arguments.

    Returns:
        Configuration: Validated configuration object

    Raises:
        ValueError: If required credentials are missing or invalid
    """
    import os
    from dotenv import load_dotenv

    # Load .env file if it exists
    load_dotenv()

    # Read required credentials from environment
    library_id = os.getenv("ZOTERO_LIBRARY_ID", "").strip()
    api_key = os.getenv("ZOTERO_API_KEY", "").strip()

    # Validate required fields
    if not library_id:
        raise ValueError(
            "Missing required environment variable: ZOTERO_LIBRARY_ID\n"
            "Please create a .env file with:\n"
            "ZOTERO_LIBRARY_ID=your_library_id\n"
            "ZOTERO_API_KEY=your_api_key\n\n"
            "Get your credentials from: https://www.zotero.org/settings/keys"
        )
    if not api_key:
        raise ValueError(
            "Missing required environment variable: ZOTERO_API_KEY\n"
            "Please create a .env file with:\n"
            "ZOTERO_LIBRARY_ID=your_library_id\n"
            "ZOTERO_API_KEY=your_api_key\n\n"
            "Get your credentials from: https://www.zotero.org/settings/keys"
        )

    # Create configuration with defaults
    # CLI arguments will be merged later in the CLI module
    return Configuration(
        library_id=library_id,
        api_key=api_key,
        output_path="digest.md",
        days=1,
        include_keywords=[],
        exclude_keywords=[],
    )


# Newsletter Aggregator Configuration Functions
# These functions are separate from the Zotero Configuration class above


def load_config(config_path: str) -> dict:
    """
    Load newsletter configuration from JSON file.

    Loads configuration from config/senders.json with defaults applied if keys are missing.
    If the file doesn't exist, raises ValueError (models are required, no defaults).

    Args:
        config_path: Path to config/senders.json file

    Returns:
        dict: Configuration dictionary with keys:
            - models: dict with "parsing" and "consolidation" model names (REQUIRED)
            - senders: dict mapping sender email to configuration
            - consolidation_prompt: str prompt for consolidation
            - retention_limit: int number of records to keep (default: 100)
            - default_parsing_prompt: str default prompt for parsing newsletters

    Raises:
        ValueError: If file doesn't exist or models configuration is missing/invalid
        json.JSONDecodeError: If file exists but contains invalid JSON
    """
    import json
    from pathlib import Path

    config_path_obj = Path(config_path)

    # If file doesn't exist, raise error (no defaults for models)
    if not config_path_obj.exists():
        raise ValueError(
            f"Configuration file not found: {config_path}\n"
            "Please create config/senders.json with:\n"
            '{\n'
            '  "models": {\n'
            '    "parsing": "gemini-2.5-flash",\n'
            '    "consolidation": "gemini-2.5-flash"\n'
            '  },\n'
            '  "senders": {},\n'
            '  "consolidation_prompt": "",\n'
            '  "retention_limit": 100\n'
            '}'
        )

    # Load and parse JSON
    with open(config_path_obj, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    # Apply defaults for missing keys (but NOT for models - that's required)
    defaults = {
        "senders": {},
        "consolidation_prompt": "",
        "retention_limit": 100,
        "max_workers": 5,
        "default_parsing_prompt": (
            "Extract articles from this newsletter. "
            "Return a JSON array with items containing: date, title, summary, link (optional)."
        ),
        "default_consolidation_prompt": (
            "Create a consolidated newsletter digest from these items. "
            "Group similar topics together and create a well-formatted markdown document. "
            "Organize by topic and include all relevant information. "
            "Use clear headings and sections to make it easy to read."
        ),
    }

    result = {**defaults, **config_data}
    
    # Validate required models configuration
    if "models" not in result:
        raise ValueError(
            "Missing 'models' configuration in config/senders.json.\n"
            "Please add:\n"
            '  "models": {\n'
            '    "parsing": "gemini-2.5-flash",\n'
            '    "consolidation": "gemini-2.5-flash"\n'
            "  }"
        )
    
    if not isinstance(result["models"], dict):
        raise ValueError("'models' configuration must be a dictionary")
    
    if "parsing" not in result["models"]:
        raise ValueError(
            "Missing 'parsing' model in config/senders.json.\n"
            "Please add: \"parsing\": \"gemini-2.5-flash\" to the models section"
        )
    
    if "consolidation" not in result["models"]:
        raise ValueError(
            "Missing 'consolidation' model in config/senders.json.\n"
            "Please add: \"consolidation\": \"gemini-2.5-flash\" to the models section"
        )

    # Ensure senders is a dict
    if not isinstance(result.get("senders"), dict):
        result["senders"] = {}

    # Ensure retention_limit is an integer
    if not isinstance(result.get("retention_limit"), int):
        result["retention_limit"] = 100

    # Ensure max_workers is an integer
    if not isinstance(result.get("max_workers"), int):
        result["max_workers"] = 5
    elif result.get("max_workers") < 1:
        result["max_workers"] = 1  # At least 1 worker
    elif result.get("max_workers") > 20:
        result["max_workers"] = 20  # Cap at 20 to avoid overwhelming the API

    return result


def save_config(config_path: str, config: dict) -> None:
    """
    Save newsletter configuration to JSON file.

    Saves configuration to config/senders.json with pretty-printed JSON formatting.
    Creates directory structure if needed.

    Args:
        config_path: Path to config/senders.json file
        config: Configuration dictionary to save

    Raises:
        OSError: If file cannot be written
        TypeError: If config cannot be serialized to JSON
    """
    import json
    from pathlib import Path

    config_path_obj = Path(config_path)

    # Create parent directory if it doesn't exist
    config_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with pretty formatting
    with open(config_path_obj, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
