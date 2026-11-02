from sqlalchemy import DDL, event

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


# Audit rows are append-only (SRS-SR-006). The ORM refuses to change them, and a
# database trigger blocks UPDATE and DELETE even from raw SQL.
@event.listens_for(AuditLog, "before_update")
@event.listens_for(AuditLog, "before_delete")
def _append_only(mapper, connection, target):
    raise PermissionError("audit_logs is append-only")


for _op in ("UPDATE", "DELETE"):
    event.listen(AuditLog.__table__, "after_create", DDL(
        f"CREATE TRIGGER audit_no_{_op.lower()} BEFORE {_op} ON audit_logs "
        "BEGIN SELECT RAISE(ABORT, 'audit_logs is append-only'); END"
    ).execute_if(dialect="sqlite"))
    event.listen(AuditLog.__table__, "after_create", DDL(
        f"CREATE TRIGGER audit_no_{_op.lower()} BEFORE {_op} ON audit_logs FOR EACH ROW "
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_logs is append-only'"
    ).execute_if(dialect="mysql"))
