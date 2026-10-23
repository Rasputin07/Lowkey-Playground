from flask import Blueprint, g, jsonify

import db
from security import authorize_student, require_auth, visible_student_ids
from services import student_data

bp = Blueprint("students", __name__, url_prefix="/api/students")


@bp.get("")
@require_auth("student", "mentor")
def list_students():
    out = []
    for s in db.list_students(mentor_id=g.user["id"]) if g.user["role"] == "mentor" else db.list_students(student_id=g.user["student_id"]):
        r, weekly = student_data.get_risk(s["id"]), db.get_weekly(s["id"])
        out.append({"id": s["id"], "name": s["name"], "department": s["department"], "semester": s["semester"],
                    "current_cgpa": s["current_cgpa"], "target_cgpa": s["target_cgpa"],
                    "latest_attendance": weekly[-1]["attendance_pct"] if weekly else None,
                    "risk_score": r["score"], "risk_level": r["level"]})
    return jsonify({"students": out})


@bp.get("/<student_id>")
@require_auth("student", "mentor")
def get_student(student_id):
    authorize_student(student_id)
    return jsonify(student_data.get_profile(student_id))


@bp.get("/<student_id>/risk")
@require_auth("student", "mentor")
def get_risk(student_id):
    authorize_student(student_id)
    return jsonify({"student_id": student_id, **student_data.get_risk(student_id)})


@bp.get("/<student_id>/timeline")
@require_auth("student", "mentor")
def get_timeline(student_id):
    authorize_student(student_id)
    return jsonify(student_data.get_timeline(student_id))
