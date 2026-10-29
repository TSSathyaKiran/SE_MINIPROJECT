"""Reset the database and load demo data:  python src/seed.py

WARNING: deletes everything in the database first.
Add demo rows for your own feature at the end of seed() if you need them.
"""
from datetime import date

from app import create_app
from app.core.security import hash_password
from app.extensions import db
from app.models import (Course, Enrollment, Fee, Grade, Prerequisite, Section, Student,
                        Term, User)

ACCOUNTS = [  # username, password, name, role
    ("admin", "admin123", "Admin User", "admin"),
    ("faculty1", "faculty123", "Dr. Rao", "faculty"),
    ("faculty2", "faculty123", "Dr. Mehta", "faculty"),
    ("student1", "student123", "Asha Kumar", "student"),
    ("student2", "student123", "Ravi Shah", "student"),
    ("student3", "student123", "Neha Iyer", "student"),
]


def seed():
    db.drop_all()
    db.create_all()

    users = {}
    for username, password, name, role in ACCOUNTS:
        users[username] = User(username=username, password_hash=hash_password(password),
                               name=name, role=role)
        db.session.add(users[username])
    db.session.flush()

    students = {}
    for i, username in enumerate(["student1", "student2", "student3"], start=1):
        user = users[username]
        students[username] = Student(
            student_no=f"S100{i}", user_id=user.id, name=user.name,
            email=f"{username}@example.edu", phone=f"98450000{i:02d}",
            address=f"{i} MG Road, Bengaluru", program="B.Tech CSE", semester=3)
        db.session.add(students[username])

    past, current = Term(name="2025-EVEN"), Term(name="2026-ODD")
    courses = {code: Course(code=code, name=name, credits=credits) for code, name, credits in [
        ("CS101", "Programming in C", 4), ("MA101", "Engineering Mathematics", 3),
        ("CS102", "Data Structures", 4), ("CS201", "Database Systems", 4),
        ("EC101", "Basic Electronics", 3)]}
    db.session.add_all([past, current, *courses.values()])
    db.session.flush()
    db.session.add_all([
        Prerequisite(course_id=courses["CS102"].id, requires_course_id=courses["CS101"].id),
        Prerequisite(course_id=courses["CS201"].id, requires_course_id=courses["CS102"].id),
    ])

    def section(code, term, faculty, capacity):
        s = Section(course_id=courses[code].id, term_id=term.id, name="A",
                    faculty_id=users[faculty].id, capacity=capacity)
        db.session.add(s)
        return s

    cs101_old, ma101_old = section("CS101", past, "faculty1", 40), section("MA101", past, "faculty2", 40)
    cs102 = section("CS102", current, "faculty1", 30)
    section("CS201", current, "faculty2", 30)
    section("EC101", current, "faculty1", 1)   # tiny section to demo "full"
    db.session.flush()

    # Completed term with final grades (transcript, prerequisites, CGPA)
    for username, results in [("student1", [(cs101_old, "A+", 9), (ma101_old, "A", 8)]),
                              ("student2", [(cs101_old, "B+", 7), (ma101_old, "F", 0)])]:
        for sec, letter, point in results:
            db.session.add(Enrollment(student_id=students[username].id, section_id=sec.id))
            db.session.add(Grade(student_id=students[username].id, section_id=sec.id,
                                 grade=letter, grade_point=point))
    # Current term: student1 and student2 take Data Structures; student3 has no CS101
    for username in ["student1", "student2"]:
        db.session.add(Enrollment(student_id=students[username].id, section_id=cs102.id))

    db.session.add_all([
        Fee(student_id=students["student1"].id, description="Tuition 2025-EVEN",
            amount_due=50000, amount_paid=50000, due_date=date(2026, 1, 15), status="paid"),
        Fee(student_id=students["student1"].id, description="Tuition 2026-ODD",
            amount_due=50000, amount_paid=25000, due_date=date(2026, 12, 15), status="due"),
        Fee(student_id=students["student2"].id, description="Tuition 2025-EVEN",
            amount_due=50000, amount_paid=40000, due_date=date(2026, 1, 15), status="overdue"),
    ])
    db.session.commit()


if __name__ == "__main__":
    with create_app("dev").app_context():
        seed()
    print("Database reset. Log in with:")
    for username, password, _, role in ACCOUNTS:
        print(f"  {role:8} {username} / {password}")
