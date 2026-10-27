# Backlog — one GitHub Issue per row

`bash scripts/create_issues.sh` turns every row into a GitHub Issue (with a Sprint milestone and owner/sprint labels). Run it before anyone opens a PR and issue #n is row #n. Use that number in your branch, commits and PR.

Story points are a rough guess (1 = an hour or two, 5 = a full day). Change them in the planning meeting.

## Sprint 1 — login, students, courses/enrollment, attendance marking

| # | Story | Owner | SRS IDs | Test cases | Pts | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Project skeleton: Flask app factory, config, db, error handler, clock, blueprints stubs, conftest, CI | Tanuj | — | smoke | 3 | — **do this first, merge day 1** |
| 2 | MySQL schema + seed data for all roles | Tanuj | Appendix B | — | 2 | 1 |
| 3 | Login + logout API with bcrypt, token sessions | Sathya | F-001, SR-003 | TC-Auth-01, TC-Sec-04 | 3 | 1 |
| 4 | `require_role` decorator + RBAC on every route | Sathya | F-002, SR-002 | TC-Auth-02, TC-Sec-03 | 3 | 3 |
| 5 | Lockout after 5 failed logins | Sathya | F-003 | TC-Auth-03 | 2 | 3 |
| 6 | 15-minute idle session timeout | Sathya | SR-005 | TC-Sec-06 | 2 | 3 |
| 7 | Login page + role dashboards (base layout, nav per role) | Sathya | 3.1 UI | — | 2 | 3 |
| 8 | Admin creates student record | Vaishnavi | F-010 | TC-Stu-01 | 3 | 1 |
| 9 | Admin updates / deactivates student (soft delete) | Vaishnavi | F-011 | TC-Stu-02 | 2 | 8 |
| 10 | Student edits own phone/address only | Vaishnavi | F-012 | TC-Stu-03 | 2 | 8, 4 |
| 11 | Search students by ID or name | Vaishnavi | F-013 | TC-Stu-04 | 2 | 8 |
| 12 | Terms, courses, sections (admin) | Srujan | F-020 | TC-Enr-01 | 3 | 1 |
| 13 | Enroll with seat + prerequisite + duplicate checks | Srujan | F-021 | TC-Enr-02 | 3 | 12 |
| 14 | Drop course within add/drop window | Srujan | F-022 | TC-Enr-03 | 2 | 13, 15 |
| 15 | Admin academic config (grading scale, deadlines) | Tanuj | F-070 | TC-Adm-01 | 3 | 1 |
| 16 | Faculty marks attendance (P/A/L) for assigned section | Tanuj | F-030 | TC-Att-01 | 3 | 12, 13 |
| 17 | Sprint 1 regression + 1-minute demo video | Tanuj (all record) | — | all S1 | 1 | all |

## Sprint 2 — grades, reports, fees, audit, non-functional

| # | Story | Owner | SRS IDs | Test cases | Pts | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | Audit log service + append-only table + GET /audit-logs | Sathya | F-071, SR-006 | TC-Adm-02, TC-Sec-07 | 3 | S1 |
| 19 | Fee balance page (read-only) | Sathya | F-060 | TC-Fee-01 | 2 | S1 |
| 20 | Block enrollment above overdue-fee threshold | Sathya | F-061 | TC-Fee-02 | 2 | 19 |
| 21 | Encrypt PII fields at rest (phone, address, email) | Sathya | SR-004, NF-003 | TC-Sec-05, TC-Sec-01 | 3 | S1 |
| 22 | Marks entry with grade-lock date | Srujan | F-040 | TC-Grd-01 | 3 | S1 |
| 23 | Finalize grades + GPA/CGPA | Srujan | F-041 | TC-Grd-02 | 3 | 22 |
| 24 | In-app grade-posted notifications | Srujan | F-042 | TC-Grd-03 | 2 | 23 |
| 25 | Student attendance % view | Vaishnavi | F-031 | TC-Att-02 | 2 | 16 |
| 26 | Unofficial transcript PDF | Vaishnavi | F-050 | TC-Rep-01 | 3 | 23 |
| 27 | Official report card PDF (admin) | Vaishnavi | F-051 | TC-Rep-02 | 2 | 26 |
| 28 | JMeter plans + accessibility (axe/Lighthouse) run | Vaishnavi | NF-001, NF-006, NF-005 | TC-Perf-01/02, TC-UX-01 | 3 | S1 |
| 29 | /health endpoint + uptime script, backup/restore script | Tanuj | NF-002, NF-004 | TC-Ops-01/02 | 2 | S1 |
| 30 | TLS config notes + testssl scan, DEVIATIONS.md | Tanuj | SR-001 | TC-Sec-02 | 2 | S1 |
| 31 | Full regression, 2-minute video, Test Summary Report | Tanuj (all) | — | all | 2 | all |

Everyone should end up with roughly the same number of PRs (Sathya 8, Vaishnavi 7, Srujan 6, Tanuj 9). If someone is short, give them a test-only story (e.g. Selenium flows for their module) — that's a real PR too.
