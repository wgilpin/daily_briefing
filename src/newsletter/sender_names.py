"""Utility for getting sender display names from the database."""

from src.db.repository import Repository


def get_sender_display_name(sender_email: str) -> str | None:
    """Get friendly display name for a sender email from the database.

    Args:
        sender_email: Email address like "news@alphasignal.ai"

    Returns:
        Display name if configured, None if not found or not configured

    Examples:
        >>> get_sender_display_name("news@alphasignal.ai")
        'Alphasignal'  # if configured in DB
        >>> get_sender_display_name("unknown@example.com")
        None  # if not in DB
    """
    if not sender_email:
        return None

    try:
        repo = Repository()
        sender = repo.get_sender(sender_email)
        return sender.display_name if sender else None
    except Exception:
        return None
