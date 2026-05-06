"""
self_modify.py — Tools for Jarvis to read and rewrite its own source code.

Gives Jarvis the ability to add new capabilities by modifying its own files
and committing/pushing the changes to its repository.

All paths are relative to the project root. Writes are sandboxed to the
project root — paths attempting to escape (../) are rejected.
"""

import os
import subprocess
import sys


def _project_root() -> str:
    """Return the absolute path to the project root."""
    from backend.config import CONFIG
    configured = CONFIG.get("project_root", "").strip()
    if configured and os.path.isdir(configured):
        return configured
    # Default: two levels up from this file (backend/systems/ → root)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _safe_path(relative_path: str) -> tuple[bool, str]:
    """
    Resolve a relative path against the project root.
    Returns (ok, absolute_path) — ok=False if the path escapes the root.
    """
    root = _project_root()
    abs_path = os.path.normpath(os.path.join(root, relative_path))
    if not abs_path.startswith(root):
        return False, ""
    return True, abs_path


# ---------------------------------------------------------------------------
# Public tool handlers
# ---------------------------------------------------------------------------

def read_source_file(data: dict) -> str:
    path = data.get("path", "").strip()
    if not path:
        return "No path provided."
    ok, abs_path = _safe_path(path)
    if not ok:
        return "Path outside project root — rejected."
    if not os.path.isfile(abs_path):
        return f"File not found: {path}"
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        # Return with line numbers for easier reference
        numbered = "\n".join(f"{i+1:4d}  {line}" for i, line in enumerate(lines))
        return f"--- {path} ({len(lines)} lines) ---\n{numbered}"
    except Exception as e:
        return f"Read failed: {e}"


def write_source_file(data: dict) -> str:
    path = data.get("path", "").strip()
    content = data.get("content", "")
    if not path:
        return "No path provided."
    ok, abs_path = _safe_path(path)
    if not ok:
        return "Path outside project root — rejected."
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written: {path}"
    except Exception as e:
        return f"Write failed: {e}"


def list_source_files(data: dict) -> str:
    directory = data.get("directory", "").strip() or "."
    ok, abs_dir = _safe_path(directory)
    if not ok:
        return "Path outside project root — rejected."
    if not os.path.isdir(abs_dir):
        return f"Directory not found: {directory}"
    try:
        lines = []
        for root, dirs, files in os.walk(abs_dir):
            # Skip hidden dirs and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            rel_root = os.path.relpath(root, _project_root())
            for fname in sorted(files):
                lines.append(os.path.join(rel_root, fname))
        return "\n".join(lines) if lines else "Empty directory."
    except Exception as e:
        return f"List failed: {e}"


def git_commit_push(data: dict) -> str:
    message = data.get("message", "").strip()
    if not message:
        return "No commit message provided."
    root = _project_root()
    try:
        # Stage all changes
        result = subprocess.run(
            ["git", "add", "-A"],
            cwd=root, capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"git add failed: {result.stderr.strip()}"

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=root, capture_output=True, text=True
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "nothing to commit" in stderr or "nothing to commit" in result.stdout:
                return "Nothing to commit — working tree clean."
            return f"git commit failed: {stderr}"

        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root, capture_output=True, text=True
        )
        branch = branch_result.stdout.strip() or "HEAD"

        # Push
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=root, capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Committed but push failed: {result.stderr.strip()}"

        return f"Committed and pushed to {branch}: {message}"
    except Exception as e:
        return f"Git operation failed: {e}"
