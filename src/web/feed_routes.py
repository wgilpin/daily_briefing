"""Flask route handlers for unified feed."""

import logging
import os
from typing import Optional

from flask import Blueprint, make_response, render_template, request

from src.models.feed_item import FeedItem
from src.models.source import NewsletterConfig, ZoteroConfig
from src.services.feed import FeedService
from src.sources.newsletter import NewsletterSource
from src.sources.zotero import ZoteroSource

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

# Default page size for feed pagination
DEFAULT_PAGE_SIZE = 50


def get_feed_service_with_sources() -> FeedService:
    """Get FeedService with registered sources.

    Creates a FeedService instance with Zotero and Newsletter sources
    configured from environment variables.

    Returns:
        FeedService: Service instance with sources registered
    """
    service = FeedService()

    # Register Zotero source if configured
    zotero_library_id = os.environ.get("ZOTERO_LIBRARY_ID")
    zotero_api_key = os.environ.get("ZOTERO_API_KEY")
    if zotero_library_id and zotero_api_key:
        zotero_config = ZoteroConfig(
            library_id=zotero_library_id,
            api_key=zotero_api_key,
            days_lookback=7,
        )
        zotero_source = ZoteroSource(zotero_config)
        service.register_source(zotero_source)

    # Register Newsletter source
    newsletter_config = NewsletterConfig(
        sender_emails=[],  # Will be loaded from config file
        max_emails_per_refresh=20,
    )
    newsletter_source = NewsletterSource(newsletter_config)
    service.register_source(newsletter_source)

    return service


def get_feed_service() -> FeedService:
    """Get or create FeedService instance.

    Returns:
        FeedService: Service instance for feed operations
    """
    return FeedService()


@bp.route("/")
def feed():
    """
    Display unified feed homepage.

    Shows combined feed from Zotero and newsletters sorted by date.
    Supports filtering by source, date range, and search.

    Query Parameters:
        source: Filter by source type (all, zotero, newsletter)
        days: Filter to items from last N days
        page: Page number for pagination
        q: Search query string

    Returns:
        HTML: Rendered feed.html template
    """
    # Get filter parameters
    source_type = request.args.get("source", "all")
    if source_type == "all":
        source_type = None

    days_str = request.args.get("days", "7")
    days: Optional[int] = None
    if days_str:
        try:
            days = int(days_str)
        except ValueError:
            days = None

    page = request.args.get("page", 1, type=int)
    offset = (page - 1) * DEFAULT_PAGE_SIZE

    # Get search query
    query = request.args.get("q", "").strip()

    # Get feed items
    service = get_feed_service()

    if query:
        # Use search if query provided
        items = service.search_items(
            query=query,
            source_type=source_type,
            limit=DEFAULT_PAGE_SIZE,
            offset=offset,
        )
    else:
        items = service.get_unified_feed(
            source_type=source_type,
            limit=DEFAULT_PAGE_SIZE,
            offset=offset,
            days=days,
        )

    return render_template(
        "feed.html",
        items=items,
        source_type=source_type or "all",
        days=days,
        page=page,
        offset=offset,
        page_size=DEFAULT_PAGE_SIZE,
        query=query,
    )


