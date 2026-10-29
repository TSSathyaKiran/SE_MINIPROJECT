"""Students (Vaishnavi): issues #11, #12, #13. Details in docs/TEAM_GUIDE.md.

  POST /students              admin                    #11  create; 400 missing field, 409 duplicate
  GET  /students/<id>         admin, faculty, own      #12  403 other student, 404 not found
  PUT  /students/<id>         admin (all fields)       #12  status="inactive" deactivates
                              own student (phone, address only; anything else -> 400)
  GET  /students/search?q=    admin, faculty           #13  by student no or name; 400 empty q
  GET  /ui/admin/students     admin page               #11-13
  GET  /ui/student/profile    student page             #12
  GET  /ui/faculty/search     faculty page             #13
"""
from flask import Blueprint, jsonify

from ..core.audit import audit
from ..core.errors import ApiError, as_int, get_json, required
from ..core.security import require_role
from ..extensions import db
from ..models import Student

bp = Blueprint("students", __name__)


@bp.post("/students")
@require_role("admin")
def create_student():
    data = required(get_json(), "studentNo", "name", "email", "program", "semester", "password")
    semester = as_int(data["semester"], "semester")
    if not 1 <= semester <= 8:
        raise ApiError(400, "invalid_field", "semester must be between 1 and 8")

    student = Student(student_no=data["studentNo"].strip(), name=data["name"].strip(),
                      email=data["email"].strip(), program=data["program"].strip(),
                      semester=semester)
    db.session.add(student)
    db.session.flush()                  # gives student.id before commit
    audit("create", "student", student.id)
    db.session.commit()
    return jsonify(id=student.id, studentNo=student.student_no, status="created"), 201