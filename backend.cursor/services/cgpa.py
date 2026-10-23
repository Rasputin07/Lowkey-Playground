"""Deterministic target-CGPA maths on a 10-point scale. The LLM only explains these numbers, never produces them."""

SCALE_MAX = 10.0


def required_sgpa(current_cgpa, credits_done, credits_this_sem, target):
    if not (0 <= target <= SCALE_MAX):
        raise ValueError("target must be between 0 and 10")
    if credits_this_sem <= 0:
        raise ValueError("credits_this_sem must be positive")
    needed = (target * (credits_done + credits_this_sem) - current_cgpa * credits_done) / credits_this_sem
    needed = round(needed, 2)
    if needed > SCALE_MAX:
        status, msg = "not_reachable_this_semester", (
            f"Reaching {target} in one semester would need an SGPA of {needed}, above the {SCALE_MAX:.0f} maximum. "
            "It would need to be spread over more than one semester.")
    elif needed <= 0:
        status, msg = "already_on_track", f"Your current CGPA already covers a target of {target} for this calculation."
    else:
        status, msg = "reachable", (f"To reach a CGPA of {target}, you would need an SGPA of about {needed} this semester "
                                    "(based on the credit totals on record; actual grading rules may differ).")
    return {"current_cgpa": current_cgpa, "target_cgpa": target, "credits_completed": credits_done,
            "credits_this_semester": credits_this_sem, "required_sgpa": needed, "status": status,
            "message": msg, "source": "calculated"}
