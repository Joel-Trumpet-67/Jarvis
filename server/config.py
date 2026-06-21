import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLIENT_DIR = os.path.join(BASE_DIR, "client")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

AI_PROVIDER = os.environ.get("AI_PROVIDER", "groq").strip().lower()

_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "llama3.1",
    "openai": "gpt-4o-mini",
}
AI_MODEL = os.environ.get("AI_MODEL", _DEFAULT_MODELS.get(AI_PROVIDER, ""))

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")

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
