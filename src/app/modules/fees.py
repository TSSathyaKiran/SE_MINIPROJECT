"""Fee visibility (Sathya): issue #4. Details in docs/TEAM_GUIDE.md.

  GET /fees/<studentId>       own student, admin   {amountDue, amountPaid, balance, overdue, history:[...]}
  GET /ui/student/fees        student page (read-only)
  plus: block enrollment when overdue balance > fee_threshold setting (in enrollment.py)
"""
from flask import Blueprint

from ..core import clock
from ..models import Fee

bp = Blueprint("fees", __name__)


def unpaid(fee):
    return max(fee.amount_due - (fee.amount_paid or 0), 0)


def is_overdue(fee):
    """Marked overdue, or past its due date, and not fully paid."""
    return unpaid(fee) > 0 and (fee.status == "overdue" or fee.due_date < clock.today())


def overdue_balance(student_id):
    """What the student still owes on overdue fees; enrollment compares it to fee_threshold."""
    fees = Fee.query.filter_by(student_id=student_id).all()
    return round(sum(unpaid(fee) for fee in fees if is_overdue(fee)), 2)
