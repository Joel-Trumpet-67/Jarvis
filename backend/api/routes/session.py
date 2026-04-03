"""
session.py — GET /api/session, DELETE /api/session

GET  returns the full conversation history for re-rendering after page refresh.
DELETE clears the session (short-term memory) without restarting the server.

Session ID is read from the X-Session-ID request header.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, request, jsonify

from backend.ai.memory.short_term import get_session, delete_session

session_bp = Blueprint("session", __name__)


def _get_session_id() -> str:
    return (request.headers.get("X-Session-ID") or
            request.args.get("session_id") or
            "default")


@session_bp.route("/api/session", methods=["GET"])
def get_session_history():
    session_id = _get_session_id()
    session    = get_session(session_id)
    messages   = session.get_messages()

    return jsonify({
        "session_id": session_id,
        "messages":   messages,
        "count":      len(messages),
    })


@session_bp.route("/api/session", methods=["DELETE"])
def clear_session():
    session_id = _get_session_id()
    delete_session(session_id)

    return jsonify({
        "success":    True,
        "session_id": session_id,
        "message":    "Session cleared.",
    })
