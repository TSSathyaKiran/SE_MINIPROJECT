import pytest
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app import create_app
from app.config import Config, TestConfig, check_keys
from app.core.crypto import decrypt, encrypt
from app.extensions import db
from app.models import Student
from encrypt_pii import encrypt_existing

PII = {"email": "asha.rao@example.edu", "phone": "9845012345",
       "address": "12 MG Road, Bengaluru"}


def save_student(client, admin, **pii):
    res = client.post("/students", json={"name": "Asha Rao", "email": PII["email"],
                                         "program": "B.Tech CSE", "semester": 3,
                                         "password": "pass1234"}, headers=admin)
    assert res.status_code == 201
    if pii:
        assert client.put(f"/students/{res.json['id']}", json=pii,
                          headers=admin).status_code == 200
    return res.json["id"]


def raw_row(student_id):
    """The PII columns exactly as stored, read with plain SQL like a database dump."""
    return db.session.execute(
        text("SELECT email, phone, address FROM students WHERE id = :id"),
        {"id": student_id}).one()


# ---- TC-Sec-05: PII encrypted at rest ----

def test_tc_sec_05_pii_unreadable_in_database(client, login_as):
    _, admin = login_as("admin")
    student_id = save_student(client, admin, phone=PII["phone"], address=PII["address"])
    stored = raw_row(student_id)
    dump = " ".join(stored)
    for value in PII.values():
        assert value not in dump
    assert all(column.startswith("gAAAAA") for column in stored)   # Fernet tokens


def test_tc_sec_05_app_still_sees_plain_text(client, login_as):
    _, admin = login_as("admin")
    student_id = save_student(client, admin, phone=PII["phone"], address=PII["address"])
    db.session.expire_all()                                         # read back from the database
    student = db.session.get(Student, student_id)
    assert {"email": student.email, "phone": student.phone,
            "address": student.address} == PII
    res = client.get(f"/students/{student_id}", headers=admin)
    assert {field: res.json[field] for field in PII} == PII


def test_tc_sec_05_empty_phone_and_address_stay_empty(client, login_as):
    _, admin = login_as("admin")
    stored = raw_row(save_student(client, admin))
    assert stored.phone is None and stored.address is None


def test_tc_sec_05_same_value_encrypts_differently(app):
    first, second = encrypt(PII["phone"]), encrypt(PII["phone"])
    assert first != second                                          # random IV each time
    assert decrypt(first) == decrypt(second) == PII["phone"]


def test_tc_sec_05_pii_key_is_used_and_other_keys_cannot_read(app):
    key = Fernet.generate_key()
    app.config["PII_KEY"] = key.decode()
    token = encrypt(PII["phone"])
    assert Fernet(key).decrypt(token.encode()).decode() == PII["phone"]

    app.config["PII_KEY"] = Fernet.generate_key().decode()
    with pytest.raises(InvalidToken):
        decrypt(token)



# ---- TC-Sec-05: the app will not start on missing or public keys ----

REAL_SECRET = "3f9c" * 16
REAL_PII_KEY = Fernet.generate_key().decode()


@pytest.mark.parametrize("secret, pii_key, bad", [
    (None, REAL_PII_KEY, ["SECRET_KEY"]),
    ("change-me", REAL_PII_KEY, ["SECRET_KEY"]),            # the old .env.example value
    ("dev-only-change-me", REAL_PII_KEY, ["SECRET_KEY"]),   # the old built-in default
    (REAL_SECRET, None, ["PII_KEY"]),
    (REAL_SECRET, "not-a-fernet-key", ["PII_KEY"]),
    (None, None, ["SECRET_KEY", "PII_KEY"]),
])
def test_tc_sec_05_app_refuses_to_start_without_real_keys(monkeypatch, secret, pii_key, bad):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch.setattr(Config, "SECRET_KEY", secret)
    monkeypatch.setattr(Config, "PII_KEY", pii_key)
    with pytest.raises(RuntimeError, match="Cannot start: " + " and ".join(bad)) as error:
        create_app("dev")
    for name in bad:
        assert f"\n{name}=" in str(error.value)                # a fresh key to paste into .env


def test_tc_sec_05_real_keys_are_accepted():
    check_keys({"SECRET_KEY": REAL_SECRET, "PII_KEY": REAL_PII_KEY})


# ---- TC-Sec-01: no PII in error messages, URLs or the audit log ----

