"""End-to-end smoke test. Run: python test_smoke.py   (uses a temp DB, no API key needed)"""
import os, tempfile, types, json
os.environ["LOWKEY_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ["ANTHROPIC_API_KEY"] = ""

import app as appmod
from services import genai

c = appmod.app.test_client()
ok = 0


def check(name, cond):
    global ok
    assert cond, "FAILED: " + name
    ok += 1
    print("PASS", name)


def login(uid):
    return {"Authorization": "Bearer " + c.post("/api/auth/mock-login", json={"user_id": uid}).get_json()["token"]}


stu, men, men2, adm = login("U_S002"), login("M01"), login("M02"), login("A01")

check("health", c.get("/api/health").get_json()["status"] == "ok")
check("401 without token", c.get("/api/students").status_code == 401)
check("student sees only self", len(c.get("/api/students", headers=stu).get_json()["students"]) == 1)
check("mentor sees 5", len(c.get("/api/students", headers=men).get_json()["students"]) == 5)
check("student blocked from peer (403)", c.get("/api/students/S003", headers=stu).status_code == 403)
check("other mentor blocked (403)", c.get("/api/students/S002", headers=men2).status_code == 403)
check("admin blocked from individual (403)", c.get("/api/students/S002", headers=adm).status_code == 403)
check("bad id 400", c.get("/api/students/xyz", headers=men).status_code == 400)
check("missing 404", c.get("/api/students/S999", headers=men).status_code == 404)

r = c.get("/api/students/S002/risk", headers=men).get_json()
check("S002 high risk", r["level"] == "high")
r3 = c.get("/api/students/S003/risk", headers=men).get_json()
check("S003 silent disengagement flagged", "silent_disengagement" in [i["key"] for i in r3["indicators"]])
check("S001 low risk", c.get("/api/students/S001/risk", headers=men).get_json()["level"] == "low")
check("timeline", len(c.get("/api/students/S002/timeline", headers=stu).get_json()["weekly"]) == 8)

p = c.post("/api/students/S002/study-plan", headers=stu, json={"hours_per_week": 8}).get_json()
check("study plan offline template", p["source"] == "template" and p["plan"]["weekly_plan"])
check("study plan validation", c.post("/api/students/S002/study-plan", headers=stu, json={"hours_per_week": 500}).status_code == 400)

ch = c.post("/api/chat", headers=stu, json={"messages": [{"role": "user", "content": "What CGPA do I need?"}]}).get_json()
check("chat offline", ch["mode"] == "offline-demo" and "SGPA" in ch["reply"])
check("chat bad body 400", c.post("/api/chat", headers=stu, json={"messages": []}).status_code == 400)
check("mentor chat needs student_id", c.post("/api/chat", headers=men, json={"messages": [{"role": "user", "content": "hi"}]}).status_code == 400)

# --- fake Claude client to exercise the tool-use loop (incl. server-fixed student) ---
class Blk:
    def __init__(s, **k): s.__dict__.update(k)
calls = []
class FakeMsgs:
    def create(self, **kw):
        calls.append(kw)
        if len(calls) == 1:
            return types.SimpleNamespace(stop_reason="tool_use", content=[Blk(type="tool_use", id="t1", name="get_risk_explanation", input={"student_id": "S001"})])
        return types.SimpleNamespace(stop_reason="end_turn", content=[Blk(type="text", text="Here is what I see.")])
genai._client = lambda: types.SimpleNamespace(messages=FakeMsgs())
ch = c.post("/api/chat", headers=stu, json={"messages": [{"role": "user", "content": "why flagged?"}]}).get_json()
tool_result = json.loads(calls[1]["messages"][-1]["content"][0]["content"])
check("tool loop works", ch["mode"] == "ai" and ch["tools_used"] == ["get_risk_explanation"])
check("model cannot switch student", tool_result["level"] == "high")  # S002's data, not S001's
check("propose tool hidden from students", all(t["name"] != "propose_intervention" for t in calls[0]["tools"]))

# --- interventions ---
check("student cannot list interventions", c.get("/api/interventions", headers=stu).status_code == 403)
iv = c.post("/api/interventions", headers=men, json={"student_id": "S002", "type": "mentor_meeting", "follow_up_date": "2099-01-01", "notes": "Check-in"})
check("create 201", iv.status_code == 201)
iid = iv.get_json()["id"]
check("other mentor cannot create", c.post("/api/interventions", headers=men2, json={"student_id": "S002", "type": "mentor_meeting"}).status_code == 403)
check("bad transition 400", c.patch(f"/api/interventions/{iid}", headers=men, json={"status": "proposed"}).status_code == 400)
done = c.patch(f"/api/interventions/{iid}", headers=men, json={"status": "completed"}).get_json()
check("completed + data-backed outcome", done["completed_on"] and done["outcome"]["label"] == "no_clear_change")
check("persisted", any(i["id"] == iid for i in c.get("/api/interventions", headers=men).get_json()["interventions"]))
seeded = [i for i in c.get("/api/interventions?student_id=S005", headers=men).get_json()["interventions"]][0]
check("seeded loop shows improvement", seeded["outcome"]["label"] == "indicators_improved")
adm_list = c.get("/api/interventions", headers=adm).get_json()["interventions"]
check("admin sees no notes", all("notes" not in i for i in adm_list))
check("dashboard mentor", c.get("/api/dashboard", headers=men).get_json()["needs_attention"][0]["id"] == "S002")
check("dashboard admin", c.get("/api/dashboard", headers=adm).get_json()["total_students"] == 6)

# --- GenAI failure falls back instead of crashing ---
class Boom:
    def create(self, **kw): raise RuntimeError("secret-key-abc leaked?")
genai._client = lambda: types.SimpleNamespace(messages=Boom())
ch = c.post("/api/chat", headers=stu, json={"messages": [{"role": "user", "content": "help"}]}).get_json()
check("API failure -> fallback, no leak", ch["mode"] == "offline-fallback" and "secret" not in json.dumps(ch))
print(f"\nAll {ok} checks passed")
