# PII protection checklist (TC-Sec-01)

Covers SRS-NF-003 (student PII protected in transit and at rest) and SRS-SR-004
(sensitive PII encrypted at rest). Run it before each release and at the final demo,
and record the result in `docs/Test_Plan/Test_Cases.md`.

## Where personal data is kept

| Data | Stored in | Protection |
| --- | --- | --- |
| Email, phone, address | `students` | Encrypted per field with Fernet (AES-128 + HMAC), `src/app/core/crypto.py` |
| Name, student number | `students` | Plain text so staff can search; only admin and faculty can search, and results leave out contact details |
| Password | `users.password_hash` | bcrypt hash with salt; never returned by any route |
| Login token | `auth_sessions.token_hash` | SHA-256 hash only |
| Marks, grades, attendance, fees | their own tables | Role checks on every route; a student only sees their own |

## Checklist

| # | Check | How it is done | Evidence | Result |
| --- | --- | --- | --- | --- |
| 1 | Encrypted in transit | HTTPS with TLS 1.2+ | HTTPS mode with TLS 1.2 minimum, TLS 1.0/1.1 not offered (#10) | Pass (2026-11-10) |
| 2 | Encrypted at rest | Email, phone and address are stored as Fernet ciphertext | `test_tc_sec_05_*` in `tests/test_crypto.py` | Pass |
| 3 | Keys kept out of the code and never public | `SECRET_KEY` and `PII_KEY` come from `.env`, which git ignores; the app refuses to start if either is missing or an example value, or `PII_KEY` is not a valid key | `test_tc_sec_05_app_refuses_to_start_without_real_keys`, `.gitignore` | Pass |
| 4 | Role checks on every API route | `require_role` / `require_login` on each route; ownership checked for student records | `test_tc_auth_02_and_tc_sec_03_roles_enforced_on_api` and each module's 403 tests | Pass |
| 5 | Passwords hashed | bcrypt with salt | `test_tc_sec_04_passwords_are_salted_hashes` | Pass |
| 6 | Sessions expire | 15 idle minutes; tokens stored hashed | `test_tc_sec_06_session_expires_after_15_idle_minutes` | Pass |
| 7 | No PII in error messages | Messages name fields, codes and student numbers only | `test_tc_sec_01_error_messages_never_include_pii` | Pass |
| 8 | No PII in URLs | Routes use numeric ids; search takes a name or student number; contact details only travel in request bodies | `test_tc_sec_01_urls_never_carry_pii` | Pass |
| 9 | No PII in logs | The app writes no log file of its own; the audit log keeps who, action, record type, id and time; the server log shows method, path and status | `test_tc_sec_01_audit_log_holds_no_pii` | Pass |
| 10 | Search leaves out contact details | `search_json()` in `modules/students.py` | `test_tc_stu_04_results_leave_out_contact_details` | Pass |
| 11 | Audit log cannot be changed | The ORM refuses, and a database trigger blocks UPDATE and DELETE | `test_tc_sec_07_audit_rows_cannot_be_changed` | Pass |
| 12 | Debug mode off outside development | `python src/run.py` starts with debug off; `FLASK_DEBUG=1` opts in, so the crash page with variable values never appears by default (#10) | Pass (2026-11-10) |

## Manual check

1. On a demo database: `python src/seed.py`, then `python src/run.py`.
2. Raw database: `sqlite3 src/instance/srs.db "SELECT student_no, email, phone, address FROM students LIMIT 3"`.
   The last three columns start with `gAAAAA` (ciphertext).
   `grep -c -a "student1@example.edu" src/instance/srs.db` prints `0`.
3. Backups (#9): run the same `grep` on a file from `backups/`; it prints `0`.
4. Log in as student1 and open My profile: the real email, phone and address show.
5. As admin, try a duplicate student number and an invalid field; as student2, open
   `/students/<student1's id>`. No email, phone or address appears in any error.
6. While doing steps 4 and 5, watch the address bar and the terminal running `run.py`:
   no email, phone or address appears.

## Existing databases (keep the records)

`python src/seed.py` deletes every record, so use it only for throw-away demo data. A
database filled before PII encryption holds plain-text email, phone and address, and the
app cannot read those students until they are encrypted. To keep the records:

1. Stop the app.
2. Back up the database (once #9 is merged, `python scripts/backup.py backup` does this):
   - SQLite: `cp src/instance/srs.db src/instance/srs-before-encryption.db`
   - MySQL: `mysqldump -u root -p srs_app > srs-before-encryption.sql`
3. MySQL only, to make room for the longer encrypted values:
   `ALTER TABLE students MODIFY email TEXT NOT NULL, MODIFY phone TEXT, MODIFY address TEXT;`
4. Put `SECRET_KEY` and `PII_KEY` in `.env`; this `PII_KEY` is used from now on.
5. `python src/encrypt_pii.py`. It prints how many students it encrypted and is safe to run
   again. If any row was encrypted with a different key it stops and changes nothing.
6. MySQL only: `OPTIMIZE TABLE students;` rebuilds the table so the old plain-text values do
   not stay in its free space. On SQLite the script runs `VACUUM`, which does the same.
7. Check with steps 2 and 4 of the manual check above, then delete the backup from step 2:
   it still holds the plain-text data.

If something goes wrong, stop the app and put the backup back
(`cp src/instance/srs-before-encryption.db src/instance/srs.db`, or
`mysql -u root -p srs_app < srs-before-encryption.sql`).

## Keys

- Every install has its own `SECRET_KEY` and `PII_KEY`; the app will not start without them.
- Keep a copy of the key somewhere safe and apart from the database backups. A backup
  on its own cannot be read, and without the key its contact details cannot be recovered.
- Changing `PII_KEY` makes existing rows unreadable. Re-encrypting with a new key is not built.
