"""Enrollment and drop (SRS-F-021, F-022): TC-Enr-02, TC-Enr-03."""
from app.extensions import db
from app.models import Course, Enrollment, Section, Term


def make_section(code="CS101", capacity=30, term_name="2026-ODD", name="A"):
    """Create a term, course and section straight in the database. Returns the Section."""
    term = Term.query.filter_by(name=term_name).first() or Term(name=term_name)
    course = Course.query.filter_by(code=code).first() or Course(code=code, name=code, credits=4)
    db.session.add_all([term, course])
    db.session.flush()
    section = Section(course_id=course.id, term_id=term.id, name=name, capacity=capacity)
    db.session.add(section)
    db.session.commit()
    return section


def test_tc_enr_02_student_enrolls_in_open_section(client, login_as):
    student, headers = login_as("student")
    section = make_section()
    res = client.post("/enroll", json={"sectionId": section.id}, headers=headers)
    assert res.status_code == 201
    assert res.json["status"] == "enrolled"
    row = db.session.get(Enrollment, res.json["enrollmentId"])
    assert row.student_id == student.student.id and row.section_id == section.id


def test_tc_enr_02_duplicate_enrollment_rejected(client, login_as):
    _, headers = login_as("student")
    section = make_section()
    assert client.post("/enroll", json={"sectionId": section.id},
                       headers=headers).status_code == 201
    res = client.post("/enroll", json={"sectionId": section.id}, headers=headers)
    assert res.status_code == 409
    assert res.json["error"]["code"] == "duplicate"


def test_tc_enr_02_full_section_rejected(client, login_as):
    section = make_section(capacity=1)
    _, first = login_as("student")
    _, second = login_as("student")
    assert client.post("/enroll", json={"sectionId": section.id},
                       headers=first).status_code == 201
    res = client.post("/enroll", json={"sectionId": section.id}, headers=second)
    assert res.status_code == 409
    assert res.json["error"]["code"] == "section_full"