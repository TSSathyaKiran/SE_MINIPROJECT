"""In-app notifications (SRS-F-042): issue #19. Details in docs/TEAM_GUIDE.md.

  GET  /notifications             logged in  my notifications, newest first
  POST /notifications/<id>/read   logged in  mark one of mine as read
  GET  /ui/student/notifications  student page
"""
from flask import Blueprint

from ..extensions import db
from ..models import Notification

bp = Blueprint("notifications", __name__)


def notify(user_id, message):
    """Add an in-app notification for a user. Call it before db.session.commit()."""
    db.session.add(Notification(user_id=user_id, message=message[:255]))