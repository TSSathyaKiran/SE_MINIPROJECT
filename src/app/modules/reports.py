"""Transcript and report card PDFs (Vaishnavi): issue #14. Details in docs/TEAM_GUIDE.md.

  GET /reports/transcript/<studentId>             own student, admin   PDF (unofficial)
  GET /reports/report-card?studentId=&termId=     admin                PDF (official)
  GET /ui/admin/report-cards                      admin page: pick student + term
"""
from io import BytesIO
from xml.sax.saxutils import escape

from flask import Blueprint, render_template, request, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..core.errors import ApiError
from ..core.security import current_user, require_login, require_role
from ..extensions import db
from ..models import Grade, Section, Student, Term

bp = Blueprint("reports", __name__)


def gpa_of(courses):
    """GPA = sum(credits * grade point) / sum(credits), 2 decimals (None if no credits)."""
    credits = sum(c["credits"] for c in courses)
    if not credits:
        return None
    return round(sum(c["credits"] * c["point"] for c in courses) / credits, 2)


def transcript_data(student):
    """Everything the transcript shows, as plain data (easy to test).

    Only finalised grades exist in the grades table, so every term listed here is complete.
    """
    by_term = {}
    for grade in Grade.query.filter_by(student_id=student.id).all():
        term = grade.section.term
        course = grade.section.course
        by_term.setdefault((term.id, term.name), []).append({
            "code": course.code, "name": course.name, "credits": course.credits,
            "grade": grade.grade, "point": grade.grade_point})

    terms, every_course = [], []
    for (_, term_name), courses in sorted(by_term.items()):
        courses.sort(key=lambda c: c["code"])
        terms.append({"term": term_name, "courses": courses, "gpa": gpa_of(courses)})
        every_course.extend(courses)

    return {"student": {"studentNo": student.student_no, "name": student.name,
                        "program": student.program, "semester": student.semester},
            "terms": terms, "cgpa": gpa_of(every_course)}


def _fmt(value):
    return "N/A" if value is None else f"{value:.2f}"


def build_transcript_pdf(data):
    """Draw transcript_data(...) as a PDF and return the bytes."""
    styles = getSampleStyleSheet()
    student = data["student"]
    story = [
        Paragraph("PES University: Unofficial Transcript", styles["Title"]),
        Paragraph(escape(f"{student['name']} ({student['studentNo']})"), styles["Heading2"]),
        Paragraph(escape(f"{student['program']}, semester {student['semester']}"),
                  styles["Normal"]),
        Spacer(1, 12),
    ]

    if not data["terms"]:
        story.append(Paragraph("No completed terms yet.", styles["Normal"]))

    for term in data["terms"]:
        story.append(Paragraph(escape(f"Term {term['term']}"), styles["Heading3"]))
        rows = [["Code", "Course", "Credits", "Grade", "Points"]]
        rows += [[c["code"], c["name"], str(c["credits"]), c["grade"], f"{c['point']:g}"]
                 for c in term["courses"]]
        table = Table(rows, hAlign="LEFT", colWidths=[60, 220, 55, 50, 50])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story += [table, Paragraph(f"Term GPA: {_fmt(term['gpa'])}", styles["Normal"]),
                  Spacer(1, 10)]

    story.append(Paragraph(f"CGPA: {_fmt(data['cgpa'])}", styles["Heading3"]))
    story.append(Paragraph("This transcript is unofficial.", styles["Italic"]))

    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, title="Unofficial Transcript").build(story)
    return buf.getvalue()


@bp.get("/reports/transcript/<int:student_id>")
@require_login
def transcript(student_id):
    user = current_user()
    if user.role == "student":
        own = Student.query.filter_by(user_id=user.id).first()
        if own is None or own.id != student_id:
            raise ApiError(403, "forbidden", "You can only view your own transcript")
    elif user.role != "admin":
        raise ApiError(403, "forbidden", "Only the student or an admin can view a transcript")

    student = db.session.get(Student, student_id)
    if student is None:
        raise ApiError(404, "not_found", "Student not found")

    pdf = build_transcript_pdf(transcript_data(student))
    return send_file(BytesIO(pdf), mimetype="application/pdf",
                     download_name=f"transcript-{student.student_no}.pdf")


