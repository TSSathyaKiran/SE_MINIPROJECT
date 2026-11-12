# System Validation Report

Date: 2026-11-12 · Prepared by: T S Sathya Kiran (Scrum Master), as part of the final
regression for #10 · Build: `main` at `9a10c89`, with all 19 issues merged. The security
fixes made after the scans were checked again on the same day (section 5).

This report checks the finished system against the acceptance criteria in SRS 7.2, using
the acceptance test suites in SRS 7.3. "System level" means the running app is used as a
whole, the way people and other tools reach it: over HTTP, in a browser, and with the
Postman collection. Results for each module are in `Unit_Test_Report.md`. How much of
the code the tests run is in `Code_Coverage_Report.md` and `Branch_Coverage_Report.md`.

## 1. System-level runs

| Run | What it does | Date | Result | Evidence |
| --- | --- | --- | --- | --- |
| System test over HTTP | `tests/test_system.py` starts the app on a local port and loads the demo data from `src/seed.py`. It then runs one pass through each SRS 7.3 suite, making the same API calls the pages make. It also runs in CI on every PR | 2026-11-12 | 8 of 8 passed | `results/pytest-coverage-run.txt` |
| Postman collection (Newman) | `tests/postman/rbac_tc_sec_03.postman_collection.json` against `python src/run.py` with the demo data (the normal settings, not the test ones: bcrypt cost 12, a database file) | 2026-11-12 | 22 requests, 23 of 23 assertions passed | `results/newman-rbac-run.txt` |
| Selenium login flow | `tests/ui/test_login_flow.py`: each role logs in through the login page; a wrong password shows the error. Headless Chrome 157; also runs in CI's `ui` job | 2026-11-12 | 4 of 4 passed | `results/selenium-login-run.txt` |
| Keyboard-only flows | `tests/ui/test_keyboard_flows.py`: login, skip link, menu, enroll and drop, marking attendance, an admin form with errors, and logout. Only key presses are used, no clicks. Headless Chrome 157; also runs in CI's `ui` job | 2026-11-12 | 5 of 5 passed | `../Test_Plan/results/keyboard-flows-run.txt` |
| Manual checks | Demo database: transcript and report card PDFs compared with the stored grades; the users table checked for password hashes; `UPDATE` and `DELETE` tried on `audit_logs` | 2026-11-11 | As expected | `../Test_Plan/Test_Summary_Report.md`, PR #68 |
| Performance (JMeter) | TC-Perf-01 (100 users) and TC-Perf-02 (1,000 users), from PR #67 | 2026-11-11 | 0% errors; P90 at most 705 ms | `tests/performance/` |
| Accessibility (axe, Lighthouse) | Login page and the three dashboards, from PR #67 | 2026-11-11 | 0 violations; Lighthouse 100 | `../Test_Plan/results/` |
| TLS and ZAP baseline | testssl.sh and an OWASP ZAP baseline scan against `HTTPS=1 python src/run.py`, from PR #66 | 2026-11-10 | TLS 1.0 and 1.1 refused; the findings are fixed (next row) | `../security/TLS_ZAP_SCAN.md` |
| Security fixes re-checked | Security headers, served Bootstrap and AEAD-only TLS 1.2 ciphers, checked with curl and openssl against `HTTPS=1 python src/run.py`. Every page opened as each role in Chrome, with no CSP errors in the console | 2026-11-12 | All headers present; a client offering only CBC ciphers is refused | `../security/TLS_ZAP_SCAN.md`, "Fixes" |
| Uptime and restore | `scripts/uptime_check.py`, plus a backup and restore of the demo database, from PR #63 | 2026-11-07 | 100% availability for the run; restore brought back every row | `../ops/OPERATIONS.md` |

## 2. Acceptance test suites (SRS 7.3)

