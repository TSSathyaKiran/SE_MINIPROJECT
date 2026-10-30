"""Faculty marks attendance: TC-Att-01 (issue #7)."""
from datetime import date

from app.extensions import db
from app.models import (Attendance, AuditLog, Course, Enrollment, Section, Term)


def _setup(login_as, add_user):
    """A logged-in faculty with their own section and one enrolled student."""
    faculty, headers = login_as("faculty")
    student_user = add_user("stud1", "student")  # add_user links student_user.student
    course = Course(code="CS999", name="Software Testing", credits=4)
    term = Term(name="2026-TEST")
    db.session.add_all([course, term])
    db.session.flush()
    section = Section(course_id=course.id, term_id=term.id, name="A",
                      faculty_id=faculty.id, capacity=30)
    db.session.add(section)
    db.session.flush()
    db.session.add(Enrollment(student_id=student_user.student.id, section_id=section.id))
    db.session.commit()
    return faculty, headers, student_user.student, section


def _mark(client, headers, section, student_id, status="present", day="2026-10-30"):
    return client.post("/attendance", headers=headers, json={
        "sectionId": section.id, "date": day,
        "records": [{"studentId": student_id, "status": status}],
    })


def test_tc_att_01_faculty_marks_and_updates_attendance(client, login_as, add_user):
    _, headers, student, section = _setup(login_as, add_user)
    res = _mark(client, headers, section, student.id)
    assert res.status_code == 200
    assert res.json == {"status": "saved", "count": 1}
    row = Attendance.query.one()
    assert (row.status, str(row.date)) == ("present", "2026-10-30")

    # marking the same student on the same day updates the row, no duplicate
    res = _mark(client, headers, section, student.id, status="late")
    assert res.status_code == 200
    assert Attendance.query.count() == 1
    assert Attendance.query.one().status == "late"


def test_tc_att_01_marking_is_audited(client, login_as, add_user):
    faculty, headers, student, section = _setup(login_as, add_user)
    _mark(client, headers, section, student.id)
    log = AuditLog.query.one()
    assert (log.user_id, log.action, log.record_type) == (faculty.id, "mark", "attendance")
    assert log.record_id == str(Attendance.query.one().id)


def test_tc_att_01_rejects_student_not_enrolled(client, login_as, add_user):
    _, headers, student, section = _setup(login_as, add_user)
    other_student = add_user("stud2", "student").student  # exists, but not enrolled
    res = _mark(client, headers, section, other_student.id)
    assert res.status_code == 400
    assert res.json["error"]["code"] == "not_enrolled"
    assert Attendance.query.count() == 0


def test_tc_att_01_rejects_other_faculty(client, login_as, add_user):
    _, _, student, section = _setup(login_as, add_user)
    _, other_headers = login_as("faculty")  # a different teacher
    res = _mark(client, other_headers, section, student.id)
    assert res.status_code == 403
    assert Attendance.query.count() == 0


def test_tc_att_01_rejects_students_and_anonymous(client, login_as, add_user):
    _, _, student, section = _setup(login_as, add_user)
    _, student_headers = login_as("student")
    assert _mark(client, student_headers, section, student.id).status_code == 403
    assert _mark(client, {}, section, student.id).status_code == 401


def test_tc_att_01_rejects_bad_status_date_and_section(client, login_as, add_user):
    _, headers, student, section = _setup(login_as, add_user)
    res = _mark(client, headers, section, student.id, status="sleeping")
    assert res.status_code == 400
    res = _mark(client, headers, section, student.id, day="30/10/2026")
    assert res.status_code == 400
    res = client.post("/attendance", headers=headers, json={
        "sectionId": 9999, "date": "2026-10-30",
        "records": [{"studentId": student.id, "status": "present"}],
    })
    assert res.status_code == 404
    assert Attendance.query.count() == 0
