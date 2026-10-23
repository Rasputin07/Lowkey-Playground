from flask import Blueprint, g, jsonify

import db
from errors import bad_request, forbidden, not_found
from routes.helpers import json_body, opt_date, opt_text
from security import authorize_student, require_auth, valid_student_id, visible_student_ids
from services import intervention_service as svc, student_data
from datetime import date

bp = Blueprint("interventions", __name__, url_prefix="/api/interventions")


def _load_authorized(iid):
    iv = db.get_intervention(iid)
    if not iv:
        raise not_found("Intervention not found.")
    if g.user["role"] == "mentor":
        authorize_student(iv["student_id"])
    return iv


@bp.get("")
@require_auth("mentor", "admin")
def list_interventions():
    from flask import request
    sid, status = request.args.get("student_id"), request.args.get("status")
    if status and status not in svc.STATUSES:
        raise bad_request(f"status must be one of {list(svc.STATUSES)}")
    ids = visible_student_ids()
    if sid:
        valid_student_id(sid)
        if sid not in ids:
            raise forbidden()
        ids = [sid]
    cache, notes = {}, g.user["role"] == "mentor"  # admin sees aggregate-level info, no mentor notes
    return jsonify({"interventions": [svc.enrich(i, notes, cache) for i in db.list_interventions(ids, status)]})


@bp.post("")
@require_auth("mentor")
def create():
    b = json_body()
    sid = valid_student_id(b.get("student_id"))
    authorize_student(sid)
    if b.get("type") not in svc.TYPES:
        raise bad_request(f"type must be one of {list(svc.TYPES)}")
    status = b.get("status", "assigned")
    if status not in ("proposed", "assigned"):
        raise bad_request("A new intervention can only start as 'proposed' or 'assigned'.")
    r = student_data.get_risk(sid)
    iv = db.create_intervention(sid, b["type"], status, g.user["id"],
                                opt_date(b.get("follow_up_date"), "follow_up_date", not_past=True),
                                opt_text(b.get("notes"), "notes"), r["score"], r["level"])
    return jsonify(svc.enrich(iv)), 201


@bp.patch("/<int:iid>")
@require_auth("mentor")
def update(iid):
    iv = _load_authorized(iid)
    b = json_body()
    fields = {}
    if "status" in b:
        svc.check_transition(iv["status"], b["status"])
        fields["status"] = b["status"]
        if b["status"] == "completed":
            fields["completed_on"] = date.today().isoformat()
    if "follow_up_date" in b:
        fields["follow_up_date"] = opt_date(b["follow_up_date"], "follow_up_date", not_past=True)
    if "notes" in b:
        fields["notes"] = opt_text(b["notes"], "notes")
    if not fields:
        raise bad_request("Nothing to update. Send status, follow_up_date and/or notes.")
    return jsonify(svc.enrich(db.update_intervention(iid, **fields)))
