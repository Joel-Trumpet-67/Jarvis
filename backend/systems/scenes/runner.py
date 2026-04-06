"""
runner.py — Executes a scene's action list and yields SSE events.

Scenes emit only token events (no command_executed spam) so the HUD
doesn't flicker. The hwnd found while waiting is passed directly into
snap() so there's no redundant second window search.
"""

import os
import time
import subprocess
import webbrowser

from backend.systems.scenes.windows import snap_and_verify, find_window
from backend.systems.apps.launcher import launch_app

_PF     = os.environ.get("ProgramFiles", r"C:\Program Files")
_CHROME = os.path.join(_PF, r"Google\Chrome\Application\chrome.exe")


def run_scene(scene: dict):
    """
    Generator. Yields SSE event dicts for each step in the scene.

    Yields:
      {"type": "token", "content": "..."}
      {"type": "done"}
    """
    greeting = scene.get("greeting", "Running scene.")
    yield {"type": "token", "content": greeting}

    for action in scene.get("actions", []):
        atype = action.get("type")

        # ── wait ──────────────────────────────────────────────────────────
        if atype == "wait":
            time.sleep(action.get("seconds", 1.0))

        # ── say ───────────────────────────────────────────────────────────
        elif atype == "say":
            text = action.get("text", "")
            if text:
                yield {"type": "token", "content": " " + text}

        # ── open_app ──────────────────────────────────────────────────────
        elif atype == "open_app":
            name = action.get("name", "")
            launch_app(name)   # fire and forget — snap handles timing

        # ── open_url ──────────────────────────────────────────────────────
        elif atype == "open_url":
            url = action.get("url", "")
            try:
                webbrowser.open(url, new=2)
            except Exception:
                pass

        # ── open_url_window ───────────────────────────────────────────────
        elif atype == "open_url_window":
            url = action.get("url", "")
            _open_in_new_window(url)

        # ── spotify_playlist ──────────────────────────────────────────────
        elif atype == "spotify_playlist":
            playlist_id = action.get("id", "")
            try:
                webbrowser.open(f"spotify:playlist:{playlist_id}")
            except Exception:
                pass

        # ── snap ──────────────────────────────────────────────────────────
        elif atype == "snap":
            title    = action.get("title", "")
            position = action.get("position", "full")
            monitor  = action.get("monitor", 0)
            wait_sec = action.get("wait", 6.0)

            # Wait for the window to appear, then pass hwnd directly so
            # snap() doesn't do a redundant second search that might fail
            hwnd = find_window(title, timeout=wait_sec)
            if hwnd:
                time.sleep(0.4)  # let the window finish rendering
                snap_and_verify(position=position, monitor_index=monitor,
                                hwnd=hwnd, max_attempts=3)

    yield {"type": "done"}


def _open_in_new_window(url: str) -> bool:
    """Open a URL in a new browser window using Chrome --new-window."""
    chrome_paths = [
        _CHROME,
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),      r"Google\Chrome\Application\chrome.exe"),
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, "--new-window", url])
                return True
            except Exception:
                pass
    try:
        webbrowser.open(url, new=1)
        return True
    except Exception:
        return False
