"""Encrypt student email, phone and address saved before PII encryption (issue #5):
    python src/encrypt_pii.py

Unlike seed.py this keeps every record. It is safe to run more than once: values
already encrypted with PII_KEY are left as they are. Back up first; the steps are in
docs/security/PII_CHECKLIST.md under "Existing databases".
"""
from cryptography.fernet import InvalidToken
from sqlalchemy import text

from app import create_app
from app.core.crypto import decrypt, encrypt
from app.extensions import db

FIELDS = ("email", "phone", "address")
UPDATE = text("UPDATE students SET email = :email, phone = :phone, address = :address "
              "WHERE id = :id")


def encrypted(value):
    """The value encrypted with PII_KEY; empty or already encrypted values stay as they are."""
    if value is None:
        return None
    try:
        decrypt(value)
        return value
    except InvalidToken:
        if value.startswith("gAAAAA"):          # ciphertext, but made with another key
            raise RuntimeError("Some student data is encrypted with a different PII_KEY. "
                               "Nothing was changed; set the key it was made with.") from None
        return encrypt(value)


def encrypt_existing():
    """Encrypt plain-text PII in place, in one transaction. Returns (changed, total)."""
    rows = db.session.execute(text("SELECT id, email, phone, address FROM students")).all()
    updates = []
    for row in rows:                            # check every row before writing any
        values = {field: encrypted(getattr(row, field)) for field in FIELDS}
        if any(values[field] != getattr(row, field) for field in FIELDS):
            updates.append({**values, "id": row.id})
    if updates:
        db.session.execute(UPDATE, updates)
    db.session.commit()
    if updates and db.engine.dialect.name == "sqlite":
        # SQLite keeps the old plain-text bytes in free space until VACUUM rewrites the file
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("VACUUM"))
    return len(updates), len(rows)


if __name__ == "__main__":
    with create_app("dev").app_context():
        changed, total = encrypt_existing()
    print(f"Encrypted {changed} of {total} student records; the others were already encrypted.")
