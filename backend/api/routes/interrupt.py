"""
interrupt.py — POST /api/interrupt

Sets the cancel_requested flag on the active session.
The engine.py stream generator checks this flag on every token
and stops yielding if it is True.

Called by the frontend when:
  - User presses Escape
  - User clicks the STOP button
  - User speaks an interrupt phrase ("stop", "cancel", etc.)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, request, jsonify

from backend.ai.memory.short_term import get_session

interrupt_bp = Blueprint("interrupt", __name__)


@interrupt_bp.route("/api/interrupt", methods=["POST"])
def interrupt():
    data       = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or
                  request.headers.get("X-Session-ID") or
                  "default")

    session = get_session(session_id)
    session.request_cancel()

    return jsonify({
        "success":    True,
        "session_id": session_id,
        "message":    "Interrupt signal received.",
    })
