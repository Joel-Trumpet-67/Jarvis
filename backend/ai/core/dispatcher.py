"""
dispatcher.py — Intent router for EIGENFORM.

Every message comes through here. The flow:

  1. Send the message to the AI model (via engine.stream_response)
  2. Buffer the full response silently
  3. Check if the response is a JSON command
       YES → execute the command, stream back a short confirmation
       NO  → stream the buffered text to the frontend normally

This lets Rocky decide when to act vs. when to speak, based on the
tool instructions in the system prompt.
"""

import re

from backend.ai.core.engine import stream_response
from backend.systems.executor import handle_command, execute_tool_call

# Keywords that suggest the model refused to act when it should have run a command
_REFUSAL_PATTERNS = [
    r"i can'?t (open|play|launch|search|access|browse)",
    r"i'?m unable to (open|play|launch|search|access|browse)",
    r"i don'?t have (the ability|access) to (open|play|launch|browse)",
    r"i cannot (open|play|launch|search|access|browse)",
]

# If these words are also in the message, it was likely a command request
_ACTION_KEYWORDS = ["youtube", "open", "play", "search", "launch", "browser", "website", "url"]


def _is_bad_refusal(user_message: str, response: str) -> bool:
    """Returns True if the model refused to act when it should have used a command."""
    resp_lower = response.lower()
    msg_lower  = user_message.lower()
    has_action = any(kw in msg_lower for kw in _ACTION_KEYWORDS)
    if not has_action:
        return False
    return any(re.search(p, resp_lower) for p in _REFUSAL_PATTERNS)


def dispatch(session_id: str, message: str, system_prompt: str):
    """
    Routes a message through the AI engine with command detection.
    Returns a generator of SSE-compatible event dicts.
    """
    return _buffered_dispatch(session_id, message, system_prompt)


def _buffered_dispatch(session_id: str, message: str, system_prompt: str):  # noqa: C901
    """
    Buffers the full model response before yielding anything to the frontend.

    - If the response is a JSON command → execute it, yield confirmation
    - If the response is normal text    → replay tokens to the frontend
    """
    tokens   = []
    metadata = {}

    for event in stream_response(session_id, message, system_prompt):
        etype = event.get("type")

        # Native function call from the model — execute immediately
        if etype == "tool_call":
            executed, confirmation = execute_tool_call(event["name"], event.get("args", {}))
            if executed and confirmation:
                yield {"type": "token", "content": confirmation}
            continue

        if etype == "token":
            tokens.append(event.get("content", ""))

        elif etype in ("error", "interrupted"):
            metadata = event
            break

        elif etype == "done":
            break

    if metadata:
        yield metadata
        return

    # Fallback: check if the model outputted a raw JSON command instead of using tool calling
    full_response = "".join(tokens)
    if full_response.strip().startswith("{"):
        executed, confirmation = handle_command(full_response)
        if executed:
            if confirmation:
                yield {"type": "token", "content": confirmation}
            yield {"type": "done"}
            return

    # Normal text response
    for token in tokens:
        yield {"type": "token", "content": token}
    yield {"type": "done"}
