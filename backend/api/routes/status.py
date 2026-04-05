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

# Cache the model reachability result so we don't spam the API on every poll
_model_cache: dict = {"reachable": None, "checked_at": 0}
_MODEL_CACHE_TTL = 45  # seconds — only re-ping every 45s


def _check_model_reachable(api_format: str, api_url: str, api_key: str) -> bool:
    """
    Ping the model API to check connectivity.
    Result is cached for 45 seconds to avoid rate-limiting after chat requests.
    """
    global _model_cache
    now = time.time()

    # Return cached result if still fresh
    if _model_cache["reachable"] is not None and (now - _model_cache["checked_at"]) < _MODEL_CACHE_TTL:
        return _model_cache["reachable"]

    try:
        if api_format == "openai":
            base = api_url.split("/chat/completions")[0]
            r = requests.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5,
            )
            result = r.status_code == 200
        else:
            base = api_url.rsplit("/api/chat", 1)[0]
            r = requests.get(f"{base}/api/tags", timeout=3)
            result = r.status_code == 200
    except Exception:
        result = False

    _model_cache["reachable"] = result
    _model_cache["checked_at"] = now
    return result


def mark_model_reachable():
    """Call this after a successful chat response to update cache immediately."""
    global _model_cache
    _model_cache["reachable"] = True
    _model_cache["checked_at"] = time.time()


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
