"""Transparent, rule-based academic indicators. A flag means 'worth a supportive check-in', never 'will fail'."""

MIN_WEEKS = 6
DISCLAIMER = ("Indicators are estimates based on the data available. They suggest where a supportive "
              "check-in may help; they do not predict outcomes and must not be used for punitive decisions.")


def _avg(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _level(score):
    return "low" if score < 20 else "medium" if score < 45 else "high"


def compute_risk(weekly, subjects):
    if len(weekly) < MIN_WEEKS:
        return {"score": None, "level": "insufficient_data", "indicators": [],
                "explanation": f"At least {MIN_WEEKS} weeks of data are needed.", "disclaimer": DISCLAIMER}

    att = [w["attendance_pct"] for w in weekly]
    quiz = [w["quiz_score"] for w in weekly]
    lms = [w["lms_logins"] for w in weekly]
    last4 = weekly[-4:]
    missed = sum(w["assignments_total"] - w["assignments_submitted"] for w in last4)
    total4 = sum(w["assignments_total"] for w in last4)
    ind = []

    def add(key, label, points, evidence, explanation):
        ind.append({"key": key, "label": label, "points": points, "evidence": evidence, "explanation": explanation})

    drop = att[-4] - att[-1]
    att_flag = drop >= 10
    if att_flag:
        add("attendance_decline", "Attendance declining", 25, {"three_weeks_ago": att[-4], "latest": att[-1]},
            f"Attendance moved from {att[-4]:.0f}% to {att[-1]:.0f}% over the last three weeks.")
    if att[-1] < 75:
        add("low_attendance", "Attendance below 75%", 15, {"latest": att[-1]},
            f"Latest weekly attendance is {att[-1]:.0f}%. Check your institution's attendance rule.")
    if missed >= 3:
        add("missed_assignments", "Missed assignments", 25, {"missed": missed, "of": total4, "weeks": 4},
            f"{missed} of the last {total4} assignments were not submitted.")
    recent_q, prev_q = _avg(quiz[-3:]), _avg(quiz[-6:-3])
    if prev_q - recent_q >= 8:
        add("quiz_decline", "Quiz scores declining", 20, {"previous_avg": round(prev_q, 1), "recent_avg": round(recent_q, 1)},
            f"Average quiz score fell from {prev_q:.0f} to {recent_q:.0f} compared with the previous three weeks.")
    recent_l, prev_l = _avg(lms[-3:]), _avg(lms[-6:-3])
    lms_flag = prev_l > 0 and (prev_l - recent_l) / prev_l >= 0.4
    if lms_flag:
        add("lms_drop", "LMS engagement dropping", 15, {"previous_avg_logins": round(prev_l, 1), "recent_avg_logins": round(recent_l, 1)},
            f"Weekly LMS logins averaged {recent_l:.1f}, down from {prev_l:.1f}.")
    if att[-1] >= 75 and not att_flag and missed >= 3 and lms_flag:
        add("silent_disengagement", "Possible silent disengagement", 10, {"latest_attendance": att[-1]},
            "Attendance looks fine, but assignments and LMS activity have dropped. A check-in may help.")
    weak = [s["subject"] for s in subjects
            if (s["quiz_avg"] is not None and s["quiz_avg"] < 50) or (s["attendance_pct"] is not None and s["attendance_pct"] < 65)]
    if weak:
        add("weak_subjects", "Subjects needing attention", min(20, 10 * len(weak)), {"subjects": weak},
            "Subjects with low quiz average or attendance: " + ", ".join(weak) + ".")

    score = min(100, sum(i["points"] for i in ind))
    level = _level(score)
    explanation = ("No concerning patterns found in the available data." if not ind else
                   "Observed: " + " ".join(i["explanation"] for i in ind) + " Consider a supportive conversation about workload and available help.")
    return {"score": score, "level": level, "indicators": ind, "explanation": explanation, "disclaimer": DISCLAIMER}
