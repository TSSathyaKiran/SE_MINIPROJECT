from datetime import datetime, timedelta

from app.core import clock
from app.extensions import db
from app.models import AuditLog, AuthSession, User


def test_tc_auth_01_login_valid_and_invalid(client, add_user):
    add_user("asha", "student")

    res = client.post("/auth/login", json={"username": "asha", "password": "pass1234"})
    assert res.status_code == 200
    assert res.json["role"] == "student" and res.json["token"]
    assert "srs_token=" in res.headers["Set-Cookie"]
    assert "HttpOnly" in res.headers["Set-Cookie"]

    for body in [{"username": "asha", "password": "wrong"},
                 {"username": "nobody", "password": "pass1234"}]:
        res = client.post("/auth/login", json=body)
        assert res.status_code == 401
        assert res.json["error"]["code"] == "invalid_credentials"
    assert AuthSession.query.count() == 1     # only the valid login made a session


def test_login_requires_username_and_password(client):
    res = client.post("/auth/login", json={"username": "asha"})
    assert res.status_code == 400


def test_tc_sec_04_passwords_are_salted_hashes(add_user):
    a, b = add_user("one", "student"), add_user("two", "student")
    assert a.password_hash != b.password_hash          # same password, different salt
    assert a.password_hash.startswith("$2b$")          # bcrypt
    assert "pass1234" not in a.password_hash


def test_tc_auth_02_and_tc_sec_03_roles_enforced_on_api(client, login_as):
    _, student = login_as("student")
    _, faculty = login_as("faculty")
    _, admin = login_as("admin")

    assert client.post("/terms", json={"name": "T1"}).status_code == 401
    assert client.post("/terms", json={"name": "T1"}, headers=student).status_code == 403
    assert client.post("/terms", json={"name": "T1"}, headers=faculty).status_code == 403
    assert client.post("/terms", json={"name": "T1"}, headers=admin).status_code == 201


def test_tc_auth_02_dashboards_per_role(client, login_as):
    _, student = login_as("student")
    assert client.get("/ui/student", headers=student).status_code == 200
    assert client.get("/ui/admin", headers=student).status_code == 403
    assert client.get("/ui/faculty", headers=student).status_code == 403


def test_tc_sec_06_session_expires_after_15_idle_minutes(client, login_as):
    start = datetime(2026, 10, 20, 9, 0)
    clock.set_now(start)
    _, headers = login_as("admin")

    clock.set_now(start + timedelta(minutes=14))       # activity keeps it alive
    assert client.get("/terms", headers=headers).status_code == 200
    clock.set_now(start + timedelta(minutes=28))       # 14 min after last activity
    assert client.get("/terms", headers=headers).status_code == 200
    clock.set_now(start + timedelta(minutes=44))       # 16 min idle
    assert client.get("/terms", headers=headers).status_code == 401
    clock.set_now(start + timedelta(minutes=45))       # old token stays dead
    assert client.get("/terms", headers=headers).status_code == 401


def test_logout_ends_the_session(client, login_as):
    _, headers = login_as("admin")
    assert client.post("/auth/logout", headers=headers).status_code == 200
    assert client.get("/terms", headers=headers).status_code == 401
    assert client.post("/auth/logout", headers=headers).status_code == 401


def test_inactive_user_cannot_log_in_and_loses_session(client, login_as):
    user, headers = login_as("student")
    db.session.get(User, user.id).status = "inactive"
    db.session.commit()

    assert client.get("/terms", headers=headers).status_code == 401
    res = client.post("/auth/login", json={"username": user.username, "password": "pass1234"})
    assert res.status_code == 403


def _login(client, password):
    return client.post("/auth/login", json={"username": "asha", "password": password})


def test_tc_auth_03_lockout_after_5_failed_logins(client, add_user):
    clock.set_now(datetime(2026, 10, 20, 9, 0))
    user = add_user("asha", "student")

    for _ in range(5):
        assert _login(client, "wrong").status_code == 401
    res = _login(client, "pass1234")                   # 6th try, right password
    assert res.status_code == 423
    assert res.json["error"]["code"] == "account_locked"
    assert AuthSession.query.count() == 0

    log = AuditLog.query.filter_by(action="lock").one()
    assert (log.record_type, log.record_id, log.user_id) == ("user", str(user.id), user.id)


def test_lock_lifts_after_15_minutes(client, add_user):
    start = datetime(2026, 10, 20, 9, 0)
    clock.set_now(start)
    user = add_user("asha", "student")
    for _ in range(5):
        _login(client, "wrong")

    clock.set_now(start + timedelta(minutes=14))
    assert _login(client, "pass1234").status_code == 423
    clock.set_now(start + timedelta(minutes=15, seconds=1))
    assert _login(client, "pass1234").status_code == 200
    assert user.failed_logins == 0 and user.locked_until is None


def test_successful_login_resets_failed_count(client, add_user):
    add_user("asha", "student")
    for _ in range(4):
        _login(client, "wrong")
    assert _login(client, "pass1234").status_code == 200
    for _ in range(4):
        _login(client, "wrong")
    assert _login(client, "pass1234").status_code == 200   # 8 failures, never 5 in a row
    assert AuditLog.query.filter_by(action="lock").count() == 0


def test_non_string_login_fields_are_a_failed_login(client, add_user):
    user = add_user("asha", "student")
    for body in [{"username": "asha", "password": 123},
                 {"username": "asha", "password": None},
                 {"username": 5, "password": "pass1234"},
                 {"username": ["asha"], "password": "pass1234"}]:
        res = client.post("/auth/login", json=body)
        assert res.status_code == 401
        assert res.json["error"]["code"] == "invalid_credentials"
    assert user.failed_logins == 2                     # the two bad passwords for asha
