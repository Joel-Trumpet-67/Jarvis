"""
voice.py — POST /api/voice (Python-side TTS fallback)

Reserved for Phase 2. Currently a stub.
Browser-side TTS via Web Speech API is used in Phase 1.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from flask import Blueprint, jsonify

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/api/voice", methods=["POST"])
def voice_tts():
    # Phase 2 will implement Python-side TTS here (pyttsx3 or similar).
    return jsonify({
        "success": False,
        "message": "Python-side TTS not yet implemented. Using browser TTS.",
    }), 501
