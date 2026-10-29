"""Terms, courses, sections and prerequisites (SRS-F-020).

Terms are finished and are the WORKED EXAMPLE for everyone: an admin-only create
API with validation, a duplicate check, audit, a list API, a page, and tests in
tests/test_courses.py. Copy this pattern for your own module.

Still to build (Srujan, issue #16):
  POST /courses            admin  {code, name, credits, prerequisites?: "CS101,CS102"}  409 duplicate code
  GET  /courses            any    {courses: [...]}
  POST /courses/sections   admin  {courseId, termId, name, facultyId, capacity}         409 duplicate section
  GET  /courses/sections   any    ?termId=  {sections: [...]}
  GET  /ui/admin/courses   admin  page: course + section forms and lists
"""
from flask import Blueprint, jsonify, render_template, request

from ..core.audit import audit
from ..core.errors import ApiError, as_int, get_json, required
from ..core.security import require_login, require_role
from ..extensions import db
from ..models import Course, Enrollment, Prerequisite, Section, Term, User

bp = Blueprint("courses", __name__)


@bp.post("/terms")
@require_role("admin")
def create_term():
    data = required(get_json(), "name")
    name = data["name"].strip()
    if Term.query.filter_by(name=name).first():
        raise ApiError(409, "duplicate_term", f"Term {name} already exists")

    term = Term(name=name)
    db.session.add(term)
    db.session.flush()                  # gives term.id before commit
    audit("create", "term", term.id)
    db.session.commit()
    return jsonify(termId=term.id, status="created"), 201


@bp.get("/terms")
@require_login
def list_terms():
    terms = Term.query.order_by(Term.name).all()
    return jsonify(terms=[{"id": t.id, "name": t.name} for t in terms])


@bp.get("/ui/admin/terms")
@require_role("admin")
def terms_page():
    return render_template("courses/terms.html", terms=Term.query.order_by(Term.name).all())


def _parse_prereq_codes(raw):
    """'cs101, CS102' (or a list) -> ['CS101', 'CS102'], blanks and repeats removed."""
    if raw in (None, ""):
        return []
    items = raw if isinstance(raw, list) else str(raw).split(",")
    codes = []
    for item in items:
        code = str(item).strip().upper()
        if code and code not in codes:
            codes.append(code)
    return codes


def _prereq_codes(course_id):
    rows = (db.session.query(Course.code)
            .join(Prerequisite, Prerequisite.requires_course_id == Course.id)
            .filter(Prerequisite.course_id == course_id)
            .order_by(Course.code).all())
    return [code for (code,) in rows]


def _course_dict(course):
    return {"id": course.id, "code": course.code, "name": course.name,
            "credits": course.credits, "prerequisites": _prereq_codes(course.id)}


@bp.post("/courses")
@require_role("admin")
def create_course():
    data = required(get_json(), "code", "name", "credits")
    code = str(data["code"]).strip().upper()
    name = str(data["name"]).strip()
    credits = as_int(data["credits"], "credits")
    if len(code) > 20 or len(name) > 120:
        raise ApiError(400, "invalid_field", "Course code or name is too long")
    if not 1 <= credits <= 5:
        raise ApiError(400, "invalid_field", "credits must be between 1 and 5")
    if Course.query.filter_by(code=code).first():
        raise ApiError(409, "duplicate_course", f"Course {code} already exists")

    # Prerequisites must already exist, which also means they can never form a loop.
    prereqs = []
    for prereq_code in _parse_prereq_codes(data.get("prerequisites")):
        prereq = Course.query.filter_by(code=prereq_code).first()
        if prereq is None:
            raise ApiError(400, "unknown_prerequisite",
                           f"Unknown prerequisite course: {prereq_code}")
        prereqs.append(prereq)

    course = Course(code=code, name=name, credits=credits)
    db.session.add(course)
    db.session.flush()                  # gives course.id before commit
    for prereq in prereqs:
        db.session.add(Prerequisite(course_id=course.id, requires_course_id=prereq.id))
    audit("create", "course", course.id)
    db.session.commit()
    return jsonify(courseId=course.id, status="created"), 201


@bp.get("/courses")
@require_login
def list_courses():
    courses = Course.query.order_by(Course.code).all()
    return jsonify(courses=[_course_dict(c) for c in courses])


def _seats_taken(section_id):
    return Enrollment.query.filter_by(section_id=section_id, status="enrolled").count()


def _section_dict(section):
    return {"id": section.id,
            "courseId": section.course_id,
            "courseCode": section.course.code,
            "courseName": section.course.name,
            "termId": section.term_id,
            "term": section.term.name,
            "name": section.name,
            "facultyId": section.faculty_id,
            "faculty": section.faculty.name if section.faculty else None,
            "capacity": section.capacity,
            "seatsTaken": _seats_taken(section.id)}


@bp.post("/courses/sections")
@require_role("admin")
def create_section():
    data = required(get_json(), "courseId", "termId", "name", "facultyId", "capacity")
    course_id = as_int(data["courseId"], "courseId")
    term_id = as_int(data["termId"], "termId")
    faculty_id = as_int(data["facultyId"], "facultyId")
    capacity = as_int(data["capacity"], "capacity")
    name = str(data["name"]).strip().upper()
    if len(name) > 10:
        raise ApiError(400, "invalid_field", "Section name is too long")
    if capacity < 1:
        raise ApiError(400, "invalid_field", "capacity must be at least 1")

    if db.session.get(Course, course_id) is None:
        raise ApiError(400, "unknown_course", "That course does not exist")
    if db.session.get(Term, term_id) is None:
        raise ApiError(400, "unknown_term", "That term does not exist")
    faculty = db.session.get(User, faculty_id)
    if faculty is None or faculty.role != "faculty":
        raise ApiError(400, "invalid_faculty", "facultyId must be a faculty user")
    if Section.query.filter_by(course_id=course_id, term_id=term_id, name=name).first():
        raise ApiError(409, "duplicate_section",
                       f"Section {name} already exists for this course and term")

    section = Section(course_id=course_id, term_id=term_id, name=name,
                      faculty_id=faculty_id, capacity=capacity)
    db.session.add(section)
    db.session.flush()                  # gives section.id before commit
    audit("create", "section", section.id)
    db.session.commit()
    return jsonify(sectionId=section.id, status="created"), 201


@bp.get("/courses/sections")
@require_login
def list_sections():
    query = Section.query.join(Course)
    term_id = request.args.get("termId")
    if term_id not in (None, ""):
        query = query.filter(Section.term_id == as_int(term_id, "termId"))
    sections = query.order_by(Course.code, Section.name).all()
    return jsonify(sections=[_section_dict(s) for s in sections])

@bp.get("/ui/admin/courses")
@require_role("admin")
def courses_page():
    courses = Course.query.order_by(Course.code).all()
    terms = Term.query.order_by(Term.name).all()
    faculty = User.query.filter_by(role="faculty", status="active").order_by(User.name).all()
    sections = Section.query.join(Course).order_by(Course.code, Section.name).all()
    return render_template("courses/admin.html",
                           courses=[_course_dict(c) for c in courses],
                           terms=terms, faculty=faculty,
                           sections=[_section_dict(s) for s in sections])