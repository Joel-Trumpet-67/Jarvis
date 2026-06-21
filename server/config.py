import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLIENT_DIR = os.path.join(BASE_DIR, "client")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

USERS = {
    "joel": {
        "password": os.environ.get("JOEL_PASSWORD", "changeme"),
        "role": "owner",
        "display_name": "Joel",
    },
    "valerie": {
        "password": os.environ.get("VALERIE_PASSWORD", "changeme"),
        "role": "guest",
        "display_name": "Valerie",
    },
}
