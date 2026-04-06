"""
dispatcher.py — Intent router for EIGENFORM.

Checks the message against command patterns BEFORE touching the AI model.
If it matches a command, it executes directly and returns Rocky's confirmation.
If nothing matches, it falls through to the AI for normal conversation.

This means commands are 100% reliable — the model's RLHF training never
gets a chance to refuse or explain limitations.
"""

import re

from backend.systems.executor import execute_tool_call
from backend.systems.apps.registry import APPS as _APP_REGISTRY
from backend.systems.scenes import registry as _scenes
from backend.systems.scenes.runner import run_scene


# ---------------------------------------------------------------------------
# Command pattern registry
# Each entry defines:
#   patterns  — regex list; first match wins
#   tool      — name matching an entry in executor._ACTIONS
#   extract   — callable(message) -> args dict passed to the tool
# ---------------------------------------------------------------------------

def _extract_youtube_query(message: str) -> dict:
    """Pull the search term out of a YouTube request."""
    msg = message.strip()

    patterns = [
        r'play\s+(.+?)\s+on\s+(?:youtube|yt)\s*$',
        r'play\s+(.+?)\s+(?:youtube|yt)',
        r'(?:search|find)\s+(?:for\s+)?(.+?)\s+on\s+(?:youtube|yt)',
        r'(?:youtube|yt)\s+(?:search\s+for|search|find|play)\s+(.+)',
        r'(?:open|launch|go\s+to)\s+(?:youtube|yt)\s+(?:and\s+)?(?:play|search\s+for|search|find)\s+(.+)',
        r'(?:put\s+on|stream|watch)\s+(.+?)\s+on\s+(?:youtube|yt)',
    ]

    for pattern in patterns:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            if query:
                return {"query": query}

    # "Open YouTube" / "Launch YouTube" with no query
    return {"query": None}


def _extract_app_name(message: str) -> dict:
    """
    Pull the app name from a launch request and return the best registry match.
    E.g. "open notepad" → {"name": "notepad"}
         "launch vs code" → {"name": "vs code"}
    """
    msg = message.lower().strip()

    # Strip the verb prefix
    for verb in ("open", "launch", "start", "run", "fire up"):
        if msg.startswith(verb):
            candidate = msg[len(verb):].strip()
            # Direct registry hit
            if candidate in _APP_REGISTRY:
                return {"name": candidate}
            # Try dropping trailing words like "for me", "please", "app"
            for suffix in (" app", " please", " for me", " now"):
                if candidate.endswith(suffix):
                    trimmed = candidate[: -len(suffix)].strip()
                    if trimmed in _APP_REGISTRY:
                        return {"name": trimmed}
            # Return the raw candidate — launcher will try it
            return {"name": candidate}

    return {"name": msg}


def _extract_url(message: str) -> dict:
    """Extract a URL from the message, or map common site names."""
    sites = {
        "google":    "https://www.google.com",
        "youtube":   "https://www.youtube.com",
        "github":    "https://www.github.com",
        "reddit":    "https://www.reddit.com",
        "twitter":   "https://www.twitter.com",
        "x":         "https://www.x.com",
        "facebook":  "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "netflix":   "https://www.netflix.com",
        "spotify":   "https://www.spotify.com",
        "twitch":    "https://www.twitch.tv",
    }

    msg = message.lower()

    # Check for an explicit URL
    url_match = re.search(r'https?://\S+', message, re.IGNORECASE)
    if url_match:
        return {"url": url_match.group(0)}

    # Match "open <site>"
    open_match = re.search(r'open\s+(\w+)', msg)
    if open_match:
        site = open_match.group(1).lower()
        if site in sites:
            return {"url": sites[site]}

    return {"url": "https://www.google.com"}


# Build a regex that matches any known app name from the registry.
# e.g. "notepad|calculator|calc|vs code|..."
_APP_NAMES_PATTERN = "|".join(
    re.escape(name) for name in sorted(_APP_REGISTRY.keys(), key=len, reverse=True)
)


