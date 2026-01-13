"""Flask route handlers for newsletter aggregator."""

import logging
import re
from datetime import datetime
from pathlib import Path

from flask import Blueprint, render_template, request, send_file

from src.newsletter.consolidator import consolidate_newsletters
from src.newsletter.email_collector import (
    collect_newsletter_emails,
    convert_emails_to_markdown,
    parse_newsletters,
)
from src.newsletter.parser import create_llm_client
from src.newsletter.storage import (
    get_all_parsed_items,
    get_processed_message_ids,
    save_consolidated_digest,
)
from src.utils.config import load_config, save_config

bp = Blueprint("newsletter", __name__)
logger = logging.getLogger(__name__)


@bp.route("/")
def index():
    """
    Display main dashboard.

    Shows collection status, number of processed emails, and provides
    buttons to trigger email collection.

    Returns:
        HTML: Rendered index.html template
    """
    # Load configuration to get sender count
    config = load_config("config/senders.json")
    senders = config.get("senders", {})
    enabled_senders = [
        email
        for email, sender_config in senders.items()
        if sender_config.get("enabled", True)
    ]

    # Get count of processed emails
    processed_ids = get_processed_message_ids("data/newsletter_aggregator.db")
    processed_count = len(processed_ids)

    # Get count of parsed items
    parsed_items = get_all_parsed_items("data/newsletter_aggregator.db")
    parsed_items_count = len(parsed_items)

    # Get count of parsed emails (emails that have been successfully parsed)
    db_path = "data/newsletter_aggregator.db"
    import sqlite3
    parsed_emails_count = 0
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE status = 'parsed'")
        parsed_emails_count = cursor.fetchone()[0]
        conn.close()
    except Exception:
        pass  # If database doesn't exist or query fails, use 0

    return render_template(
        "index.html",
        enabled_senders_count=len(enabled_senders),
        processed_count=processed_count,
        parsed_items_count=parsed_items_count,
        parsed_emails_count=parsed_emails_count,
    )


@bp.route("/collect", methods=["POST"])
def collect():
    """
    Trigger email collection from Gmail.

    Collects emails from configured senders and returns HTMX response
    with status update.

    Returns:
        HTML: HTMX response fragment with collection status
    """
    logger.info("=== Collecting emails from Gmail ===")
    result = collect_newsletter_emails()
    logger.info(f"Collection result: {result}")

    if result["success"]:
        status_class = "success"
        status_message = f"Successfully collected {result['emails_collected']} email(s)"
    else:
        status_class = "error"
        status_message = "Collection failed"
        if result["errors"]:
            status_message += ": " + "; ".join(result["errors"])

    # Return HTMX response fragment
    return f"""
    <div id="collection-status" class="status {status_class}">
        <p>{status_message}</p>
    </div>
    <div id="collection-stats">
        <p>Emails collected: {result['emails_collected']}</p>
    </div>
    """


@bp.route("/process", methods=["POST"])
def process():
    """
    Process collected emails (convert to markdown and parse).

    Converts collected emails to markdown format, then parses them using LLM
    with configurable prompts. Returns HTMX response with status update.

    Returns:
        HTML: HTMX response fragment with processing status
    """
    logger.info("=== Processing emails - Starting ===")
    
    # Step 1: Convert emails to markdown
    logger.info("Step 1: Converting emails to markdown...")
    conversion_result = convert_emails_to_markdown()
    logger.info(f"Conversion result: {conversion_result}")

    conversion_status = ""
    if conversion_result["success"]:
        conversion_status = f"Converted {conversion_result['emails_converted']} email(s) to markdown. "
    else:
        conversion_status = f"Conversion issues: {conversion_result.get('emails_converted', 0)} converted. "

    # Step 2: Parse markdown files
    logger.info("Step 2: Parsing newsletters with LLM...")
    parsing_result = parse_newsletters()
    logger.info(f"Parsing result: {parsing_result}")

    # Check if parsing actually succeeded (at least one email parsed)
    if parsing_result["success"] and parsing_result.get("emails_parsed", 0) > 0:
        status_class = "success"
        status_message = (
            conversion_status
            + f"Parsed {parsing_result['emails_parsed']} newsletter(s) successfully."
        )
    elif parsing_result.get("emails_parsed", 0) == 0 and parsing_result["success"]:
        # Success but 0 parsed - likely all failed or no files
        status_class = "warning"
        status_message = conversion_status + "No newsletters parsed."
        if parsing_result.get("errors"):
            error_count = len(parsing_result["errors"])
            status_message += f" {error_count} error(s) occurred."
            if error_count <= 5:
                status_message += " " + "; ".join(parsing_result["errors"])
            else:
                status_message += " First few: " + "; ".join(parsing_result["errors"][:3]) + f" ... and {error_count - 3} more."
    else:
        status_class = "error"
        status_message = conversion_status + "Parsing failed"
        if parsing_result.get("errors"):
            error_count = len(parsing_result["errors"])
            if error_count <= 5:
                status_message += ": " + "; ".join(parsing_result["errors"])
            else:
                status_message += f": {error_count} errors. First few: " + "; ".join(parsing_result["errors"][:3]) + f" ... and {error_count - 3} more."

    # Return HTMX response fragment
    return f"""
    <div id="processing-status" class="status {status_class}">
        <p>{status_message}</p>
    </div>
    <div id="processing-stats">
        <p>Emails converted: {conversion_result.get('emails_converted', 0)}</p>
        <p>Newsletters parsed: {parsing_result.get('emails_parsed', 0)}</p>
    </div>
    """


