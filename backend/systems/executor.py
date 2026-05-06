"""
executor.py — Executes structured JSON commands from the AI model.

Jarvis outputs a JSON object when it wants to perform an action.
This module parses and executes those commands safely.

Only predefined actions are allowed. Anything unrecognised is ignored.
"""

import json
import webbrowser
import urllib.parse

from backend.systems.apps.launcher import launch_app as _launch_app
from backend.systems import media as _media
from backend.systems import self_modify as _self_modify
from backend.systems import github_ops as _github


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
    # System / browser
    "open_app":            _open_app,
    "open_url":            _open_url,
    "search_youtube":      _search_youtube,
    # Media
    "next_track":          _media.next_track,
    "prev_track":          _media.prev_track,
    "play":                _media.play,
    "pause":               _media.pause,
    "play_pause":          _media.play_pause,
    "stop_media":          _media.stop_media,
    "volume_up":           _media.volume_up,
    "volume_down":         _media.volume_down,
    "mute":                _media.mute,
    # Self-modification
    "read_source_file":    _self_modify.read_source_file,
    "write_source_file":   _self_modify.write_source_file,
    "list_source_files":   _self_modify.list_source_files,
    "git_commit_push":     _self_modify.git_commit_push,
    # GitHub repo management
    "github_create_repo":  _github.github_create_repo,
    "github_read_file":    _github.github_read_file,
    "github_write_file":   _github.github_write_file,
    "github_list_repos":   _github.github_list_repos,
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
    {
        "type": "function",
        "function": {
            "name": "read_source_file",
            "description": (
                "Read a file from Jarvis's own source code. Use this when asked to "
                "inspect, review, or understand any file in the project."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root, e.g. 'backend/systems/executor.py'",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_source_file",
            "description": (
                "Write or overwrite a file in Jarvis's own source code. Use this to "
                "add new capabilities, fix bugs, or modify any part of the codebase."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_source_files",
            "description": "List all files in a directory of Jarvis's own source code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Relative path from project root, e.g. 'backend/systems'",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit_push",
            "description": (
                "Stage all changes, commit with a message, and push to the remote "
                "repository. Use after writing source files to save the changes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Commit message describing the change",
                    }
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_create_repo",
            "description": "Create a new GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Repository name",
                    },
                    "description": {
                        "type": "string",
                        "description": "Repository description",
                    },
                    "private": {
                        "type": "boolean",
                        "description": "Whether the repository should be private",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_read_file",
            "description": "Read a file from any GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository in 'owner/name' format, e.g. 'joel-trumpet-67/jarvis'",
                    },
                    "path": {
                        "type": "string",
                        "description": "File path within the repository",
                    },
                },
                "required": ["repo", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_write_file",
            "description": "Create or update a file in a GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "Repository in 'owner/name' format",
                    },
                    "path": {
                        "type": "string",
                        "description": "File path within the repository",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content",
                    },
                    "message": {
                        "type": "string",
                        "description": "Commit message",
                    },
                },
                "required": ["repo", "path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_list_repos",
            "description": "List GitHub repositories for a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "GitHub username (defaults to configured github_owner)",
                    }
                },
                "required": [],
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
