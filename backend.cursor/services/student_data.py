"""Builds student views from db.py + risk/cgpa services. Routes and GenAI both use this, so numbers never diverge."""
import db
from errors import not_found
from services import risk as risk_svc, cgpa as cgpa_svc


def _student(student_id):
    s = db.get_student(student_id)
    if not s:
        raise not_found("Student not found.")
    return s


def get_risk(student_id):
    _student(student_id)
    return risk_svc.compute_risk(db.get_weekly(student_id), db.get_subjects(student_id))


def get_cgpa_plan(student_id, target=None):
    s = _student(student_id)
    credits = sum(x["credits"] for x in db.get_subjects(student_id))
    return cgpa_svc.required_sgpa(s["current_cgpa"], s["credits_completed"], credits,
                                  s["target_cgpa"] if target is None else target)


def get_timeline(student_id):
    _student(student_id)
    weekly, subjects = db.get_weekly(student_id), db.get_subjects(student_id)
    trend = []
    for k in range(risk_svc.MIN_WEEKS, len(weekly) + 1):
        r = risk_svc.compute_risk(weekly[:k], subjects)
        trend.append({"week": weekly[k - 1]["week"], "risk_score": r["score"], "risk_level": r["level"]})
    return {"student_id": student_id, "weekly": weekly, "risk_by_week": trend,
            "note": "Risk by week uses current subject-level data for all weeks (prototype simplification)."}


def get_profile(student_id):
    s = _student(student_id)
    weekly = db.get_weekly(student_id)
    return {**s, "subjects": db.get_subjects(student_id), "assignments": db.get_assignments(student_id),
            "latest_week": weekly[-1] if weekly else None, "risk_summary": _brief(get_risk(student_id))}


def _brief(r):
    return {"score": r["score"], "level": r["level"]}


def get_facts(student_id):
    """Minimal, de-identified facts for the LLM (no name, no id)."""
    s = _student(student_id)
    weekly = db.get_weekly(student_id)
    return {"semester": s["semester"], "department": s["department"],
            "current_cgpa": s["current_cgpa"], "target_cgpa": s["target_cgpa"],
            "subjects": db.get_subjects(student_id),
            "upcoming_or_missed_assignments": [a for a in db.get_assignments(student_id) if a["status"] != "submitted"],
            "last_4_weeks": weekly[-4:],
            "risk": {k: v for k, v in get_risk(student_id).items() if k in ("score", "level", "indicators")},
            "cgpa_plan": get_cgpa_plan(student_id)}
