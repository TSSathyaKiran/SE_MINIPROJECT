"""Audit log viewer (Sathya): issue #3. Details in docs/TEAM_GUIDE.md.
Writing entries is already done: core/audit.py.

  GET /audit-logs             admin   ?module=&from=&to=   {logs:[{actor, action, recordType, recordId, timestamp}]}
  GET /ui/admin/audit         admin page with filters
  plus: audit rows can never be updated or deleted (SRS-SR-006)
"""
from flask import Blueprint

bp = Blueprint("auditlog", __name__)
