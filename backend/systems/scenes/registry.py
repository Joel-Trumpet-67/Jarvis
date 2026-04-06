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
    # Primary monitor   (0): 1920×1080  — VS Code (left 2/3) + Spotify (right 1/3)
    # Secondary monitor (1): 1366×768   — Claude (left half) + ChatGPT (right half)
    "home": {
        "patterns": [
            r"wake\s+up\s+daddy.?s\s+home",
            r"daddy.?s\s+home",
            r"i.?m\s+home",
        ],
        "greeting": "Welcome home. Setting things up.",
        "actions": [
            # 1. Start Spotify playing — don't snap yet, it re-maximizes on load
            {"type": "spotify_playlist", "id": "4K92J71PPuxqvq8l8Q2tlO"},

            # 2. VS Code with EIGENFORM — snap left half of primary
            {"type": "open_app", "name": "eigenform"},
            {"type": "snap",   "title": "Visual Studio Code", "position": "left",
                                "monitor": 0, "wait": 10},

            # 3. Snap Spotify — do it twice because Spotify re-maximizes on load
            {"type": "snap",   "title": "Spotify",  "position": "right",
                                "monitor": 0, "wait": 4},
            {"type": "wait",   "seconds": 1.5},
            {"type": "snap",   "title": "Spotify",  "position": "right",
                                "monitor": 0, "wait": 2},

            # 4. Claude desktop app — left half of secondary monitor
            {"type": "open_app", "name": "claude"},
            {"type": "snap",   "title": "Claude",   "position": "left",
                                "monitor": 1, "wait": 8},

            # 5. ChatGPT desktop app — right half of secondary monitor
            {"type": "open_app", "name": "chatgpt"},
            {"type": "snap",   "title": "ChatGPT",  "position": "right",
                                "monitor": 1, "wait": 8},

            {"type": "say", "text": "All set."},
        ],
    },

    # ── Work mode ──────────────────────────────────────────────────────────
    "work": {
        "patterns": [
            r"work\s+mode",
            r"let.?s\s+work",
            r"time\s+to\s+work",
        ],
        "greeting": "Work mode.",
        "actions": [
            {"type": "open_app", "name": "eigenform"},
            {"type": "snap",     "title": "EIGENFORM", "position": "full",
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
