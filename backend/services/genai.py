"""
GenAI layer (Claude API). Rules enforced here:
  * API key stays on the backend; only minimal de-identified facts are sent.
  * Numbers come from our own calculations (tools / facts), never invented by the model.
  * The model never chooses which student to read: the server fixes the student per request.
  * If the API is unavailable the app falls back to a clearly labelled template answer.
"""
import json
import logging
import re

import config
import db
from services import student_data, intervention_service

log = logging.getLogger("lowkey.genai")
DISCLAIMER = "AI-generated suggestion. Numbers marked 'calculated' come from your records; please verify with your institution."

BASE_RULES = (
    "You are Lowkey Copilot, a supportive academic assistant inside a student-success app. "
    "Use ONLY data from the provided facts or tool results. Never invent grades, attendance rules, CGPA values, or "
    "deadlines; if something is missing, say it is not available. Never guarantee an outcome or a CGPA. "
    "Describe risk as 'worth a check-in', never as 'you will fail'. Be warm, concise and practical. "
    "Mark numbers from tools as calculated from records, and your advice as suggestions."
)


def _client():
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=config.GENAI_TIMEOUT_S)
    except Exception:  # package missing or bad config
        log.warning("Anthropic client unavailable; using offline mode")
        return None


# ------------------------------------------------------------------ study plan
def _template_plan(facts, hours):
    subs = sorted(facts["subjects"], key=lambda s: (s["quiz_avg"] or 0))
    focus = subs[:2] or facts["subjects"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    plan = []
    for i, d in enumerate(days):
        s = focus[i % len(focus)] if i < 4 else subs[-1]
        task = ["Review lecture notes and fix gaps", "Solve 10 practice questions"] if i < 4 else ["Revision + short self-quiz"]
        plan.append({"day": d, "focus": s["subject"], "tasks": task})
    return {"summary": f"Focus first on {', '.join(s['subject'] for s in focus)}, where quiz averages are lowest. "
                       f"Aim for about {hours} study hours this week.",
            "weekly_plan": plan, "notes": "Template plan generated without AI."}


def generate_study_plan(student_id, hours=10, focus_subject=None, target=None):
    facts = student_data.get_facts(student_id)
    if target is not None:
        facts["cgpa_plan"] = student_data.get_cgpa_plan(student_id, target)
    calculated = facts["cgpa_plan"]
    client = _client()
    plan, source, warning = None, "template", None
    if client:
        prompt = (
            "Create a one-week study plan from these facts. Respond with ONLY JSON: "
            '{"summary": str, "weekly_plan": [{"day": str, "focus": str, "tasks": [str]}], "notes": str}. '
            f"Study hours available per week: {hours}. "
            + (f"Student wants extra focus on: {focus_subject}. " if focus_subject else "")
            + "Explain the required SGPA from cgpa_plan without changing its numbers.\nFACTS:\n" + json.dumps(facts))
        try:
            resp = client.messages.create(model=config.GENAI_MODEL, max_tokens=config.GENAI_MAX_TOKENS,
                                          system=BASE_RULES, messages=[{"role": "user", "content": prompt}])
            text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
            parsed = json.loads(text)
            if isinstance(parsed.get("weekly_plan"), list) and isinstance(parsed.get("summary"), str):
                parsed.setdefault("notes", "")
                plan, source = parsed, "ai"
        except Exception as e:  # API error, timeout, bad JSON
            log.warning("Study plan GenAI failed: %s", type(e).__name__)
            warning = "AI service unavailable or returned an unusable answer; showing a template plan instead."
    if plan is None:
        plan = _template_plan(facts, hours)
        warning = warning or "AI is not configured; showing a template plan."
    return {"student_id": student_id, "source": source, "calculated": calculated, "plan": plan,
            "warning": warning, "disclaimer": DISCLAIMER}


# ------------------------------------------------------------------ chat
TOOLS = [
    {"name": "get_student_summary", "description": "Current CGPA, subject-wise attendance/quiz/internal marks, pending or missed assignments and the last 4 weeks of activity for the current student.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "get_risk_explanation", "description": "Rule-based academic indicators with evidence for why the student may need support.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "calculate_target_cgpa", "description": "Calculate the SGPA needed this semester to reach a target CGPA. Defaults to the student's saved target.",
     "input_schema": {"type": "object", "properties": {"target_cgpa": {"type": "number", "minimum": 0, "maximum": 10}}}},
    {"name": "get_weekly_timeline", "description": "Weekly attendance, assignment, LMS and quiz trends.",
     "input_schema": {"type": "object", "properties": {}}},
]
PROPOSE_TOOL = {
    "name": "propose_intervention",
    "description": "MENTOR ONLY. Create a DRAFT intervention (status 'proposed') that the mentor must still review and assign.",
    "input_schema": {"type": "object", "required": ["type"], "properties": {
        "type": {"type": "string", "enum": list(intervention_service.TYPES)},
        "notes": {"type": "string", "maxLength": 500}}},
}


def _run_tool(name, args, student_id, user):
    """Execute a tool. student_id is fixed by the server; the model can never pick another student."""
    args = args or {}
    if name == "get_student_summary":
        return student_data.get_facts(student_id)
    if name == "get_risk_explanation":
        return student_data.get_risk(student_id)
    if name == "get_weekly_timeline":
        return student_data.get_timeline(student_id)
    if name == "calculate_target_cgpa":
        t = args.get("target_cgpa")
        if t is not None and not (isinstance(t, (int, float)) and 0 <= t <= 10):
            return {"error": "target_cgpa must be between 0 and 10"}
        return student_data.get_cgpa_plan(student_id, t)
    if name == "propose_intervention" and user["role"] == "mentor":
        t = args.get("type")
        if t not in intervention_service.TYPES:
            return {"error": "invalid intervention type"}
        r = student_data.get_risk(student_id)
        iv = db.create_intervention(student_id, t, "proposed", user["id"], None,
                                    str(args.get("notes", ""))[:500], r["score"], r["level"])
        return {"created": True, "intervention_id": iv["id"], "status": "proposed",
                "note": "Draft only. The mentor must review and assign it."}
    return {"error": f"unknown or unavailable tool: {name}"}


def _offline_chat(student_id, last_msg):
    m = last_msg.lower()
    if any(w in m for w in ("cgpa", "target", "grade")):
        text = student_data.get_cgpa_plan(student_id)["message"]
    elif any(w in m for w in ("plan", "study", "schedule")):
        text = generate_study_plan(student_id)["plan"]["summary"]
    else:
        text = student_data.get_risk(student_id)["explanation"]
    return text + " (Offline demo mode: AI is not connected.)"


def chat(user, student_id, messages):
    last = messages[-1]["content"]
    client = _client()
    if not client:
        return {"reply": _offline_chat(student_id, last), "mode": "offline-demo", "tools_used": [], "disclaimer": DISCLAIMER}

    tools = TOOLS + ([PROPOSE_TOOL] if user["role"] == "mentor" else [])
    system = BASE_RULES + (" The user is a mentor reviewing one assigned student; you may draft interventions but never claim they are approved."
                           if user["role"] == "mentor" else " The user is the student; speak to them directly.")
    convo, used = [dict(m) for m in messages], []
    try:
        for _ in range(5):
            resp = client.messages.create(model=config.GENAI_MODEL, max_tokens=config.GENAI_MAX_TOKENS,
                                          system=system, tools=tools, messages=convo)
            if resp.stop_reason != "tool_use":
                text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
                return {"reply": text or "Sorry, I could not produce an answer.", "mode": "ai",
                        "tools_used": used, "disclaimer": DISCLAIMER}
            convo.append({"role": "assistant", "content": resp.content})
            results = []
            for b in resp.content:
                if getattr(b, "type", "") == "tool_use":
                    used.append(b.name)
                    out = _run_tool(b.name, b.input, student_id, user)
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out, default=str)})
            convo.append({"role": "user", "content": results})
        return {"reply": "I needed too many steps for that. Could you ask a narrower question?", "mode": "ai",
                "tools_used": used, "disclaimer": DISCLAIMER}
    except Exception as e:
        log.warning("Chat GenAI failed: %s", type(e).__name__)
        return {"reply": _offline_chat(student_id, last), "mode": "offline-fallback", "tools_used": used,
                "warning": "AI service is unavailable right now.", "disclaimer": DISCLAIMER}
