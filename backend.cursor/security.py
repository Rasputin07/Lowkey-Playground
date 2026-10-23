"""
MOCK LOGIN (prototype only). Not production authentication: tokens are random strings kept in memory
and there are no passwords. What IS real: every route checks role + ownership on the backend.
"""
import re
import secrets
from functools import wraps

from flask import g, request

import db
from errors import AppError, bad_request, forbidden, not_found

SESSIONS = {}  # token -> user_id  (cleared on restart)
STUDENT_ID_RE = re.compile(r"^S\d{3}$")


def create_session(user_id):
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = user_id
    return token


def require_auth(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            header = request.headers.get("Authorization", "")
            token = header[7:] if header.startswith("Bearer ") else ""
            user = db.get_user(SESSIONS[token]) if token in SESSIONS else None
            if not user:
                raise AppError(401, "unauthorized", "Please log in.")
            if roles and user["role"] not in roles:
                raise forbidden("Your role cannot perform this action.")
            g.user = user
            return fn(*a, **kw)
        return wrapper
    return deco


def valid_student_id(student_id):
    if not STUDENT_ID_RE.match(student_id or ""):
        raise bad_request("Invalid student id format (expected like S001).")
    return student_id


def authorize_student(student_id):
    """Backend-enforced access: student -> self, mentor -> assigned students, admin -> no individual records."""
    valid_student_id(student_id)
    student = db.get_student(student_id)
    if not student:
        raise not_found("Student not found.")
    u = g.user
    allowed = (u["role"] == "student" and u["student_id"] == student_id) or \
              (u["role"] == "mentor" and student["mentor_id"] == u["id"])
    if not allowed:
        raise forbidden("You do not have access to this student's records.")
    return student


def visible_student_ids():
    u = g.user
    if u["role"] == "student":
        return [u["student_id"]]
    if u["role"] == "mentor":
        return [s["id"] for s in db.list_students(mentor_id=u["id"])]
    return [s["id"] for s in db.list_students()]  # admin: used for aggregates only
