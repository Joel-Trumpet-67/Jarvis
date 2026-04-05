"""
registry.py — App name → executable mapping for the EIGENFORM app launcher.

Keys are lowercase names Rocky recognises (and aliases).
Values are either:
  - A plain executable name (resolved from PATH)
  - An absolute path
  - A list [executable, arg1, arg2, ...]

Add entries here to teach Rocky about new apps.
"""

import os

_LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
_APPDATA      = os.environ.get("APPDATA", "")
_PF           = os.environ.get("ProgramFiles", r"C:\Program Files")
_PF86         = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

# ---------------------------------------------------------------------------
# App registry
# name → executable (str) or argument list (list[str])
# ---------------------------------------------------------------------------

APPS: dict[str, str | list[str]] = {
    # ── Windows built-ins ────────────────────────────────────────────────────
    "notepad":          "notepad.exe",
    "calculator":       "calc.exe",
    "calc":             "calc.exe",
    "paint":            "mspaint.exe",
    "mspaint":          "mspaint.exe",
    "snipping tool":    "snippingtool.exe",
    "snip":             "snippingtool.exe",
    "task manager":     "taskmgr.exe",
    "taskmgr":          "taskmgr.exe",
    "explorer":         "explorer.exe",
    "file explorer":    "explorer.exe",
    "cmd":              "cmd.exe",
    "command prompt":   "cmd.exe",
    "powershell":       "powershell.exe",
    "terminal":         "wt.exe",      # Windows Terminal (if installed)
    "wordpad":          "wordpad.exe",
    "clock":            ["explorer.exe", "shell:Alarms"],
    "settings":         ["explorer.exe", "ms-settings:"],
    "control panel":    "control.exe",
    "device manager":   ["devmgmt.msc"],

    # ── Browsers ─────────────────────────────────────────────────────────────
    "edge":     os.path.join(_PF86, r"Microsoft\Edge\Application\msedge.exe"),
    "chrome":   os.path.join(_PF,   r"Google\Chrome\Application\chrome.exe"),
    "firefox":  os.path.join(_PF,   r"Mozilla Firefox\firefox.exe"),
    "brave":    os.path.join(_APPDATA, r"..\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),

    # ── Media / communication ────────────────────────────────────────────────
    "spotify":  os.path.join(_APPDATA, r"Spotify\Spotify.exe"),
    "discord":  os.path.join(_LOCALAPPDATA, r"Discord\app-*\Discord.exe"),
    "steam":    os.path.join(_PF86, r"Steam\steam.exe"),
    "vlc":      os.path.join(_PF,   r"VideoLAN\VLC\vlc.exe"),

    # ── AI apps (Windows Store / MSIX — launched via shell: URI) ─────────────
    # Format: "shell:AppsFolder\<PackageFamilyName>!<AppId>"
    "claude":   "shell:AppsFolder\\Claude_pzs8sxrjxfjjc!Claude",
    "chatgpt":  os.path.join(_LOCALAPPDATA, r"Microsoft\WindowsApps\chatgpt.exe"),

    # ── Dev tools ────────────────────────────────────────────────────────────
    "code":       "code",
    "vscode":     "code",
    "vs code":    "code",
    # Open VS Code directly into the EIGENFORM project
    "eigenform":  ["code", r"C:\Users\Joel\Documents\GitHub\EIGENFORM"],
    "git bash":   os.path.join(_PF, r"Git\git-bash.exe"),
    "postman":    os.path.join(_LOCALAPPDATA, r"Postman\Postman.exe"),

    # ── Office ───────────────────────────────────────────────────────────────
    "word":       os.path.join(_PF, r"Microsoft Office\root\Office16\WINWORD.EXE"),
    "excel":      os.path.join(_PF, r"Microsoft Office\root\Office16\EXCEL.EXE"),
    "powerpoint": os.path.join(_PF, r"Microsoft Office\root\Office16\POWERPNT.EXE"),
    "outlook":    os.path.join(_PF, r"Microsoft Office\root\Office16\OUTLOOK.EXE"),
}


def resolve(name: str) -> str | list[str] | None:
    """
    Return the executable (or arg list) for a given app name, or None if unknown.
    Normalises the name to lowercase before lookup.
    """
    return APPS.get(name.lower().strip())
