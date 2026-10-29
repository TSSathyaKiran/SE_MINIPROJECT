"""Academic settings the admin can change (SRS-F-070). Never hard-code these."""
import json
from datetime import date

from ..extensions import db
from ..models import Setting

DEFAULTS = {
    "add_drop_deadline": "2026-12-31",
    "grade_lock_date": "2026-12-31",
    "fee_threshold": 5000,
    # [minimum %, letter, grade point], highest first (10-point scale)
    "grading_scale": [[90, "O", 10], [80, "A+", 9], [70, "A", 8], [60, "B+", 7],
                      [55, "B", 6], [50, "C", 5], [40, "P", 4], [0, "F", 0]],
}


def get_setting(key):
    row = db.session.get(Setting, key)
    return json.loads(row.value) if row else DEFAULTS[key]


def get_date(key):
    return date.fromisoformat(get_setting(key))


def set_setting(key, value):
    """Save a setting. Caller validates the value and commits."""
    if key not in DEFAULTS:
        raise KeyError(key)
    row = db.session.get(Setting, key) or Setting(key=key)
    row.value = json.dumps(value)
    db.session.add(row)