@bp.route("/api/feed")
def api_feed():
    """
    Get feed items as HTMX partial.

    Returns HTML fragment with feed items for dynamic updates.

    Query Parameters:
        source: Filter by source type (all, zotero, newsletter)
        days: Filter to items from last N days
        offset: Number of items to skip
        q: Search query string

    Returns:
        HTML: HTMX response fragment with feed items
    """
    # Get filter parameters
    source_type = request.args.get("source", "all")
    if source_type == "all":
        source_type = None

    days_str = request.args.get("days", "")
    days: Optional[int] = None
    if days_str:
        try:
            days = int(days_str)
        except ValueError:
            days = None

    offset = request.args.get("offset", 0, type=int)

    # Get search query
    query = request.args.get("q", "").strip()

    # Get feed items
    service = get_feed_service()

    if query:
        # Use search if query provided
        items = service.search_items(
            query=query,
            source_type=source_type,
            limit=DEFAULT_PAGE_SIZE,
            offset=offset,
        )
    else:
        items = service.get_unified_feed(
            source_type=source_type,
            limit=DEFAULT_PAGE_SIZE,
            offset=offset,
            days=days,
        )

    if not items:
        if query:
            return f"""
            <div class="empty-state">
                <p>No items found matching "{query}".</p>
                <p>Try a different search term or clear the search.</p>
            </div>
            """
        return """
        <div class="empty-state">
            <p>No feed items found.</p>
            <p>Click "Refresh Feed" to fetch items from your sources.</p>
        </div>
        """

    # Render items
    html_parts = []
    for item in items:
        html_parts.append(_render_feed_item(item))

    return "\n".join(html_parts)


@bp.route("/api/refresh", methods=["POST"])
def api_refresh():
    """
    Trigger refresh of all feed sources.

    Fetches new items from all configured sources and saves them
    to the database. Returns HTMX partial with status and triggers feed reload.

    Returns:
        HTML: HTMX response fragment with refresh status
    """
    try:
        service = get_feed_service_with_sources()
        result = service.refresh_all()

        if result["success"]:
            # Build status message
            source_messages = []
            for source_type, source_result in result["sources"].items():
                if source_result["error"]:
                    source_messages.append(
                        f"{source_type.capitalize()}: Failed ({source_result['error'][:50]})"
                    )
                else:
                    source_messages.append(
                        f"{source_type.capitalize()}: {source_result['items_fetched']} items"
                    )

            # Check if any source had errors (partial success)
            has_errors = any(
                s["error"] for s in result["sources"].values()
            )

            if has_errors:
                status_class = "partial"
                status_text = "Partial refresh complete"
            else:
                status_class = "success"
                status_text = "Refresh complete"

            response = make_response(f"""
            <div id="refresh-status" class="status {status_class}">
                <p><strong>{status_text}</strong></p>
                <p>{'. '.join(source_messages)}</p>
                <p>Total: {result['total_items']} items fetched</p>
            </div>
            """)
            # Trigger feed reload after status is shown
            response.headers['HX-Trigger'] = 'feedRefreshed'
            return response
        else:
            return """
            <div id="refresh-status" class="status error">
                <p><strong>Refresh failed</strong></p>
                <p>Could not fetch from any sources. Check your configuration.</p>
            </div>
            """

    except Exception as e:
        logger.error(f"Error during refresh: {e}")
        return f"""
        <div id="refresh-status" class="status error">
            <p><strong>Refresh failed</strong></p>
            <p>Error: {str(e)[:100]}</p>
        </div>
        """


@bp.route("/api/health")
def api_health():
    """
    Health check endpoint for container orchestration.

    Returns JSON with health status of the application and its dependencies.

    Returns:
        JSON: Health status with database and source configuration status
    """
    import json
    from flask import Response

    health = {
        "status": "healthy",
        "database": "unknown",
        "sources": {},
    }

    # Check database connection
    try:
        from src.db.connection import get_connection
        conn = get_connection()
        if conn and not conn.closed:
            health["database"] = "connected"
        else:
            health["database"] = "disconnected"
            health["status"] = "unhealthy"
    except Exception as e:
        health["database"] = "disconnected"
        health["error"] = str(e)[:100]
        health["status"] = "unhealthy"

    # Check source configuration
    zotero_configured = bool(
        os.environ.get("ZOTERO_LIBRARY_ID") and os.environ.get("ZOTERO_API_KEY")
    )
    health["sources"]["zotero"] = "configured" if zotero_configured else "not configured"

    # Newsletter is always "configured" as it uses local storage
    health["sources"]["newsletter"] = "configured"

    status_code = 200 if health["status"] == "healthy" else 503
    return Response(
        json.dumps(health),
        status=status_code,
        mimetype="application/json"
    )


