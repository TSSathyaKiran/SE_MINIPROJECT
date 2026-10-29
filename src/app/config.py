import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    # Relative SQLite paths live in src/instance/. Set DATABASE_URL for MySQL.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///srs.db")
    PII_KEY = os.getenv("PII_KEY")
    SESSION_IDLE_MINUTES = 15  # SRS-SR-005
    BCRYPT_ROUNDS = 12


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory, fresh for every test
    BCRYPT_ROUNDS = 4                      # fast hashing in tests only


CONFIGS = {"dev": Config, "test": TestConfig}
