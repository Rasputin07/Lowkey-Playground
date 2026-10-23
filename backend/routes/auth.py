from flask import Blueprint, g, jsonify

import db
from errors import bad_request, not_found
from routes.helpers import json_body
from security import create_session, require_auth

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.get("/demo-users")
def demo_users():
    """For the mock-login dropdown only."""
    return jsonify({"mock_auth": True, "users": [{k: u[k] for k in ("id", "name", "role")} for u in db.list_users()]})


@bp.post("/mock-login")
def mock_login():
    uid = json_body().get("user_id")
    if not isinstance(uid, str):
        raise bad_request("user_id is required.")
    user = db.get_user(uid)
    if not user:
        raise not_found("Unknown demo user.")
    return jsonify({"token": create_session(uid), "user": user, "mock_auth": True,
                    "notice": "Mock login for demonstration. Not production authentication."})


@bp.get("/me")
@require_auth()
def me():
    return jsonify({"user": g.user})
