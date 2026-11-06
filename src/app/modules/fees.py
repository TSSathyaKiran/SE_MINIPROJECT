"""Fee visibility (Sathya): issue #4. Details in docs/TEAM_GUIDE.md.

  GET /fees/<studentId>       own student, admin   {amountDue, amountPaid, balance, overdue, history:[...]}
  GET /ui/student/fees        student page (read-only)
  plus: block enrollment when overdue balance > fee_threshold setting (in enrollment.py)
"""
from flask import Blueprint, jsonify, render_template

from ..core import clock
from ..core.errors import ApiError
from ..core.security import current_user, require_login, require_role
from ..extensions import db
from ..models import Fee, Student

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


def fee_summary(student_id):
    """Totals and history for one student, oldest due date first."""
    fees = Fee.query.filter_by(student_id=student_id).order_by(Fee.due_date, Fee.id).all()
    amount_due = sum(fee.amount_due for fee in fees)
    amount_paid = sum(fee.amount_paid or 0 for fee in fees)
    return {"amountDue": round(amount_due, 2), "amountPaid": round(amount_paid, 2),
            "balance": round(amount_due - amount_paid, 2),
            "overdue": overdue_balance(student_id),
            "history": [{"description": fee.description, "amountDue": fee.amount_due,
                         "amountPaid": fee.amount_paid or 0,
                         "dueDate": fee.due_date.isoformat(),
                         # a "due" fee past its date is shown as overdue
                         "status": "overdue" if is_overdue(fee) else fee.status}
                        for fee in fees]}


@bp.get("/fees/<int:student_id>")
@require_login
def get_fees(student_id):
    user = current_user()
    if user.role == "student":
        if user.student is None or user.student.id != student_id:
            raise ApiError(403, "forbidden", "You can only view your own fees")
    elif user.role != "admin":
        raise ApiError(403, "forbidden", "Only the student or an admin can view fees")
    if db.session.get(Student, student_id) is None:
        raise ApiError(404, "not_found", "Student not found")
    return jsonify(fee_summary(student_id))


@bp.get("/ui/student/fees")
@require_role("student")
def fees_page():
    """Read-only: no pay or edit controls, payments happen outside the system."""
    student = current_user().student
    if student is None:
        raise ApiError(403, "forbidden", "This account has no student record")
    return render_template("fees/fees.html", fees=fee_summary(student.id))
