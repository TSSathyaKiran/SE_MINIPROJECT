
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
from ..core.security import hash_password, require_role
from ..extensions import db
from ..models import Student, User

bp = Blueprint("students", __name__)


def next_student_no():
    numbers = [
        int(s.student_no[1:])
        for s in Student.query.all()
        if s.student_no and s.student_no[1:].isdigit()
    ]
    return f"S{max(numbers, default=1000) + 1}"


@bp.post("/students")
@require_role("admin")
def create_student():
    data = required(
        get_json(),
        "name",
        "email",
        "program",
        "semester",
        "password",
    )

    name = data["name"].strip()
    email = data["email"].strip()
    program = data["program"].strip()

    semester = as_int(data["semester"], "semester")
    if not 1 <= semester <= 8:
        raise ApiError(
            400,
            "invalid_field",
            "semester must be between 1 and 8",
        )

    student_no = str(data.get("studentNo", "")).strip()

    if student_no:
        if Student.query.filter_by(student_no=student_no).first():
            raise ApiError(
                409,
                "duplicate_student",
                f"Student {student_no} already exists",
            )
    else:
        student_no = next_student_no()

    username = student_no.lower()

    if User.query.filter_by(username=username).first():
        raise ApiError(
            409,
            "duplicate_student",
            "The login username already exists",
        )

    user = User(
        username=username,
        password_hash=hash_password(data["password"]),
        name=name,
        role="student",
    )

    db.session.add(user)
    db.session.flush()

    student = Student(
        student_no=student_no,
        name=name,
        email=email,
        program=program,
        semester=semester,
        user_id=user.id,
    )

    db.session.add(student)
    db.session.flush()

    audit("create", "student", student.id)
    db.session.commit()

    return jsonify(
        id=student.id,
        studentNo=student.student_no,
        status="created",
    ), 201
