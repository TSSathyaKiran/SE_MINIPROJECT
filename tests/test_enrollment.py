"""Enrollment and drop (SRS-F-021, F-022): TC-Enr-02, TC-Enr-03."""
from datetime import datetime

from app.core import clock
from app.core.settings import set_setting
from app.extensions import db
from app.models import AuditLog, Course, Enrollment, Grade, Prerequisite, Section, Term
from app.extensions import db
from app.models import Course, Enrollment, Grade, Prerequisite, Section, Term

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
def add_prerequisite(section, required_code):
    required_course = Course.query.filter_by(code=required_code).first()
    db.session.add(Prerequisite(course_id=section.course_id,
                                requires_course_id=required_course.id))
    db.session.commit()


def give_grade(user, code, point, letter):
    """Give the student a final grade in an old section of course `code`."""
    old = make_section(code=code, term_name="2025-EVEN")
    db.session.add(Grade(student_id=user.student.id, section_id=old.id,
                         grade=letter, grade_point=point))
    db.session.commit()


def test_tc_enr_02_prerequisite_unmet_without_grade(client, login_as):
    student, headers = login_as("student")
    make_section(code="CS101", term_name="2025-EVEN")
    target = make_section(code="CS102")
    add_prerequisite(target, "CS101")
    res = client.post("/enroll", json={"sectionId": target.id}, headers=headers)
    assert res.status_code == 409
    assert res.json["error"]["code"] == "prerequisite_unmet"
    assert "CS101" in res.json["error"]["message"]
    assert Enrollment.query.filter_by(section_id=target.id).count() == 0


def test_tc_enr_02_prerequisite_failed_course_does_not_count(client, login_as):
    student, headers = login_as("student")
    give_grade(student, "CS101", 0, "F")
    target = make_section(code="CS102")
    add_prerequisite(target, "CS101")
    res = client.post("/enroll", json={"sectionId": target.id}, headers=headers)
    assert res.status_code == 409
    assert res.json["error"]["code"] == "prerequisite_unmet"


def test_tc_enr_02_prerequisite_passed_allows_enrollment(client, login_as):
    student, headers = login_as("student")
    give_grade(student, "CS101", 9, "A+")
    target = make_section(code="CS102")
    add_prerequisite(target, "CS101")
    res = client.post("/enroll", json={"sectionId": target.id}, headers=headers)
    assert res.status_code == 201


def test_tc_enr_02_every_prerequisite_is_required(client, login_as):
    student, headers = login_as("student")
    give_grade(student, "CS101", 9, "A+")
    make_section(code="MA101", term_name="2025-EVEN")          # MA101 exists but is not passed
    target = make_section(code="CS201")
    add_prerequisite(target, "CS101")
    add_prerequisite(target, "MA101")
    res = client.post("/enroll", json={"sectionId": target.id}, headers=headers)
    assert res.status_code == 409
    assert "MA101" in res.json["error"]["message"]
    assert "CS101" not in res.json["error"]["message"]


def test_tc_enr_02_only_students_can_enroll(client, login_as):
    section = make_section()
    _, faculty = login_as("faculty")
    _, admin = login_as("admin")
    assert client.post("/enroll", json={"sectionId": section.id}, headers=faculty).status_code == 403
    assert client.post("/enroll", json={"sectionId": section.id}, headers=admin).status_code == 403
    assert client.post("/enroll", json={"sectionId": section.id}).status_code == 401


def test_tc_enr_02_bad_requests(client, login_as):
    _, headers = login_as("student")
    assert client.post("/enroll", json={}, headers=headers).status_code == 400
    assert client.post("/enroll", json={"sectionId": "abc"}, headers=headers).status_code == 400
    assert client.post("/enroll", json={"sectionId": 9999}, headers=headers).status_code == 404


def test_tc_enr_02_dropped_seat_is_free_for_someone_else(client, login_as):
    section = make_section(capacity=1)
    first, first_headers = login_as("student")
    _, second_headers = login_as("student")
    db.session.add(Enrollment(student_id=first.student.id, section_id=section.id,
                              status="dropped"))
    db.session.commit()
    assert client.post("/enroll", json={"sectionId": section.id},
                       headers=second_headers).status_code == 201
    res = client.post("/enroll", json={"sectionId": section.id}, headers=first_headers)
    assert res.status_code == 409                       # the seat is taken again
    assert res.json["error"]["code"] == "section_full"


