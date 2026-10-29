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
from flask import Blueprint, jsonify, render_template

from ..core.audit import audit
from ..core.errors import ApiError, as_int, get_json, required
from ..core.security import require_login, require_role
from ..extensions import db
from ..models import Course, Term

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


def _course_dict(course):
    return {"id": course.id, "code": course.code, "name": course.name,
            "credits": course.credits}


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

    course = Course(code=code, name=name, credits=credits)
    db.session.add(course)
    db.session.flush()                  # gives course.id before commit
    audit("create", "course", course.id)
    db.session.commit()
    return jsonify(courseId=course.id, status="created"), 201


@bp.get("/courses")
@require_login
def list_courses():
    courses = Course.query.order_by(Course.code).all()
    return jsonify(courses=[_course_dict(c) for c in courses])