def report_card_data(student, term):
    """Return grades and GPA for one student's selected term."""
    grades = (
        Grade.query
        .filter_by(student_id=student.id)
        .join(Section, Grade.section_id == Section.id)
        .filter(Section.term_id == term.id)
        .all()
    )

    courses = []
    for grade in grades:
        course = grade.section.course
        courses.append({
            "code": course.code,
            "name": course.name,
            "credits": course.credits,
            "grade": grade.grade,
            "point": grade.grade_point,
        })

    courses.sort(key=lambda course: course["code"])

    return {
        "student": {
            "studentNo": student.student_no,
            "name": student.name,
            "program": student.program,
            "semester": student.semester,
        },
        "term": term.name,
        "courses": courses,
        "gpa": gpa_of(courses),
    }


def build_report_card_pdf(data):
    """Build an official report card PDF and return its bytes."""
    styles = getSampleStyleSheet()
    student = data["student"]

    story = [
        Paragraph("PES University", styles["Title"]),
        Paragraph("Official Student Report Card", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(
            escape(f"Name: {student['name']}"),
            styles["Normal"],
        ),
        Paragraph(
            escape(f"Student Number: {student['studentNo']}"),
            styles["Normal"],
        ),
        Paragraph(
            escape(f"Program: {student['program']}"),
            styles["Normal"],
        ),
        Paragraph(
            escape(f"Semester: {student['semester']}"),
            styles["Normal"],
        ),
        Paragraph(
            escape(f"Academic Term: {data['term']}"),
            styles["Normal"],
        ),
        Spacer(1, 14),
    ]

    rows = [["Course Code", "Course", "Credits", "Grade", "Points"]]
    rows += [
        [
            course["code"],
            Paragraph(escape(course["name"]), styles["Normal"]),
            str(course["credits"]),
            course["grade"],
            f"{course['point']:g}",
        ]
        for course in data["courses"]
    ]

    if not data["courses"]:
        rows.append(["-", "No grades available", "-", "-", "-"])

    table = Table(rows, hAlign="LEFT", colWidths=[75, 205, 55, 55, 55])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.extend([
        table,
        Spacer(1, 14),
        Paragraph(f"Term GPA: {_fmt(data['gpa'])}", styles["Heading2"]),
        Spacer(1, 12),
        Paragraph("Official Report Card", styles["Italic"]),
    ])

    buf = BytesIO()
    SimpleDocTemplate(
        buf, pagesize=A4, title="Official Student Report Card"
    ).build(story)
    return buf.getvalue()


@bp.get("/reports/report-card")
@require_role("admin")
def report_card():
    """Download an official report card. Admin access only."""
    try:
        student_id = int(request.args.get("studentId", ""))
        term_id = int(request.args.get("termId", ""))
    except (TypeError, ValueError):
        raise ApiError(
            400, "invalid_field",
            "studentId and termId must be valid integers",
        )

    student = db.session.get(Student, student_id)
    if student is None:
        raise ApiError(404, "not_found", "Student not found")

    term = db.session.get(Term, term_id)
    if term is None:
        raise ApiError(404, "not_found", "Term not found")

    pdf = build_report_card_pdf(report_card_data(student, term))
    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        download_name=f"report-card-{student.student_no}-{term.name}.pdf",
    )


@bp.get("/ui/admin/report-cards")
@require_role("admin")
def report_cards_page():
    """Admin page for selecting a student and term for a report card."""
    students = Student.query.order_by(Student.student_no).all()
    terms = Term.query.order_by(Term.name.desc()).all()
    return render_template(
        "reports/report_cards.html",
        students=students,
        terms=terms,
    )
