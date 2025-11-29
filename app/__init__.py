"""
LaserOstop CM Chatbot Application.

Flask application factory for the LaserOstop Tunisia community manager chatbot.
"""

import logging
from flask import Flask
from flask_cors import CORS

from .config import FLASK_ENV, FLASK_DEBUG


def create_app() -> Flask:
    """
    Application factory for Flask app.

    Returns:
        Configured Flask application instance.
    """
    # Create Flask app
    app = Flask(__name__)

    # Configure app
    app.config["ENV"] = FLASK_ENV
    app.config["DEBUG"] = FLASK_DEBUG
    app.config["JSON_AS_ASCII"] = False  # Important for Arabic/French text

    # Enable CORS
    CORS(app)

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if FLASK_DEBUG else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Register routes
    from .api import register_routes
    register_routes(app)

    # Initialize database immediately
    with app.app_context():
        from .db import init_db
        init_db()

    return app


# For direct execution: python -m app
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
