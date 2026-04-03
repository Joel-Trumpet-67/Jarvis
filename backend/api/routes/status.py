"""
status.py — GET /api/status

Health check endpoint. Pings the Ollama API and reports system state.
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

# Record server start time for uptime reporting
_START_TIME = time.time()


@status_bp.route("/api/status", methods=["GET"])
def status():
    model_url  = CONFIG.get("model_api_url", "http://localhost:11434/api/chat")
    model_name = CONFIG.get("model_name", "mistral")

    # Ping Ollama's /api/tags — lighter than a full chat call
    model_reachable = False
    try:
        base_url = model_url.rsplit("/api/chat", 1)[0]
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        model_reachable = r.status_code == 200
    except Exception:
        model_reachable = False

    sessions       = get_all_sessions()
    total_messages = sum(s.message_count() for s in sessions.values())

    return jsonify({
        "status":              "online",
        "model_reachable":     model_reachable,
        "model_url":           model_url,
        "model_name":          model_name,
        "session_count":       len(sessions),
        "total_message_count": total_messages,
        "uptime_seconds":      int(time.time() - _START_TIME),
    })