| Suite | Requirements | Test cases | What the system-level runs showed | Result |
| --- | --- | --- | --- | --- |
| Authentication and RBAC | SRS-F-001, 002, 003, SR-002, SR-005 | TC-Auth-01 to 03, TC-Sec-03, TC-Sec-06 | All six demo accounts log in and get the right role. A wrong password gets 401. A token stops working after logout. Wrong roles get 403 on admin and faculty routes, both over HTTP and in the Postman run. Five wrong passwords lock the account, so the sixth try with the correct password gets 423. Idle expiry is covered by `tests/test_auth.py` | Passed |
| Student Records | SRS-F-010 to 013 | TC-Stu-01 to 04 | The admin creates a student; a duplicate student number gets 409. Faculty find the student by name, and the results leave out contact details. The student can change their phone but not their program (400 `locked_field`). After deactivation the student cannot log in, but the record and the phone change are kept. Both changes are in the audit log | Passed |
| Course and Enrollment | SRS-F-020, 021, 022 | TC-Enr-01 to 03 | A student without CS101 cannot take CS102 (409 `prerequisite_unmet`). The one-seat EC101 is full for the second student. Dropping before the deadline frees the seat, and dropping twice gets 409 | Passed |
| Attendance | SRS-F-030, 031 | TC-Att-01, 02 | Faculty marks two days as Present, Late and Absent; another faculty member gets 403. The students see 100% and 0%: Late does not count as present (`docs/DEVIATIONS.md`). A student gets 403 on another student's summary. The four entries are in the audit log | Passed |
| Grades and GPA | SRS-F-040, 041, 042 | TC-Grd-01 to 03 | Faculty adds an assessment and marks, then finalises two grades; another faculty member cannot finalise. Marks are locked after finalising (409). Term GPAs are 8.57 and 9.00, and the CGPA is 8.73 = (4×9 + 3×8 + 4×9) / 11. The second student's CGPA is 4.73. student1 gets one "grade posted" notification, and student2 cannot mark it read. The audit entries name the faculty member. The SRS example (8.64) is checked in `tests/test_grading.py` | Passed |
| Reports and Transcripts | SRS-F-050, 051 | TC-Rep-01, 02 | Students download their own transcript PDF and get 403 on someone else's. The admin downloads a report card PDF; a student gets 403. By hand, the PDFs' courses, grades, GPA and CGPA matched the stored data | Passed |
| Fee Visibility | SRS-F-060, 061 | TC-Fee-01, 02 | student2 sees 10,000 overdue; student1 sees 25,000 due but not overdue. Other students and faculty get 403; the admin can view. student2 cannot enroll, because 10,000 overdue is over the 5,000 limit (409 `fees_overdue`) | Passed |
| Security | SRS-SR-001 to 006, NF-003 | TC-Sec-01 to 07 | Another student's profile, grades, fees and transcript get 403, with only an error in the body: no name or student number. Lockout works. Every change in the run is in the audit log with who made it. TLS 1.2+ only (PR #66). Passwords are salted bcrypt hashes and student email, phone and address are encrypted (tests plus the manual check). The audit log refuses `UPDATE` and `DELETE` at the database. The ZAP and testssl findings are fixed, and faculty see a student's record without contact details | Passed |
| Performance | SRS-NF-001, 006 | TC-Perf-01, 02 | 100 and 1,000 virtual users with 0% errors. P90 was 705 ms for login and at most 26 ms for the pages, well under the 3 s target | Passed, with a deviation: short runs, at most 10 users at once |
| Usability/Accessibility | SRS-NF-005 | TC-UX-01 | axe found 0 WCAG 2.1 AA violations and Lighthouse scored 100 on 4 pages. The key flows for every role work with the keyboard only: forward and reverse Tab order, Enter and Space on buttons, arrow keys in radio groups, and typing to choose a list item. Errors appear next to the form in a `role="alert"` box, and the skip link moves past the menu | Passed, with a deviation: the keyboard check was scripted |
| Availability and retention (not a 7.3 suite) | SRS-NF-002, 004 | TC-Ops-01, 02 | The uptime check logged every check and flagged a stopped app. The restore brought back students and audit logs. The retention rule is documented | Passed |

## 3. Acceptance criteria (SRS 7.2)

| Criterion | Result | Evidence |
| --- | --- | --- |
| All high-priority functional requirements are implemented and verified | Met | All 21 functional requirements (SRS-F-001 to 071) passed their test cases, including every High-priority one. `docs/Test_Plan/Test_Cases.md` |
| All critical security requirements pass testing | Met | SRS-SR-001 to 006 (TC-Sec-02 to 07) and SRS-NF-003 (TC-Sec-01) passed |
| GPA/CGPA calculations match expected results for test datasets | Met | The SRS example gives 8.64 (`tests/test_grading.py`). The demo data gives 8.57, 9.00, 8.73 and 4.73 over HTTP (`tests/test_system.py`). The PDFs were checked by hand |
| Student records remain consistent after create/update/deactivate operations | Met | The student records suite in section 2; TC-Stu-01 and TC-Stu-02 |
| The RTM contains traceability from requirements to modules and test cases | Met | `docs/Test_Plan/RTM.csv`: each of the 33 requirements traces to a design spec, a module and a test case, and all 33 are A (Passed) |
| No critical defects remain at final demonstration | Met | Two defects were logged and both are fixed and closed (section 4). There are no open issues |

## 4. Defects

| Defect | Priority | Fixed in | Status |
| --- | --- | --- | --- |
| #37 Login returns 500 on a malformed JSON body instead of 401 | High | PR #50 (2026-10-31) | Closed |
| #57 Drop button on the student courses page drops the wrong course | High | PR #58 (2026-11-04) | Closed |

Both fixes have tests: `test_non_string_login_fields_are_a_failed_login` (`tests/test_auth.py`) and
`test_tc_enr_03_drop_button_uses_the_enrollment_id` (`tests/test_enrollment.py`).

## 5. Open items (none is a defect in a requirement)

1. **Sustained load:** the 10-minute runs at 100 and 1,000 users in TC-Perf-01 and 02 were
   not done (`docs/DEVIATIONS.md`).
2. **Scanner re-runs:** the ZAP findings (missing security headers, third-party files,
   `Server` version) and the CBC suites testssl noted were fixed on 2026-11-12. Tests,
   curl and openssl check the fixes, but neither scanner was run again. The ZAP scan also
   covered only the public login pages.
3. **Self-signed certificate:** expected for the localhost demo; a real deployment needs
   a certificate from a certificate authority.

## 6. Conclusion

All six acceptance criteria in SRS 7.2 are met. All ten SRS 7.3 suites and the
availability and retention checks passed. Two of them passed with documented deviations:
the performance runs were short, and the keyboard check was scripted. The open items in
section 5 are longer runs, scanner re-runs and a real certificate; none of them is a failed
requirement or an open defect.