@bp.route("/consolidate", methods=["POST"])
def consolidate():
    """
    Generate consolidated newsletter digest from all parsed items.

    Retrieves all parsed items from database, consolidates them using LLM,
    saves the digest, and returns HTMX response with digest content or download link.

    Returns:
        HTML: HTMX response fragment with consolidation status and digest link
    """
    logger.info("=== Consolidating newsletter digest ===")
    
    result = {
        "success": False,
        "digest_path": None,
        "errors": [],
    }

    try:
        # Load configuration
        config = load_config("config/senders.json")
        # Get consolidation prompt, use default if empty
        consolidation_prompt = config.get("consolidation_prompt", "").strip()
        if not consolidation_prompt:
            consolidation_prompt = config.get(
                "default_consolidation_prompt",
                "Create a consolidated newsletter digest from these items. "
                "Group similar topics together and create a well-formatted markdown document.",
            )

        # Get all parsed items from database
        db_path = "data/newsletter_aggregator.db"
        parsed_items = get_all_parsed_items(db_path)
        logger.info(f"Found {len(parsed_items)} parsed items to consolidate")

        if not parsed_items:
            result["errors"].append("No parsed items found. Please process emails first.")
            return f"""
            <div id="consolidation-status" class="status error">
                <p>No items to consolidate. Please process emails first.</p>
            </div>
            """

        # Create LLM client
        try:
            llm_client = create_llm_client()
        except ValueError as e:
            result["errors"].append(
                f"LLM client setup failed: {str(e)}\n"
                "Please set GEMINI_API_KEY environment variable."
            )
            return f"""
            <div id="consolidation-status" class="status error">
                <p>{result['errors'][0]}</p>
            </div>
            """

        # Consolidate newsletters
        try:
            # Models are validated in load_config - will raise ValueError if missing
            consolidation_model = config["models"]["consolidation"]
            logger.info(f"Consolidating with model: {consolidation_model}")
            consolidated_markdown = consolidate_newsletters(
                parsed_items, consolidation_prompt, llm_client, consolidation_model
            )
        except Exception as e:
            result["errors"].append(f"Failed to consolidate newsletters: {str(e)}")
            return f"""
            <div id="consolidation-status" class="status error">
                <p>{result['errors'][0]}</p>
            </div>
            """

        # Save consolidated digest
        try:
            output_dir = "data/output"
            digest_path = save_consolidated_digest(consolidated_markdown, output_dir)
            result["digest_path"] = digest_path
            result["success"] = True

            # Extract timestamp from filename for download link
            timestamp = Path(digest_path).stem.replace("digest_", "")

            return f"""
            <div id="consolidation-status" class="status success">
                <p>Successfully consolidated {len(parsed_items)} items into newsletter digest.</p>
            </div>
            <div id="digest-section">
                <h3>Consolidated Newsletter</h3>
                <p><a href="/digest/{timestamp}" target="_blank">Download Digest</a></p>
                <div class="digest-preview">
                    <pre>{consolidated_markdown[:500]}...</pre>
                </div>
            </div>
            """

        except Exception as e:
            result["errors"].append(f"Failed to save digest: {str(e)}")
            return f"""
            <div id="consolidation-status" class="status error">
                <p>{result['errors'][0]}</p>
            </div>
            """

    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
        return f"""
        <div id="consolidation-status" class="status error">
            <p>{result['errors'][0]}</p>
        </div>
        """


