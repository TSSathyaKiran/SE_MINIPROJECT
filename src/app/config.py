import os
import secrets

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Values that have been in this repo as examples; they are public, so never valid keys.
EXAMPLE_SECRETS = {"change-me", "dev-only-change-me"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")   # required, see check_keys()
    # Relative SQLite paths live in src/instance/. Set DATABASE_URL for MySQL.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///srs.db")
    PII_KEY = os.getenv("PII_KEY")         # required: encrypts student PII (SRS-SR-004)
    SESSION_IDLE_MINUTES = 15  # SRS-SR-005
    BCRYPT_ROUNDS = 12


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory, fresh for every test
    BCRYPT_ROUNDS = 4                      # fast hashing in tests only
    SECRET_KEY = secrets.token_hex(32)     # fresh keys each run: nothing outlives a test
    PII_KEY = Fernet.generate_key().decode()


def check_keys(config):
    """Refuse to start with a missing or example SECRET_KEY, or a missing or invalid PII_KEY.

    Only TestConfig makes its own keys, so the app cannot run on public ones.
    """
    missing = {}
    secret = (config.get("SECRET_KEY") or "").strip()
    if not secret or secret in EXAMPLE_SECRETS:
        missing["SECRET_KEY"] = secrets.token_hex(32)
    try:
        Fernet(config.get("PII_KEY") or "")
    except ValueError:
        missing["PII_KEY"] = Fernet.generate_key().decode()
    if missing:
        raise RuntimeError(
            f"Cannot start: {' and '.join(missing)} must be set to a real key in .env.\n"
            "Add these lines to .env in the project folder (never commit that file):\n"
            + "\n".join(f"{name}={key}" for name, key in missing.items()))


CONFIGS = {"dev": Config, "test": TestConfig}
