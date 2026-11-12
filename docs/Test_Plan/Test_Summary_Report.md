# Test Summary Report

Date: 2026-11-12 · Prepared by: Tanuj N (QA Lead), final regression by T S Sathya Kiran · Issue: #10

Final report, after every other issue was merged (#15 last, in PR #67). It replaces the
interim report of 2026-11-10. The 2026-11-12 update adds the system-level runs and the
keyboard check that closes TC-UX-01. It also adds the unit test, system validation, code
coverage and branch coverage reports, which are in `docs/reports/` (section 6).

## 1. What was tested

- **Automated suite** on `main` with #15 merged: **257 tests, all passing** (pytest,
  SQLite in memory, about 10 s). Run it with the same command as CI:
  `pytest -q tests --ignore=tests/ui --ignore=tests/performance --ignore=tests/security`.
  Tests are named after their test case (`test_tc_<area>_<nn>_...`). Eight of them
  (`tests/test_system.py`) start the app on a local port with the demo data. They then go
  through every SRS 7.3 acceptance suite over real HTTP.
- **Browser tests** (Selenium, headless Chrome, run locally on 2026-11-12): the login flow
  (`tests/ui/test_login_flow.py`, 4 passed) and the keyboard-only flows for every role
  (`tests/ui/test_keyboard_flows.py`, 5 passed).
- **Postman collection** for TC-Sec-03, run with Newman against `python src/run.py` and the
  demo data (2026-11-12): 23 of 23 assertions passed.
- **Manual checks** on a freshly seeded database: transcript and report card PDFs opened
  and compared with the stored grades; the users table inspected for password hashes;
  `UPDATE` and `DELETE` on `audit_logs` tried with the database account.
- **Performance** (JMeter) and **accessibility** (axe, Lighthouse, Selenium keyboard
  traversal), from PR #67: `tests/performance/` and `docs/Test_Plan/results/`.
- **HTTPS and security scans** (testssl.sh, OWASP ZAP baseline), from PR #66:
  `docs/security/TLS_ZAP_SCAN.md`.

## 2. Test case status

33 test cases in `docs/Test_Plan/Test_Cases.md`, one per SRS requirement:

| Status | Count |
| --- | --- |
| Passed | 33 |
| Partially verified | 0 |
| Failed / not tested | 0 |

| Area | Test cases | Status | Evidence |
| --- | --- | --- | --- |
| Login and roles | TC-Auth-01, 02, 03 | Passed | `tests/test_auth.py`, `tests/test_rbac.py` |
| Student records | TC-Stu-01, 02, 03, 04 | Passed | `tests/test_students.py`, `tests/test_students_search.py` |
| Courses and enrollment | TC-Enr-01, 02, 03 | Passed | `tests/test_courses.py`, `tests/test_enrollment.py` |
| Attendance | TC-Att-01, 02 | Passed | `tests/test_attendance.py` |
| Grades, GPA/CGPA, notifications | TC-Grd-01, 02, 03 | Passed | `tests/test_grading.py`, `tests/test_notifications.py` |
| Transcript and report card | TC-Rep-01, 02 | Passed | `tests/test_reports.py` + PDFs checked by hand |
| Fees | TC-Fee-01, 02 | Passed | `tests/test_fees.py` |
| Admin settings and audit log | TC-Adm-01, 02 | Passed | `tests/test_admin.py`, `tests/test_auditlog.py` |
| Security | TC-Sec-01 to 07 | Passed | `tests/test_crypto.py`, `tests/test_rbac.py`, `tests/test_auth.py`, `tests/test_auditlog.py`, `tests/test_tls.py`, `docs/security/` |
| Availability and retention | TC-Ops-01, 02 | Passed | `tests/test_ops.py`, `docs/ops/OPERATIONS.md` |
| Performance | TC-Perf-01, 02 | Passed, with a deviation | `tests/performance/` |
| Accessibility | TC-UX-01 | Passed, with a deviation | `docs/Test_Plan/results/`, `tests/ui/test_keyboard_flows.py` |

