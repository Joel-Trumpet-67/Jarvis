"""
executor.py — Executes structured JSON commands from the AI model.

Rocky outputs a JSON object when it wants to perform an action.
This module parses and executes those commands safely.

Only predefined actions are allowed. Anything unrecognised is ignored.
"""

import json
import webbrowser
import urllib.parse

from backend.systems.apps.launcher import launch_app as _launch_app


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def _open_app(data: dict) -> str:
    name = data.get("name", "").strip()
    if not name:
        return "No app name provided."
    ok, msg = _launch_app(name)
    if not ok:
        return f"I don't know how to open '{name}'."
    return msg


def _open_url(data: dict) -> str:
    url = data.get("url", "").strip()
    if not url:
        return "No URL provided."
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url, new=2)
    return f"Opened {url}."


def _search_youtube(data: dict) -> str:
    query = data.get("query", "").strip()
    if not query:
        return "No search query provided."
    encoded = urllib.parse.urlencode({"search_query": query})
    url = f"https://www.youtube.com/results?{encoded}"
    webbrowser.open(url, new=2)
    return f"Opening YouTube — {query}."


# ---------------------------------------------------------------------------
# Dispatch table — only these actions are permitted
# ---------------------------------------------------------------------------

_ACTIONS = {
    "open_app":       _open_app,
    "open_url":       _open_url,
    "search_youtube": _search_youtube,
}


# ---------------------------------------------------------------------------
# OpenAI-format tool definitions (sent in the API payload)
# The model uses these to decide when to call a tool vs. respond in text.
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": (
                "Open a desktop application by name. Use this when the user wants "
                "to launch an app like Notepad, Calculator, Chrome, Spotify, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The app name, e.g. 'notepad', 'calculator', 'chrome'",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": (
                "Search YouTube for a song, video, or topic and open the results "
                "in the user's browser. Use this whenever the user wants to play "
                "music, watch a video, or search YouTube."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. 'Bohemian Rhapsody Queen'",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": (
                "Open a specific URL in the user's browser. Use this when the user "
                "wants to open a website or navigate to a specific page."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to open, e.g. 'https://www.youtube.com'",
                    }
                },
                "required": ["url"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def execute_tool_call(name: str, args: dict) -> tuple[bool, str]:
    """
    Execute a tool call from the model's native function calling output.

    Returns:
        (True,  confirmation_message)  — tool recognised and executed
        (False, "")                    — unknown tool
    """
    handler = _ACTIONS.get(name)
    if handler is None:
        return False, ""
    try:
        message = handler(args)
        return True, message
    except Exception as e:
        return True, f"Command failed: {e}"


def handle_command(response_text: str) -> tuple[bool, str]:
    """
    Try to parse response_text as a JSON command and execute it.

    Returns:
        (True,  confirmation_message)  — command recognised and executed
        (False, "")                    — not a command, treat as normal text
    """
    text = response_text.strip()

    if not text.startswith("{"):
        return False, ""

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False, ""

    action = data.get("action", "")
    handler = _ACTIONS.get(action)

    if handler is None:
        return False, ""

    try:
        message = handler(data)
        return True, message
    except Exception as e:
        return True, f"Command failed: {e}"
