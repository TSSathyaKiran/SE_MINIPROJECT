"""Fees: TC-Fee-01 (issue #4)."""
from datetime import date, datetime

from app.core import clock
from app.extensions import db
from app.models import Fee


def add_fee(student, description, due, paid, due_date, status):
    db.session.add(Fee(student_id=student.id, description=description, amount_due=due,
                       amount_paid=paid, due_date=due_date, status=status))
    db.session.commit()


def seed_fees(student):
    """Like seed.py: one paid fee, one half paid and not due yet, one overdue."""
    add_fee(student, "Tuition 2025-EVEN", 50000, 50000, date(2026, 1, 15), "paid")
    add_fee(student, "Tuition 2026-ODD", 50000, 25000, date(2026, 12, 15), "due")
    add_fee(student, "Library fine", 2000, 500, date(2026, 9, 1), "overdue")


# ---- TC-Fee-01: balance and payment-status history ----

def test_tc_fee_01_student_sees_balance_and_history(client, login_as):
    clock.set_now(datetime(2026, 11, 5, 10, 0))
    user, headers = login_as("student")
    seed_fees(user.student)
    res = client.get(f"/fees/{user.student.id}", headers=headers)
    assert res.status_code == 200
    assert (res.json["amountDue"], res.json["amountPaid"]) == (102000, 75500)
    assert res.json["balance"] == 26500
    assert res.json["overdue"] == 1500
    assert [(h["description"], h["amountDue"], h["amountPaid"], h["dueDate"], h["status"])
            for h in res.json["history"]] == [
        ("Tuition 2025-EVEN", 50000, 50000, "2026-01-15", "paid"),
        ("Library fine", 2000, 500, "2026-09-01", "overdue"),
        ("Tuition 2026-ODD", 50000, 25000, "2026-12-15", "due"),
    ]


def test_tc_fee_01_unpaid_fee_past_due_date_counts_as_overdue(client, login_as):
    clock.set_now(datetime(2026, 11, 5, 10, 0))
    user, headers = login_as("student")
    add_fee(user.student, "Hostel", 3000, 0, date(2026, 11, 1), "due")
    add_fee(user.student, "Exam fee", 1000, 1000, date(2026, 10, 1), "due")
    res = client.get(f"/fees/{user.student.id}", headers=headers)
    assert res.json["overdue"] == 3000
    assert [h["status"] for h in res.json["history"]] == ["due", "overdue"]


def test_tc_fee_01_student_without_fees_gets_zeros(client, login_as):
    user, headers = login_as("student")
    res = client.get(f"/fees/{user.student.id}", headers=headers)
    assert res.status_code == 200
    assert res.json == {"amountDue": 0, "amountPaid": 0, "balance": 0, "overdue": 0,
                        "history": []}


def test_tc_fee_01_admin_can_view_any_student(client, login_as):
    user, _ = login_as("student")
    seed_fees(user.student)
    _, admin = login_as("admin")
    res = client.get(f"/fees/{user.student.id}", headers=admin)
    assert res.status_code == 200
    assert len(res.json["history"]) == 3


def test_tc_fee_01_other_users_get_403_and_unknown_404(client, login_as):
    owner, _ = login_as("student")
    _, other_student = login_as("student")
    _, faculty = login_as("faculty")
    _, admin = login_as("admin")
    url = f"/fees/{owner.student.id}"
    assert client.get(url, headers=other_student).status_code == 403
    assert client.get(url, headers=faculty).status_code == 403
    assert client.get(url).status_code == 401
    assert client.get("/fees/9999", headers=admin).status_code == 404


def test_tc_fee_01_fees_are_read_only(client, login_as):
    user, headers = login_as("student")
    url = f"/fees/{user.student.id}"
    for method in (client.post, client.put, client.delete):
        assert method(url, json={"amountPaid": 0}, headers=headers).status_code == 405
