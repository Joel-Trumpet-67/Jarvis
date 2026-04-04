"""
status.py — GET /api/status

Health check endpoint. Works with both Ollama and OpenAI-compatible APIs.
Used by the frontend HUD every 30 seconds to update the status indicator.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import time
import requests
from flask import Blueprint, jsonify

from backend.config import CONFIG
from backend.ai.memory.short_term import get_all_sessions

status_bp = Blueprint("status", __name__)

_START_TIME = time.time()


def _check_model_reachable(api_format: str, api_url: str, api_key: str) -> bool:
    """
    Ping the model API to check connectivity.
    Uses format-appropriate endpoints so both Ollama and Groq/OpenAI work.
    """
    try:
        if api_format == "openai":
            # OpenAI-compatible: hit the models list endpoint
            # e.g. https://api.groq.com/openai/v1/chat/completions
            #   -> https://api.groq.com/openai/v1/models
            base = api_url.split("/chat/completions")[0]
            r = requests.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5,
            )
            return r.status_code == 200
        else:
            # Ollama: ping /api/tags
            base = api_url.rsplit("/api/chat", 1)[0]
            r = requests.get(f"{base}/api/tags", timeout=3)
            return r.status_code == 200
    except Exception:
        return False


@status_bp.route("/api/status", methods=["GET"])
def status():
    api_format = CONFIG.get("api_format", "ollama")
    model_url  = CONFIG.get("model_api_url", "http://localhost:11434/api/chat")
    model_name = CONFIG.get("model_name", "mistral")
    api_key    = CONFIG.get("api_key", "")

    model_reachable = _check_model_reachable(api_format, model_url, api_key)

    sessions       = get_all_sessions()
    total_messages = sum(s.message_count() for s in sessions.values())

    return jsonify({
        "status":              "online",
        "model_reachable":     model_reachable,
        "model_url":           model_url,
        "model_name":          model_name,
        "api_format":          api_format,
        "session_count":       len(sessions),
        "total_message_count": total_messages,
        "uptime_seconds":      int(time.time() - _START_TIME),
    })
