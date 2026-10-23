from collections import Counter

from flask import Blueprint, g, jsonify

import db
from security import require_auth
from services import intervention_service as svc, student_data

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("")
@require_auth()
def dashboard():
    u = g.user
    if u["role"] == "student":
        s = db.get_student(u["student_id"])
        r, w = student_data.get_risk(s["id"]), db.get_weekly(s["id"])
        return jsonify({"role": "student", "current_cgpa": s["current_cgpa"], "target_cgpa": s["target_cgpa"],
                        "latest_attendance": w[-1]["attendance_pct"] if w else None,
                        "risk_level": r["level"], "risk_score": r["score"]})
    students = db.list_students(mentor_id=u["id"]) if u["role"] == "mentor" else db.list_students()
    risks = {s["id"]: student_data.get_risk(s["id"]) for s in students}
    ivs = db.list_interventions([s["id"] for s in students])
    cache = {}
    outcomes = Counter(e["outcome"]["label"] for e in (svc.enrich(i, False, cache) for i in ivs) if e["outcome"])
    out = {"role": u["role"], "total_students": len(students),
           "risk_distribution": dict(Counter(r["level"] for r in risks.values())),
           "interventions": {"by_status": dict(Counter(i["status"] for i in ivs)), "completed_outcomes": dict(outcomes),
                             "note": "Outcomes are computed from recorded indicators; association only. Seeded records are demo data."},
           "data_notice": "Prototype uses fictional student data."}
    if u["role"] == "mentor":
        out["needs_attention"] = sorted(
            [{"id": s["id"], "name": s["name"], "risk_level": risks[s["id"]]["level"], "risk_score": risks[s["id"]]["score"]}
             for s in students if risks[s["id"]]["level"] in ("medium", "high")],
            key=lambda x: -(x["risk_score"] or 0))
    return jsonify(out)
