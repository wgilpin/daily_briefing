"""Flask application for unified feed aggregator."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

# Load environment variables from .env file
load_dotenv()

from src.newsletter.storage import init_database, init_data_directories


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

        conn = get_connection()
        migration_files = sorted(migrations_dir.glob("*.sql"))

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

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set Flask's logger to INFO level
    app.logger.setLevel(logging.INFO)

    # Initialize databases on startup
    with app.app_context():
        # Run PostgreSQL migrations (for unified feed)
        run_migrations()

        # Initialize SQLite database (for newsletter legacy)
        db_path = "data/newsletter_aggregator.db"
        init_database(db_path)
        init_data_directories()

    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {"error": "Not found"}, 404

    # Temporarily disabled to see actual errors during debugging
    # @app.errorhandler(500)
    # def internal_error(error):
    #     """Handle 500 errors."""
    #     return {"error": "Internal server error"}, 500

    # Register blueprints
    from src.web.feed_routes import bp as main_bp

    app.register_blueprint(main_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)

