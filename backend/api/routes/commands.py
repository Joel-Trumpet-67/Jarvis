"""
commands.py — POST /api/command (direct system command execution)

Phase 1: Stub. Returns 501 Not Implemented.
Phase 4: Full dispatcher-based execution implemented here.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, jsonify

commands_bp = Blueprint("commands", __name__)


@commands_bp.route("/api/command", methods=["POST"])
def execute_command():
    # Phase 4 will implement plugin-based command routing here.
    return jsonify({
        "success": False,
        "message": "Direct command execution not yet implemented. (Phase 4)",
    }), 501
