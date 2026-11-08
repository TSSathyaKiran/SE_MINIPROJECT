# Operations: uptime, backup, restore and retention

How to keep the SRS app available and its data safe (SRS-NF-002, SRS-NF-004;
TC-Ops-01, TC-Ops-02). Both scripts use only the Python standard library.

## Uptime check (TC-Ops-01)

`scripts/uptime_check.py` calls `GET /health` every 60 seconds, appends a
`time,status` row (`ok` or `down`, ISO 8601 UTC) to a CSV log, and prints the
availability percentage so far. Stop it with Ctrl+C; the final availability
line prints before exit. It exits non-zero if any check failed, so a
scheduler can alert on it.

```bash
python src/run.py &                                  # the app must be running
python scripts/uptime_check.py                       # logs to logs/uptime.csv
python scripts/uptime_check.py --url http://localhost:8000 --interval 60 --csv logs/uptime.csv
```

## Backup and restore (TC-Ops-01)

`scripts/backup.py` reads the same `DATABASE_URL` as the app (default: the
SQLite file `src/instance/srs.db`).

```bash
python scripts/backup.py backup                  # -> backups/srs-<timestamp>.db
python scripts/backup.py backup my-backup.db
python scripts/backup.py restore backups/srs-<timestamp>.db
```

- **SQLite:** backup uses sqlite3's online backup API, so it is consistent
  even while the app is running. Restore first checks the backup file is a
  valid database (`PRAGMA integrity_check`), copies the current database to
  `<db>.pre-restore-<timestamp>.db` as a safety net, then replaces it.
- **MySQL:** the script prints the exact `mysqldump` / `mysql` commands to
  run, with the host, port, user and database filled in from `DATABASE_URL`.

## Retention rule (SRS-NF-004, TC-Ops-02)

- **No job ever deletes records or audit logs.** Students are deactivated,
  not deleted, and the audit log is append-only (enforced by a database
  trigger). There is no cleanup or rotation job, and none may be added
  without changing this rule.
- **Backups are kept for 7 years.** Take a backup at least daily while the
  project is running and store copies outside the app directory; do not
  delete a backup younger than 7 years.

## Verification results (2026-11-07)

- **Uptime run:** app seeded and started locally, then
  `python scripts/uptime_check.py` (default 60 s interval). Every check
  returned `ok`; availability **100.0%** (2/2 checks). A run against a
  stopped app logged `down` and exited 1, so failures are detected.
  Log: `logs/uptime.csv`.
- **Restore test:** backed up the seeded database (3 students, 1 audit log
  row, 3 terms), deleted those rows directly, then ran
  `python scripts/backup.py restore`. All rows came back (3 students,
  1 audit log, 3 terms), the append-only audit triggers were intact, and
  the pre-restore safety copy was written. A corrupt file was rejected
  before any restore happened.
- **Automated tests:** `tests/test_ops.py` covers the same paths
  (uptime ok/down logging, availability math, restore keeps students and
  audit logs, corrupt backup rejected, MySQL commands, this retention rule).