@bp.route("/settings")
def settings():
    """
    Display settings page.

    Shows configuration options for Zotero and newsletter sources.

    Returns:
        HTML: Rendered settings.html template
    """
    # Get Zotero config from environment
    zotero_library_id = os.environ.get("ZOTERO_LIBRARY_ID")
    zotero_api_key = os.environ.get("ZOTERO_API_KEY")
    zotero_configured = bool(zotero_library_id and zotero_api_key)

    # Get stored Zotero settings from repository
    try:
        from src.db.repository import Repository
        repo = Repository()
        zotero_source_config = repo.get_source_config("zotero")
        zotero_settings = zotero_source_config.settings if zotero_source_config else {}
    except Exception:
        zotero_settings = {}

    zotero_config = {
        "configured": zotero_configured,
        "library_id": zotero_library_id[:8] + "..." if zotero_library_id and len(zotero_library_id) > 8 else zotero_library_id,
        "days_lookback": zotero_settings.get("days_lookback", 7),
        "include_keywords": zotero_settings.get("include_keywords", []),
        "exclude_keywords": zotero_settings.get("exclude_keywords", []),
    }

    # Get newsletter config from the newsletter config file
    try:
        from src.newsletter.config import load_senders_config
        senders = load_senders_config()
    except Exception:
        senders = {}

    newsletter_config = {
        "configured": bool(senders),
        "senders": senders,
        "max_emails": 20,
    }

    return render_template(
        "settings.html",
        zotero_config=zotero_config,
        newsletter_config=newsletter_config,
    )


@bp.route("/api/settings/zotero", methods=["POST"])
def api_settings_zotero():
    """
    Update Zotero source settings.

    Form Parameters:
        days_lookback: Number of days to look back
        include_keywords: Comma-separated keywords to include
        exclude_keywords: Comma-separated keywords to exclude

    Returns:
        HTML: HTMX response fragment with status
    """
    try:
        from src.db.repository import Repository
        from src.models.source import SourceConfig

        days_lookback = request.form.get("days_lookback", "7")
        include_keywords = request.form.get("include_keywords", "")
        exclude_keywords = request.form.get("exclude_keywords", "")

        # Parse keywords
        include_list = [k.strip() for k in include_keywords.split(",") if k.strip()]
        exclude_list = [k.strip() for k in exclude_keywords.split(",") if k.strip()]

        # Get existing config or create new
        repo = Repository()
        existing = repo.get_source_config("zotero")

        settings = {
            "days_lookback": int(days_lookback),
            "include_keywords": include_list,
            "exclude_keywords": exclude_list,
        }

        config = SourceConfig(
            source_type="zotero",
            enabled=existing.enabled if existing else True,
            last_refresh=existing.last_refresh if existing else None,
            last_error=existing.last_error if existing else None,
            settings=settings,
        )
        repo.save_source_config(config)

        return """
        <div class="status success">
            <p>Zotero settings updated successfully.</p>
        </div>
        """
    except Exception as e:
        logger.error(f"Error updating Zotero settings: {e}")
        return f"""
        <div class="status error">
            <p>Error: {str(e)[:100]}</p>
        </div>
        """


@bp.route("/api/settings/newsletter", methods=["POST"])
def api_settings_newsletter():
    """
    Update newsletter source settings.

    Form Parameters:
        max_emails_per_refresh: Maximum emails to process per refresh

    Returns:
        HTML: HTMX response fragment with status
    """
    try:
        from src.db.repository import Repository
        from src.models.source import SourceConfig

        max_emails = request.form.get("max_emails_per_refresh", "20")

        repo = Repository()
        existing = repo.get_source_config("newsletter")

        settings = existing.settings if existing else {}
        settings["max_emails_per_refresh"] = int(max_emails)

        config = SourceConfig(
            source_type="newsletter",
            enabled=existing.enabled if existing else True,
            last_refresh=existing.last_refresh if existing else None,
            last_error=existing.last_error if existing else None,
            settings=settings,
        )
        repo.save_source_config(config)

        return """
        <div class="status success">
            <p>Newsletter settings updated successfully.</p>
        </div>
        """
    except Exception as e:
        logger.error(f"Error updating newsletter settings: {e}")
        return f"""
        <div class="status error">
            <p>Error: {str(e)[:100]}</p>
        </div>
        """


