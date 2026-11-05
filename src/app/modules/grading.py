"""Marks entry and grades (Srujan): issues #18 and #19. Details in docs/TEAM_GUIDE.md.

  POST /grades/assessments   faculty  {sectionId, name, maxMarks}  (the section's faculty)
  POST /grades/marks         faculty  {assessmentId, studentId, score}  403 after grade lock
  POST /grades/finalize      faculty  {sectionId}                       (issue #19)
  GET  /ui/faculty/marks     faculty page: my sections, assessments, marks
"""
import math

from flask import Blueprint, jsonify

from ..core.audit import audit
from ..core.errors import ApiError, as_float, as_int, get_json, required
from ..core.security import current_user, require_role
from ..extensions import db
from ..models import Assessment, Section

bp = Blueprint("grading", __name__)


def section_of_this_faculty(section_id):
    """The section, if it exists and the logged-in faculty teaches it."""
    section = db.session.get(Section, section_id)
    if section is None:
        raise ApiError(404, "section_not_found", "That section does not exist")
    if section.faculty_id != current_user().id:
        raise ApiError(403, "forbidden", "You are not the faculty of this section")
    return section


@bp.post("/grades/assessments")
@require_role("faculty")
def create_assessment():
    data = required(get_json(), "sectionId", "name", "maxMarks")
    section = section_of_this_faculty(as_int(data["sectionId"], "sectionId"))
    name = str(data["name"]).strip()
    max_marks = as_float(data["maxMarks"], "maxMarks")
    if len(name) > 80:
        raise ApiError(400, "invalid_field", "Assessment name is too long")
    if not math.isfinite(max_marks) or max_marks <= 0:
        raise ApiError(400, "invalid_field", "maxMarks must be a number above 0")
    if Assessment.query.filter_by(section_id=section.id, name=name).first():
        raise ApiError(409, "duplicate_assessment",
                       f"This section already has an assessment called {name}")

    assessment = Assessment(section_id=section.id, name=name, max_marks=max_marks)
    db.session.add(assessment)
    db.session.flush()                  # gives assessment.id before commit
    audit("create", "assessment", assessment.id)
    db.session.commit()
    return jsonify(assessmentId=assessment.id, status="created"), 201