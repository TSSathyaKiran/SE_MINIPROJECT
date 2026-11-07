"""Marks entry (SRS-F-040): TC-Grd-01."""
from datetime import datetime, timedelta

import pytest

from app.core import clock
from app.core.settings import set_setting
from app.extensions import db
from app.models import Assessment, AuditLog, Course, Enrollment, Mark, Section, Term
from app.modules.grading import gpa, grade_for

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


def set_lock_date(day):
    set_setting("grade_lock_date", day)
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


# Set the clock BEFORE login_as in each test: a session expires after 15 idle minutes,
# so moving the clock after logging in would log the faculty out.

def test_tc_grd_01_marks_rejected_after_the_lock_date(client, login_as):
    set_lock_date("2026-11-30")
    clock.set_now(datetime(2026, 12, 1, 9, 0))
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    res = client.post("/grades/marks", headers=headers, json={
        "assessmentId": assessment.id, "studentId": student.student.id, "score": 10})
    assert res.status_code == 403
    assert res.json["error"]["code"] == "grades_locked"
    assert Mark.query.count() == 0


def test_tc_grd_01_marks_still_allowed_on_the_lock_date_itself(client, login_as):
    set_lock_date("2026-11-30")
    clock.set_now(datetime(2026, 11, 30, 17, 0))
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    res = client.post("/grades/marks", headers=headers, json={
        "assessmentId": assessment.id, "studentId": student.student.id, "score": 10})
    assert res.status_code == 201


