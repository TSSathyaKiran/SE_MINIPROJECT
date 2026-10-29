"""In-app notifications (Srujan): issue #19. Details in docs/TEAM_GUIDE.md.

  GET  /notifications             logged-in user   {notifications:[...]}
  POST /notifications/<id>/read   owner
  GET  /ui/student/notifications  student page
"""
from flask import Blueprint

bp = Blueprint("notifications", __name__)