def test_tc_sec_01_error_messages_never_include_pii(client, login_as):
    _, admin = login_as("admin")
    student_id = save_student(client, admin, phone=PII["phone"], address=PII["address"])
    student_no = db.session.get(Student, student_id).student_no
    token = client.post("/auth/login", json={"username": student_no.lower(),
                                             "password": "pass1234"}).json["token"]
    own = {"Authorization": f"Bearer {token}"}
    _, other = login_as("student")

    errors = [
        client.post("/students", json={"studentNo": student_no, "name": "Asha Rao",       # 409
                                       "email": PII["email"], "program": "B.Tech CSE",
                                       "semester": 3, "password": "pass1234"}, headers=admin),
        client.put(f"/students/{student_id}", json={"email": PII["email"],                # 400
                                                     "semester": "third"}, headers=admin),
        client.put(f"/students/{student_id}", json={"phone": PII["phone"],                # 400
                                                     "nickname": "Ash"}, headers=admin),
        client.put(f"/students/{student_id}", json={"email": PII["email"]}, headers=own),  # 400
        client.put(f"/students/{student_id}", json={"address": PII["address"]},           # 403
                   headers=other),
        client.get(f"/students/{student_id}", headers=other),                             # 403
    ]
    assert [res.status_code for res in errors] == [409, 400, 400, 400, 403, 403]
    for res in errors:
        body = res.get_data(as_text=True)
        assert not [value for value in PII.values() if value in body], body


def test_tc_sec_01_urls_never_carry_pii(app):
    """Routes find a student by numeric id, never by email, phone or address."""
    for rule in app.url_map.iter_rules():
        assert not rule.arguments & set(PII), rule.rule


def test_tc_sec_01_audit_log_holds_no_pii(client, login_as):
    _, admin = login_as("admin")
    save_student(client, admin, phone=PII["phone"], address=PII["address"])
    rows = db.session.execute(text("SELECT * FROM audit_logs")).all()
    assert len(rows) == 2                                           # create + update
    dump = " ".join(str(value) for row in rows for value in row)
    assert not [value for value in PII.values() if value in dump]


# ---- Existing databases: src/encrypt_pii.py encrypts old records and keeps them ----

def insert_plain_student(student_no, email, phone=None, address=None):
    """A student row as saved before encryption: plain text, written with plain SQL."""
    db.session.execute(text(
        "INSERT INTO students (student_no, name, email, phone, address, program, semester, status) "
        "VALUES (:no, 'Old Record', :email, :phone, :address, 'B.Tech CSE', 3, 'active')"),
        {"no": student_no, "email": email, "phone": phone, "address": address})
    db.session.commit()


def raw_emails():
    return dict(db.session.execute(text("SELECT student_no, email FROM students")).all())


def test_tc_sec_05_encrypt_pii_keeps_and_encrypts_old_records(add_user):
    add_user("newer", "student")                                   # saved encrypted already
    insert_plain_student("S0001", **PII)
    insert_plain_student("S0002", "old.two@example.edu")
    assert encrypt_existing() == (2, 3)

    stored = db.session.execute(text("SELECT email, phone, address FROM students")).all()
    dump = " ".join(str(value) for row in stored for value in row)
    assert not [value for value in [*PII.values(), "old.two@example.edu"] if value in dump]
    db.session.expire_all()
    first = Student.query.filter_by(student_no="S0001").one()
    second = Student.query.filter_by(student_no="S0002").one()
    assert {"email": first.email, "phone": first.phone, "address": first.address} == PII
    assert (second.email, second.phone, second.address) == ("old.two@example.edu", None, None)
    assert encrypt_existing() == (0, 3)                             # safe to run again


def test_tc_sec_05_encrypt_pii_changes_nothing_if_another_key_was_used(app, add_user):
    insert_plain_student("S0001", "old.one@example.edu")
    add_user("newer", "student")                                   # encrypted with the old key
    app.config["PII_KEY"] = Fernet.generate_key().decode()
    with pytest.raises(RuntimeError, match="different PII_KEY"):
        encrypt_existing()
    assert raw_emails()["S0001"] == "old.one@example.edu"           # left exactly as it was


def test_tc_sec_05_encrypt_pii_leaves_no_plain_text_in_the_file(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    monkeypatch.setattr(TestConfig, "SQLALCHEMY_DATABASE_URI", f"sqlite:///{path}")
    with create_app("test").app_context():
        for student_no in ("S0001", "S0002", "S0003"):
            insert_plain_student(student_no, **PII)
        assert PII["email"].encode() in path.read_bytes()
        encrypt_existing()
        db.session.remove()
        db.engine.dispose()
    data = path.read_bytes()                                        # the raw file, like a dump
    assert not [value for value in PII.values() if value.encode() in data]
