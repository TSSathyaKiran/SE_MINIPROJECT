"""Enrollment and drop (Srujan): issue #17. Details in docs/TEAM_GUIDE.md.

  POST   /enroll              student  {sectionId}  409 full / prerequisite unmet / duplicate
  DELETE /enroll/<id>         student  own enrollment; 403 after the add/drop deadline
  GET    /ui/student/courses  student page: open sections, my enrollments, enroll/drop buttons
"""
from flask import Blueprint, jsonify

from ..core.audit import audit
from ..core.errors import ApiError, as_int, get_json, required
from ..core.security import current_user, require_role
from ..extensions import db
from ..models import Enrollment, Section

bp = Blueprint("enrollment", __name__)


def seats_taken(section_id):
    """Only 'enrolled' rows hold a seat, so a dropped student frees theirs."""
    return Enrollment.query.filter_by(section_id=section_id, status="enrolled").count()


@bp.post("/enroll")
@require_role("student")
def enroll():
    data = required(get_json(), "sectionId")
    section_id = as_int(data["sectionId"], "sectionId")
    student = current_user().student
    if student is None:
        raise ApiError(403, "forbidden", "This account has no student record")

    # Lock the section row so two students cannot take the last seat at the same time.
    section = Section.query.filter_by(id=section_id).with_for_update().first()
    if section is None:
        raise ApiError(404, "section_not_found", "That section does not exist")

    if Enrollment.query.filter_by(student_id=student.id, section_id=section.id,
                                  status="enrolled").first():
        raise ApiError(409, "duplicate", "You are already enrolled in this section")
    # (issue #4, Sathya: the overdue-fee check goes here)
    if seats_taken(section.id) >= section.capacity:
        raise ApiError(409, "section_full", "This section is full")
    # (next commit: prerequisite check goes here)

    # A student who dropped this section and comes back reuses the old row,
    # so anything linked to it (such as attendance) stays attached.
    enrollment = Enrollment.query.filter_by(student_id=student.id, section_id=section.id,
                                            status="dropped").first()
    if enrollment:
        enrollment.status = "enrolled"
    else:
        enrollment = Enrollment(student_id=student.id, section_id=section.id,
                                status="enrolled")
        db.session.add(enrollment)
        db.session.flush()              # gives enrollment.id before commit
    audit("enroll", "enrollment", enrollment.id)
    db.session.commit()                 # the seat check and the insert are one transaction
    return jsonify(enrollmentId=enrollment.id, status="enrolled"), 201