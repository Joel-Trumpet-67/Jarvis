"""
run.py — EIGENFORM entry point.

Run from the project root:
    python run.py

This ensures the project root is on sys.path so all backend imports resolve
correctly regardless of your terminal's working directory.
"""

import sys
import os

# Add project root to path — must be before any backend imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import create_app
from backend.config import CONFIG
from backend.ai.personality.responses import get_boot_message


def main():
    app  = create_app()
    host = CONFIG.get("flask_host", "127.0.0.1")
    port = CONFIG.get("flask_port", 5000)
    debug = CONFIG.get("flask_debug", False)

    print(f"\n{'=' * 54}")
    print(f"  EIGENFORM  —  J.A.R.V.I.S. Backend")
    print(f"{'=' * 54}")
    print(f"  Model  : {CONFIG.get('model_name')} @ {CONFIG.get('model_api_url')}")
    print(f"  Server : http://{host}:{port}")
    print(f"  Status : {get_boot_message()}")
    print(f"{'=' * 54}")
    print(f"  Open frontend/index.html in your browser to begin.")
    print(f"  Press Ctrl+C to stop.\n")

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
