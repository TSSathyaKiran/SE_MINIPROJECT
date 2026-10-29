"""Marks, grades, GPA/CGPA (Srujan): issues #18 and #19. Details in docs/TEAM_GUIDE.md.

  POST /grades/assessments    assigned faculty  {sectionId, name, maxMarks}            #18
  POST /grades/marks          assigned faculty  {assessmentId, studentId, score}       #18  400 > max, 403 after grade lock
  POST /grades/finalize       assigned faculty  {sectionId}  -> grades, GPA, notify    #19  409 already finalised
  GET  /grades/<studentId>    own student, admin  grades + GPA per term + CGPA         #19
  GET  /ui/faculty/marks      faculty page                                             #18, #19
  GET  /ui/student/grades     student page (link to transcript PDF)                    #19
"""
from flask import Blueprint

bp = Blueprint("grading", __name__)
