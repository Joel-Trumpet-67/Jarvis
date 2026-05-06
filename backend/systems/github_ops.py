"""
github_ops.py — GitHub API operations for Jarvis.

Allows Jarvis to create repositories, read files, and write files
via the GitHub REST API using a personal access token from settings.json.

Token must have: repo scope (for private repos) or public_repo (for public).
Set "github_token" and "github_owner" in data/config/settings.json.
"""

import base64
import json
import urllib.request
import urllib.error

from backend.config import CONFIG


def _token() -> str:
    return CONFIG.get("github_token", "").strip()


def _owner() -> str:
    return CONFIG.get("github_owner", "").strip()


def _api(method: str, endpoint: str, body: dict = None) -> tuple[bool, dict | str]:
    """
    Make a GitHub API request.
    Returns (success, response_dict_or_error_string).
    """
    token = _token()
    if not token:
        return False, "No GitHub token configured. Add 'github_token' to settings.json."

    url = f"https://api.github.com{endpoint}"
    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Jarvis-Self")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            return False, err_body.get("message", str(e))
        except Exception:
            return False, str(e)
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def github_create_repo(data: dict) -> str:
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    private = bool(data.get("private", False))

    if not name:
        return "No repository name provided."

    ok, resp = _api("POST", "/user/repos", {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": True,
    })

    if not ok:
        return f"Failed to create repo: {resp}"

    url = resp.get("html_url", "")
    visibility = "private" if private else "public"
    return f"Created {visibility} repo: {url}"


def github_read_file(data: dict) -> str:
    repo = data.get("repo", "").strip()
    path = data.get("path", "").strip()

    if not repo or not path:
        return "Both 'repo' (owner/name) and 'path' are required."

    ok, resp = _api("GET", f"/repos/{repo}/contents/{path}")

    if not ok:
        return f"Failed to read file: {resp}"

    if isinstance(resp, list):
        # Directory listing
        entries = [f"{e['type']}  {e['name']}" for e in resp]
        return "\n".join(entries)

    encoding = resp.get("encoding", "")
    content = resp.get("content", "")

    if encoding == "base64":
        try:
            decoded = base64.b64decode(content).decode("utf-8")
            return f"--- {path} ---\n{decoded}"
        except Exception as e:
            return f"Failed to decode file content: {e}"

    return content or "Empty file."


def github_write_file(data: dict) -> str:
    repo = data.get("repo", "").strip()
    path = data.get("path", "").strip()
    content = data.get("content", "")
    message = data.get("message", "Update via Jarvis").strip()

    if not repo or not path:
        return "Both 'repo' (owner/name) and 'path' are required."

    # Check if file exists to get its SHA (required for updates)
    sha = None
    ok, existing = _api("GET", f"/repos/{repo}/contents/{path}")
    if ok and isinstance(existing, dict):
        sha = existing.get("sha")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    body = {
        "message": message,
        "content": encoded,
    }
    if sha:
        body["sha"] = sha

    ok, resp = _api("PUT", f"/repos/{repo}/contents/{path}", body)

    if not ok:
        return f"Failed to write file: {resp}"

    action = "Updated" if sha else "Created"
    commit_url = resp.get("commit", {}).get("html_url", "")
    return f"{action} {path} in {repo}. Commit: {commit_url}"


def github_list_repos(data: dict) -> str:
    owner = data.get("owner", _owner()).strip()
    if not owner:
        return "No owner specified and no 'github_owner' in settings.json."

    ok, resp = _api("GET", f"/users/{owner}/repos?per_page=50&sort=updated")
    if not ok:
        return f"Failed to list repos: {resp}"

    if not isinstance(resp, list):
        return "Unexpected response from GitHub."

    lines = [f"{r['name']}  ({'private' if r['private'] else 'public'})  {r.get('html_url','')}"
             for r in resp]
    return "\n".join(lines) if lines else f"No repos found for {owner}."
