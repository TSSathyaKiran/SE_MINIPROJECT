"""Faculty marks attendance: TC-Att-01 (issue #7)."""
import re
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


def _login_page(client, user, password="pass1234"):
    """Log the shared test client in over the cookie, like a browser would."""
    res = client.post("/auth/login", json={"username": user.username, "password": password})
    assert res.status_code == 200, res.json


def test_tc_att_01_page_redirects_when_logged_out(client):
    res = client.get("/ui/faculty/attendance")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/ui/login")


def test_tc_att_01_page_is_faculty_only(client, login_as):
    student, _ = login_as("student")
    _login_page(client, student)
    assert client.get("/ui/faculty/attendance").status_code == 403
    admin, _ = login_as("admin")
    _login_page(client, admin)
    assert client.get("/ui/faculty/attendance").status_code == 403


def test_tc_att_01_page_lists_only_my_sections(client, login_as, add_user):
    faculty, _, _, _ = _setup(login_as, add_user)   # mine: CS999
    other_faculty = add_user("prof2", "faculty")
    course = Course(code="CS998", name="Databases", credits=4)
    db.session.add(course)
    db.session.flush()
    term = Term.query.one()
    db.session.add(Section(course_id=course.id, term_id=term.id, name="B",
                           faculty_id=other_faculty.id, capacity=30))
    db.session.commit()
    _login_page(client, faculty)
    res = client.get("/ui/faculty/attendance")
    assert res.status_code == 200
    assert b"CS999" in res.data
    assert b"CS998" not in res.data


def test_tc_att_01_page_shows_enrolled_roster_with_saved_marks(client, login_as, add_user):
    faculty, headers, student, section = _setup(login_as, add_user)
    other_student = add_user("stud2", "student").student  # exists, but not enrolled
    _mark(client, headers, section, student.id, status="absent")
    _login_page(client, faculty)
    res = client.get(f"/ui/faculty/attendance?sectionId={section.id}&date=2026-10-30")
    assert res.status_code == 200
    assert student.name.encode() in res.data
    assert other_student.name.encode() not in res.data
    # the saved mark is preselected, not the "present" default
    assert re.search(rb'value="absent"[^>]*checked', res.data)
    assert not re.search(rb'value="present"[^>]*checked', res.data)


def test_tc_att_01_page_rejects_other_facultys_section(client, login_as, add_user):
    _, _, _, section = _setup(login_as, add_user)
    other_faculty, _ = login_as("faculty")  # a different teacher
    _login_page(client, other_faculty)
    res = client.get(f"/ui/faculty/attendance?sectionId={section.id}")
    assert res.status_code == 403


def test_tc_att_01_page_rejects_bad_section_and_date(client, login_as, add_user):
    faculty, _, _, section = _setup(login_as, add_user)
    _login_page(client, faculty)
    res = client.get("/ui/faculty/attendance?sectionId=9999")
    assert res.status_code == 404
    res = client.get(f"/ui/faculty/attendance?sectionId={section.id}&date=30/10/2026")
    assert res.status_code == 400


def test_tc_att_01_faculty_menu_link_is_live(client, login_as):
    faculty, _ = login_as("faculty")
    _login_page(client, faculty)
    res = client.get("/ui/faculty")
    assert res.status_code == 200
    assert b'href="/ui/faculty/attendance"' in res.data
