"""Intervention rules: allowed status transitions + outcome computed from recorded data only."""
from errors import bad_request
from services import student_data

TYPES = ("mentor_meeting", "remedial_class", "study_plan_review", "counseling_referral")
STATUSES = ("proposed", "assigned", "completed", "cancelled")
TRANSITIONS = {"proposed": {"assigned", "cancelled"}, "assigned": {"completed", "cancelled"},
               "completed": set(), "cancelled": set()}
CAVEAT = "Change in indicators after an intervention is an association, not proof the intervention caused it."


def check_transition(old, new):
    if new not in STATUSES:
        raise bad_request(f"status must be one of {list(STATUSES)}")
    if new != old and new not in TRANSITIONS[old]:
        raise bad_request(f"Cannot change status from '{old}' to '{new}'.")


def enrich(iv, include_notes=True, _cache=None):
    """Attach a data-backed outcome. Only completed interventions with a baseline get one."""
    out = dict(iv)
    if not include_notes:
        out.pop("notes", None)
    out["outcome"] = None
    if iv["status"] == "completed" and iv.get("baseline_risk_score") is not None:
        cache = _cache if _cache is not None else {}
        sid = iv["student_id"]
        if sid not in cache:
            cache[sid] = student_data.get_risk(sid)
        cur = cache[sid]["score"]
        if cur is not None:
            delta = iv["baseline_risk_score"] - cur
            label = "indicators_improved" if delta >= 10 else "indicators_worsened" if delta <= -10 else "no_clear_change"
            out["outcome"] = {"label": label, "baseline_score": iv["baseline_risk_score"],
                              "current_score": cur, "change": -delta, "caveat": CAVEAT}
    return out
