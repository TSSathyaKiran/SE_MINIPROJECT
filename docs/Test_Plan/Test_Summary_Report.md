# Test Summary Report

Date: 2026-11-11 · Prepared by: Tanuj N (QA Lead), final regression by T S Sathya Kiran · Issue: #10

Final report, after every other issue was merged (#15 last, in PR #67). It replaces the
interim report of 2026-11-10.

## 1. What was tested

- **Automated suite** on `main` with #15 merged: **249 tests, all passing** (pytest,
  SQLite in memory, about 6 s). Run it with the same command as CI:
  `pytest -q tests --ignore=tests/ui --ignore=tests/performance --ignore=tests/security`.
  Tests are named after their test case (`test_tc_<area>_<nn>_...`).
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
| Passed | 32 |
| Partially verified | 1 (TC-UX-01) |
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
| Accessibility | TC-UX-01 | Partially verified | `docs/Test_Plan/results/` |

New in this round: `tests/test_rbac.py` checks TC-Sec-03 on every route. It holds the
role matrix from SAD 4.3 and fails if a route is added without a role check or with
different roles.

## 3. Requirement coverage (RTM)

`docs/Test_Plan/RTM.csv`: 30 requirements P, SRS-NF-001 and SRS-NF-006 Y (as recorded in
PR #67), SRS-NF-005 N until the manual keyboard check of TC-UX-01 is done.

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
the login, admin, faculty and student pages; an automated Tab traversal completed a full
cycle on all four pages with no missing focus indicators found. Manual keyboard checks
(activating links and buttons, reverse navigation, form errors) are still to do.

## 5. Open items

1. **TC-UX-01 manual keyboard check** not done; SRS-NF-005 stays N.
2. **Sustained load runs** for TC-Perf-01 and TC-Perf-02 not done (section 4).
3. **ZAP findings, not fixed:** missing CSP, anti-clickjacking, HSTS and
   X-Content-Type-Options headers; missing Subresource Integrity; `Server` version header
   exposed. See `docs/security/TLS_ZAP_SCAN.md`. The scan covered the public login pages
   only.
4. **testssl LUCKY13 note:** CBC ciphers offered (potentially vulnerable, experimental
   check). Cipher hardening not done.
5. **Selenium tests** (`tests/ui/`) need `selenium` and Chrome, which are not in
   `requirements.txt`, so CI skips them; their last run (4 passed) is in
   `docs/Test_Plan/results/selenium-login-run.txt`. A plain `pytest` without selenium
   installed stops at `tests/ui/`; use the CI command in section 1.

## 6. Demo videos

- Feature demo: _link to be added_
- Test run demo: _link to be added_

## 7. Deviations

See `docs/DEVIATIONS.md`: every row now names the PR that made the change.
