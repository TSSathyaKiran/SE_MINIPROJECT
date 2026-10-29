"""Fee visibility (Sathya): issue #4. Details in docs/TEAM_GUIDE.md.

  GET /fees/<studentId>       own student, admin   {amountDue, amountPaid, balance, overdue, history:[...]}
  GET /ui/student/fees        student page (read-only)
  plus: block enrollment when overdue balance > fee_threshold setting (in enrollment.py)
"""
from flask import Blueprint

bp = Blueprint("fees", __name__)
