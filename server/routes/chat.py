from flask import Blueprint, jsonify, request, session

from server.services import ai, memory
from server.utils.auth import login_required

chat_bp = Blueprint("chat", __name__)


@chat_bp.get("/api/chat/history")
@login_required
def history():
    return jsonify(memory.load_history(session["user"]))


@chat_bp.post("/api/chat")
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        reply = ai.generate_response(session["user"], session["display_name"], message)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"reply": reply})