_COMMANDS = [
    # ── App launcher ──────────────────────────────────────────────────────────
    {
        "name": "open_app",
        "patterns": [
            rf'\b(?:open|launch|start|run)\s+(?:{_APP_NAMES_PATTERN})\b',
            rf'\bfire\s+up\s+(?:{_APP_NAMES_PATTERN})\b',
        ],
        "tool":    "open_app",
        "extract": _extract_app_name,
    },

    # ── Media control ─────────────────────────────────────────────────────────
    {
        "name": "next_track",
        "patterns": [
            r'\b(?:next|skip)\s+(?:track|song|music)\b',
            r'\bskip\b',
            r'\bclick\s+(?:the\s+)?next\b',
            r'\bpress\s+next\b',
            r'\bnext\s+(?:song|track)\b',
            r'\bgo\s+to\s+(?:the\s+)?next\b',
        ],
        "tool":    "next_track",
        "extract": lambda _: {},
    },
    {
        "name": "prev_track",
        "patterns": [
            r'\b(?:previous|prev|last|back)\s+(?:track|song|music)\b',
            r'\bgo\s+back\b',
            r'\bplay\s+(?:that\s+)?again\b',
            r'\breplay\b',
        ],
        "tool":    "prev_track",
        "extract": lambda _: {},
    },
    {
        "name": "play_pause",
        "patterns": [
            r'^\s*play\s*$',                                         # bare "play"
            r'^\s*pause\s*$',                                        # bare "pause"
            r'\bpause\s+(?:the\s+)?(?:music|song|track|spotify)\b', # "pause the music"
            r'\bunpause\b',
            r'\b(?:press|click|hit)\s+play\b',                      # "press play", "click play"
            r'\b(?:press|click|hit)\s+pause\b',
            r'\bresume\s+(?:the\s+)?(?:music|song|spotify|playing)?\b',
            r'\bplay[/ ]pause\b',
            r'\bplay\s+(?:the\s+)?(?:music|song|spotify)\b',
            r'\bstop\s+(?:the\s+)?music\b',
            r'\btoggle\s+(?:the\s+)?(?:music|playback)\b',
            r'\bkeep\s+playing\b',
        ],
        "tool":    "play_pause",
        "extract": lambda _: {},
    },
    {
        "name": "volume_up",
        "patterns": [
            r'\bvolume\s+up\b',
            r'\bturn\s+(?:it|the\s+volume|music)?\s*up\b',
            r'\blouder\b',
        ],
        "tool":    "volume_up",
        "extract": lambda _: {},
    },
    {
        "name": "volume_down",
        "patterns": [
            r'\bvolume\s+down\b',
            r'\bturn\s+(?:it|the\s+volume|music)?\s*down\b',
            r'\bquieter\b',
            r'\blower\s+(?:the\s+)?volume\b',
        ],
        "tool":    "volume_down",
        "extract": lambda _: {},
    },
    {
        "name": "mute",
        "patterns": [
            r'\bmute\b',
            r'\bsilence\s+(?:the\s+)?(?:music|audio|sound)?\b',
        ],
        "tool":    "mute",
        "extract": lambda _: {},
    },

    # ── YouTube ───────────────────────────────────────────────────────────────
    {
        "name": "search_youtube",
        "patterns": [
            r'\b(?:play|stream|watch|put\s+on)\b.{1,60}\b(?:youtube|yt)\b',
            r'\b(?:youtube|yt)\b.{0,60}\b(?:play|search|find|watch)\b',
            r'\bsearch\b.{0,30}\b(?:youtube|yt)\b',
            r'\b(?:find|search\s+for)\b.{1,60}\b(?:on\s+)?(?:youtube|yt)\b',
        ],
        "tool":    "search_youtube",
        "extract": _extract_youtube_query,
    },
    {
        "name": "open_youtube",
        "patterns": [
            r'\b(?:open|launch|go\s+to)\s+(?:youtube|yt)\b',
        ],
        "tool":    "open_url",
        "extract": lambda msg: {"url": "https://www.youtube.com"},
    },
    {
        "name": "open_site",
        "patterns": [
            r'\bopen\s+(?:google|github|reddit|twitter|facebook|instagram|netflix|twitch|x\.com)\b',
            r'\bgo\s+to\s+(?:google|github|reddit|twitter|facebook|instagram|netflix|twitch)\b',
            r'\bgo\s+to\s+spotify\s*$',   # only bare "go to spotify" — not "go to spotify and click next"
        ],
        "tool":    "open_url",
        "extract": _extract_url,
    },
]


def _match(message: str):
    """Return the first matching command entry, or None."""
    lowered = message.lower()
    for cmd in _COMMANDS:
        for pattern in cmd["patterns"]:
            if re.search(pattern, lowered):
                return cmd
    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def dispatch(session_id: str, message: str, system_prompt: str):
    """
    Routes a message to a scene, a direct command, or the AI engine.
    Priority: scenes → commands → AI model
    """
    # 1. Scene triggers — highest priority
    scene = _scenes.match(message)
    if scene:
        return run_scene(scene)

    # 2. Single commands
    cmd = _match(message)
    if cmd:
        return _run_command(cmd, message)

    # 3. AI model
    from backend.ai.core.engine import stream_response
    return stream_response(session_id, message, system_prompt)


def _run_command(cmd: dict, message: str):
    """Execute a matched command and yield a confirmation token."""
    args = cmd["extract"](message)
    executed, confirmation = execute_tool_call(cmd["tool"], args)

    # Emit a structured command_executed event for the frontend to style
    yield {
        "type":    "command_executed",
        "command": cmd["name"],
        "args":    args,
        "ok":      executed,
    }

    if executed and confirmation:
        yield {"type": "token", "content": confirmation}
    elif not executed:
        yield {"type": "token", "content": "Couldn't run that command."}

    yield {"type": "done"}
