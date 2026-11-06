"""Fees: TC-Fee-01 and TC-Fee-02 (issue #4)."""
from datetime import date, datetime

from app.core import clock
from app.extensions import db
from app.models import Course, Enrollment, Fee, Section, Term


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


def test_tc_fee_01_fee_page_shows_records_without_pay_controls(client, login_as):
    clock.set_now(datetime(2026, 11, 5, 10, 0))
    user, headers = login_as("student")
    seed_fees(user.student)
    res = client.get("/ui/student/fees", headers=headers)
    assert res.status_code == 200
    page = res.data.decode()
    for text in ("Tuition 2025-EVEN", "Library fine", "₹102,000.00",
                 "₹26,500.00", "₹1,500.00", "outside this system"):
        assert text in page, text
    main = page[page.index("<main"):page.index("</main>")]
    for control in ("<form", "<button", "<input"):  # read-only: nothing to pay or edit
        assert control not in main, control


def test_fee_page_is_for_students_only(client, login_as):
    _, admin = login_as("admin")
    assert client.get("/ui/student/fees", headers=admin).status_code == 403
    assert client.get("/ui/student/fees").status_code == 302      # sent to the login page


def test_fee_page_is_live_in_student_menu(client, login_as):
    _, headers = login_as("student")
    assert b'href="/ui/student/fees"' in client.get("/ui/student", headers=headers).data


# ---- TC-Fee-02: enrollment blocked above the overdue threshold ----
# Set the clock BEFORE login_as: moving it later would end the 15-minute session.

def open_section(code="CS150"):
    term = Term(name="2026-ODD")
    course = Course(code=code, name=code, credits=4)
    db.session.add_all([term, course])
    db.session.flush()
    section = Section(course_id=course.id, term_id=term.id, name="A", capacity=30)
    db.session.add(section)
    db.session.commit()
    return section


def setup_overdue(login_as, client, overdue, threshold=5000):
    """Admin sets the threshold; a student owes `overdue` on a fee past its due date."""
    clock.set_now(datetime(2026, 11, 6, 9, 0))
    _, admin = login_as("admin")
    assert client.put("/admin/config", json={"feeThreshold": threshold},
                      headers=admin).status_code == 200
    user, headers = login_as("student")
    add_fee(user.student, "Tuition 2025-EVEN", 50000, 50000 - overdue,
            date(2026, 1, 15), "overdue")
    return admin, user, headers


def test_tc_fee_02_overdue_above_threshold_blocks_enrollment(client, login_as):
    _, user, headers = setup_overdue(login_as, client, overdue=10000)
    res = client.post("/enroll", json={"sectionId": open_section().id}, headers=headers)
    assert res.status_code == 409
    assert res.json["error"]["code"] == "fees_overdue"
    assert "overdue fees" in res.json["error"]["message"]
    assert Enrollment.query.filter_by(student_id=user.student.id).count() == 0


def test_tc_fee_02_balance_reduced_below_threshold_allows_enrollment(client, login_as):
    _, user, headers = setup_overdue(login_as, client, overdue=10000)
    section = open_section()
    assert client.post("/enroll", json={"sectionId": section.id}, headers=headers).status_code == 409
    fee = Fee.query.filter_by(student_id=user.student.id).one()
    fee.amount_paid = 46000                         # 4,000 still overdue, under 5,000
    db.session.commit()
    assert client.post("/enroll", json={"sectionId": section.id}, headers=headers).status_code == 201


def test_tc_fee_02_changed_threshold_takes_effect(client, login_as):
    admin, _, headers = setup_overdue(login_as, client, overdue=10000)
    section = open_section()
    assert client.post("/enroll", json={"sectionId": section.id}, headers=headers).status_code == 409
    assert client.put("/admin/config", json={"feeThreshold": 20000},
                      headers=admin).status_code == 200
    assert client.post("/enroll", json={"sectionId": section.id}, headers=headers).status_code == 201


def test_tc_fee_02_overdue_equal_to_threshold_is_allowed(client, login_as):
    _, _, headers = setup_overdue(login_as, client, overdue=5000)
    res = client.post("/enroll", json={"sectionId": open_section().id}, headers=headers)
    assert res.status_code == 201


def test_tc_fee_02_fees_not_yet_due_do_not_block(client, login_as):
    clock.set_now(datetime(2026, 11, 6, 9, 0))
    user, headers = login_as("student")
    add_fee(user.student, "Tuition 2026-ODD", 50000, 0, date(2026, 12, 15), "due")
    res = client.post("/enroll", json={"sectionId": open_section().id}, headers=headers)
    assert res.status_code == 201