@bp.route("/digest/<timestamp>")
def get_digest(timestamp):
    """
    Serve consolidated markdown file for download.

    Args:
        timestamp: Timestamp from filename (format: YYYYMMDD_HHMMSS)

    Returns:
        File: Markdown file for download
    """
    digest_path = Path("data/output") / f"digest_{timestamp}.md"

    if not digest_path.exists():
        return "Digest file not found", 404

    return send_file(
        str(digest_path),
        mimetype="text/markdown",
        as_attachment=True,
        download_name=f"newsletter_digest_{timestamp}.md",
    )


@bp.route("/config")
def config():
    """
    Display configuration page with current senders and prompts.

    Returns:
        HTML: Configuration page with current settings and forms for editing
    """
    # Load current configuration
    config_data = load_config("config/senders.json")
    senders = config_data.get("senders", {})
    consolidation_prompt = config_data.get("consolidation_prompt", "")
    retention_limit = config_data.get("retention_limit", 100)
    default_parsing_prompt = config_data.get(
        "default_parsing_prompt",
        "Extract articles from this newsletter. "
        "Return a JSON array with items containing: date, title, summary, link (optional).",
    )
    default_consolidation_prompt = config_data.get(
        "default_consolidation_prompt",
        "Create a consolidated newsletter digest from these items. "
        "Group similar topics together and create a well-formatted markdown document.",
    )

    return render_template(
        "config.html",
        senders=senders,
        consolidation_prompt=consolidation_prompt,
        retention_limit=retention_limit,
        default_parsing_prompt=default_parsing_prompt,
        default_consolidation_prompt=default_consolidation_prompt,
    )


def _validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


@bp.route("/config/senders", methods=["POST"])
def add_or_update_sender():
    """
    Add or update sender configuration.

    Handles both creating new senders and updating existing ones.
    Saves configuration to config/senders.json.

    Returns:
        HTML: HTMX response fragment with status update
    """
    config_path = "config/senders.json"
    config_data = load_config(config_path)

    # Get form data
    email = request.form.get("email", "").strip()
    parsing_prompt = request.form.get("parsing_prompt", "").strip()
    enabled = request.form.get("enabled") == "true"
    action = request.form.get("action", "add")  # "add" or "update"

    # Use default parsing prompt if not provided
    if not parsing_prompt:
        parsing_prompt = config_data.get(
            "default_parsing_prompt",
            "Extract articles from this newsletter. "
            "Return a JSON array with items containing: date, title, summary, link (optional).",
        )

    # Validation
    errors = []
    if not email:
        errors.append("Email address is required")
    elif not _validate_email(email):
        errors.append("Invalid email address format")

    if errors:
        error_msg = '; '.join(errors)
        return f"""
        <div id="sender-status" class="status error">
            <p>Validation failed: {error_msg}</p>
        </div>
        """

    # Initialize senders dict if needed
    if "senders" not in config_data:
        config_data["senders"] = {}

    # Check if sender exists
    sender_exists = email in config_data["senders"]

    # Add or update sender
    if sender_exists and action == "add":
        return """
        <div id="sender-status" class="status error">
            <p>Sender already exists. Use edit to update.</p>
        </div>
        """

    # Create or update sender config
    sender_config = {
        "parsing_prompt": parsing_prompt,
        "enabled": enabled,
    }

    # Set created_at only for new senders
    if not sender_exists:
        sender_config["created_at"] = datetime.now().isoformat() + "Z"
    else:
        # Preserve created_at for existing senders
        if "created_at" in config_data["senders"][email]:
            sender_config["created_at"] = config_data["senders"][email]["created_at"]

    config_data["senders"][email] = sender_config

    # Save configuration
    try:
        save_config(config_path, config_data)
        action_text = "updated" if sender_exists else "added"
        return f"""
        <div id="sender-status" class="status success">
            <p>Sender {action_text} successfully: {email}</p>
        </div>
        <div hx-get="/config/senders/list" hx-trigger="load" hx-target="#senders-list" hx-swap="innerHTML"></div>
        """
    except Exception as e:
        return f"""
        <div id="sender-status" class="status error">
            <p>Failed to save configuration: {str(e)}</p>
        </div>
        """


