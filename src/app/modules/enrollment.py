"""Enrollment and drop (Srujan): issue #17. Details in docs/TEAM_GUIDE.md.

  POST   /enroll              student  {sectionId}  409 full / prerequisite unmet / duplicate
  DELETE /enroll/<id>         student  own enrollment; 403 after the add/drop deadline
  GET    /ui/student/courses  student page: open sections, my enrollments, enroll/drop buttons
"""
from flask import Blueprint, jsonify, render_template

from ..core import clock
from ..core.audit import audit
from ..core.errors import ApiError, as_int, get_json, required
from ..core.security import current_user, require_role
from ..core.settings import get_date
from ..extensions import db
from ..models import Course, Enrollment, Grade, Prerequisite, Section, Term

bp = Blueprint("enrollment", __name__)


def seats_taken(section_id):
    """Only 'enrolled' rows hold a seat, so a dropped student frees theirs."""
    return Enrollment.query.filter_by(section_id=section_id, status="enrolled").count()


def unmet_prerequisites(student_id, course_id):
    """Codes of prerequisite courses the student has not passed yet.

    A course counts as passed when the student has a final Grade for any section of
    it with grade_point > 0 (an F is 0, so a failed course must be taken again).
    """
    missing = []
    links = Prerequisite.query.filter_by(course_id=course_id).all()
    for link in links:
        passed = (Grade.query.join(Section, Grade.section_id == Section.id)
                  .filter(Grade.student_id == student_id,
                          Section.course_id == link.requires_course_id,
                          Grade.grade_point > 0).first())
        if passed is None:
            missing.append(db.session.get(Course, link.requires_course_id).code)
    return sorted(missing)


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
    missing = unmet_prerequisites(student.id, section.course_id)
    if missing:
        raise ApiError(409, "prerequisite_unmet",
                       "Prerequisite not met: " + ", ".join(missing))

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


@bp.delete("/enroll/<int:enrollment_id>")
@require_role("student")
def drop(enrollment_id):
    enrollment = db.session.get(Enrollment, enrollment_id)
    if enrollment is None:
        raise ApiError(404, "enrollment_not_found", "That enrollment does not exist")
    student = current_user().student
    if student is None or enrollment.student_id != student.id:
        raise ApiError(403, "forbidden", "This is not your enrollment")
    if enrollment.status == "dropped":
        raise ApiError(409, "already_dropped", "You have already dropped this section")
    # The last day itself is still allowed; the deadline comes from admin settings.
    if clock.today() > get_date("add_drop_deadline"):
        raise ApiError(403, "drop_closed", "The add/drop deadline has passed")

    enrollment.status = "dropped"       # frees the seat; the row stays as history
    audit("drop", "enrollment", enrollment.id)
    db.session.commit()
    return jsonify(enrollmentId=enrollment.id, status="dropped")


def _prerequisite_codes(course_id):
    rows = (db.session.query(Course.code)
            .join(Prerequisite, Prerequisite.requires_course_id == Course.id)
            .filter(Prerequisite.course_id == course_id)
            .order_by(Course.code).all())
    return [code for (code,) in rows]


def _section_view(section):
    return {"id": section.id,
            "code": section.course.code,
            "name": section.course.name,
            "credits": section.course.credits,
            "section": section.name,
            "term": section.term.name,
            "faculty": section.faculty.name if section.faculty else "Not assigned",
            "capacity": section.capacity,
            "seats_taken": seats_taken(section.id),
            "prerequisites": _prerequisite_codes(section.course_id)}


@bp.get("/ui/student/courses")
@require_role("student")
def courses_page():
    student = current_user().student
    if student is None:
        raise ApiError(403, "forbidden", "This account has no student record")

    deadline = get_date("add_drop_deadline")
    mine = (Enrollment.query.filter_by(student_id=student.id, status="enrolled")
            .order_by(Enrollment.id).all())
    my_section_ids = {e.section_id for e in mine}
    my_enrollments = [{"id": e.id, **_section_view(e.section)} for e in mine]

    # "Latest term" = the term created most recently
    term = Term.query.order_by(Term.id.desc()).first()
    sections = []
    if term:
        rows = (Section.query.join(Course).filter(Section.term_id == term.id)
                .order_by(Course.code, Section.name).all())
        for section in rows:
            view = _section_view(section)
            view["enrolled"] = section.id in my_section_ids
            view["full"] = view["seats_taken"] >= view["capacity"]
            sections.append(view)

    return render_template("enrollment/courses.html", term=term, sections=sections,
                           my_enrollments=my_enrollments, deadline=deadline,
                           drop_open=clock.today() <= deadline)