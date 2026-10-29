"""Enrollment and drop (Srujan): issue #17. Details in docs/TEAM_GUIDE.md.

  POST   /enroll              student  {sectionId}  409 full / prerequisite unmet / duplicate
  DELETE /enroll/<id>         student  own enrollment; 403 after the add/drop deadline
  GET    /ui/student/courses  student page: open sections, my enrollments, enroll/drop buttons
"""
from flask import Blueprint

bp = Blueprint("enrollment", __name__)
