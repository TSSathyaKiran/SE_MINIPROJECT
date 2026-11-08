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
| 1 | Encrypted in transit | HTTPS with TLS 1.2+ | TC-Sec-02, issue #10 | Pending (#10) |
| 2 | Encrypted at rest | Email, phone and address are stored as Fernet ciphertext | `test_tc_sec_05_*` in `tests/test_crypto.py` | Pass |
| 3 | Key kept out of the code | `PII_KEY` in `.env`, which git ignores; without it, a key is derived from `SECRET_KEY` (development only) | `.gitignore`, `.env.example` | Pass |
| 4 | Role checks on every API route | `require_role` / `require_login` on each route; ownership checked for student records | `test_tc_auth_02_and_tc_sec_03_roles_enforced_on_api` and each module's 403 tests | Pass |
| 5 | Passwords hashed | bcrypt with salt | `test_tc_sec_04_passwords_are_salted_hashes` | Pass |
| 6 | Sessions expire | 15 idle minutes; tokens stored hashed | `test_tc_sec_06_session_expires_after_15_idle_minutes` | Pass |
| 7 | No PII in error messages | Messages name fields, codes and student numbers only | `test_tc_sec_01_error_messages_never_include_pii` | Pass |
| 8 | No PII in URLs | Routes use numeric ids; search takes a name or student number; contact details only travel in request bodies | `test_tc_sec_01_urls_never_carry_pii` | Pass |
| 9 | No PII in logs | The app writes no log file of its own; the audit log keeps who, action, record type, id and time; the server log shows method, path and status | `test_tc_sec_01_audit_log_holds_no_pii` | Pass |
| 10 | Search leaves out contact details | `search_json()` in `modules/students.py` | `test_tc_stu_04_results_leave_out_contact_details` | Pass |
| 11 | Audit log cannot be changed | The ORM refuses, and a database trigger blocks UPDATE and DELETE | `test_tc_sec_07_audit_rows_cannot_be_changed` | Pass |
| 12 | Debug mode off outside development | `python src/run.py` starts with `debug=True`, whose crash page shows variable values | Production setup in #10 | Pending (#10) |

## Manual check

1. `python src/seed.py`, then `python src/run.py`.
2. Raw database: `sqlite3 src/instance/srs.db "SELECT student_no, email, phone, address FROM students LIMIT 3"`.
   The last three columns start with `gAAAAA` (ciphertext).
   `grep -c -a "student1@example.edu" src/instance/srs.db` prints `0`.
3. Backups (#9): run the same `grep` on a file from `backups/`; it prints `0`.
4. Log in as student1 and open My profile: the real email, phone and address show.
5. As admin, try a duplicate student number and an invalid field; as student2, open
   `/students/<student1's id>`. No email, phone or address appears in any error.
6. While doing steps 4 and 5, watch the address bar and the terminal running `run.py`:
   no email, phone or address appears.

## Keys

- Production sets its own `PII_KEY` (generate one as shown in `.env.example`).
- Keep a copy of the key somewhere safe and apart from the database backups. A backup
  on its own cannot be read, and without the key its contact details cannot be recovered.
- Changing `PII_KEY` (or `SECRET_KEY`, when `PII_KEY` is not set) makes existing rows
  unreadable. Re-encrypting with a new key is not built; re-seed in development.
