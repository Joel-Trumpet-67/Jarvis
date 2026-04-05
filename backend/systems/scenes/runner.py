"""
runner.py — Executes a scene's action list and yields SSE events.

Each action runs in sequence. Snap actions wait for the target window
to appear before positioning it. Rocky narrates progress via token events.
"""

import os
import time
import subprocess
import webbrowser

from backend.systems.scenes.windows import snap, find_window
from backend.systems.apps.launcher import launch_app

_PF    = os.environ.get("ProgramFiles",      r"C:\Program Files")
_CHROME = os.path.join(_PF, r"Google\Chrome\Application\chrome.exe")


def run_scene(scene: dict):
    """
    Generator. Yields SSE event dicts for each step in the scene.

    Yields:
      {"type": "token",            "content": "..."}
      {"type": "command_executed", "command": "scene_step", "args": {...}, "ok": bool}
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
            ok, msg = launch_app(name)
            yield {
                "type":    "command_executed",
                "command": "open_app",
                "args":    {"name": name},
                "ok":      ok,
            }

        # ── open_url ──────────────────────────────────────────────────────
        elif atype == "open_url":
            url = action.get("url", "")
            try:
                webbrowser.open(url, new=2)
                ok = True
            except Exception:
                ok = False
            yield {
                "type":    "command_executed",
                "command": "open_url",
                "args":    {"url": url},
                "ok":      ok,
            }

        # ── open_url_window ───────────────────────────────────────────────
        elif atype == "open_url_window":
            url = action.get("url", "")
            ok = _open_in_new_window(url)
            yield {
                "type":    "command_executed",
                "command": "open_url_window",
                "args":    {"url": url},
                "ok":      ok,
            }

        # ── spotify_playlist ──────────────────────────────────────────────
        elif atype == "spotify_playlist":
            playlist_id = action.get("id", "")
            uri = f"spotify:playlist:{playlist_id}"
            try:
                webbrowser.open(uri)
                ok = True
            except Exception:
                ok = False
            yield {
                "type":    "command_executed",
                "command": "spotify_playlist",
                "args":    {"id": playlist_id},
                "ok":      ok,
            }

        # ── snap ──────────────────────────────────────────────────────────
        elif atype == "snap":
            title    = action.get("title", "")
            position = action.get("position", "full")
            monitor  = action.get("monitor", 0)
            wait_sec = action.get("wait", 5.0)

            # Wait for the window to appear
            hwnd = find_window(title, timeout=wait_sec)
            if hwnd:
                time.sleep(0.4)  # let the window finish rendering
                ok = snap(title, position, monitor)
            else:
                ok = False

            yield {
                "type":    "command_executed",
                "command": "snap",
                "args":    {"title": title, "position": position, "monitor": monitor},
                "ok":      ok,
            }

    yield {"type": "done"}


def _open_in_new_window(url: str) -> bool:
    """
    Open a URL in a new browser window (not a tab).
    Tries Chrome first (--new-window flag), falls back to webbrowser.
    """
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

    # Fallback
    try:
        webbrowser.open(url, new=1)
        return True
    except Exception:
        return False
