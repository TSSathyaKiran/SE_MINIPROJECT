"""Tests for transcript and report PDF generation (issue #14)."""

from app.extensions import db
from app.models import Course, Grade, Section, Student, Term
from app.modules.reports import (build_transcript_pdf, transcript_data, report_card_data, build_report_card_pdf)


def _add_grade(student, term, code, name, credits, grade, point):
    course = Course(code=code, name=name, credits=credits)
    db.session.add(course)
    db.session.flush()

    section = Section(
        course_id=course.id,
        term_id=term.id,
        name="A",
        capacity=30,
    )
    db.session.add(section)
    db.session.flush()

    db.session.add(Grade(
        student_id=student.id,
        section_id=section.id,
        grade=grade,
        grade_point=point,
    ))


def _add_transcript_data(student):
    term1 = Term(name="2026-ODD")
    term2 = Term(name="2027-EVEN")
    db.session.add_all([term1, term2])
    db.session.flush()

    _add_grade(student, term1, "CS101", "Programming", 4, "A+", 9)
    _add_grade(student, term1, "MA101", "Mathematics", 3, "A", 8)
    _add_grade(student, term2, "CS201", "Data Structures", 3, "O", 10)

    db.session.commit()


def test_tc_rep_01_transcript_data_and_pdf(login_as):
    student_user, _ = login_as("student")
    student = student_user.student
    _add_transcript_data(student)

    data = transcript_data(student)

    assert data["student"]["studentNo"] == student.student_no
    assert len(data["terms"]) == 2

    first_term = data["terms"][0]
    assert first_term["term"] == "2026-ODD"
    assert [course["code"] for course in first_term["courses"]] == [
        "CS101", "MA101"
    ]
    assert first_term["gpa"] == 8.57
    assert data["terms"][1]["gpa"] == 10.0
    assert data["cgpa"] == 9.0

    pdf = build_transcript_pdf(data)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_tc_rep_01_transcript_access(client, login_as):
    student_user, student_headers = login_as("student")
    another_student, _ = login_as("student")
    _, admin_headers = login_as("admin")
    _, faculty_headers = login_as("faculty")

    student = student_user.student
    _add_transcript_data(student)

    own = client.get(
        f"/reports/transcript/{student.id}",
        headers=student_headers,
    )
    assert own.status_code == 200
    assert own.mimetype == "application/pdf"
    assert own.data.startswith(b"%PDF")

    other = client.get(
        f"/reports/transcript/{another_student.student.id}",
        headers=student_headers,
    )
    assert other.status_code == 403

    admin = client.get(
        f"/reports/transcript/{student.id}",
        headers=admin_headers,
    )
    assert admin.status_code == 200
    assert admin.mimetype == "application/pdf"

    faculty = client.get(
        f"/reports/transcript/{student.id}",
        headers=faculty_headers,
    )
    assert faculty.status_code == 403

    assert client.get(f"/reports/transcript/{student.id}").status_code == 401


def test_tc_rep_02_admin_report_card_pdf(client, login_as):
    student_user, _ = login_as("student")
    _, admin_headers = login_as("admin")
    student = student_user.student
    _add_transcript_data(student)

    term = Term.query.filter_by(name="2026-ODD").one()

    response = client.get(
        f"/reports/report-card?studentId={student.id}&termId={term.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")
    assert "report-card" in response.headers["Content-Disposition"]


def test_tc_rep_02_report_card_data_contains_selected_term(login_as):
    student_user, _ = login_as("student")
    student = student_user.student
    _add_transcript_data(student)

    term = Term.query.filter_by(name="2026-ODD").one()
    data = report_card_data(student, term)

    assert data["term"] == "2026-ODD"
    assert [course["code"] for course in data["courses"]] == [
        "CS101", "MA101"
    ]
    assert data["gpa"] == 8.57

    pdf = build_report_card_pdf(data)
    assert pdf.startswith(b"%PDF")


def test_tc_rep_02_only_admin_can_download_report_card(client, login_as):
    student_user, student_headers = login_as("student")
    _, faculty_headers = login_as("faculty")
    _, admin_headers = login_as("admin")

    student = student_user.student
    _add_transcript_data(student)
    term = Term.query.filter_by(name="2026-ODD").one()

    url = f"/reports/report-card?studentId={student.id}&termId={term.id}"

    assert client.get(url, headers=student_headers).status_code == 403
    assert client.get(url, headers=faculty_headers).status_code == 403
    assert client.get(url).status_code == 401
    assert client.get(url, headers=admin_headers).status_code == 200


def test_tc_rep_02_invalid_report_card_ids(client, login_as):
    _, admin_headers = login_as("admin")

    assert client.get(
        "/reports/report-card",
        headers=admin_headers,
    ).status_code == 400

    assert client.get(
        "/reports/report-card?studentId=abc&termId=1",
        headers=admin_headers,
    ).status_code == 400

    assert client.get(
        "/reports/report-card?studentId=9999&termId=1",
        headers=admin_headers,
    ).status_code == 404

    assert client.get(
        "/reports/report-card?studentId=1&termId=9999",
        headers=admin_headers,
    ).status_code == 404
