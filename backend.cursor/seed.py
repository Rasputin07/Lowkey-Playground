"""Fictional demo data. NOT real student records. Replace with Member 2's dataset if you have one."""
from datetime import date, timedelta

USERS = [
    ("U_S001", "Aarav Mehta", "student", "S001"), ("U_S002", "Diya Sharma", "student", "S002"),
    ("U_S003", "Kabir Singh", "student", "S003"), ("U_S004", "Meera Nair", "student", "S004"),
    ("U_S005", "Rohan Das", "student", "S005"), ("U_S006", "Sneha Iyer", "student", "S006"),
    ("M01", "Dr. Priya Rao (Mentor)", "mentor", None), ("M02", "Prof. Arjun Verma (Mentor)", "mentor", None),
    ("A01", "Dept. Admin", "admin", None),
]
# id, name, dept, sem, mentor, cgpa, target, credits_done
STUDENTS = [
    ("S001", "Aarav Mehta", "CSE", 4, "M01", 8.2, 8.5, 78),
    ("S002", "Diya Sharma", "CSE", 4, "M01", 6.4, 7.5, 74),
    ("S003", "Kabir Singh", "CSE", 4, "M01", 7.1, 8.0, 76),
    ("S004", "Meera Nair", "CSE", 4, "M01", 7.6, 8.0, 78),
    ("S005", "Rohan Das", "CSE", 4, "M01", 6.9, 7.5, 72),
    ("S006", "Sneha Iyer", "CSE", 4, "M02", 8.8, 9.0, 80),
]
SUBJECTS = ["Data Structures", "Mathematics", "DBMS", "Operating Systems"]
CREDITS = [4, 4, 3, 3]
# per subject: (attendance_pct, quiz_avg, internal_marks/50)
SUBJECT_DATA = {
    "S001": [(91, 80, 42), (90, 78, 40), (92, 82, 44), (89, 79, 41)],
    "S002": [(60, 52, 22), (58, 45, 18), (66, 55, 25), (64, 50, 21)],
    "S003": [(88, 55, 28), (87, 50, 24), (86, 60, 30), (88, 48, 22)],
    "S004": [(83, 74, 36), (80, 42, 17), (84, 70, 35), (82, 68, 34)],
    "S005": [(85, 76, 35), (84, 70, 32), (88, 78, 36), (86, 72, 33)],
    "S006": [(94, 90, 45), (93, 88, 44), (95, 91, 46), (94, 89, 45)],
}
# 8 weeks each: attendance %, assignments submitted (of 2/week), LMS logins, quiz score
WEEKLY = {
    "S001": ([90, 91, 89, 92, 90, 91, 90, 92], [2, 2, 2, 2, 2, 2, 2, 2], [9, 10, 8, 9, 10, 9, 9, 10], [78, 80, 79, 82, 81, 80, 83, 82]),
    "S002": ([85, 83, 80, 74, 70, 66, 63, 61], [2, 2, 2, 1, 1, 0, 1, 0], [8, 7, 6, 4, 3, 2, 2, 1], [70, 68, 66, 60, 58, 55, 52, 50]),
    "S003": ([88, 87, 89, 86, 88, 87, 86, 88], [2, 2, 2, 2, 1, 1, 0, 1], [10, 9, 9, 7, 5, 3, 2, 2], [74, 72, 70, 66, 60, 57, 54, 52]),
    "S004": ([82, 84, 81, 83, 80, 82, 81, 83], [2, 2, 2, 2, 2, 1, 2, 2], [7, 8, 7, 7, 6, 7, 7, 6], [72, 74, 70, 64, 58, 55, 52, 50]),
    "S005": ([70, 68, 66, 72, 78, 82, 85, 86], [1, 0, 1, 1, 2, 2, 2, 2], [3, 2, 3, 5, 7, 8, 9, 9], [45, 48, 50, 58, 63, 68, 72, 75]),
    "S006": ([93, 94, 92, 95, 94, 93, 95, 94], [2, 2, 2, 2, 2, 2, 2, 2], [11, 10, 12, 11, 10, 11, 12, 11], [85, 86, 88, 87, 89, 90, 88, 91]),
}


def load(c):
    d = date.today()
    c.executemany("INSERT INTO users VALUES (?,?,?,?)", USERS)
    c.executemany("INSERT INTO students VALUES (?,?,?,?,?,?,?,?)", STUDENTS)
    for sid, rows in SUBJECT_DATA.items():
        for name, cr, (att, quiz, internal) in zip(SUBJECTS, CREDITS, rows):
            c.execute("INSERT INTO subjects (student_id,subject,credits,attendance_pct,quiz_avg,internal_marks) "
                      "VALUES (?,?,?,?,?,?)", (sid, name, cr, att, quiz, internal))
    for sid, (att, sub, lms, quiz) in WEEKLY.items():
        for i in range(8):
            c.execute("INSERT INTO weekly_metrics VALUES (?,?,?,?,?,?,?)",
                      (sid, i + 1, att[i], sub[i], 2, lms[i], quiz[i]))
        for off, subj, title in [(3, "Mathematics", "Problem Set 5"), (7, "DBMS", "ER Diagram Task")]:
            c.execute("INSERT INTO assignments (student_id,subject,title,due_date,status) VALUES (?,?,?,?,?)",
                      (sid, subj, title, (d + timedelta(days=off)).isoformat(), "pending"))
    for sid, subj, title in [("S002", "Data Structures", "Linked List Lab"), ("S003", "Operating Systems", "Scheduling Report")]:
        c.execute("INSERT INTO assignments (student_id,subject,title,due_date,status) VALUES (?,?,?,?,?)",
                  (sid, subj, title, (d - timedelta(days=4)).isoformat(), "missed"))
    # Illustrative interventions (demo data): one finished loop, one open.
    c.execute("INSERT INTO interventions (student_id,type,status,created_by,created_on,follow_up_date,completed_on,notes,"
              "baseline_risk_score,baseline_risk_level) VALUES (?,?,?,?,?,?,?,?,?,?)",
              ("S005", "mentor_meeting", "completed", "M01", (d - timedelta(days=35)).isoformat(),
               (d - timedelta(days=21)).isoformat(), (d - timedelta(days=22)).isoformat(),
               "Discussed workload and set weekly check-ins. (Demo record)", 70, "high"))
    c.execute("INSERT INTO interventions (student_id,type,status,created_by,created_on,follow_up_date,notes,"
              "baseline_risk_score,baseline_risk_level) VALUES (?,?,?,?,?,?,?,?,?)",
              ("S004", "remedial_class", "assigned", "M01", (d - timedelta(days=6)).isoformat(),
               (d + timedelta(days=8)).isoformat(), "Mathematics remedial sessions. (Demo record)", 30, "medium"))
