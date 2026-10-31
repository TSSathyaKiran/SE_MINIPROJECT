from app.extensions import db
from app.models import (AuditLog, AuthSession, Course, Enrollment, Grade, Section,
                        Student, Term)


def body(**over):
    data = {"name": "Asha Rao", "email": "asha@test.edu", "program": "B.Tech CSE",
            "semester": 3, "password": "pass1234"}
    data.update(over)
    return data


def make_history(student):
    """Give a student an enrollment and a grade so we can check history is kept."""
    term = Term(name="2026-ODD")
    course = Course(code="CS101", name="Intro", credits=4)
    db.session.add_all([term, course])
    db.session.flush()
    section = Section(course_id=course.id, term_id=term.id, name="A", capacity=30)
    db.session.add(section)
    db.session.flush()
    db.session.add_all([Enrollment(student_id=student.id, section_id=section.id),
                        Grade(student_id=student.id, section_id=section.id,
                              grade="A", grade_point=9)])
    db.session.commit()


# ---- TC-Stu-01: create (#11) ----

def test_tc_stu_01_admin_creates_student_and_login(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/students", json=body(), headers=admin)
    assert res.status_code == 201
    assert res.json["status"] == "created"
    student = db.session.get(Student, res.json["id"])
    assert student.status == "active"
    assert student.user.role == "student"
    login = client.post("/auth/login", json={"username": res.json["studentNo"].lower(),
                                             "password": "pass1234"})
    assert login.status_code == 200


def test_tc_stu_01_missing_field_returns_400(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/students", json=body(email=" "), headers=admin)
    assert res.status_code == 400
    assert res.json["error"]["code"] == "missing_field"
    assert Student.query.count() == 0


def test_tc_stu_01_semester_out_of_range_returns_400(client, login_as):
    _, admin = login_as("admin")
    for bad in (0, 9):
        assert client.post("/students", json=body(semester=bad), headers=admin).status_code == 400


def test_tc_stu_01_duplicate_student_no_returns_409(client, login_as):
    _, admin = login_as("admin")
    client.post("/students", json=body(studentNo="S2001"), headers=admin)
    res = client.post("/students", json=body(studentNo="S2001", email="b@test.edu"), headers=admin)
    assert res.status_code == 409
    assert Student.query.count() == 1
    assert "b@test.edu" not in res.json["error"]["message"]


def test_tc_stu_01_generates_next_student_no(client, login_as):
    _, admin = login_as("admin")
    first = client.post("/students", json=body(), headers=admin).json["studentNo"]
    second = client.post("/students", json=body(email="c@test.edu"), headers=admin).json["studentNo"]
    assert int(second[1:]) == int(first[1:]) + 1


def test_tc_stu_01_only_admin_can_create(client, login_as):
    _, student = login_as("student")
    assert client.post("/students", json=body(), headers=student).status_code == 403
    assert client.post("/students", json=body()).status_code == 401


def test_tc_stu_01_create_is_audited(client, login_as):
    admin_user, admin = login_as("admin")
    res = client.post("/students", json=body(), headers=admin)
    log = AuditLog.query.filter_by(record_type="student").one()
    assert (log.user_id, log.action, log.record_id) == (admin_user.id, "create", str(res.json["id"]))


def test_admin_students_page_loads(client, login_as):
    _, admin = login_as("admin")
    assert client.get("/ui/admin/students", headers=admin).status_code == 200


# ---- GET /students/<id> (#12) ----

def test_get_student_by_admin_faculty_and_owner(client, login_as):
    _, admin = login_as("admin")
    _, faculty = login_as("faculty")
    user, owner = login_as("student")
    sid = user.student.id
    for headers in (admin, faculty, owner):
        res = client.get(f"/students/{sid}", headers=headers)
        assert res.status_code == 200
        assert res.json["id"] == sid


def test_get_student_other_student_returns_403(client, login_as):
    _, mine = login_as("student")
    other, _ = login_as("student")
    assert client.get(f"/students/{other.student.id}", headers=mine).status_code == 403


def test_get_student_unknown_returns_404(client, login_as):
    _, admin = login_as("admin")
    assert client.get("/students/9999", headers=admin).status_code == 404


# ---- TC-Stu-02: update and deactivate (#12) ----

def test_tc_stu_02_admin_updates_student(client, login_as):
    admin_user, admin = login_as("admin")
    user, _ = login_as("student")
    sid = user.student.id
    res = client.put(f"/students/{sid}",
                     json={"name": "New Name", "semester": 5, "phone": "9999999999"},
                     headers=admin)
    assert res.status_code == 200
    student = db.session.get(Student, sid)
    assert (student.name, student.semester, student.phone) == ("New Name", 5, "9999999999")
    log = AuditLog.query.filter_by(action="update", record_type="student").one()
    assert (log.user_id, log.record_id) == (admin_user.id, str(sid))


def test_tc_stu_02_update_rejects_bad_input(client, login_as):
    _, admin = login_as("admin")
    user, _ = login_as("student")
    url = f"/students/{user.student.id}"
    assert client.put(url, json={}, headers=admin).status_code == 400
    assert client.put(url, json={"studentNo": "S1"}, headers=admin).status_code == 400
    assert client.put(url, json={"semester": 12}, headers=admin).status_code == 400
    assert client.put(url, json={"status": "gone"}, headers=admin).status_code == 400
    assert client.put("/students/9999", json={"name": "X"}, headers=admin).status_code == 404


def test_tc_stu_02_deactivate_blocks_login_and_keeps_history(client, login_as):
    admin_user, admin = login_as("admin")
    user, student_headers = login_as("student")
    student = user.student
    sid, username = student.id, user.username
    make_history(student)

    res = client.put(f"/students/{sid}", json={"status": "inactive"}, headers=admin)
    assert res.status_code == 200
    assert res.json["status"] == "inactive"

    # cannot log in and old session no longer works
    login = client.post("/auth/login", json={"username": username, "password": "pass1234"})
    assert login.status_code != 200
    assert "token" not in (login.json or {})
    assert AuthSession.query.filter_by(user_id=user.id).count() == 0
    assert client.get(f"/students/{sid}", headers=student_headers).status_code == 401

    # history is kept
    assert db.session.get(Student, sid).status == "inactive"
    assert Enrollment.query.filter_by(student_id=sid).count() == 1
    assert Grade.query.filter_by(student_id=sid).count() == 1
    assert client.get(f"/students/{sid}", headers=admin).status_code == 200

    log = AuditLog.query.filter_by(action="deactivate").one()
    assert (log.user_id, log.record_type, log.record_id) == (admin_user.id, "student", str(sid))


def test_tc_stu_02_only_admin_can_update(client, login_as):
    _, faculty = login_as("faculty")
    user, _ = login_as("student")
    url = f"/students/{user.student.id}"
    assert client.put(url, json={"name": "X"}, headers=faculty).status_code == 403
    assert client.put(url, json={"name": "X"}).status_code == 401