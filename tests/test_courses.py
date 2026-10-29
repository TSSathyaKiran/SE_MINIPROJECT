"""Terms are the worked example. Add your course/section tests (issue #16) below."""
from app.models import AuditLog, Term


def test_admin_creates_and_lists_terms(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    assert res.status_code == 201
    assert res.json == {"termId": 1, "status": "created"}

    _, student = login_as("student")
    res = client.get("/terms", headers=student)
    assert res.json["terms"] == [{"id": 1, "name": "2026-ODD"}]


def test_create_term_rejects_missing_name(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/terms", json={"name": "  "}, headers=admin)
    assert res.status_code == 400
    assert res.json["error"]["code"] == "missing_field"


def test_create_term_rejects_duplicate(client, login_as):
    _, admin = login_as("admin")
    client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    res = client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    assert res.status_code == 409
    assert Term.query.count() == 1


def test_create_term_is_audited(client, login_as):
    admin_user, admin = login_as("admin")
    client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    log = AuditLog.query.one()
    assert (log.user_id, log.action, log.record_type, log.record_id) == \
        (admin_user.id, "create", "term", "1")
def test_tc_enr_01_course_created_and_listed(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/courses", headers=admin,
                      json={"code": "cs101", "name": "Intro to Programming", "credits": 4})
    assert res.status_code == 201
    listed = client.get("/courses", headers=admin).json["courses"]
    assert [c["code"] for c in listed] == ["CS101"]


def test_tc_enr_01_duplicate_course_code_rejected(client, login_as):
    _, admin = login_as("admin")
    body = {"code": "CS101", "name": "Intro", "credits": 4}
    assert client.post("/courses", json=body, headers=admin).status_code == 201
    assert client.post("/courses", json=body, headers=admin).status_code == 409


def test_tc_enr_01_course_validation_and_role(client, login_as):
    _, admin = login_as("admin")
    _, student = login_as("student")
    assert client.post("/courses", json={"code": "CS101", "name": "Intro"},
                       headers=admin).status_code == 400            # credits missing
    assert client.post("/courses", json={"code": "CS101", "name": "Intro", "credits": 9},
                       headers=admin).status_code == 400            # credits out of range
    assert client.post("/courses", json={"code": "CS101", "name": "Intro", "credits": 4},
                       headers=student).status_code == 403          # students can't create
    assert client.get("/courses").status_code == 401                # must be logged in
def test_tc_enr_01_course_prerequisites_saved_and_listed(client, login_as):
    _, admin = login_as("admin")
    for code in ("CS101", "CS102"):
        client.post("/courses", json={"code": code, "name": code, "credits": 4}, headers=admin)
    res = client.post("/courses", headers=admin, json={
        "code": "CS201", "name": "Data Structures", "credits": 4,
        "prerequisites": "cs101, CS102"})
    assert res.status_code == 201
    courses = {c["code"]: c for c in client.get("/courses", headers=admin).json["courses"]}
    assert courses["CS201"]["prerequisites"] == ["CS101", "CS102"]
    assert courses["CS101"]["prerequisites"] == []


def test_tc_enr_01_unknown_prerequisite_rejected(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/courses", headers=admin, json={
        "code": "CS201", "name": "Data Structures", "credits": 4, "prerequisites": "CS999"})
    assert res.status_code == 400
    assert client.get("/courses", headers=admin).json["courses"] == []