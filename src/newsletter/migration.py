"""One-time migration of senders.json configuration to PostgreSQL."""

import json
from pathlib import Path

from src.db.repository import Repository
from src.models.newsletter_models import SenderRecord


def migrate_senders_if_needed(config_path: Path) -> None:
    """Migrate senders.json to the database if it exists.

    Algorithm:
    - If config_path does not exist: return immediately (no-op)
    - Parse JSON; raise RuntimeError on JSONDecodeError
    - For each sender: insert if not already in DB (DB wins on conflict)
    - For each global config key: insert if not already in DB (DB wins on conflict)
    - Rename config_path to config_path.parent / (config_path.name + '.bak')

    Args:
        config_path: Absolute path to the senders.json file.

    Raises:
        RuntimeError: If the file contains invalid JSON (aborts startup).
    """
    if not config_path.exists():
        return

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Failed to parse {config_path}: {exc}. Fix or remove the file before starting."
        ) from exc

    repo = Repository()

    # Migrate senders
    senders = data.get("senders", {})
    for email, sender_data in senders.items():
        if not repo.sender_exists(email):
            record = SenderRecord(
                email=email,
                display_name=sender_data.get("display_name"),
                parsing_prompt=sender_data.get("parsing_prompt", ""),
                enabled=sender_data.get("enabled", True),
            )
            repo.add_sender(record)

    # Migrate global config keys (everything except "senders")
    json_keys = {"models", "excluded_topics"}
    for key, value in data.items():
        if key == "senders":
            continue
        if not repo.config_key_exists(key):
            str_value = json.dumps(value) if key in json_keys else str(value)
            repo.set_config_value(key, str_value)

    # Rename the file so it won't be processed again
    bak_path = config_path.parent / (config_path.name + ".bak")
    config_path.rename(bak_path)
