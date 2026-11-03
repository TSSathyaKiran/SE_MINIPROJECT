from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from app.core import clock
from app.extensions import db
from app.models import AuditLog, Course, Enrollment, Section, Term


def make_section(faculty, student):
    """A section taught by `faculty` with `student` enrolled, so attendance can be marked."""
    term = Term(name="2026-ODD")
    course = Course(code="CS101", name="Intro", credits=4)
    db.session.add_all([term, course])
    db.session.flush()
    section = Section(course_id=course.id, term_id=term.id, name="A",
                      faculty_id=faculty.id, capacity=30)
    db.session.add(section)
    db.session.flush()
    db.session.add(Enrollment(student_id=student.id, section_id=section.id))
    db.session.commit()
    return section


# ---- TC-Adm-02: every change is logged with actor, action, record and time ----

def test_tc_adm_02_changes_are_logged_with_actor_and_record(client, login_as):
    clock.set_now(datetime(2026, 10, 20, 9, 0))
    admin, admin_h = login_as("admin")
    faculty, faculty_h = login_as("faculty")
    student, _ = login_as("student")

    term_id = client.post("/terms", json={"name": "2026-EVEN"}, headers=admin_h).json["termId"]
    sid = student.student.id
    client.put(f"/students/{sid}", json={"semester": 4}, headers=admin_h)
    section = make_section(faculty, student.student)
    client.post("/attendance", json={"sectionId": section.id, "date": "2026-10-20",
                                     "records": [{"studentId": sid, "status": "present"}]},
                headers=faculty_h)
    client.put(f"/students/{sid}", json={"status": "inactive"}, headers=admin_h)

    res = client.get("/audit-logs", headers=admin_h)
    assert res.status_code == 200
    got = [(log["actor"], log["action"], log["recordType"]) for log in res.json["logs"]]
    assert got == [(admin.username, "deactivate", "student"),     # newest first
                   (faculty.username, "mark", "attendance"),
                   (admin.username, "update", "student"),
                   (admin.username, "create", "term")]
    create = res.json["logs"][-1]
    assert create["recordId"] == str(term_id)
    assert create["timestamp"] == "2026-10-20T09:00:00"


def test_audit_logs_filter_by_module_and_dates(client, login_as):
    admin, admin_h = login_as("admin")
    for day in (19, 20, 21):
        for record_type in ("term", "course"):
            db.session.add(AuditLog(user_id=admin.id, action="create", record_type=record_type,
                                    record_id="1", timestamp=datetime(2026, 10, day, 12, 0)))
    db.session.commit()

    def logs(query):
        return client.get(f"/audit-logs?{query}", headers=admin_h).json["logs"]

    assert len(logs("")) == 6
    assert {log["recordType"] for log in logs("module=term")} == {"term"}
    assert len(logs("module=term")) == 3
    assert len(logs("from=2026-10-20")) == 4
    assert len(logs("to=2026-10-20")) == 4                  # the whole of the 20th counts
    assert len(logs("module=course&from=2026-10-20&to=2026-10-20")) == 1


def test_audit_logs_admin_only_and_bad_dates(client, login_as):
    _, admin_h = login_as("admin")
    _, faculty_h = login_as("faculty")
    _, student_h = login_as("student")
    assert client.get("/audit-logs").status_code == 401
    assert client.get("/audit-logs", headers=faculty_h).status_code == 403
    assert client.get("/audit-logs", headers=student_h).status_code == 403
    assert client.get("/audit-logs?from=20-10-2026", headers=admin_h).status_code == 400
    res = client.get("/audit-logs?from=2026-10-21&to=2026-10-20", headers=admin_h)
    assert res.status_code == 400


# ---- TC-Sec-07: audit rows cannot be changed from the API, the ORM or raw SQL ----

def test_tc_sec_07_audit_rows_cannot_be_changed(client, login_as):
    _, admin_h = login_as("admin")
    client.post("/terms", json={"name": "2026-ODD"}, headers=admin_h)
    log = AuditLog.query.one()
    before = (log.user_id, log.action, log.record_type, log.record_id, log.timestamp)

    for method in (client.put, client.patch, client.delete):            # API
        assert method("/audit-logs", json={}, headers=admin_h).status_code == 405

    log.action = "nothing happened"                                      # ORM update
    with pytest.raises(PermissionError):
        db.session.commit()
    db.session.rollback()
    db.session.delete(log)                                               # ORM delete
    with pytest.raises(PermissionError):
        db.session.commit()
    db.session.rollback()

    for sql in ("UPDATE audit_logs SET action = 'x'", "DELETE FROM audit_logs"):  # raw SQL
        with pytest.raises(DatabaseError, match="append-only"):
            db.session.execute(text(sql))
        db.session.rollback()

    log = AuditLog.query.one()
    assert (log.user_id, log.action, log.record_type, log.record_id, log.timestamp) == before


def test_new_audit_rows_can_still_be_added(client, login_as):
    _, admin_h = login_as("admin")
    client.post("/terms", json={"name": "T1"}, headers=admin_h)
    client.post("/terms", json={"name": "T2"}, headers=admin_h)
    assert AuditLog.query.count() == 2


def test_admin_audit_page_lists_and_filters(client, login_as):
    admin, admin_h = login_as("admin")
    _, student_h = login_as("student")
    client.post("/terms", json={"name": "2026-ODD"}, headers=admin_h)
    client.post("/courses", json={"code": "CS999", "name": "X", "credits": 3}, headers=admin_h)

    html = client.get("/ui/admin/audit", headers=admin_h).get_data(as_text=True)
    assert admin.username in html and "<td>term</td>" in html and "<td>course</td>" in html
    html = client.get("/ui/admin/audit?module=term", headers=admin_h).get_data(as_text=True)
    assert "<td>term</td>" in html and "<td>course</td>" not in html
    assert client.get("/ui/admin/audit", headers=student_h).status_code == 403
