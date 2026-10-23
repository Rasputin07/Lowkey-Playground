# Lowkey backend (Flask)

## Requirements
Python 3.10+. Optional: an Anthropic API key (without one, the app runs in clearly labelled **offline-demo** mode).

## Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env          # then paste ANTHROPIC_API_KEY into .env
python app.py                    # http://127.0.0.1:5000  (DB is created + seeded on first start)
python test_smoke.py             # 32 end-to-end checks
```
Reset demo data: stop the server, delete `backend/lowkey.db`, start again.

## Auth (MOCK, prototype only)
`GET /api/auth/demo-users` lists users. `POST /api/auth/mock-login {"user_id":"M01"}` returns a token.
Send `Authorization: Bearer <token>` on every other call. Roles are enforced on the backend:
student = own record; mentor = assigned students; admin = aggregates + interventions (no notes, no individual profiles).
Demo users: `U_S001`..`U_S006` (students), `M01` (mentor of S001-S005), `M02`, `A01`.

## Endpoints
| Method | Path | Roles |
|---|---|---|
| GET | /api/health | any |
| GET | /api/dashboard | all (shape depends on role) |
| GET | /api/students | student, mentor |
| GET | /api/students/{id} | student(own), mentor |
| GET | /api/students/{id}/risk | student(own), mentor |
| GET | /api/students/{id}/timeline | student(own), mentor |
| POST | /api/students/{id}/study-plan `{hours_per_week?, focus_subject?, target_cgpa?}` | student(own), mentor |
| GET | /api/interventions?student_id=&status= | mentor, admin |
| POST | /api/interventions `{student_id, type, follow_up_date?, notes?, status?}` | mentor |
| PATCH | /api/interventions/{id} `{status?, follow_up_date?, notes?}` | mentor |
| POST | /api/chat `{messages:[{role,content}], student_id?}` | student, mentor (mentor must send student_id) |

Errors always look like `{"error": {"code": "...", "message": "..."}}` (400, 401, 403, 404, 502/503, 500).
Intervention types: mentor_meeting, remedial_class, study_plan_review, counseling_referral.
Status flow: proposed -> assigned -> completed (or cancelled). `outcome` is computed from recorded risk indicators
(baseline at creation vs current) and always carries a "not proof of causation" caveat.

## Frontend: chat call
```js
const res = await fetch("http://127.0.0.1:5000/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  body: JSON.stringify({ messages: history /* [{role:"user",content:"..."}] */, student_id /* mentors only */ }),
});
const { reply, mode, disclaimer } = await res.json(); // mode: ai | offline-demo | offline-fallback
```
Show the `mode` and `disclaimer` in the UI. Keep the full `messages` history on the client and resend it each time.

## Plugging in Member 2's database
Everything touches the DB only through `db.py`. Replace function bodies there (keep names and return shapes) and
delete `seed.py` once the real dataset is loaded.

## Common problems
- **CORS error in browser**: add your frontend origin to `CORS_ORIGINS` in `.env`.
- **401**: token missing/expired (sessions reset when the server restarts); log in again.
- **mode = offline-demo**: `ANTHROPIC_API_KEY` is empty or `.env` is not in `backend/`.
- **ModuleNotFoundError**: run commands from inside `backend/` with the venv active.
