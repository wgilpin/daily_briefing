"""Configuration management for Zotero API Digest."""

from dataclasses import dataclass


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

