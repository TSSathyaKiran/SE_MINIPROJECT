"""Audit log viewer (Sathya): issue #3. Details in docs/TEAM_GUIDE.md.
Writing entries is already done: core/audit.py.

  GET /audit-logs             admin   ?module=&from=&to=   {logs:[{actor, action, recordType, recordId, timestamp}]}
  GET /ui/admin/audit         admin page with filters
  plus: audit rows can never be updated or deleted (SRS-SR-006)
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from ..core.errors import ApiError
from ..core.security import require_role
from ..extensions import db
from ..models import AuditLog, User

bp = Blueprint("auditlog", __name__)


def _parse_date(value, field):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ApiError(400, "invalid_field", f"{field} must be a date like 2026-10-30")


def find_logs(module="", date_from="", date_to=""):
    """Audit entries, newest first. Blank filters are ignored; both dates are inclusive."""
    query = (db.session.query(AuditLog, User.username)
             .outerjoin(User, AuditLog.user_id == User.id))
    start = _parse_date(date_from, "from") if date_from else None
    end = _parse_date(date_to, "to") if date_to else None
    if start and end and start > end:
        raise ApiError(400, "invalid_field", "from must be on or before to")
    if module:
        query = query.filter(AuditLog.record_type == module)
    if start:
        query = query.filter(AuditLog.timestamp >= start)
    if end:
        query = query.filter(AuditLog.timestamp < end + timedelta(days=1))
    rows = query.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).all()
    return [{"id": log.id, "actor": username or "system", "action": log.action,
             "recordType": log.record_type, "recordId": log.record_id,
             "timestamp": log.timestamp.isoformat(timespec="seconds")}
            for log, username in rows]


@bp.get("/audit-logs")
@require_role("admin")
def list_logs():
    args = request.args
    return jsonify(logs=find_logs(args.get("module", "").strip(),
                                  args.get("from", "").strip(),
                                  args.get("to", "").strip()))


@bp.get("/ui/admin/audit")
@require_role("admin")
def audit_page():
    filters = {"module": request.args.get("module", "").strip(),
               "date_from": request.args.get("from", "").strip(),
               "date_to": request.args.get("to", "").strip()}
    modules = [m for (m,) in db.session.query(AuditLog.record_type).distinct()
               .order_by(AuditLog.record_type)]
    return render_template("auditlog/audit.html", filters=filters, modules=modules,
                           logs=find_logs(filters["module"], filters["date_from"],
                                          filters["date_to"]))
