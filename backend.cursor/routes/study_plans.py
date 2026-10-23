from flask import Blueprint, jsonify

from errors import bad_request
from routes.helpers import json_body, opt_text
from security import authorize_student, require_auth
from services import genai

bp = Blueprint("study_plans", __name__, url_prefix="/api/students")


@bp.post("/<student_id>/study-plan")
@require_auth("student", "mentor")
def study_plan(student_id):
    authorize_student(student_id)
    body = json_body(required=False)
    hours = body.get("hours_per_week", 10)
    if not isinstance(hours, int) or isinstance(hours, bool) or not 1 <= hours <= 60:
        raise bad_request("hours_per_week must be an integer between 1 and 60.")
    target = body.get("target_cgpa")
    if target is not None and (isinstance(target, bool) or not isinstance(target, (int, float)) or not 0 <= target <= 10):
        raise bad_request("target_cgpa must be a number between 0 and 10.")
    focus = opt_text(body.get("focus_subject"), "focus_subject", 60)
    return jsonify(genai.generate_study_plan(student_id, hours, focus, target))
