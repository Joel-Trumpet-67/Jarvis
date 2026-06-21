import json
import os
from datetime import datetime, timezone

from server.config import DATA_DIR


def _user_dir(username):
    return os.path.join(DATA_DIR, "users", username)


def _profile_path(username):
    return os.path.join(_user_dir(username), "profile.json")


def _history_path(username):
    return os.path.join(_user_dir(username), "history.json")


def load_profile(username):
    path = _profile_path(username)
    if not os.path.exists(path):
        return {"name": username.capitalize(), "preferences": {}, "facts": []}
    with open(path, "r") as f:
        return json.load(f)


def save_profile(username, profile):
    os.makedirs(_user_dir(username), exist_ok=True)
    with open(_profile_path(username), "w") as f:
        json.dump(profile, f, indent=2)


def update_profile(username, add_facts=None, remove_facts=None, preferences=None):
    profile = load_profile(username)
    facts = profile.get("facts", [])

    for fact in remove_facts or []:
        facts = [f for f in facts if f != fact]

    for fact in add_facts or []:
        if fact and fact not in facts:
            facts.append(fact)

    profile["facts"] = facts
    profile.setdefault("preferences", {})
    profile["preferences"].update(preferences or {})

    save_profile(username, profile)
    return profile


def load_history(username):
    path = _history_path(username)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def append_history(username, role, content):
    history = load_history(username)
    history.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    os.makedirs(_user_dir(username), exist_ok=True)
    with open(_history_path(username), "w") as f:
        json.dump(history, f, indent=2)
    return history
