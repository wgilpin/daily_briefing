"""Configuration management for newsletter senders."""

import json
from pathlib import Path
from typing import Dict, Any


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