@bp.route("/api/settings/newsletter/senders", methods=["POST"])
def api_settings_newsletter_sender():
    """
    Add a new newsletter sender.

    Form Parameters:
        email: Email address of the sender to add

    Returns:
        HTML: HTMX response fragment with status
    """
    try:
        from src.newsletter.config import load_senders_config, save_senders_config

        email = request.form.get("email", "").strip().lower()
        if not email:
            return """
            <div class="status error">
                <p>Email address is required.</p>
            </div>
            """

        # Load existing senders and add new one
        senders = load_senders_config()
        if email in senders:
            return """
            <div class="status error">
                <p>This sender is already configured.</p>
            </div>
            """

        senders[email] = {
            "enabled": True,
            "parsing_prompt": "",
        }
        save_senders_config(senders)

        return f"""
        <div class="status success">
            <p>Sender {email} added successfully. Refresh the page to see the updated list.</p>
        </div>
        """
    except Exception as e:
        logger.error(f"Error adding newsletter sender: {e}")
        return f"""
        <div class="status error">
            <p>Error: {str(e)[:100]}</p>
        </div>
        """


@bp.route("/api/settings/newsletter/senders/<email>", methods=["DELETE"])
def api_settings_delete_sender(email: str):
    """
    Delete a newsletter sender.

    Args:
        email: Email address of the sender to delete

    Returns:
        HTML: HTMX response fragment with status
    """
    try:
        from src.newsletter.config import load_senders_config, save_senders_config

        senders = load_senders_config()
        if email not in senders:
            return """
            <div class="status error">
                <p>Sender not found.</p>
            </div>
            """

        del senders[email]
        save_senders_config(senders)

        return f"""
        <div class="status success">
            <p>Sender {email} deleted successfully. Refresh the page to see the updated list.</p>
        </div>
        """
    except Exception as e:
        logger.error(f"Error deleting newsletter sender: {e}")
        return f"""
        <div class="status error">
            <p>Error: {str(e)[:100]}</p>
        </div>
        """


def _render_feed_item(item: FeedItem) -> str:
    """Render a single feed item as HTML.

    Args:
        item: FeedItem to render

    Returns:
        str: HTML string for the feed item
    """
    # Format metadata
    metadata_html = ""
    if item.metadata:
        metadata_parts = []
        if item.metadata.get("authors"):
            metadata_parts.append(
                f'<span class="metadata-item"><strong>Authors:</strong> {item.metadata["authors"]}</span>'
            )
        if item.metadata.get("sender"):
            metadata_parts.append(
                f'<span class="metadata-item"><strong>From:</strong> {item.metadata["sender"]}</span>'
            )
        if metadata_parts:
            metadata_html = f'<div class="feed-item-metadata">{" ".join(metadata_parts)}</div>'

    # Format title with optional link
    if item.link:
        title_html = f'<a href="{item.link}" target="_blank" rel="noopener noreferrer">{item.title}</a>'
    else:
        title_html = item.title

    # Format summary
    summary_html = ""
    if item.summary:
        # Truncate to 300 chars
        summary = item.summary[:300] + "..." if len(item.summary) > 300 else item.summary
        summary_html = f'<p class="feed-item-summary">{summary}</p>'

    return f"""
    <article class="feed-item" data-source="{item.source_type}">
        <div class="feed-item-header">
            <span class="source-badge {item.source_type}">{item.source_type.capitalize()}</span>
            <time datetime="{item.date.isoformat()}">{item.date.strftime('%Y-%m-%d')}</time>
        </div>
        <h3 class="feed-item-title">{title_html}</h3>
        {summary_html}
        {metadata_html}
    </article>
    """