@bp.route("/config/senders/<email>", methods=["DELETE"])
def delete_sender(email):
    """
    Delete a sender from configuration.

    Args:
        email: Email address of sender to delete

    Returns:
        HTML: HTMX response fragment with status update
    """
    config_path = "config/senders.json"
    config_data = load_config(config_path)

    if email not in config_data.get("senders", {}):
        return """
        <div id="sender-status" class="status error">
            <p>Sender not found.</p>
        </div>
        """

    # Delete sender
    del config_data["senders"][email]

    # Save configuration
    try:
        save_config(config_path, config_data)
        return f"""
        <div id="sender-status" class="status success">
            <p>Sender deleted successfully: {email}</p>
        </div>
        <div hx-get="/config/senders/list" hx-trigger="load" hx-target="#senders-list" hx-swap="innerHTML"></div>
        """
    except Exception as e:
        return f"""
        <div id="sender-status" class="status error">
            <p>Failed to save configuration: {str(e)}</p>
        </div>
        """


@bp.route("/config/senders/list")
def list_senders():
    """
    Return HTML fragment with list of senders for HTMX updates.

    Returns:
        HTML: Fragment with sender list
    """
    config_data = load_config("config/senders.json")
    senders = config_data.get("senders", {})

    if not senders:
        return '<div id="senders-list"><p>No senders configured yet.</p></div>'

    html = '<div id="senders-list"><ul class="senders-list">'
    for email, config in senders.items():
        enabled_class = "enabled" if config.get("enabled", True) else "disabled"
        enabled_text = "Enabled" if config.get("enabled", True) else "Disabled"
        html += f"""
        <li class="sender-item">
            <div class="sender-header">
                <strong>{email}</strong>
                <span class="status-badge {enabled_class}">{enabled_text}</span>
                <button 
                    hx-delete="/config/senders/{email}" 
                    hx-target="#sender-status" 
                    hx-swap="innerHTML"
                    class="btn-small btn-danger"
                    onclick="return confirm('Delete {email}?')"
                >Delete</button>
            </div>
            <p class="prompt-preview">{config.get('parsing_prompt', 'No prompt')[:100]}{'...' if len(config.get('parsing_prompt', '')) > 100 else ''}</p>
        </li>
        """
    html += "</ul></div>"
    return html


@bp.route("/config/consolidation", methods=["POST"])
def update_consolidation_prompt():
    """
    Update consolidation prompt in configuration.

    Saves updated consolidation prompt to config/senders.json.

    Returns:
        HTML: HTMX response fragment with status update
    """
    config_path = "config/senders.json"
    config_data = load_config(config_path)

    consolidation_prompt = request.form.get("consolidation_prompt", "").strip()
    
    # If empty, use default from config
    if not consolidation_prompt:
        consolidation_prompt = config_data.get(
            "default_consolidation_prompt",
            "Create a consolidated newsletter digest from these items. "
            "Group similar topics together and create a well-formatted markdown document.",
        )

    # Validation - should not be empty at this point (we have default)
    if not consolidation_prompt:
        return """
        <div id="consolidation-status" class="status error">
            <p>Consolidation prompt is required.</p>
        </div>
        """

    # Update consolidation prompt
    config_data["consolidation_prompt"] = consolidation_prompt

    # Save configuration
    try:
        save_config(config_path, config_data)
        return """
        <div id="consolidation-status" class="status success">
            <p>Consolidation prompt updated successfully.</p>
        </div>
        """


@bp.route("/config/retention", methods=["POST"])
def update_retention_limit():
    """
    Update retention limit in configuration.

    Saves updated retention limit to config/senders.json.

    Returns:
        HTML: HTMX response fragment with status update
    """
    config_path = "config/senders.json"
    config_data = load_config(config_path)

    try:
        retention_limit = int(request.form.get("retention_limit", "100"))
    except (ValueError, TypeError):
        return """
        <div id="retention-status" class="status error">
            <p>Retention limit must be a positive integer.</p>
        </div>
        """

    # Validation
    if retention_limit <= 0:
        return """
        <div id="retention-status" class="status error">
            <p>Retention limit must be greater than 0.</p>
        </div>
        """

    # Update retention limit
    config_data["retention_limit"] = retention_limit

    # Save configuration
    try:
        save_config(config_path, config_data)
        return f"""
        <div id="retention-status" class="status success">
            <p>Retention limit updated to {retention_limit} records.</p>
        </div>
        """
    except Exception as e:
        logger.error(f"Failed to save retention limit: {str(e)}")
        return f"""
        <div id="retention-status" class="status error">
            <p>Failed to save retention limit: {str(e)}</p>
        </div>
        """
    except Exception as e:
        return f"""
        <div id="consolidation-status" class="status error">
            <p>Failed to save configuration: {str(e)}</p>
        </div>
        """
