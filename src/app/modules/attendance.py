"""Attendance (Tanuj): issues #7 and #8. Details in docs/TEAM_GUIDE.md.

  POST /attendance                         assigned faculty  {sectionId, date, records:[{studentId,status}]}  #7
  GET  /attendance/<studentId>/summary     own student, faculty, admin  ?sectionId=                         #8
  GET  /ui/faculty/attendance              faculty page: pick section + date, mark P/A/L                    #7
  GET  /ui/student/attendance              student page: % per course                                       #8
"""
from flask import Blueprint

bp = Blueprint("attendance", __name__)