def test_tc_enr_02_re_enrolling_after_a_drop_reuses_the_row(client, login_as):
    section = make_section(capacity=5)
    student, headers = login_as("student")
    dropped = Enrollment(student_id=student.student.id, section_id=section.id,
                         status="dropped")
    db.session.add(dropped)
    db.session.commit()
    dropped_id = dropped.id
    res = client.post("/enroll", json={"sectionId": section.id}, headers=headers)
    assert res.status_code == 201
    assert res.json["enrollmentId"] == dropped_id
    rows = Enrollment.query.filter_by(student_id=student.student.id,
                                      section_id=section.id).all()
    assert len(rows) == 1 and rows[0].status == "enrolled"
def set_deadline(day):
    set_setting("add_drop_deadline", day)
    db.session.commit()


def enrolled(user, section):
    row = Enrollment(student_id=user.student.id, section_id=section.id, status="enrolled")
    db.session.add(row)
    db.session.commit()
    return row.id


# Set the clock BEFORE login_as in each test: a session expires after 15 idle minutes,
# so moving the clock after logging in would log the student out.

def test_tc_enr_03_drop_before_deadline_frees_the_seat(client, login_as):
    set_deadline("2026-11-15")
    clock.set_now(datetime(2026, 11, 10, 9, 0))
    section = make_section(capacity=1)
    student, headers = login_as("student")
    _, other_headers = login_as("student")
    enrollment_id = enrolled(student, section)

    res = client.delete(f"/enroll/{enrollment_id}", headers=headers)
    assert res.status_code == 200
    assert res.json["status"] == "dropped"
    assert db.session.get(Enrollment, enrollment_id).status == "dropped"
    # the seat is free again, so another student can take it
    assert client.post("/enroll", json={"sectionId": section.id},
                       headers=other_headers).status_code == 201


def test_tc_enr_03_drop_on_the_deadline_day_is_still_allowed(client, login_as):
    set_deadline("2026-11-15")
    clock.set_now(datetime(2026, 11, 15, 17, 0))
    section = make_section()
    student, headers = login_as("student")
    enrollment_id = enrolled(student, section)
    assert client.delete(f"/enroll/{enrollment_id}", headers=headers).status_code == 200


def test_tc_enr_03_drop_after_deadline_rejected(client, login_as):
    set_deadline("2026-11-15")
    clock.set_now(datetime(2026, 11, 16, 9, 0))
    section = make_section()
    student, headers = login_as("student")
    enrollment_id = enrolled(student, section)

    res = client.delete(f"/enroll/{enrollment_id}", headers=headers)
    assert res.status_code == 403
    assert res.json["error"]["code"] == "drop_closed"
    assert db.session.get(Enrollment, enrollment_id).status == "enrolled"   # nothing changed


def test_tc_enr_03_deadline_comes_from_settings(client, login_as):
    set_deadline("2026-11-30")           # admin moved the deadline later
    clock.set_now(datetime(2026, 11, 20, 9, 0))
    section = make_section()
    student, headers = login_as("student")
    enrollment_id = enrolled(student, section)
    assert client.delete(f"/enroll/{enrollment_id}", headers=headers).status_code == 200


def test_tc_enr_03_only_own_enrollment_can_be_dropped(client, login_as):
    section = make_section()
    owner, _ = login_as("student")
    _, intruder = login_as("student")
    _, faculty = login_as("faculty")
    enrollment_id = enrolled(owner, section)

    assert client.delete(f"/enroll/{enrollment_id}", headers=intruder).status_code == 403
    assert client.delete(f"/enroll/{enrollment_id}", headers=faculty).status_code == 403
    assert client.delete(f"/enroll/{enrollment_id}").status_code == 401
    assert db.session.get(Enrollment, enrollment_id).status == "enrolled"
    assert client.delete("/enroll/9999", headers=intruder).status_code == 404


def test_tc_enr_03_dropping_twice_is_rejected(client, login_as):
    section = make_section()
    student, headers = login_as("student")
    enrollment_id = enrolled(student, section)
    assert client.delete(f"/enroll/{enrollment_id}", headers=headers).status_code == 200
    res = client.delete(f"/enroll/{enrollment_id}", headers=headers)
    assert res.status_code == 409
    assert res.json["error"]["code"] == "already_dropped"


