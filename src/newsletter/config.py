"""Configuration management for newsletter senders."""

import json
from pathlib import Path
from typing import Dict, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict


class ModelConfig(BaseModel):
    """LLM model configuration."""
    parsing: str
    consolidation: str


class SenderConfig(BaseModel):
    """Configuration for a newsletter sender."""
    parsing_prompt: str
    enabled: bool
    created_at: str


class NewsletterConfig(BaseModel):
    """Newsletter configuration including exclusions.

    Stored in config/senders.json at root level.
    """
    model_config = ConfigDict(strict=False)

    senders: Dict[str, Dict[str, Any]]
    consolidation_prompt: str = Field(default="")  # Falls back to default_consolidation_prompt if empty
    retention_limit: int
    days_lookback: int
    max_workers: int
    default_parsing_prompt: str
    default_consolidation_prompt: str
    models: Dict[str, str]

    excluded_topics: list[str] = Field(
        default_factory=list,
        description="List of topics to exclude from consolidated newsletters"
    )

    @field_validator('excluded_topics')
    @classmethod
    def validate_exclusions(cls, v: list[str]) -> list[str]:
        """Validate exclusion list constraints.

        Rules:
        - Maximum 50 topics
        - Each topic maximum 100 characters
        - No empty strings
        - Duplicates allowed (per spec clarifications)
        """
        if len(v) > 50:
            raise ValueError("Maximum 50 excluded topics allowed")

        for i, topic in enumerate(v):
            topic_stripped = topic.strip()
            if not topic_stripped:
                raise ValueError(f"Topic at index {i} cannot be empty or whitespace")
            if len(topic) > 100:
                raise ValueError(
                    f"Topic '{topic[:50]}...' exceeds 100 character limit "
                    f"({len(topic)} characters)"
                )

        return v


def load_config(path: Path | str = Path("config/senders.json")) -> NewsletterConfig:
    """Load newsletter configuration from JSON file.

    Args:
        path: Path to configuration file

    Returns:
        NewsletterConfig: Validated configuration object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config doesn't match schema
    """
    if isinstance(path, str):
        path = Path(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return NewsletterConfig(**data)


def save_config(config: NewsletterConfig, path: Path | str = Path("config/senders.json")) -> None:
    """Save newsletter configuration to JSON file atomically.

    Uses atomic write pattern (write to temp file, then rename) for safety.

    Args:
        config: Configuration object to save
        path: Path to configuration file
    """
    if isinstance(path, str):
        path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

    # Atomic rename (POSIX guarantees atomicity)
    temp_path.replace(path)


def load_senders_config(config_path: str = "config/senders.json") -> Dict[str, Any]:
    """
    Load newsletter senders configuration from JSON file.

    Args:
        config_path: Path to senders configuration file

    Returns:
        Dictionary of sender configurations
    """
    path = Path(config_path)
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("senders", {})
    except Exception:
        return {}


def save_senders_config(senders: Dict[str, Any], config_path: str = "config/senders.json") -> None:
    """
    Save newsletter senders configuration to JSON file.

    Args:
        senders: Dictionary of sender configurations
        config_path: Path to senders configuration file
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing config to preserve other settings
    existing_config = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except Exception:
            pass

    # Update senders section
    existing_config["senders"] = senders

    # Write back to file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing_config, f, indent=2, ensure_ascii=False)