def test_tc_grd_01_existing_mark_cannot_be_changed_after_the_lock_date(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    body = {"assessmentId": assessment.id, "studentId": student.student.id}
    assert client.post("/grades/marks", json={**body, "score": 30},
                       headers=headers).status_code == 201
    # the admin moves the lock date to yesterday (the clock stays put so the session stays valid)
    set_lock_date((clock.today() - timedelta(days=1)).isoformat())
    res = client.post("/grades/marks", json={**body, "score": 45}, headers=headers)
    assert res.status_code == 403
    assert res.json["error"]["code"] == "grades_locked"
    assert Mark.query.one().score == 30
def test_tc_grd_01_mark_entry_and_update_are_audited(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    body = {"assessmentId": assessment.id, "studentId": student.student.id}
    first = client.post("/grades/marks", json={**body, "score": 20}, headers=headers)
    client.post("/grades/marks", json={**body, "score": 25}, headers=headers)
    logs = AuditLog.query.filter_by(record_type="mark").order_by(AuditLog.id).all()
    assert [log.action for log in logs] == ["grade", "grade"]
    assert all(log.record_id == str(first.json["markId"]) for log in logs)
    assert all(log.user_id == faculty.id for log in logs)


def test_tc_grd_01_missing_or_bad_fields_rejected(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    ok = {"assessmentId": assessment.id, "studentId": student.student.id, "score": 10}
    for missing in ("assessmentId", "studentId", "score"):
        body = {k: v for k, v in ok.items() if k != missing}
        assert client.post("/grades/marks", json=body, headers=headers).status_code == 400
    assert client.post("/grades/marks", json={**ok, "assessmentId": "x"},
                       headers=headers).status_code == 400
    assert client.post("/grades/marks", json={**ok, "studentId": "x"},
                       headers=headers).status_code == 400
    assert Mark.query.count() == 0


def test_tc_grd_01_marks_are_kept_per_student_and_per_assessment(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    midterm = add_assessment(section, "Midterm", 50)
    quiz = add_assessment(section, "Quiz", 10)
    first, _ = login_as("student")
    second, _ = login_as("student")
    enroll(first, section)
    enroll(second, section)

    def post(assessment, student, score):
        return client.post("/grades/marks", headers=headers, json={
            "assessmentId": assessment.id, "studentId": student.student.id, "score": score})

    assert post(midterm, first, 40).status_code == 201
    assert post(quiz, first, 8).status_code == 201         # same student, other assessment
    assert post(midterm, second, 30).status_code == 201    # other student, same assessment
    assert post(midterm, first, 45).status_code == 200     # only this one is updated
    scores = {(m.assessment_id, m.student_id): m.score for m in Mark.query.all()}
    assert scores == {(midterm.id, first.student.id): 45,
                      (quiz.id, first.student.id): 8,
                      (midterm.id, second.student.id): 30}


def test_tc_grd_01_lock_answers_before_other_errors_but_after_ownership(client, login_as):
    set_lock_date("2026-11-30")
    clock.set_now(datetime(2026, 12, 1, 9, 0))
    faculty, headers = login_as("faculty")
    _, other_faculty = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    not_enrolled, _ = login_as("student")
    body = {"assessmentId": assessment.id, "studentId": not_enrolled.student.id, "score": 999}
    # the section's own faculty is told the marks are locked, not about enrollment or score
    res = client.post("/grades/marks", json=body, headers=headers)
    assert res.status_code == 403 and res.json["error"]["code"] == "grades_locked"
    # a faculty member from another section is still told "forbidden"
    res = client.post("/grades/marks", json=body, headers=other_faculty)
    assert res.status_code == 403 and res.json["error"]["code"] == "forbidden"
def test_tc_grd_01_marks_page_lists_my_sections(client, login_as):
    faculty, headers = login_as("faculty")
    make_section(faculty, code="CS150")
    res = client.get("/ui/faculty/marks", headers=headers)
    assert res.status_code == 200
    assert b"CS150" in res.data


def test_tc_grd_01_marks_page_shows_assessments_and_mark_forms(client, login_as):
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    add_assessment(section, "Midterm", 50)
    student, _ = login_as("student")
    enroll(student, section)
    res = client.get(f"/ui/faculty/marks?sectionId={section.id}", headers=headers)
    assert res.status_code == 200
    assert b"Midterm" in res.data
    assert student.student.student_no.encode() in res.data
    assert b'data-api="/grades/marks"' in res.data
    assert b'data-api="/grades/assessments"' in res.data


def test_tc_grd_01_marks_page_is_read_only_after_the_lock_date(client, login_as):
    set_lock_date("2026-11-30")
    clock.set_now(datetime(2026, 12, 1, 9, 0))
    faculty, headers = login_as("faculty")
    section = make_section(faculty)
    assessment = add_assessment(section)
    student, _ = login_as("student")
    enroll(student, section)
    db.session.add(Mark(assessment_id=assessment.id, student_id=student.student.id, score=42))
    db.session.commit()
    res = client.get(f"/ui/faculty/marks?sectionId={section.id}", headers=headers)
    assert b"read-only" in res.data
    assert b"<span>42</span>" in res.data                       # the saved mark is shown
    assert b'data-api="/grades/marks"' not in res.data          # but cannot be edited
    assert b'data-api="/grades/assessments"' not in res.data


def test_tc_grd_01_marks_page_is_only_for_the_sections_faculty(client, login_as):
    faculty, _ = login_as("faculty")
    section = make_section(faculty)
    _, other_faculty = login_as("faculty")
    _, student = login_as("student")
    url = f"/ui/faculty/marks?sectionId={section.id}"
    assert client.get(url, headers=other_faculty).status_code == 403
    assert client.get(url, headers=student).status_code == 403
    assert client.get(url).status_code == 302                    # sent to the login page
    assert client.get("/ui/faculty/marks?sectionId=abc",
                      headers=other_faculty).status_code == 400
def test_tc_grd_02_gpa_matches_the_srs_example():
    assert gpa([(4, 9), (3, 8), (4, 10), (3, 7)]) == 8.64      # 121 / 14


def test_tc_grd_02_gpa_edge_cases():
    assert gpa([]) == 0.0                   # no courses: no division by zero
    assert gpa([(4, 10)]) == 10.0
    assert gpa([(3, 0), (3, 0)]) == 0.0
    assert gpa([(4, 9), (0, 5)]) == 9.0     # a course with zero credits counts for nothing


def test_tc_grd_02_cgpa_is_credit_weighted_not_an_average_of_term_gpas():
    term1 = [(4, 9), (3, 8), (4, 10), (3, 7)]
    term2 = [(4, 8), (3, 9)]
    assert gpa(term1) == 8.64               # 121 / 14
    assert gpa(term2) == 8.43               # 59 / 7
    assert gpa(term1 + term2) == 8.57       # 180 / 21, the hand-calculated CGPA
    assert round((gpa(term1) + gpa(term2)) / 2, 2) != gpa(term1 + term2)


@pytest.mark.parametrize("percent, letter, point", [
    (100, "O", 10), (90, "O", 10), (89.99, "A+", 9), (80, "A+", 9), (79.99, "A", 8),
    (70, "A", 8), (60, "B+", 7), (55, "B", 6), (50, "C", 5), (40, "P", 4),
    (39.99, "F", 0), (0, "F", 0)])
def test_tc_grd_02_grade_for_uses_the_default_scale(app, percent, letter, point):
    assert grade_for(percent) == (letter, point)


def test_tc_grd_02_grade_for_reads_the_scale_from_settings(app):
    # an admin-edited scale, saved in no particular order
    set_setting("grading_scale", [[0, "F", 0], [75, "D", 8], [50, "P", 5]])
    db.session.commit()
    assert grade_for(80) == ("D", 8)
    assert grade_for(75) == ("D", 8)
    assert grade_for(60) == ("P", 5)
    assert grade_for(10) == ("F", 0)