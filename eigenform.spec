# -*- mode: python ; coding: utf-8 -*-
"""
eigenform.spec — PyInstaller build spec for EIGENFORM.

Build command (from project root):
    pyinstaller eigenform.spec

Output:
    dist/EIGENFORM/EIGENFORM.exe   ← double-click to launch
    dist/EIGENFORM/data/           ← copy your settings.json here

The frontend/ folder is bundled inside the exe.
The data/ folder (settings.json, app_registry.json) stays OUTSIDE
the exe so you can edit your API key and preferences without rebuilding.
"""

import os

ROOT = os.path.abspath(".")

# ── Analysis ─────────────────────────────────────────────────────────────────

a = Analysis(
    ["run.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[
        # Bundle the entire frontend inside the exe
        (os.path.join(ROOT, "frontend"), "frontend"),
    ],
    hiddenimports=[
        # Flask internals PyInstaller sometimes misses
        "flask",
        "flask.templating",
        "flask.json",
        "werkzeug",
        "werkzeug.serving",
        "werkzeug.exceptions",
        "werkzeug.routing",
        "werkzeug.middleware.shared_data",
        "werkzeug.debug",
        # Requests
        "requests",
        "urllib3",
        "charset_normalizer",
        "certifi",
        "idna",
        # Backend packages (ensure all submodules are found)
        "backend",
        "backend.config",
        "backend.main",
        "backend.ai",
        "backend.ai.core",
        "backend.ai.core.engine",
        "backend.ai.core.dispatcher",
        "backend.ai.core.response",
        "backend.ai.memory",
        "backend.ai.memory.short_term",
        "backend.ai.memory.long_term",
        "backend.ai.memory.context",
        "backend.ai.personality",
        "backend.ai.personality.jarvis",
        "backend.ai.personality.responses",
        "backend.ai.nlp",
        "backend.ai.reasoning",
        "backend.ai.speech",
        "backend.api",
        "backend.api.routes",
        "backend.api.routes.chat",
        "backend.api.routes.voice",
        "backend.api.routes.status",
        "backend.api.routes.session",
        "backend.api.routes.interrupt",
        "backend.systems",
        "backend.systems.apps",
        "backend.systems.files",
        "backend.systems.os_control",
        "backend.systems.web",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy packages we don't need
        "tkinter",
        "unittest",
        "email",
        "html",
        "http.server",
        "xml",
        "xmlrpc",
        "pydoc",
        "doctest",
        "difflib",
        "pickle",
        "sqlite3",
        "numpy",
        "pandas",
        "matplotlib",
        "PIL",
    ],
    noarchive=False,
    optimize=1,
)

# ── PYZ archive ───────────────────────────────────────────────────────────────

pyz = PYZ(a.pure)

# ── EXE ──────────────────────────────────────────────────────────────────────

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EIGENFORM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # Keep console for now — shows server status
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # Add icon path here when you have one
)

# ── COLLECT (onedir bundle) ───────────────────────────────────────────────────

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="EIGENFORM",
)
