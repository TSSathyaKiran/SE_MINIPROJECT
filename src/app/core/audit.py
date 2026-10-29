from ..extensions import db
from ..models import AuditLog
from .security import current_user


def audit(action, record_type, record_id, actor_id=None):
    """Record a change (SRS-F-071). Call it before db.session.commit().

        audit("create", "student", student.id)
    """
    if actor_id is None and current_user():
        actor_id = current_user().id
    db.session.add(AuditLog(user_id=actor_id, action=action,
                            record_type=record_type, record_id=str(record_id)))
