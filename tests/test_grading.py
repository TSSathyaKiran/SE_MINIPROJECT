"""Marks entry (SRS-F-040): TC-Grd-01."""
from app.extensions import db
from app.models import Assessment, AuditLog, Course, Section, Term


def make_section(faculty, code="CS102", capacity=30):
    """Create a term, course and a section taught by `faculty`. Returns the Section."""
    term = Term.query.filter_by(name="2026-ODD").first() or Term(name="2026-ODD")
    course = Course.query.filter_by(code=code).first() or Course(code=code, name=code, credits=4)
    db.session.add_all([term, course])
    db.session.flush()
    section = Section(course_id=course.id, term_id=term.id, name="A",
                      faculty_id=faculty.id, capacity=capacity)
    db.session.add(section)
    db.session.commit()
    return section


def test_tc_grd_01_faculty_creates_assessment(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    res = client.post("/grades/assessments", headers=headers,
                      json={"sectionId": section.id, "name": "Midterm", "maxMarks": 50})
    assert res.status_code == 201
    row = db.session.get(Assessment, res.json["assessmentId"])
    assert row.section_id == section.id and row.name == "Midterm" and row.max_marks == 50


def test_tc_grd_01_only_the_sections_faculty_can_create_assessments(client, login_as):
    faculty, _ = login_as("faculty")
    section = make_section(faculty)
    _, other_faculty = login_as("faculty")
    _, student = login_as("student")
    _, admin = login_as("admin")
    body = {"sectionId": section.id, "name": "Midterm", "maxMarks": 50}
    assert client.post("/grades/assessments", json=body, headers=other_faculty).status_code == 403
    assert client.post("/grades/assessments", json=body, headers=student).status_code == 403
    assert client.post("/grades/assessments", json=body, headers=admin).status_code == 403
    assert client.post("/grades/assessments", json=body).status_code == 401
    assert Assessment.query.count() == 0


def test_tc_grd_01_assessment_validation(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)

    def post(**changes):
        body = {"sectionId": section.id, "name": "Midterm", "maxMarks": 50, **changes}
        return client.post("/grades/assessments", json=body, headers=headers)

    assert post(maxMarks=0).status_code == 400
    assert post(maxMarks=-5).status_code == 400
    assert post(maxMarks="abc").status_code == 400
    assert post(maxMarks="nan").status_code == 400
    assert post(maxMarks="inf").status_code == 400
    assert post(name="   ").status_code == 400
    assert post(sectionId="x").status_code == 400
    assert post(sectionId=9999).status_code == 404
    assert Assessment.query.count() == 0


def test_tc_grd_01_duplicate_assessment_name_rejected(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    body = {"sectionId": section.id, "name": "Midterm", "maxMarks": 50}
    assert client.post("/grades/assessments", json=body, headers=headers).status_code == 201
    res = client.post("/grades/assessments", json=body, headers=headers)
    assert res.status_code == 409
    assert res.json["error"]["code"] == "duplicate_assessment"
    assert Assessment.query.count() == 1


def test_tc_grd_01_assessment_creation_is_audited(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    res = client.post("/grades/assessments", headers=headers,
                      json={"sectionId": section.id, "name": "Quiz 1", "maxMarks": 10})
    log = AuditLog.query.filter_by(record_type="assessment").one()
    assert log.action == "create" and log.record_id == str(res.json["assessmentId"])