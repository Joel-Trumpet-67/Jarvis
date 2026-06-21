import json
import os

from server.config import DATA_DIR

REGISTRY_PATH = os.path.join(DATA_DIR, "tools", "registry.json")


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return []
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)


def save_registry(registry):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def get_tool(tool_id):
    return next((t for t in load_registry() if t["tool_id"] == tool_id), None)


def add_proposed_tool(tool_id, description, code):
    registry = load_registry()
    if any(t["tool_id"] == tool_id for t in registry):
        return registry

    registry.append(
        {
            "tool_id": tool_id,
            "description": description,
            "code": code,
            "approved": False,
            "rejected": False,
            "rejection_reason": None,
        }
    )
    save_registry(registry)
    return registry


def set_approval(tool_id, approved, rejection_reason=None):
    registry = load_registry()
    for tool in registry:
        if tool["tool_id"] == tool_id:
            tool["approved"] = approved
            tool["rejected"] = not approved
            tool["rejection_reason"] = rejection_reason if not approved else None
            break
    save_registry(registry)
    return registry


def pending_tools():
    return [t for t in load_registry() if not t["approved"] and not t["rejected"]]
