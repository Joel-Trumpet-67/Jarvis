"""
registry.py — Scene definitions for EIGENFORM.

A scene is a named routine Rocky runs when a trigger phrase is detected.
Each scene has:
  patterns  — regex list (any match triggers the scene)
  greeting  — what Rocky says when the scene starts
  actions   — list of steps executed in order

────────────────────────────────────────────────────────────────
Action types
────────────────────────────────────────────────────────────────

  open_app
    name: str       — app name from systems/apps/registry.py

  open_url
    url: str        — full URL; opens in default browser

  open_url_window
    url: str        — opens URL in a NEW browser window (not tab)

  spotify_playlist
    id: str         — Spotify playlist ID (from the share URL)

  snap
    title: str      — substring of the window title to find
    position: str   — left | right | full | max
                      top-left | top-right | bottom-left | bottom-right
    monitor: int    — 0 = primary (1920×1080), 1 = secondary (1366×768)
    wait: float     — seconds to wait for the window to appear (default 5)

  wait
    seconds: float  — pause between actions

  say
    text: str       — Rocky says something mid-scene

────────────────────────────────────────────────────────────────
"""

import os

_PF    = os.environ.get("ProgramFiles",        r"C:\Program Files")
_PF86  = os.environ.get("ProgramFiles(x86)",   r"C:\Program Files (x86)")
_CHROME = os.path.join(_PF, r"Google\Chrome\Application\chrome.exe")

SCENES: dict[str, dict] = {

    # ── "Daddy's home" ─────────────────────────────────────────────────────
    "home": {
        "patterns": [
            r"wake\s+up\s+daddy.?s\s+home",
            r"daddy.?s\s+home",
            r"i.?m\s+home",
        ],
        "greeting": "Welcome home. Setting things up.",
        "actions": [
            # Music first — plays in the background while everything else loads
            {"type": "spotify_playlist", "id": "4K92J71PPuxqvq8l8Q2tlO"},
            {"type": "wait", "seconds": 1.0},

            # Dev setup on primary monitor (1920×1080, monitor 0)
            {"type": "open_app",    "name": "vs code"},
            {"type": "snap",        "title": "Visual Studio Code",
                                    "position": "left", "monitor": 0, "wait": 7},

            # ChatGPT — right half of primary
            {"type": "open_url_window", "url": "https://chatgpt.com"},
            {"type": "snap",        "title": "ChatGPT",
                                    "position": "right", "monitor": 0, "wait": 8},

            # Claude — full screen on secondary monitor
            {"type": "open_url_window", "url": "https://claude.ai"},
            {"type": "snap",        "title": "Claude",
                                    "position": "full", "monitor": 1, "wait": 8},

            {"type": "say", "text": "All set."},
        ],
    },

    # ── Work mode (example — edit to taste) ────────────────────────────────
    "work": {
        "patterns": [
            r"work\s+mode",
            r"let.?s\s+work",
            r"time\s+to\s+work",
        ],
        "greeting": "Work mode. Pulling everything up.",
        "actions": [
            {"type": "open_app",        "name": "vs code"},
            {"type": "snap",            "title": "Visual Studio Code",
                                        "position": "full", "monitor": 0, "wait": 7},
            {"type": "open_url_window", "url": "https://github.com"},
            {"type": "snap",            "title": "GitHub",
                                        "position": "full", "monitor": 1, "wait": 8},
            {"type": "say", "text": "VS Code on the main screen, GitHub on the side."},
        ],
    },

}


def get(name: str) -> dict | None:
    return SCENES.get(name)


def match(message: str) -> dict | None:
    """Return the first scene whose patterns match the message, or None."""
    import re
    lowered = message.lower().strip()
    for scene in SCENES.values():
        for pattern in scene.get("patterns", []):
            if re.search(pattern, lowered):
                return scene
    return None
