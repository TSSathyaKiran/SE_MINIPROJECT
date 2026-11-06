#!/usr/bin/env python3
"""Backup and restore the SRS database (SRS-NF-004, TC-Ops-01).

SQLite (the default): a consistent copy made with sqlite3's online backup
API, safe to run while the app is up.
MySQL (DATABASE_URL=mysql...): prints the mysqldump / mysql commands to run.

    python scripts/backup.py backup                       # backups/srs-<timestamp>.db
    python scripts/backup.py backup path/to/file.db
    python scripts/backup.py restore backups/srs-<timestamp>.db

Restore validates the backup file first and keeps a .pre-restore copy of
the current database next to it, so a bad restore can be undone by hand.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "src" / "instance" / "srs.db"


def database_url():
    """The URL the app uses: DATABASE_URL, else the default SQLite file."""
    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB}")


def sqlite_path(url):
    """Filesystem path for a sqlite:/// URL. Relative paths live in
    src/instance/, matching the Flask app config."""
    path = url[len("sqlite:///"):]
    p = Path(path)
    return p if p.is_absolute() else ROOT / "src" / "instance" / path


def is_sqlite(url):
    return url.startswith("sqlite:///") or url == "sqlite://"


def mysql_commands(url, action, file):
    """The mysqldump / mysql commands for a mysql:// URL."""
    u = urlparse(url)
    base = f"-h {u.hostname} -P {u.port or 3306} -u {u.username} -p"
    name = u.path.lstrip("/")
    if action == "backup":
        return f"mysqldump {base} {name} > {file}"
    return f"mysql {base} {name} < {file}"


def check_sqlite_file(path):
    """Raise SystemExit unless path is a valid, intact SQLite database."""
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise SystemExit(f"error: {path} failed SQLite integrity_check")
    except sqlite3.DatabaseError as exc:
        raise SystemExit(f"error: {path} is not a SQLite database ({exc})")


def backup_sqlite(db_path, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as src, sqlite3.connect(out) as dst:
        src.backup(dst)
    return out


def restore_sqlite(backup_file, db_path):
    check_sqlite_file(backup_file)
    db_path = Path(db_path)
    if db_path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safety = db_path.with_suffix(f".pre-restore-{stamp}.db")
        shutil.copy2(db_path, safety)
        print(f"Current database copied to {safety}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(backup_file) as src, sqlite3.connect(db_path) as dst:
        src.backup(dst)
    return db_path


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) < 1 or argv[0] not in ("backup", "restore"):
        raise SystemExit("usage: backup.py backup [file] | restore <file>")
    action = argv[0]
    url = database_url()

    if action == "backup":
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = Path(argv[1]) if len(argv) > 1 else ROOT / "backups" / f"srs-{stamp}.db"
        if not is_sqlite(url):
            print("MySQL database detected. Run:")
            print(f"  {mysql_commands(url, 'backup', out)}")
            return 0
        done = backup_sqlite(sqlite_path(url), out)
        print(f"Backup written to {done}")
        return 0

    if len(argv) < 2:
        raise SystemExit("usage: backup.py restore <file>")
    if not is_sqlite(url):
        print("MySQL database detected. Run:")
        print(f"  {mysql_commands(url, 'restore', argv[1])}")
        return 0
    done = restore_sqlite(argv[1], sqlite_path(url))
    print(f"Restored {argv[1]} into {done}")
    return 0


if __name__ == "__main__":
    main()
