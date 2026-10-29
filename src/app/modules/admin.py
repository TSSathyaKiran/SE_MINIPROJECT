"""Academic settings (Tanuj): issue #6. Details in docs/TEAM_GUIDE.md.

  GET /admin/config           admin   all settings (see core/settings.py)
  PUT /admin/config           admin   {gradingScale?, addDropDeadline?, gradeLockDate?, feeThreshold?}  400 invalid
  GET /ui/admin/config        admin page
"""
import math
from datetime import date

from flask import Blueprint, jsonify, render_template

from ..core.audit import audit
from ..core.errors import ApiError, get_json
from ..core.security import require_role
from ..core.settings import get_setting, set_setting
from ..extensions import db

bp = Blueprint("admin", __name__)

FIELDS = ["gradingScale", "addDropDeadline", "gradeLockDate", "feeThreshold"]


def _config_json():
    return jsonify(
        gradingScale=get_setting("grading_scale"),
        addDropDeadline=get_setting("add_drop_deadline"),
        gradeLockDate=get_setting("grade_lock_date"),
        feeThreshold=get_setting("fee_threshold"),
    )


@bp.get("/admin/config")
@require_role("admin")
def get_config():
    return _config_json()


def _as_number(raw, field):
    try:
        number = float(raw)
    except (TypeError, ValueError):
        raise ApiError(400, "invalid_field", f"{field} must be a number")
    if not math.isfinite(number):
        raise ApiError(400, "invalid_field", f"{field} must be a finite number")
    return int(number) if number == int(number) else number


def _valid_date(value, field):
    try:
        date.fromisoformat(str(value))
    except ValueError:
        raise ApiError(400, "invalid_field", f"{field} must be a date like 2026-12-31")
    return str(value)


def _valid_threshold(value):
    threshold = _as_number(value, "feeThreshold")
    if threshold < 0:
        raise ApiError(400, "invalid_field", "feeThreshold cannot be negative")
    return threshold


def _valid_grading_scale(value):
    """Accept [[90, "O", 10], ...] or text with one "90,O,10" per line."""
    rows = [line.split(",") for line in value.strip().splitlines() if line.strip()] \
        if isinstance(value, str) else value
    if not isinstance(rows, list) or not rows:
        raise ApiError(400, "invalid_field", "gradingScale needs at least one row")

    scale = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 3:
            raise ApiError(400, "invalid_field", "gradingScale rows must look like 90,O,10")
        minimum = _as_number(str(row[0]).strip(), "gradingScale minimum %")
        letter = str(row[1]).strip()
        point = _as_number(str(row[2]).strip(), "gradingScale grade point")
        if not letter:
            raise ApiError(400, "invalid_field", "gradingScale rows need a letter grade")
        scale.append([minimum, letter, point])

    minimums = [row[0] for row in scale]
    if minimums != sorted(minimums, reverse=True):
        raise ApiError(400, "invalid_field", "gradingScale must be highest first")
    if minimums[-1] != 0:
        raise ApiError(400, "invalid_field", "gradingScale must end at 0")
    return scale


@bp.put("/admin/config")
@require_role("admin")
def update_config():
    data = get_json()
    updates = {}
    if "gradingScale" in data:
        updates["grading_scale"] = _valid_grading_scale(data["gradingScale"])
    if "addDropDeadline" in data:
        updates["add_drop_deadline"] = _valid_date(data["addDropDeadline"], "addDropDeadline")
    if "gradeLockDate" in data:
        updates["grade_lock_date"] = _valid_date(data["gradeLockDate"], "gradeLockDate")
    if "feeThreshold" in data:
        updates["fee_threshold"] = _valid_threshold(data["feeThreshold"])
    if not updates:
        raise ApiError(400, "missing_field", "Send at least one of: " + ", ".join(FIELDS))

    for key, value in updates.items():
        set_setting(key, value)
        audit("update", "config", key)
    db.session.commit()
    return _config_json()

def _scale_text(scale):
    """The grading scale as textarea lines: one "90,O,10" per line."""
    return "\n".join(",".join(str(part) for part in row) for row in scale)


@bp.get("/ui/admin/config")
@require_role("admin")
def config_page():
    return render_template(
        "admin/config.html",
        grading_scale=_scale_text(get_setting("grading_scale")),
        add_drop_deadline=get_setting("add_drop_deadline"),
        grade_lock_date=get_setting("grade_lock_date"),
        fee_threshold=get_setting("fee_threshold"),
    )
