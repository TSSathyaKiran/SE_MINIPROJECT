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
def test_tc_enr_01_section_created_and_listed(client, login_as, add_user):
    _, admin = login_as("admin")
    faculty = add_user("prof1", "faculty")
    term = client.post("/terms", json={"name": "2026-ODD"}, headers=admin).json["termId"]
    course = client.post("/courses", headers=admin,
                         json={"code": "CS101", "name": "Intro", "credits": 4}).json["courseId"]
    res = client.post("/courses/sections", headers=admin, json={
        "courseId": course, "termId": term, "name": "A",
        "facultyId": faculty.id, "capacity": 30})
    assert res.status_code == 201
    sections = client.get(f"/courses/sections?termId={term}", headers=admin).json["sections"]
    assert len(sections) == 1
    assert sections[0]["courseCode"] == "CS101"
    assert sections[0]["capacity"] == 30 and sections[0]["seatsTaken"] == 0
def _enr01_setup(client, admin, add_user):
    """Creates a faculty user, a term and a course. Returns a valid section body."""
    faculty = add_user("prof1", "faculty")
    term = client.post("/terms", json={"name": "2026-ODD"}, headers=admin).json["termId"]
    course = client.post("/courses", headers=admin,
                         json={"code": "CS101", "name": "Intro", "credits": 4}).json["courseId"]
    return {"courseId": course, "termId": term, "name": "A",
            "facultyId": faculty.id, "capacity": 30}


def test_tc_enr_01_duplicate_section_rejected(client, login_as, add_user):
    _, admin = login_as("admin")
    body = _enr01_setup(client, admin, add_user)
    assert client.post("/courses/sections", json=body, headers=admin).status_code == 201
    assert client.post("/courses/sections", json=body, headers=admin).status_code == 409
    # the name is upper-cased, so "a" is the same section as "A"
    assert client.post("/courses/sections", json={**body, "name": "a"},
                       headers=admin).status_code == 409
    # a different section name is fine
    assert client.post("/courses/sections", json={**body, "name": "B"},
                       headers=admin).status_code == 201


def test_tc_enr_01_section_validation(client, login_as, add_user):
    _, admin = login_as("admin")
    student, _ = login_as("student")
    body = _enr01_setup(client, admin, add_user)

    def post(**changes):
        return client.post("/courses/sections", json={**body, **changes}, headers=admin)

    assert post(courseId=9999).status_code == 400        # unknown course
    assert post(termId=9999).status_code == 400          # unknown term
    assert post(facultyId=student.id).status_code == 400  # not a faculty user
    assert post(facultyId=9999).status_code == 400       # unknown user
    assert post(capacity=0).status_code == 400           # capacity must be >= 1
    assert post(capacity="many").status_code == 400      # not a number
    no_name = {k: v for k, v in body.items() if k != "name"}
    assert client.post("/courses/sections", json=no_name, headers=admin).status_code == 400


def test_tc_enr_01_only_admin_creates_sections(client, login_as, add_user):
    _, admin = login_as("admin")
    _, student = login_as("student")
    body = _enr01_setup(client, admin, add_user)
    assert client.post("/courses/sections", json=body, headers=student).status_code == 403
    assert client.post("/courses/sections", json=body).status_code == 401
    assert client.get("/courses/sections").status_code == 401


def test_tc_enr_01_sections_filtered_by_term(client, login_as, add_user):
    _, admin = login_as("admin")
    body = _enr01_setup(client, admin, add_user)
    term2 = client.post("/terms", json={"name": "2027-EVEN"}, headers=admin).json["termId"]
    client.post("/courses/sections", json=body, headers=admin)
    client.post("/courses/sections", json={**body, "termId": term2}, headers=admin)

    everything = client.get("/courses/sections", headers=admin).json["sections"]
    assert len(everything) == 2
    only_first = client.get(f"/courses/sections?termId={body['termId']}",
                            headers=admin).json["sections"]
    assert len(only_first) == 1 and only_first[0]["term"] == "2026-ODD"
    assert client.get("/courses/sections?termId=abc", headers=admin).status_code == 400


def test_tc_enr_01_seats_taken_counts_only_enrolled(client, login_as, add_user):
    from app.extensions import db
    from app.models import Enrollment
    _, admin = login_as("admin")
    body = _enr01_setup(client, admin, add_user)
    section_id = client.post("/courses/sections", json=body, headers=admin).json["sectionId"]
    first, _ = login_as("student")
    second, _ = login_as("student")
    db.session.add_all([
        Enrollment(student_id=first.student.id, section_id=section_id, status="enrolled"),
        Enrollment(student_id=second.student.id, section_id=section_id, status="dropped")])
    db.session.commit()
    section = client.get("/courses/sections", headers=admin).json["sections"][0]
    assert section["seatsTaken"] == 1       # the dropped student does not hold a seat
def test_tc_enr_01_admin_courses_page(client, login_as, add_user):
    _, admin = login_as("admin")
    body = _enr01_setup(client, admin, add_user)
    client.post("/courses/sections", json=body, headers=admin)
    res = client.get("/ui/admin/courses", headers=admin)
    assert res.status_code == 200
    assert b"CS101" in res.data
    _, student = login_as("student")
    assert client.get("/ui/admin/courses", headers=student).status_code == 403
    assert client.get("/ui/admin/courses").status_code == 302     # redirected to login
