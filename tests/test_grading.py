"""Marks entry (SRS-F-040): TC-Grd-01."""
import pytest

from app.core.settings import set_setting
from app.extensions import db
from app.models import Assessment, AuditLog, Course, Enrollment, Mark, Section, Term


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


@pytest.fixture(autouse=True)
def lock_date_far_away(app):
    """The default grade-lock date is a calendar date, so push it far away for every test.
    Tests that need a specific lock date set it themselves."""
    set_setting("grade_lock_date", "2099-12-31")
    db.session.commit()


def add_assessment(section, name="Midterm", max_marks=50):
    row = Assessment(section_id=section.id, name=name, max_marks=max_marks)
    db.session.add(row)
    db.session.commit()
    return row


def enroll(student_user, section, status="enrolled"):
    row = Enrollment(student_id=student_user.student.id, section_id=section.id, status=status)
    db.session.add(row)
    db.session.commit()
    return row


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


def test_tc_grd_01_faculty_enters_a_mark(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    res = client.post("/grades/marks", headers=headers, json={
        "assessmentId": assessment.id, "studentId": student.student.id, "score": 42.5})
    assert res.status_code == 201
    assert res.json["status"] == "created"
    mark = db.session.get(Mark, res.json["markId"])
    assert mark.score == 42.5 and mark.student_id == student.student.id


def test_tc_grd_01_entering_again_updates_the_same_mark(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    body = {"assessmentId": assessment.id, "studentId": student.student.id}
    first = client.post("/grades/marks", json={**body, "score": 30}, headers=headers)
    second = client.post("/grades/marks", json={**body, "score": 35}, headers=headers)
    assert first.status_code == 201 and second.status_code == 200
    assert second.json["status"] == "updated"
    assert second.json["markId"] == first.json["markId"]
    assert Mark.query.count() == 1 and Mark.query.one().score == 35


def test_tc_grd_01_score_must_be_between_zero_and_max(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section, max_marks=50)
    student, _ = login_as("student")
    enroll(student, section)
    body = {"assessmentId": assessment.id, "studentId": student.student.id}

    def post(score):
        return client.post("/grades/marks", json={**body, "score": score}, headers=headers)

    assert post(0).status_code == 201            # zero is allowed
    assert post(50).status_code == 200           # the maximum is allowed
    assert post(50.5).status_code == 400         # above the maximum
    assert post(-1).status_code == 400           # negative
    assert post("abc").status_code == 400        # not a number
    assert post("nan").status_code == 400        # not a real number
    assert Mark.query.one().score == 50          # the bad attempts changed nothing


def test_tc_grd_01_student_must_be_enrolled_in_the_section(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    other_section = make_section(faculty, code="CS103")
    assessment = add_assessment(section)
    not_enrolled, _ = login_as("student")
    dropped, _ = login_as("student")
    other, _ = login_as("student")
    enroll(dropped, section, status="dropped")
    enroll(other, other_section)                 # enrolled, but in a different section
    for student in (not_enrolled, dropped, other):
        res = client.post("/grades/marks", headers=headers, json={
            "assessmentId": assessment.id, "studentId": student.student.id, "score": 10})
        assert res.status_code == 400
        assert res.json["error"]["code"] == "student_not_enrolled"
    unknown = client.post("/grades/marks", headers=headers, json={
        "assessmentId": assessment.id, "studentId": 9999, "score": 10})
    assert unknown.status_code == 400
    assert Mark.query.count() == 0


def test_tc_grd_01_only_the_sections_faculty_can_enter_marks(client, login_as):
    faculty, _ = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, student_headers = login_as("student")
    enroll(student, section)
    _, other_faculty = login_as("faculty")
    _, admin = login_as("admin")
    body = {"assessmentId": assessment.id, "studentId": student.student.id, "score": 10}
    assert client.post("/grades/marks", json=body, headers=other_faculty).status_code == 403
    assert client.post("/grades/marks", json=body, headers=student_headers).status_code == 403
    assert client.post("/grades/marks", json=body, headers=admin).status_code == 403
    assert client.post("/grades/marks", json=body).status_code == 401
    assert client.post("/grades/marks", headers=other_faculty,
                       json={**body, "assessmentId": 9999}).status_code == 404
    assert Mark.query.count() == 0