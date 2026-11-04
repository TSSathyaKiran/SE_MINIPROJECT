"""Attendance (Tanuj): issues #7 and #8. Details in docs/TEAM_GUIDE.md.

  POST /attendance                         assigned faculty  {sectionId, date, records:[{studentId,status}]}  #7
  GET  /attendance/<studentId>/summary     own student, faculty, admin  ?sectionId=                         #8
  GET  /ui/faculty/attendance              faculty page: pick section + date, mark P/A/L                    #7
  GET  /ui/student/attendance              student page: % per course                                       #8
"""
from datetime import date

from flask import Blueprint, jsonify, render_template, request

from ..core import clock
from ..core.audit import audit
from ..core.errors import ApiError, as_int, get_json, required
from ..core.security import current_user, require_login, require_role
from ..extensions import db
from ..models import Attendance, Course, Enrollment, Section, Student

bp = Blueprint("attendance", __name__)

STATUSES = ("present", "absent", "late")


def attendance_summary(enrollment):
    """Present/absent/late counts and percentage for one enrollment.

    percentage = round(present / total * 100, 1), and 0 when there are no
    sessions yet. Late never counts as present (docs/DEVIATIONS.md).
    """
    counts = {status: 0 for status in STATUSES}
    for row in Attendance.query.filter_by(enrollment_id=enrollment.id):
        if row.status in counts:
            counts[row.status] += 1
    total = sum(counts.values())
    percentage = round(counts["present"] / total * 100, 1) if total else 0
    return {"present": counts["present"], "absent": counts["absent"],
            "late": counts["late"], "total": total, "percentage": percentage}


def _current_enrollments(student, section=None):
    """The student's enrolled enrollments, optionally limited to one section."""
    query = Enrollment.query.filter_by(student_id=student.id, status="enrolled")
    if section is not None:
        query = query.filter_by(section_id=section.id)
    return (query.join(Enrollment.section).join(Section.course)
            .order_by(Course.code, Section.name).all())


@bp.get("/attendance/<int:student_id>/summary")
@require_login
def attendance_summary_api(student_id):
    """Summary for one section (?sectionId=) or every current enrollment.

    Only the student themself, the section's faculty, or an admin may read it.
    """
    student = db.session.get(Student, student_id)
    if student is None:
        raise ApiError(404, "not_found", "Unknown student")
    section = None
    if "sectionId" in request.args:
        section = db.session.get(Section, as_int(request.args["sectionId"], "sectionId"))
        if section is None:
            raise ApiError(404, "not_found", "Unknown section")

    user = current_user()
    enrollments = _current_enrollments(student, section)
    if user.role == "faculty":
        if section is not None:
            allowed = section.faculty_id == user.id
        else:
            # a faculty only ever sees their own sections, never the whole student
            allowed = any(e.section.faculty_id == user.id for e in enrollments)
            enrollments = [e for e in enrollments if e.section.faculty_id == user.id]
    else:
        allowed = user.role == "admin" or student.user_id == user.id
    if not allowed:
        raise ApiError(403, "forbidden", "You are not allowed to see this summary")

    return jsonify(
        studentId=student.id,
        sections=[{"sectionId": e.section_id,
                   "courseCode": e.section.course.code,
                   "courseName": e.section.course.name,
                   "section": e.section.name,
                   **attendance_summary(e)} for e in enrollments])


@bp.get("/ui/student/attendance")
@require_role("student")
def student_attendance_page():
    """My attendance percentage, one table per course."""
    student = current_user().student
    enrollments = _current_enrollments(student) if student else []
    rows = [{"enrollment": e, "summary": attendance_summary(e)} for e in enrollments]
    return render_template("attendance/student.html", rows=rows)


@bp.get("/ui/faculty/attendance")
@require_role("faculty")
def attendance_page():
    """Pick one of my sections and a date, then mark that day's roster."""
    sections = (Section.query.filter_by(faculty_id=current_user().id)
                .join(Section.course)
                .order_by(Course.code, Section.name)
                .all())

    section = None
    if "sectionId" in request.args:
        section = db.session.get(Section, as_int(request.args["sectionId"], "sectionId"))
        if section is None:
            raise ApiError(404, "not_found", "Unknown section")
        if section.faculty_id != current_user().id:
            raise ApiError(403, "forbidden", "Not your section")
    elif sections:
        section = sections[0]

    day_text = request.args.get("date") or clock.today().isoformat()
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        raise ApiError(400, "invalid_field", "date must look like 2026-10-30")

    roster = []
    if section is not None:
        enrollments = (Enrollment.query.filter_by(section_id=section.id, status="enrolled")
                       .join(Enrollment.student)
                       .order_by(Student.name)
                       .all())
        marked = {row.enrollment.student_id: row.status
                  for row in Attendance.query.filter(
                      Attendance.enrollment_id.in_([e.id for e in enrollments]),
                      Attendance.date == day)}
        roster = [{"student": e.student, "status": marked.get(e.student_id)}
                  for e in enrollments]

    return render_template("attendance/mark.html", sections=sections, section=section,
                           day=day.isoformat(), roster=roster)


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
        if enrollment is None:
            raise ApiError(400, "not_enrolled",
                           "Student is not enrolled in this section")
        row = Attendance.query.filter_by(enrollment_id=enrollment.id, date=day).first() \
            or Attendance(enrollment_id=enrollment.id, date=day)
        row.status = status
        db.session.add(row)
        db.session.flush()                    # gives row.id before commit
        audit("mark", "attendance", row.id)
        saved += 1
    db.session.commit()
    return jsonify(status="saved", count=saved)
