"""
ALL database access lives in this file.

Member 2: if you already have your own DB functions, replace the bodies of the
functions below (keep the names + return shapes: dicts / lists of dicts) and
nothing else in the backend needs to change.
"""
import contextlib
import sqlite3
from datetime import date

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student','mentor','admin')),
    student_id TEXT
);
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, department TEXT, semester INTEGER,
    mentor_id TEXT, current_cgpa REAL NOT NULL, target_cgpa REAL NOT NULL,
    credits_completed INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL, subject TEXT NOT NULL,
    credits INTEGER NOT NULL, attendance_pct REAL, quiz_avg REAL, internal_marks REAL
);
CREATE TABLE IF NOT EXISTS weekly_metrics (
    student_id TEXT NOT NULL, week INTEGER NOT NULL, attendance_pct REAL,
    assignments_submitted INTEGER, assignments_total INTEGER, lms_logins INTEGER,
    quiz_score REAL, PRIMARY KEY (student_id, week)
);
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL, subject TEXT,
    title TEXT, due_date TEXT, status TEXT CHECK (status IN ('submitted','missed','pending'))
);
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL, type TEXT NOT NULL,
    status TEXT NOT NULL, created_by TEXT NOT NULL, created_on TEXT NOT NULL,
    follow_up_date TEXT, completed_on TEXT, notes TEXT,
    baseline_risk_score INTEGER, baseline_risk_level TEXT
);
"""


@contextlib.contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _rows(cur):
    return [dict(r) for r in cur.fetchall()]


def init_db():
    """Create tables and load fictional demo data if the DB is empty."""
    with connect() as c:
        c.executescript(SCHEMA)
        empty = c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        if empty:
            import seed
            seed.load(c)


# ---------- users ----------
def get_user(user_id):
    with connect() as c:
        r = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(r) if r else None


def list_users():
    with connect() as c:
        return _rows(c.execute("SELECT * FROM users ORDER BY role, id"))


# ---------- students ----------
def list_students(mentor_id=None, student_id=None):
    sql, args = "SELECT * FROM students", []
    if mentor_id:
        sql += " WHERE mentor_id=?"; args.append(mentor_id)
    elif student_id:
        sql += " WHERE id=?"; args.append(student_id)
    with connect() as c:
        return _rows(c.execute(sql + " ORDER BY id", args))


def get_student(student_id):
    with connect() as c:
        r = c.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
        return dict(r) if r else None


def get_subjects(student_id):
    with connect() as c:
        return _rows(c.execute("SELECT subject, credits, attendance_pct, quiz_avg, internal_marks "
                               "FROM subjects WHERE student_id=? ORDER BY id", (student_id,)))


def get_weekly(student_id):
    with connect() as c:
        return _rows(c.execute("SELECT * FROM weekly_metrics WHERE student_id=? ORDER BY week", (student_id,)))


def get_assignments(student_id):
    with connect() as c:
        return _rows(c.execute("SELECT subject, title, due_date, status FROM assignments "
                               "WHERE student_id=? ORDER BY due_date", (student_id,)))


# ---------- interventions ----------
def list_interventions(student_ids=None, status=None):
    sql, args, where = "SELECT * FROM interventions", [], []
    if student_ids is not None:
        if not student_ids:
            return []
        where.append(f"student_id IN ({','.join('?' * len(student_ids))})"); args += list(student_ids)
    if status:
        where.append("status=?"); args.append(status)
    if where:
        sql += " WHERE " + " AND ".join(where)
    with connect() as c:
        return _rows(c.execute(sql + " ORDER BY id DESC", args))


def get_intervention(iid):
    with connect() as c:
        r = c.execute("SELECT * FROM interventions WHERE id=?", (iid,)).fetchone()
        return dict(r) if r else None


def create_intervention(student_id, type_, status, created_by, follow_up_date, notes,
                        baseline_score, baseline_level):
    with connect() as c:
        cur = c.execute(
            "INSERT INTO interventions (student_id,type,status,created_by,created_on,follow_up_date,"
            "notes,baseline_risk_score,baseline_risk_level) VALUES (?,?,?,?,?,?,?,?,?)",
            (student_id, type_, status, created_by, date.today().isoformat(), follow_up_date,
             notes, baseline_score, baseline_level))
        iid = cur.lastrowid
    return get_intervention(iid)


def update_intervention(iid, **fields):
    allowed = {"status", "follow_up_date", "completed_on", "notes"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if fields:
        sets = ", ".join(f"{k}=?" for k in fields)
        with connect() as c:
            c.execute(f"UPDATE interventions SET {sets} WHERE id=?", (*fields.values(), iid))
    return get_intervention(iid)
