"""
main.py — Flask application factory.

Registers all route blueprints, configures CORS, and returns the app.
Do NOT run this file directly — use run.py from the project root instead.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_cors import CORS

from backend.config import CONFIG
from backend.api.routes.chat import chat_bp
from backend.api.routes.voice import voice_bp
from backend.api.routes.status import status_bp
from backend.api.routes.session import session_bp
from backend.api.routes.interrupt import interrupt_bp


def create_app() -> Flask:
    app = Flask(__name__)

    # Restrict CORS to localhost only — this is a local tool
    port = CONFIG.get("flask_port", 5000)
    CORS(app, origins=[
        "http://localhost",
        "http://127.0.0.1",
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
        # Allow file:// origin for opening index.html directly
        "null",
    ])

    # Register all route blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(interrupt_bp)

    return app
