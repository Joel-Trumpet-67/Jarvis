from hmac import compare_digest

from flask import Blueprint, jsonify, request, session

from server.config import USERS

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    user = USERS.get(username)
    if not user or not compare_digest(password, user["password"]):
        return jsonify({"error": "invalid credentials"}), 401

    session["user"] = username
    session["role"] = user["role"]
    session["display_name"] = user["display_name"]

    return jsonify(
        {"username": username, "role": user["role"], "display_name": user["display_name"]}
    )


@auth_bp.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@auth_bp.get("/api/auth/me")
def me():
    if "user" not in session:
        return jsonify({"authenticated": False})

    return jsonify(
        {
            "authenticated": True,
            "username": session["user"],
            "role": session["role"],
            "display_name": session["display_name"],
        }
    )
