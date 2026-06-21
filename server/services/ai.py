import json
import re

from anthropic import Anthropic

from server.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from server.services import memory, registry

_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

PROPOSE_TOOL_PATTERN = re.compile(r"<propose_tool>(.*?)</propose_tool>", re.DOTALL)
MEMORY_UPDATE_PATTERN = re.compile(r"<memory_update>(.*?)</memory_update>", re.DOTALL)


def _build_system_prompt(display_name, profile, tools):
    tool_lines = (
        "\n".join(
            f"- {t['tool_id']} "
            f"({'approved' if t['approved'] else 'rejected' if t['rejected'] else 'pending approval'}): "
            f"{t['description']}"
            for t in tools
        )
        or "No tools registered yet."
    )

    facts = "\n".join(f"- {fact}" for fact in profile.get("facts", [])) or "No stored facts yet."
    preferences = json.dumps(profile.get("preferences", {}), indent=2)

    return f"""You are Jarvis, a personal AI assistant for {display_name}.

Always refer to {display_name} by name when it feels natural. You have persistent memory of facts \
and preferences about {display_name}. Reference this context naturally without being asked to.

Known facts about {display_name}:
{facts}

Known preferences:
{preferences}

Available tools in the registry:
{tool_lines}

Two special blocks you can append to the very end of your reply. Both are stripped before \
{display_name} sees the message, so never mention them out loud.

1. If {display_name} tells you to remember something, states a preference, or corrects a fact you \
got wrong, append exactly one block:
<memory_update>{{"add_facts": ["short factual statement"], "remove_facts": ["exact old fact text to \
remove, only when correcting a mistake"], "preferences": {{"key": "value"}}}}</memory_update>
Omit keys you don't need. Never repeat a fact you have already been corrected on.

2. If {display_name} asks for something that needs a capability not in the tool registry above, \
write the tool yourself and append exactly one block:
<propose_tool>{{"tool_id": "snake_case_id", "description": "plain English description", "code": \
"python function code as a string"}}</propose_tool>
Never propose a tool that is already listed above, approved, pending, or rejected.
"""


def _extract_block(pattern, text):
    match = pattern.search(text)
    if not match:
        return text, None
    cleaned = pattern.sub("", text).strip()
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        payload = None
    return cleaned, payload


def generate_response(username, display_name, message):
    if _client is None:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    profile = memory.load_profile(username)
    tools = registry.load_registry()
    history = memory.load_history(username)[-20:]

    system_prompt = _build_system_prompt(display_name, profile, tools)

    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    messages.append({"role": "user", "content": message})

    response = _client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    raw_text = "".join(block.text for block in response.content if block.type == "text")

    raw_text, memory_payload = _extract_block(MEMORY_UPDATE_PATTERN, raw_text)
    raw_text, tool_payload = _extract_block(PROPOSE_TOOL_PATTERN, raw_text)

    if memory_payload:
        memory.update_profile(
            username,
            add_facts=memory_payload.get("add_facts"),
            remove_facts=memory_payload.get("remove_facts"),
            preferences=memory_payload.get("preferences"),
        )

    if tool_payload and all(k in tool_payload for k in ("tool_id", "description", "code")):
        registry.add_proposed_tool(
            tool_payload["tool_id"], tool_payload["description"], tool_payload["code"]
        )

    memory.append_history(username, "user", message)
    memory.append_history(username, "assistant", raw_text)

    return raw_text
