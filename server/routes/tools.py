from flask import Blueprint, jsonify, request

from server.services import registry
from server.utils.auth import login_required, owner_required

tools_bp = Blueprint("tools", __name__)


@tools_bp.get("/api/tools")
@login_required
def list_tools():
    return jsonify(registry.load_registry())


@tools_bp.get("/api/tools/pending")
@login_required
def list_pending():
    return jsonify(registry.pending_tools())


@tools_bp.post("/api/tools/<tool_id>/approve")
@login_required
@owner_required
def approve_tool(tool_id):
    if registry.get_tool(tool_id) is None:
        return jsonify({"error": "tool not found"}), 404
    return jsonify(registry.set_approval(tool_id, approved=True))


@tools_bp.post("/api/tools/<tool_id>/reject")
@login_required
@owner_required
def reject_tool(tool_id):
    if registry.get_tool(tool_id) is None:
        return jsonify({"error": "tool not found"}), 404
    data = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "").strip() or "No reason given"
    return jsonify(registry.set_approval(tool_id, approved=False, rejection_reason=reason))
