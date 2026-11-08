"""Tests for the ops scripts: uptime check, backup and restore.

TC-Ops-01: uptime check logs time,status and a backup restores intact.
TC-Ops-02: restore keeps every record (nothing deleted) and the retention
rule is documented in docs/ops/OPERATIONS.md.

The scripts are plain files in scripts/, so import them by path.
"""
import csv
import importlib.util
import sqlite3
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parent.parent


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


uptime_check = load_script("uptime_check")
backup = load_script("backup")


@pytest.fixture
def live_server(app):
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()


def make_db(path):
    """A minimal SRS database file with one student and one audit log row."""
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE students (
        id INTEGER PRIMARY KEY, student_no TEXT UNIQUE NOT NULL,
        user_id INTEGER, name TEXT NOT NULL, email TEXT NOT NULL,
        phone TEXT, address TEXT, program TEXT NOT NULL,
        semester INTEGER NOT NULL, status TEXT DEFAULT 'active')""")
    con.execute("""CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT NOT NULL,
        record_type TEXT NOT NULL, record_id TEXT NOT NULL,
        timestamp TEXT NOT NULL)""")
    con.execute("INSERT INTO students (student_no, name, email, program, semester) "
                "VALUES ('S9001', 'Test Student', 't@test.edu', 'B.Tech CSE', 3)")
    con.execute("INSERT INTO audit_logs (user_id, action, record_type, record_id, timestamp) "
                "VALUES (1, 'create', 'student', '1', '2026-11-06 10:00:00')")
    con.commit()
    con.close()
    return path


# TC-Ops-01: uptime check

def test_check_health_ok_and_down(live_server):
    assert uptime_check.check_health(live_server) is True
    assert uptime_check.check_health("http://127.0.0.1:1") is False  # nothing listening


def test_uptime_log_rows_and_availability(tmp_path):
    log = tmp_path / "uptime.csv"
    uptime_check.append_row(log, True)
    uptime_check.append_row(log, False)
    with open(log) as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["time", "status"]
    assert [r[1] for r in rows[1:]] == ["ok", "down"]
    assert uptime_check.availability(2, 1) == 50.0
    assert uptime_check.availability(0, 0) == 0.0


# TC-Ops-01 / TC-Ops-02: backup and restore keep students and audit logs

def test_restored_backup_keeps_students_and_audit_logs(tmp_path):
    db_path = make_db(tmp_path / "srs.db")
    out = backup.backup_sqlite(str(db_path), tmp_path / "backup.db")

    con = sqlite3.connect(db_path)
    con.execute("DELETE FROM students")
    con.execute("DELETE FROM audit_logs")
    con.commit()
    con.close()

    backup.restore_sqlite(str(out), str(db_path))
    con = sqlite3.connect(db_path)
    students = con.execute("SELECT student_no, name FROM students").fetchall()
    audits = con.execute("SELECT action, record_type FROM audit_logs").fetchall()
    con.close()
    assert students == [("S9001", "Test Student")]
    assert audits == [("create", "student")]


def test_restore_rejects_a_file_that_is_not_a_database(tmp_path):
    bad = tmp_path / "bad.db"
    bad.write_text("not a database")
    with pytest.raises(SystemExit):
        backup.restore_sqlite(str(bad), str(tmp_path / "srs.db"))


def test_mysql_prints_dump_and_restore_commands():
    url = "mysql://srs:secret@db.example.com:3307/srsdb"
    assert backup.mysql_commands(url, "backup", "dump.sql") == \
        "mysqldump -h db.example.com -P 3307 -u srs -p srsdb > dump.sql"
    assert backup.mysql_commands(url, "restore", "dump.sql") == \
        "mysql -h db.example.com -P 3307 -u srs -p srsdb < dump.sql"


# TC-Ops-02: the retention rule is written down

def test_retention_rule_documented():
    doc = (ROOT / "docs" / "ops" / "OPERATIONS.md").read_text()
    assert "7 years" in doc
    assert "no job ever deletes" in doc.lower()
