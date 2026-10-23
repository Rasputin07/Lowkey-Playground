from flask import Blueprint, g, jsonify

from errors import bad_request
from routes.helpers import json_body
from security import authorize_student, require_auth
from services import genai

bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@bp.post("")
@require_auth("student", "mentor")
def chat():
    b = json_body()
    msgs = b.get("messages")
    if not isinstance(msgs, list) or not 1 <= len(msgs) <= 20:
        raise bad_request("messages must be a list of 1-20 items.")
    clean = []
    for m in msgs:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant") or not isinstance(m.get("content"), str) \
                or not 1 <= len(m["content"].strip()) <= 2000:
            raise bad_request("Each message needs role (user/assistant) and content of 1-2000 characters.")
        clean.append({"role": m["role"], "content": m["content"].strip()})
    if clean[0]["role"] != "user" or clean[-1]["role"] != "user":
        raise bad_request("Conversation must start and end with a user message.")
    # The server decides whose data the model sees.
    sid = g.user["student_id"] if g.user["role"] == "student" else b.get("student_id")
    authorize_student(sid)
    return jsonify(genai.chat(g.user, sid, clean))
