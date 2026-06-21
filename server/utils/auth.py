from functools import wraps

from flask import jsonify, session


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)

    return wrapper


def owner_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "owner":
            return jsonify({"error": "forbidden"}), 403
        return f(*args, **kwargs)

    return wrapper
