"""Utility for getting sender display names from configuration."""

from src.utils.config import load_config


def get_sender_display_name(sender_email: str) -> str | None:
    """Get friendly display name for a sender email from configuration.

    Args:
        sender_email: Email address like "news@alphasignal.ai"

    Returns:
        Display name if configured, None if not found or not configured

    Examples:
        >>> get_sender_display_name("news@alphasignal.ai")
        'Alphasignal'  # if configured in senders.json
        >>> get_sender_display_name("unknown@example.com")
        None  # if not in configuration
    """
    if not sender_email:
        return None

    try:
        config = load_config("config/senders.json")
        senders = config.get("senders", {})

        sender_config = senders.get(sender_email, {})
        return sender_config.get("display_name")
    except Exception:
        return None
