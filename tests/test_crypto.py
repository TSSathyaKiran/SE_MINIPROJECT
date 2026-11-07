import pytest
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.core.crypto import decrypt, encrypt
from app.extensions import db
from app.models import Student

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
