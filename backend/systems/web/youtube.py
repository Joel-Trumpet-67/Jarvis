"""
youtube.py — Opens YouTube and searches for a song or video.
"""

import re
import webbrowser
import urllib.parse


# Phrases stripped from the user's message before using the remainder as the search query
_STRIP_PHRASES = [
    r"play\s+(.+?)\s+(?:on\s+)?youtube",
    r"(?:open|launch|go\s+to)\s+youtube\s+(?:and\s+)?(?:play|search\s+for|search|find)?\s*(.*)",
    r"(?:search|find)\s+(?:for\s+)?(.+?)\s+on\s+(?:youtube|yt)",
    r"youtube\s+(?:search\s+for|search|find|play)\s+(.*)",
    r"(?:open|launch|go\s+to)\s+youtube",
    r"youtube",
]


def extract_query(message: str) -> str | None:
    """Pull the search term out of the user's message. Returns None if no query found."""
    msg = message.strip().lower()

    for pattern in _STRIP_PHRASES:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            try:
                query = match.group(1).strip()
                return query if query else None
            except IndexError:
                return None

    return None


def open_youtube(query: str | None = None) -> dict:
    """
    Opens YouTube in the default browser.
    If a query is provided, opens the search results page for it.
    """
    if query:
        url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": query})
        message = f"Opening YouTube — searching for {query}."
    else:
        url = "https://www.youtube.com"
        message = "Opening YouTube."

    try:
        webbrowser.open(url, new=2)
        return {"success": True, "message": message}
    except Exception as e:
        return {"success": False, "message": f"Couldn't open YouTube: {e}"}
