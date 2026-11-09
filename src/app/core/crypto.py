"""Field-level encryption for student PII (SRS-SR-004).

    email = db.Column(EncryptedString, nullable=False)

The database only ever holds Fernet ciphertext (AES-128 + HMAC); the app reads
and writes plain text. The key is PII_KEY from .env; the app will not start without
it (config.check_keys). Changing the key makes existing rows unreadable.
"""
from cryptography.fernet import Fernet
from flask import current_app
from sqlalchemy.types import Text, TypeDecorator


def _fernet():
    return Fernet(current_app.config["PII_KEY"])


def encrypt(value):
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token):
    return _fernet().decrypt(token.encode()).decode()


class EncryptedString(TypeDecorator):
    """Text column stored encrypted. Text, because the ciphertext is longer than the value.

    Each save uses a fresh random IV, so the same value encrypts differently every
    time: filter_by() and LIKE searches on these columns cannot work.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else encrypt(value)

    def process_result_value(self, value, dialect):
        return None if value is None else decrypt(value)
