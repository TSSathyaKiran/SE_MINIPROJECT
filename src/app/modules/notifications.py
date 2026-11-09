"""In-app notifications (SRS-F-042): issue #19. Details in docs/TEAM_GUIDE.md.

  GET  /notifications             logged in  my notifications, newest first
  POST /notifications/<id>/read   logged in  mark one of mine as read
  GET  /ui/student/notifications  student page
"""
from flask import Blueprint, jsonify, render_template

from ..core.errors import ApiError
from ..core.security import current_user, require_login, require_role
from ..extensions import db
from ..models import Notification

bp = Blueprint("notifications", __name__)


def notify(user_id, message):
    """Add an in-app notification for a user. Call it before db.session.commit()."""
    db.session.add(Notification(user_id=user_id, message=message[:255]))


def _my_notifications():
    return (Notification.query.filter_by(user_id=current_user().id)
            .order_by(Notification.id.desc()).all())


@bp.get("/notifications")
@require_login
def list_notifications():
    rows = _my_notifications()
    return jsonify(
        notifications=[{"id": n.id, "message": n.message, "read": bool(n.read),
                        "createdAt": n.created_at.isoformat() if n.created_at else None}
                       for n in rows],
        unread=sum(1 for n in rows if not n.read))


@bp.post("/notifications/<int:notification_id>/read")
@require_login
def mark_read(notification_id):
    note = db.session.get(Notification, notification_id)
    if note is None:
        raise ApiError(404, "notification_not_found", "That notification does not exist")
    if note.user_id != current_user().id:
        raise ApiError(403, "forbidden", "This is not your notification")
    note.read = True                    # marking it read twice is harmless
    db.session.commit()
    return jsonify(notificationId=note.id, status="read")


@bp.get("/ui/student/notifications")
@require_role("student")
def notifications_page():
    return render_template("notifications/list.html", notifications=_my_notifications())