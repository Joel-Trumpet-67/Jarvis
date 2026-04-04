"""
config.py — Loads settings.json and exposes CONFIG dict.
Every other backend module imports from here.
"""

import json
import os
import sys


def _get_root() -> str:
    """
    Return the project root directory.
    - Frozen (PyInstaller exe): root = directory containing the exe,
      so settings.json lives next to EIGENFORM.exe and stays editable.
    - Source: root = project root (two levels up from this file).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_ROOT = _get_root()
SETTINGS_PATH = os.path.join(_ROOT, "data", "config", "settings.json")


def load_config() -> dict:
    if not os.path.exists(SETTINGS_PATH):
        print(f"[EIGENFORM] FATAL: settings.json not found at:\n  {SETTINGS_PATH}")
        sys.exit(1)

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        print(
            f"[EIGENFORM] Config loaded — "
            f"model: {config.get('model_name')} "
            f"@ {config.get('model_api_url')}"
        )
        return config

    except json.JSONDecodeError as e:
        print(f"[EIGENFORM] FATAL: settings.json is malformed:\n  {e}")
        sys.exit(1)


CONFIG: dict = load_config()
