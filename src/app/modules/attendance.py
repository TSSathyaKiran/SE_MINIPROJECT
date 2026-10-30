"""Attendance (Tanuj): issues #7 and #8. Details in docs/TEAM_GUIDE.md.

  POST /attendance                         assigned faculty  {sectionId, date, records:[{studentId,status}]}  #7
  GET  /attendance/<studentId>/summary     own student, faculty, admin  ?sectionId=                         #8
  GET  /ui/faculty/attendance              faculty page: pick section + date, mark P/A/L                    #7
  GET  /ui/student/attendance              student page: % per course                                       #8
"""
from datetime import date

from flask import Blueprint, jsonify

from ..core.audit import audit
from ..core.errors import ApiError, get_json, required
from ..core.security import current_user, require_role
from ..extensions import db
from ..models import Attendance, Enrollment, Section

bp = Blueprint("attendance", __name__)

STATUSES = ("present", "absent", "late")



@bp.post("/attendance")
@require_role("faculty")
def mark_attendance():
    data = required(get_json(), "sectionId", "date", "records")
    section = db.session.get(Section, data["sectionId"])
    if section is None:
        raise ApiError(404, "not_found", "Unknown section")
    if section.faculty_id != current_user().id:
        raise ApiError(403, "forbidden", "Not your section")

    try:
        day = date.fromisoformat(str(data["date"]))
    except ValueError:
        raise ApiError(400, "invalid_field", "date must look like 2026-10-30")
    records = data["records"]
    if not isinstance(records, list) or not records:
        raise ApiError(400, "invalid_field", "records must be a non-empty list")

    saved = 0
    for record in records:
        if not isinstance(record, dict):
            raise ApiError(400, "invalid_field",
                           "each record needs a studentId and a status")
        status = str(record.get("status", ""))
        if status not in STATUSES:
            raise ApiError(400, "invalid_field",
                           "status must be present, absent or late")
        enrollment = Enrollment.query.filter_by(
            section_id=section.id, student_id=record.get("studentId"),
            status="enrolled").first()
        row = Attendance.query.filter_by(enrollment_id=enrollment.id, date=day).first() \
            or Attendance(enrollment_id=enrollment.id, date=day)
        row.status = status
        db.session.add(row)
        db.session.flush()                    # gives row.id before commit
        audit("mark", "attendance", row.id)
        saved += 1
    db.session.commit()
    return jsonify(status="saved", count=saved)
