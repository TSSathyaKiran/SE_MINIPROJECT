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
from ..core.errors import ApiError, get_json, required
from ..core.security import require_login, require_role
from ..extensions import db
from ..models import Term

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
