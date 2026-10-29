"""Shared test fixtures. Every test gets a fresh, empty in-memory database.

    def test_something(client, login_as, add_user):
        admin, headers = login_as("admin")             # creates + logs in an admin
        res = client.post("/terms", json={"name": "2026-ODD"}, headers=headers)

        student, student_headers = login_as("student")  # student.student is the Student row
        faculty = add_user("prof", "faculty")           # just create, no login

`client` itself is never logged in, so requests without headers are anonymous.
To test time-based rules, call clock.set_now(datetime(...)) (reset after each test).
"""
import pytest

from app import create_app
from app.core import clock
from app.core.security import hash_password
from app.extensions import db
from app.models import Student, User

PASSWORD = "pass1234"


@pytest.fixture
def app():
    app = create_app("test")
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()
    clock.set_now(None)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def add_user(app):
    def _add_user(username, role, password=PASSWORD):
        user = User(username=username, password_hash=hash_password(password),
                    name=username.title(), role=role)
        db.session.add(user)
        db.session.flush()
        if role == "student":
            db.session.add(Student(student_no=f"S{9000 + user.id}", user_id=user.id,
                                   name=user.name, email=f"{username}@test.edu",
                                   program="B.Tech CSE", semester=3))
        db.session.commit()
        return user
    return _add_user


@pytest.fixture
def login_as(app, add_user):
    count = {"n": 0}

    def _login_as(role, username=None):
        count["n"] += 1
        user = add_user(username or f"{role}{count['n']}", role)
        res = app.test_client().post("/auth/login",
                                     json={"username": user.username, "password": PASSWORD})
        assert res.status_code == 200, res.json
        return user, {"Authorization": f"Bearer {res.json['token']}"}
    return _login_as