def test_tc_enr_03_enroll_and_drop_are_audited(client, login_as):
    section = make_section()
    _, headers = login_as("student")
    res = client.post("/enroll", json={"sectionId": section.id}, headers=headers)
    client.delete(f"/enroll/{res.json['enrollmentId']}", headers=headers)
    actions = [a.action for a in
               AuditLog.query.filter_by(record_type="enrollment").order_by(AuditLog.id)]
    assert actions == ["enroll", "drop"]
def test_tc_enr_02_courses_page_lists_sections_with_enroll_form(client, login_as):
    section = make_section(code="CS150")
    _, headers = login_as("student")
    res = client.get("/ui/student/courses", headers=headers)
    assert res.status_code == 200
    assert b"CS150" in res.data
    assert f'name="sectionId" value="{section.id}"'.encode() in res.data


def test_tc_enr_03_courses_page_shows_drop_for_my_enrollment(client, login_as):
    section = make_section(code="CS150")
    student, headers = login_as("student")
    enrollment_id = enrolled(student, section)
    res = client.get("/ui/student/courses", headers=headers)
    assert f'data-api="/enroll/{enrollment_id}"'.encode() in res.data
    assert b'name="sectionId"' not in res.data        # already enrolled: no Enroll form


def test_tc_enr_03_courses_page_hides_drop_after_deadline(client, login_as):
    set_deadline("2026-11-15")
    clock.set_now(datetime(2026, 11, 16, 9, 0))
    section = make_section(code="CS150")
    student, headers = login_as("student")
    enrolled(student, section)
    res = client.get("/ui/student/courses", headers=headers)
    assert b"Dropping is closed" in res.data
    assert b'data-method="DELETE"' not in res.data


def test_tc_enr_02_courses_page_is_for_students_only(client, login_as):
    _, admin = login_as("admin")
    assert client.get("/ui/student/courses", headers=admin).status_code == 403
    assert client.get("/ui/student/courses").status_code == 302      # sent to the login page
def test_tc_enr_03_drop_button_uses_the_enrollment_id(client, login_as):
    # Three sections (ids 1, 2, 3) but only two enrollments (ids 1, 2), so ids differ.
    sections = [make_section(code=f"CS1{n}0") for n in (5, 6, 7)]
    student, headers = login_as("student")
    enrollment_ids = [enrolled(student, s) for s in sections[1:]]
    page = client.get("/ui/student/courses", headers=headers).data
    for enrollment_id in enrollment_ids:
        assert f'data-api="/enroll/{enrollment_id}"'.encode() in page
    wrong_ids = {s.id for s in sections[1:]} - set(enrollment_ids)   # section ids only
    assert wrong_ids
    for section_id in wrong_ids:
        assert f'data-api="/enroll/{section_id}"'.encode() not in page


def test_tc_enr_03_dropping_one_course_leaves_the_other_untouched(client, login_as):
    sections = [make_section(code=f"CS1{n}0") for n in (5, 6)]
    student, headers = login_as("student")
    first, second = [enrolled(student, s) for s in sections]
    res = client.delete(f"/enroll/{first}", headers=headers)
    assert res.status_code == 200
    assert db.session.get(Enrollment, first).status == "dropped"
    assert db.session.get(Enrollment, second).status == "enrolled"
def test_tc_enr_03_graded_course_cannot_be_dropped(client, login_as):
    section = make_section(code="CS101", term_name="2025-EVEN")
    student, headers = login_as("student")
    enrollment_id = enrolled(student, section)
    db.session.add(Grade(student_id=student.student.id, section_id=section.id,
                         grade="A+", grade_point=9))
    db.session.commit()
    res = client.delete(f"/enroll/{enrollment_id}", headers=headers)
    assert res.status_code == 403
    assert res.json["error"]["code"] == "course_completed"
    assert db.session.get(Enrollment, enrollment_id).status == "enrolled"


def test_tc_enr_03_page_shows_completed_instead_of_drop_for_graded_course(client, login_as):
    done = make_section(code="CS101", term_name="2025-EVEN")
    current = make_section(code="CS102", term_name="2026-ODD")
    student, headers = login_as("student")
    done_id = enrolled(student, done)
    current_id = enrolled(student, current)
    db.session.add(Grade(student_id=student.student.id, section_id=done.id,
                         grade="A+", grade_point=9))
    db.session.commit()
    page = client.get("/ui/student/courses", headers=headers).data
    assert b"Completed" in page
    assert f'data-api="/enroll/{done_id}"'.encode() not in page     # no Drop for a graded course
    assert f'data-api="/enroll/{current_id}"'.encode() in page      # still droppable
