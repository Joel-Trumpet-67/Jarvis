"""
registry.py — Scene definitions for Jarvis.

A scene is a named routine Jarvis runs when a trigger phrase is detected.
Each scene has:
  patterns  — regex list (any match triggers the scene)
  greeting  — what Jarvis says when the scene starts
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
    monitor: int    — 0 = primary, 1 = secondary
    wait: float     — seconds to wait for the window to appear (default 5)

  wait
    seconds: float  — pause between actions

  say
    text: str       — Jarvis says something mid-scene

────────────────────────────────────────────────────────────────
"""

import os

_PF    = os.environ.get("ProgramFiles",        r"C:\Program Files")
_PF86  = os.environ.get("ProgramFiles(x86)",   r"C:\Program Files (x86)")
_CHROME = os.path.join(_PF, r"Google\Chrome\Application\chrome.exe")

SCENES: dict = {

    # ── "Daddy's home" ──────────────────────────────────────────────────
    "home": {
        "patterns": [
            r"wake\s+up\s+daddy.?s\s+home",
            r"daddy.?s\s+home",
            r"i.?m\s+home",
        ],
        "greeting": "Welcome home. Setting things up.",
        "actions": [
            {"type": "spotify_playlist", "id": "4K92J71PPuxqvq8l8Q2tlO"},
            {"type": "open_app", "name": "vscode"},
            {"type": "snap",    "title": "Visual Studio Code", "position": "left",
                                 "monitor": 0, "wait": 10},
            {"type": "snap",    "title": "Spotify",  "position": "right",
                                 "monitor": 0, "wait": 4},
            {"type": "open_app", "name": "claude"},
            {"type": "snap",    "title": "Claude",   "position": "left",
                                 "monitor": 1, "wait": 8},
            {"type": "open_app", "name": "chatgpt"},
            {"type": "snap",    "title": "ChatGPT",  "position": "right",
                                 "monitor": 1, "wait": 8},
            {"type": "say", "text": "All set."},
        ],
    },

    # ── Work mode ──────────────────────────────────────────────────────
    "work": {
        "patterns": [
            r"work\s+mode",
            r"let.?s\s+work",
            r"time\s+to\s+work",
        ],
        "greeting": "Work mode.",
        "actions": [
            {"type": "open_app", "name": "vscode"},
            {"type": "snap",    "title": "Visual Studio Code", "position": "full",
                                 "monitor": 0, "wait": 8},
            {"type": "say", "text": "VS Code up."},
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
