#!/usr/bin/env python3
"""
Main entry point for LaserOstop CM Chatbot Flask application.

This script starts the Flask development server.
For production, use a WSGI server like Gunicorn instead.

Usage:
    python run.py
"""

from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