New in this round: `tests/test_rbac.py` checks TC-Sec-03 on every route. It holds the
role matrix from SAD 4.3 and fails if a route is added without a role check or with
different roles. `tests/test_system.py` runs the acceptance suites end to end, and
`tests/ui/test_keyboard_flows.py` covers step 2 of TC-UX-01. Results for each suite are in
`docs/reports/System_Validation_Report.md`.

## 3. Requirement coverage (RTM)

`docs/Test_Plan/RTM.csv` and the RTM in Test Plan section 13: all 33 requirements are **A**
(Passed). The codes follow the Test Plan legend: N = Not tested, P = In progress,
A = Passed, F = Failed. The previous version used P for passed rows and Y for the two
performance rows; both are now A.

## 4. Performance and accessibility results (PR #67)

| Run | Users | Samples | Errors | P90 login | P90 dashboard | P90 search |
| --- | --- | --- | --- | --- | --- | --- |
| TC-Perf-01 | 100, 20 s ramp-up | 300 | 0% | 705 ms | 24 ms | 26 ms |
| TC-Perf-02 | 1,000, 100 s ramp-up | 3,000 | 0% | 661 ms | 23 ms | 25 ms |

Each virtual user ran the workflow once, so the JMeter logs show at most 5 (TC-Perf-01)
and 10 (TC-Perf-02) users active at the same time. These runs show response times well
under the 3 s target at that load; the 10-minute runs at 100 and 1,000 users in the Test
Plan were not done (see `docs/DEVIATIONS.md`).

Accessibility: axe found no violations and the Lighthouse accessibility score was 100 on
the login, admin, faculty and student pages. An automated Tab traversal completed a full
cycle on all four pages with no missing focus indicators. The key flows of every role
also work with the keyboard only (2026-11-12): links and buttons open with Enter or
Space, Shift+Tab goes back, radio groups change with the arrow keys, and form errors
appear in the form's `role="alert"` box. This check was scripted with Selenium instead of
done by hand (see `docs/DEVIATIONS.md`).

## 5. Open items

1. **Sustained load runs** for TC-Perf-01 and TC-Perf-02 not done (section 4).
2. **ZAP findings, not fixed:** missing CSP, anti-clickjacking, HSTS and
   X-Content-Type-Options headers; missing Subresource Integrity; `Server` version header
   exposed. See `docs/security/TLS_ZAP_SCAN.md`. The scan covered the public login pages
   only.
3. **testssl LUCKY13 note:** CBC ciphers offered (potentially vulnerable, experimental
   check). Cipher hardening not done.
4. **Selenium tests** (`tests/ui/`) need `selenium` and Chrome, which are not in
   `requirements.txt`, so CI skips them. Their last runs (2026-11-12) are in
   `docs/reports/results/selenium-login-run.txt` and
   `docs/Test_Plan/results/keyboard-flows-run.txt`. A plain `pytest` without selenium
   installed stops at `tests/ui/`; use the CI command in section 1.

## 6. Reports

| Report | Result |
| --- | --- |
| `docs/reports/Unit_Test_Report.md` | 257 tests (43 unit, 206 API, 8 system), all passed |
| `docs/reports/System_Validation_Report.md` | All 6 acceptance criteria in SRS 7.2 met; all 10 SRS 7.3 suites passed |
| `docs/reports/Code_Coverage_Report.md` | Line coverage 97.7% for the application (`src/app/`), 94.5% overall |
| `docs/reports/Branch_Coverage_Report.md` | Branch coverage 91.4% for the application, 88.7% overall |

The unit and coverage reports are written by `python scripts/make_reports.py` from one
run of the CI tests with pytest-cov; run it again to refresh them. The code the tests do
not run is listed line by line in the coverage reports. Most of it is in three groups:

- **Defensive error paths:** a student login with no student record, names that are too
  long, malformed grading-scale rows, and two finalise requests at the same moment.
- **The admin Academic settings page:** only the refusal for other roles is tested; the
  API behind it is fully tested.
- **The command-line parts of `scripts/backup.py` and `scripts/uptime_check.py`:**
  argument handling and the check loop. `docs/ops/OPERATIONS.md` records hand runs of
  both.

## 7. Demo videos

- Feature demo: _link to be added_
- Test run demo: _link to be added_

## 8. Deviations

See `docs/DEVIATIONS.md`: every row now names the PR that made the change.
