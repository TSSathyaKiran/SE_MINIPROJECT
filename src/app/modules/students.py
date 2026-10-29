"""Students (Vaishnavi): issues #11, #12, #13. Details in docs/TEAM_GUIDE.md.

  POST /students              admin                    #11  create; 400 missing field, 409 duplicate
  GET  /students/<id>         admin, faculty, own      #12  403 other student, 404 not found
  PUT  /students/<id>         admin (all fields)       #12  status="inactive" deactivates
                              own student (phone, address only; anything else -> 400)
  GET  /students/search?q=    admin, faculty           #13  by student no or name; 400 empty q
  GET  /ui/admin/students     admin page               #11-13
  GET  /ui/student/profile    student page             #12
  GET  /ui/faculty/search     faculty page             #13
"""
from flask import Blueprint

bp = Blueprint("students", __name__)
