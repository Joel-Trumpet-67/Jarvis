"""
launcher.py — Opens desktop applications via subprocess.

Uses the registry to map app names to executables.
Returns (success: bool, message: str) so the dispatcher can pass
a confirmation token back to the frontend.
"""

import os
import glob
import subprocess

from backend.systems.apps.registry import resolve


def _resolve_glob(path: str) -> str:
    """
    If `path` contains a glob wildcard, expand it and return the first match.
    Returns the original path unchanged if no wildcards or no match found.
    """
    if '*' not in path and '?' not in path:
        return path
    matches = sorted(glob.glob(path))
    return matches[-1] if matches else path  # latest version (lexicographic)


def launch_app(name: str) -> tuple[bool, str]:
    """
    Launch an application by name.

    Returns:
        (True,  "Opening <name>.")   — launched successfully
        (True,  "Couldn't open...")  — recognised but failed to start
        (False, "")                  — app name not in registry
    """
    target = resolve(name)
    if target is None:
        return False, ""

    # Normalise to a list of args
    if isinstance(target, str):
        args = [target]
    else:
        args = list(target)

    executable = _resolve_glob(args[0])
    args[0] = executable

    # If the path doesn't exist and it's not a bare command name (i.e. in PATH),
    # skip rather than crash.
    if os.path.isabs(executable) and not os.path.exists(executable):
        return True, f"Can't find {name} — it may not be installed."

    try:
        subprocess.Popen(args, shell=False, close_fds=True)
        display = name.title()
        return True, f"Opening {display}."
    except FileNotFoundError:
        return True, f"Can't find {name} — it may not be installed."
    except PermissionError:
        return True, f"Permission denied opening {name}."
    except Exception as e:
        return True, f"Couldn't open {name}: {e}"
