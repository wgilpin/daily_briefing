"""Flask application for unified feed aggregator."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

# Load environment variables from .env file
load_dotenv()

from src.newsletter.storage import init_data_directories  # noqa: E402


def run_migrations() -> None:
    """Run PostgreSQL database migrations.

    Reads and executes SQL migration files from src/db/migrations/
    in alphabetical order. Only runs if DATABASE_URL is configured.
    """
    logger = logging.getLogger(__name__)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set, skipping PostgreSQL migrations")
        return

    migrations_dir = Path(__file__).parent.parent / "db" / "migrations"
    if not migrations_dir.exists():
        logger.warning(f"Migrations directory not found: {migrations_dir}")
        return

    try:
        from src.db.connection import get_connection

        migration_files = sorted(migrations_dir.glob("*.sql"))

        with get_connection() as conn:
            for migration_file in migration_files:
                logger.info(f"Running migration: {migration_file.name}")
                sql = migration_file.read_text()

                with conn.cursor() as cursor:
                    cursor.execute(sql)
                conn.commit()

            logger.info(f"Successfully ran {len(migration_files)} migration(s)")

    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        # Don't raise - allow app to start even if migrations fail
        # This enables graceful degradation


def create_app() -> Flask:
    """
    Create and configure Flask application.

    Initializes the Flask app with basic error handling and database setup.

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Basic configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["PERMANENT_SESSION_LIFETIME"] = 30 * 24 * 60 * 60  # 30 days in seconds
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Disable ALL caching in development - both server and client side
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    @app.after_request
    def add_no_cache_headers(response):
        """Add headers to prevent any caching during development."""
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # Simple logging configuration - logs to stderr by default (which appears in terminal)
    # Ensure logs directory exists for file logging backup
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger with UTF-8 encoding for emoji support
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True,
        encoding='utf-8'
    )

    # Add file handler for persistent logs
    file_handler = logging.FileHandler(log_dir / "app.log", mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)

    # Log startup - these WILL appear in terminal
    print("=" * 60, flush=True)
    print("Daily Briefing Application Starting", flush=True)
    print("=" * 60, flush=True)
    logging.info("=" * 60)
    logging.info("Daily Briefing Application Starting")
    logging.info("=" * 60)

    # Initialize databases on startup
    with app.app_context():
        # Initialize connection pool before running migrations
        from src.db.connection import initialize_pool
        initialize_pool()

        # Run PostgreSQL migrations (for unified feed)
        run_migrations()

        # Migrate senders.json to DB if it exists (one-time, idempotent)
        try:
            from src.newsletter.migration import migrate_senders_if_needed
            _senders_json = Path(__file__).parent.parent.parent / "config" / "senders.json"
            migrate_senders_if_needed(_senders_json)
        except RuntimeError as exc:
            logging.error(f"Startup aborted: {exc}")
            raise

        # Initialize file system directories
        init_data_directories()

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        from src.auth.service import get_user_by_id
        from src.db.connection import get_connection

        try:
            with get_connection() as conn:
                user_dict = get_user_by_id(conn, int(user_id))
                if user_dict:
                    # Create a simple user object for Flask-Login
                    class User:
                        def __init__(self, user_dict):
                            self.id = user_dict["id"]
                            self.email = user_dict["email"]
                            self.name = user_dict["name"]
                            self.is_active = user_dict["is_active"]

                        def is_authenticated(self):
                            return True

                        def is_anonymous(self):
                            return False

                        def get_id(self):
                            return str(self.id)

                    return User(user_dict)
        except Exception:
            pass
        return None

    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors with logging."""
        import traceback
        from flask import request

        # Force output to console
        print("=" * 60, flush=True)
        print("500 INTERNAL SERVER ERROR", flush=True)
        print("=" * 60, flush=True)
        print(f"Error: {error}", flush=True)
        print(traceback.format_exc(), flush=True)
        print("=" * 60, flush=True)

        app.logger.error("=" * 60)
        app.logger.error("500 INTERNAL SERVER ERROR")
        app.logger.error("=" * 60)
        app.logger.error(f"Error: {error}")
        app.logger.error(traceback.format_exc())
        app.logger.error("=" * 60)

        # Check if this is an HTMX request (expects HTML)
        if request.headers.get('HX-Request'):
            return f"""
            <div class="status error">
                <p><strong>Internal Server Error</strong></p>
                <p>Error: {str(error)}</p>
                <details>
                    <summary>Technical details</summary>
                    <pre style="font-size: 10px;">{traceback.format_exc()}</pre>
                </details>
            </div>
            """, 500

        # Otherwise return JSON
        return {"error": "Internal server error", "details": str(error)}, 500

    # Register blueprints
    from src.web.feed_routes import bp as main_bp
    from src.web.auth_routes import bp as auth_bp
    from src.web.audio_routes import audio_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(audio_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)

