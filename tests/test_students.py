
from app.extensions import db
from app.models import AuditLog, Student, User


def body(**over):
    data = {
        "name": "Asha Rao",
        "email": "asha@test.edu",
        "program": "B.Tech CSE",
        "semester": 3,
        "password": "pass1234",
    }
    data.update(over)
    return data


def test_tc_stu_01_admin_creates_student_and_login(client, login_as):
    _, admin = login_as("admin")

    res = client.post("/students", json=body(), headers=admin)

    assert res.status_code == 201
    assert res.json["status"] == "created"

    student = db.session.get(Student, res.json["id"])
    assert student is not None
    assert student.status == "active"
    assert student.user.role == "student"

    login = client.post(
        "/auth/login",
        json={
            "username": res.json["studentNo"].lower(),
            "password": "pass1234",
        },
    )
    assert login.status_code == 200


def test_tc_stu_01_missing_field_returns_400(client, login_as):
    _, admin = login_as("admin")

    res = client.post(
        "/students",
        json=body(email=" "),
        headers=admin,
    )

    assert res.status_code == 400
    assert res.json["error"]["code"] == "missing_field"
    assert Student.query.count() == 0


def test_tc_stu_01_semester_out_of_range_returns_400(client, login_as):
    _, admin = login_as("admin")

    for bad in (0, 9):
        res = client.post(
            "/students",
            json=body(semester=bad),
            headers=admin,
        )
        assert res.status_code == 400

    assert Student.query.count() == 0


def test_tc_stu_01_duplicate_student_no_returns_409(client, login_as):
    _, admin = login_as("admin")

    first = client.post(
        "/students",
        json=body(studentNo="S2001"),
        headers=admin,
    )
    assert first.status_code == 201

    second = client.post(
        "/students",
        json=body(studentNo="S2001", email="b@test.edu"),
        headers=admin,
    )

    assert second.status_code == 409
    assert Student.query.count() == 1


def test_tc_stu_01_generates_next_student_no(client, login_as):
    _, admin = login_as("admin")

    first = client.post(
        "/students",
        json=body(),
        headers=admin,
    )
    assert first.status_code == 201

    second = client.post(
        "/students",
        json=body(email="c@test.edu"),
        headers=admin,
    )
    assert second.status_code == 201

    first_no = first.json["studentNo"]
    second_no = second.json["studentNo"]

    assert second_no.startswith("S")
    assert int(second_no[1:]) == int(first_no[1:]) + 1


def test_tc_stu_01_only_admin_can_create(client, login_as):
    _, student = login_as("student")

    count_before = Student.query.count()

    forbidden = client.post(
        "/students",
        json=body(),
        headers=student,
    )
    unauthorized = client.post("/students", json=body())

    assert forbidden.status_code == 403
    assert unauthorized.status_code == 401
    assert Student.query.count() == count_before


def test_tc_stu_01_create_is_audited(client, login_as):
    admin_user, admin = login_as("admin")

    res = client.post(
        "/students",
        json=body(),
        headers=admin,
    )

    assert res.status_code == 201

    log = AuditLog.query.filter_by(
        record_type="student",
        action="create",
        record_id=str(res.json["id"]),
    ).one()

    assert log.user_id == admin_user.id
