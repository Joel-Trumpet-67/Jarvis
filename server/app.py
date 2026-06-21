import os

from flask import Flask, send_from_directory

from server.config import CLIENT_DIR, DATA_DIR, SECRET_KEY
from server.routes.auth import auth_bp
from server.routes.chat import chat_bp
from server.routes.tools import tools_bp


def create_app():
    app = Flask(__name__, static_folder=CLIENT_DIR, static_url_path="")
    app.secret_key = SECRET_KEY

    for username in ("joel", "valerie"):
        os.makedirs(os.path.join(DATA_DIR, "users", username), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "tools"), exist_ok=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(tools_bp)

    @app.route("/")
    def index():
        return send_from_directory(CLIENT_DIR, "index.html")

    return app
