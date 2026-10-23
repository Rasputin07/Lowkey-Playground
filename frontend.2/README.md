# LOWKEY 🎓
**Understand your progress. Shape your future.**

LOWKEY is an early academic-risk detection and student-support prototype with two role-based interfaces (Student, Mentor). Risk indicators are transparent rules that prompt human review. They are never predictions of failure.

## Run it
```bash
node server.js        # Node 18+, no npm install needed
# open http://localhost:3000
```
No Node? Open `index.html` directly, or use the bundled `lowkey-single.html`. The app then runs on an **offline demo store** (same API logic, data kept in your browser). The sidebar shows **Live API** or **Offline demo store**.

## Demo logins (fictional data)
| Role | Email (or short name) | Password |
|------|-----------------------|----------|
| Student | `student@lowkey.demo` (or `student`) | `student123` |
| Mentor | `mentor@lowkey.demo` (or `mentor`) | `mentor123` |

Select the matching role card first.

## Structure
```
index.html            app entry (login + role-based shell)
server.js             zero-dependency Node server: static files + /api/*
shared/core.js        risk rules, CGPA maths, mock AI, API router (used by server AND browser fallback)
data/seed.js          fictional students, users, seed intervention
css/style.css         light/dark theme, responsive layout
js/api.js             API client (server first, offline fallback)
js/charts.js          SVG charts: line, bar, comparison bars
js/app.js             session, login, navigation, loading/error states
js/student.js         student views and actions
js/dashboard.js       mentor overview, directory, profile, risk, assistant, fairness, timeline
js/interventions.js   record interventions, status, outcomes, AI drafts
js/main.js            settings, theme, start-up
```

## API (all under `/api`, Bearer token)
| Method & path | Who | Purpose |
|---|---|---|
| `POST /login`, `POST /logout`, `GET /me` | all | session |
| `GET /students`, `GET /students/:id` | mentor (assigned) / student (own) | records |
| `GET /summary` | mentor | totals, attendance, assignment completion, trends, distribution |
| `GET/POST /interventions`, `PATCH /interventions/:id` | mentor (GET filtered for students) | support tracking |
| `GET/POST /requests` | student POST, mentor GET | meeting requests |
| `POST /ai` | role-checked | mock AI text from verified numbers |
| `POST /reset` | mentor | restore demo data |

Role checks run in the router, not just the UI. Every view shows loading, empty, error and "AI temporarily unavailable" states, and forms validate input.

## Limitations
- Demo authentication (simple hashes, in-memory sessions) is **not production security**.
- All data is **fictional**. The fairness table and before/after comparisons are illustrative and do not prove causation or fairness.
- AI is **template-based (mock mode)**. No live model or API key is used.
- Risk rules are hand-written and unvalidated. Grade scale and prior-credit assumptions are placeholders.
- Charts are dependency-free SVG, not Chart.js.

## Publish
GitHub Pages: Settings → Pages → Deploy from `main` / root. It runs in offline-demo mode (no server). For the live API, host `server.js` on any Node host.

## Chatbot
A floating "Ask LOWKEY" assistant (students and mentors). `POST /api/chat {messages:[{role,content}], sid?}`; mentors must send `sid`.
- **Default (no key):** grounded answers computed from the student's record (indicators, attendance, deadlines, target-CGPA maths, plans). Works offline too.
- **Live AI:** `ANTHROPIC_API_KEY=your_key node server.js` (optional `GENAI_MODEL`). The server sends only the student's computed facts plus the conversation to Claude; the key never reaches the browser. If the call fails it falls back to the grounded answer (`mode: mock-fallback`).
- Student chats live only in the browser tab and are not visible to mentors. Self-harm wording gets a fixed supportive reply (Tele-MANAS 14416 in India) and is never sent to the AI.
