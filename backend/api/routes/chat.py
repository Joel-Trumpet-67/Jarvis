"""
chat.py — POST /api/chat

Main SSE streaming endpoint. Accepts a message, streams tokens back
as Server-Sent Events. The frontend reads this via fetch + ReadableStream.

SSE event format (each line):
  data: {"type": "token", "content": "..."}\n\n
  data: {"type": "done"}\n\n
  data: {"type": "error", "code": "...", "message": "..."}\n\n
  data: {"type": "interrupted"}\n\n
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import json

from flask import Blueprint, request, Response, stream_with_context

from backend.ai.core.dispatcher import dispatch
from backend.ai.personality.jarvis import get_system_prompt
from backend.api.routes.status import mark_model_reachable

chat_bp = Blueprint("chat", __name__)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data:
        return Response(
            json.dumps({"error": "Request body must be JSON."}),
            status=400,
            mimetype="application/json",
        )

    message    = (data.get("message") or "").strip()
    session_id = (data.get("session_id") or
                  request.headers.get("X-Session-ID") or
                  "default")

    if not message:
        return Response(
            json.dumps({"error": "Message cannot be empty."}),
            status=400,
            mimetype="application/json",
        )

    system_prompt = get_system_prompt()

    def generate():
        for event in dispatch(session_id, message, system_prompt):
            if event.get("type") == "done":
                mark_model_reachable()
            yield f"data: {json.dumps(event)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )
