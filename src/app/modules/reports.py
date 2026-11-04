"""Transcript and report card PDFs (Vaishnavi): issue #14. Details in docs/TEAM_GUIDE.md.

  GET /reports/transcript/<studentId>             own student, admin   PDF (unofficial)
  GET /reports/report-card?studentId=&termId=     admin                PDF (official)
  GET /ui/admin/report-cards                      admin page: pick student + term
"""
from io import BytesIO
from xml.sax.saxutils import escape

from flask import Blueprint
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models import Grade

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