import re
from datetime import date

from flask import request

from errors import bad_request


def json_body(required=True):
    data = request.get_json(silent=True)
    if data is None:
        if required:
            raise bad_request("Request body must be valid JSON.")
        return {}
    if not isinstance(data, dict):
        raise bad_request("Request body must be a JSON object.")
    return data


def opt_date(value, field, not_past=False):
    if value in (None, ""):
        return None
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise bad_request(f"{field} must be YYYY-MM-DD.")
    try:
        d = date.fromisoformat(value)
    except ValueError:
        raise bad_request(f"{field} is not a valid date.")
    if not_past and d < date.today():
        raise bad_request(f"{field} cannot be in the past.")
    return value


def opt_text(value, field, max_len=1000):
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > max_len:
        raise bad_request(f"{field} must be text up to {max_len} characters.")
    return value.strip()
