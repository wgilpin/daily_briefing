"""Configuration management for newsletter senders."""

import json
from pathlib import Path
from typing import Dict, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.db.repository import Repository
from src.models.newsletter_models import SenderRecord


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
    """Load newsletter configuration from the database.

    Args:
        path: Unused — kept for backward-compatible signature.

    Returns:
        NewsletterConfig: Validated configuration object
    """
    repo = Repository()
    db_config = repo.get_newsletter_config()
    senders_list = repo.get_all_senders()
    senders_dict: Dict[str, Any] = {
        s.email: {
            "parsing_prompt": s.parsing_prompt,
            "enabled": s.enabled,
            "display_name": s.display_name,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in senders_list
    }

    defaults: Dict[str, Any] = {
        "senders": senders_dict,
        "consolidation_prompt": "",
        "retention_limit": 100,
        "days_lookback": 30,
        "max_workers": 10,
        "default_parsing_prompt": "",
        "default_consolidation_prompt": "",
        "models": {"parsing": "gemini-2.0-flash", "consolidation": "gemini-2.0-flash"},
        "excluded_topics": [],
    }
    defaults.update(db_config)
    defaults["senders"] = senders_dict
    return NewsletterConfig(**defaults)


def save_config(config: NewsletterConfig, path: Path | str = Path("config/senders.json")) -> None:
    """Persist newsletter configuration to the database.

    Args:
        config: Configuration object to save
        path: Unused — kept for backward-compatible signature.
    """
    repo = Repository()
    values: Dict[str, str] = {
        "consolidation_prompt": config.consolidation_prompt,
        "retention_limit": str(config.retention_limit),
        "days_lookback": str(config.days_lookback),
        "max_workers": str(config.max_workers),
        "default_parsing_prompt": config.default_parsing_prompt,
        "default_consolidation_prompt": config.default_consolidation_prompt,
        "models": json.dumps(config.models),
        "excluded_topics": json.dumps(config.excluded_topics),
    }
    repo.set_config_values(values)


def load_senders_config(config_path: str = "config/senders.json") -> Dict[str, SenderRecord]:
    """Load newsletter senders from the database.

    Args:
        config_path: Unused — kept for backward-compatible signature.

    Returns:
        Dict mapping email to SenderRecord.
    """
    repo = Repository()
    senders = repo.get_all_senders()
    return {s.email: s for s in senders}


def save_senders_config(senders: Dict[str, Any], config_path: str = "config/senders.json") -> None:
    """Persist newsletter senders to the database.

    Args:
        senders: Dict mapping email to SenderRecord (or legacy dict).
        config_path: Unused — kept for backward-compatible signature.
    """
    repo = Repository()
    for email, sender_data in senders.items():
        if isinstance(sender_data, SenderRecord):
            record = sender_data
        else:
            record = SenderRecord(
                email=email,
                display_name=sender_data.get("display_name"),
                parsing_prompt=sender_data.get("parsing_prompt", ""),
                enabled=sender_data.get("enabled", True),
            )
        if repo.sender_exists(email):
            repo.update_sender(record)
        else:
            repo.add_sender(record)
