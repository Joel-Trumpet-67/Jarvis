"""
run.py — EIGENFORM entry point.

Run from the project root:
    python run.py

Starts Flask in a background thread, then opens the app in
Edge/Chrome app mode (no address bar, no tabs — looks native).
Falls back to the default browser if neither is found.
"""

import sys
import os
import time
import threading
import subprocess
import webbrowser

# Add project root to path — must be before any backend imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import create_app
from backend.config import CONFIG
from backend.ai.personality.responses import get_boot_message


# ── Browser / app window ─────────────────────────────────────────────────────

# Edge and Chrome paths to check (in preference order)
_BROWSER_PATHS = [
    # Microsoft Edge (built into Windows 10/11)
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    # Google Chrome
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def _find_browser() -> str | None:
    """Return the path to the first available Edge/Chrome install."""
    for path in _BROWSER_PATHS:
        if os.path.exists(path):
            return path
    return None


def _wait_for_flask(url: str, timeout: float = 8.0) -> bool:
    """
    Poll the Flask server until it responds or times out.
    Returns True if the server came up within timeout seconds.
    """
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.15)
    return False


def _open_app_window(url: str) -> None:
    """
    Open the app in a dedicated app-mode window (no browser chrome).
    Falls back to the system default browser if Edge/Chrome aren't found.
    """
    browser = _find_browser()
    if browser:
        subprocess.Popen([
            browser,
            f"--app={url}",
            "--window-size=1280,820",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
        ])
        print(f"  Window : App mode via {os.path.basename(browser)}")
    else:
        webbrowser.open(url)
        print("  Window : Opened in default browser (Edge/Chrome not found)")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    app   = create_app()
    host  = CONFIG.get("flask_host",  "127.0.0.1")
    port  = CONFIG.get("flask_port",  5000)
    debug = CONFIG.get("flask_debug", False)
    url   = f"http://{host}:{port}"

    print(f"\n{'=' * 54}")
    print(f"  EIGENFORM  —  J.A.R.V.I.S.")
    print(f"{'=' * 54}")
    print(f"  Model  : {CONFIG.get('model_name')} @ {CONFIG.get('model_api_url')}")
    print(f"  Server : {url}")
    print(f"  Status : {get_boot_message()}")
    print(f"{'=' * 54}")

    # Start Flask in a daemon thread so the main thread can open the window
    flask_thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False),
        daemon=True,
        name="flask",
    )
    flask_thread.start()

    # Wait for Flask to be ready, then open the app window
    if _wait_for_flask(url):
        _open_app_window(url)
    else:
        print("  WARNING: Flask didn't respond in time — opening anyway.")
        _open_app_window(url)

    print(f"  Press Ctrl+C to stop.\n")

    # Keep the main thread alive (Flask daemon thread runs until we exit)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Shutting down EIGENFORM. Goodbye.")


if __name__ == "__main__":
    main()
