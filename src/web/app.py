"""Flask application for newsletter aggregator."""

import logging
import sys

from dotenv import load_dotenv
from flask import Flask

# Load environment variables from .env file
load_dotenv()

from src.newsletter.storage import init_database, init_data_directories


def create_app() -> Flask:
    """
    Create and configure Flask application.

    Initializes the Flask app with basic error handling and database setup.

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Basic configuration
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
    
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

    # Initialize database and data directories on startup
    with app.app_context():
        db_path = "data/newsletter_aggregator.db"
        init_database(db_path)
        init_data_directories()

    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return {"error": "Internal server error"}, 500

    # Register blueprints
    from src.web.routes import bp

    app.register_blueprint(bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)

