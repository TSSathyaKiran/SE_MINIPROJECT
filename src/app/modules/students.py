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
from flask import Blueprint, jsonify, render_template

from ..core.audit import audit
from ..core.errors import ApiError, as_int, get_json, required
from ..core.security import current_user, hash_password, require_login, require_role
from ..extensions import db
from ..models import AuthSession, Student, User

bp = Blueprint("students", __name__)

ADMIN_FIELDS = ("name", "email", "phone", "address", "program", "semester", "status")


def next_student_no():
    numbers = [int(s.student_no[1:]) for s in Student.query.all() if s.student_no[1:].isdigit()]
    return f"S{max(numbers, default=1000) + 1}"


def student_json(s):
    return {"id": s.id, "studentNo": s.student_no, "name": s.name, "email": s.email,
            "phone": s.phone, "address": s.address, "program": s.program,
            "semester": s.semester, "status": s.status}


@bp.post("/students")
@require_role("admin")
def create_student():
    data = required(get_json(), "name", "email", "program", "semester", "password")
    semester = as_int(data["semester"], "semester")
    if not 1 <= semester <= 8:
        raise ApiError(400, "invalid_field", "semester must be between 1 and 8")

    student_no = str(data.get("studentNo", "")).strip()
    if student_no:
        if Student.query.filter_by(student_no=student_no).first():
            raise ApiError(409, "duplicate_student", f"Student {student_no} already exists")
    else:
        student_no = next_student_no()

    username = student_no.lower()
    if User.query.filter_by(username=username).first():
        raise ApiError(409, "duplicate_student", f"Login {username} already exists")
    user = User(username=username, password_hash=hash_password(data["password"]),
                name=data["name"].strip(), role="student")
    db.session.add(user)
    db.session.flush()

    student = Student(student_no=student_no, user_id=user.id, name=data["name"].strip(),
                      email=data["email"].strip(), program=data["program"].strip(),
                      semester=semester)
    db.session.add(student)
    db.session.flush()                  # gives student.id before commit
    audit("create", "student", student.id)
    db.session.commit()
    return jsonify(id=student.id, studentNo=student.student_no, status="created"), 201


@bp.get("/students/<int:student_id>")
@require_login
def get_student(student_id):
    user = current_user()
    if user.role == "student":
        own = Student.query.filter_by(user_id=user.id).first()
        if own is None or own.id != student_id:
            raise ApiError(403, "forbidden", "You can only view your own record")
    student = db.session.get(Student, student_id)
    if student is None:
        raise ApiError(404, "not_found", "Student not found")
    return jsonify(student_json(student))


@bp.put("/students/<int:student_id>")
@require_role("admin")
def update_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        raise ApiError(404, "not_found", "Student not found")

    data = get_json()
    unknown = [k for k in data if k not in ADMIN_FIELDS]
    if not data or unknown:
        raise ApiError(400, "invalid_field",
                       "Send one or more of: " + ", ".join(ADMIN_FIELDS))

    updates = {}
    for field in ("name", "email", "program"):
        if field in data:
            updates[field] = required(data, field)[field].strip()
    for field in ("phone", "address"):
        if field in data:
            updates[field] = str(data[field]).strip()
    if "semester" in data:
        semester = as_int(data["semester"], "semester")
        if not 1 <= semester <= 8:
            raise ApiError(400, "invalid_field", "semester must be between 1 and 8")
        updates["semester"] = semester
    if "status" in data:
        if data["status"] not in ("active", "inactive"):
            raise ApiError(400, "invalid_field", "status must be active or inactive")
        updates["status"] = data["status"]

    deactivating = updates.get("status") == "inactive" and student.status != "inactive"
    for field, value in updates.items():
        setattr(student, field, value)

    if "status" in updates and student.user is not None:
        student.user.status = updates["status"]
        if deactivating:
            AuthSession.query.filter_by(user_id=student.user.id).delete()

    audit("deactivate" if deactivating else "update", "student", student.id)
    db.session.commit()
    return jsonify(student_json(student))


@bp.get("/ui/admin/students")
@require_role("admin")
def students_page():
    return render_template("students/admin.html",
                           students=Student.query.order_by(Student.student_no).all())