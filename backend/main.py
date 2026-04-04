"""
main.py — Flask application factory.

Registers all route blueprints and serves the frontend as static files.
Flask serves index.html at / so everything runs on the same origin —
no CORS issues, no file:// workarounds needed.

Do NOT run this file directly — use run.py from the project root instead.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory

from backend.config import CONFIG
from backend.api.routes.chat import chat_bp
from backend.api.routes.voice import voice_bp
from backend.api.routes.status import status_bp
from backend.api.routes.session import session_bp
from backend.api.routes.interrupt import interrupt_bp

# Resolve the frontend directory relative to this file
_ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND = os.path.join(_ROOT, "frontend")


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)

    # ── Serve frontend files ──────────────────────────────────────

    @app.route("/")
    def index():
        return send_from_directory(_FRONTEND, "index.html")

    @app.route("/<path:filename>")
    def frontend_static(filename):
        """Serve any frontend file (css/, js/, assets/, etc.)"""
        return send_from_directory(_FRONTEND, filename)

    # ── Register API blueprints ───────────────────────────────────
    app.register_blueprint(chat_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(interrupt_bp)

    return app
