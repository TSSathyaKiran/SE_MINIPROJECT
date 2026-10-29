# Backlog

19 issues cover all 33 requirements in the SRS. Issue #n on GitHub is row #n here; `bash scripts/sync_issues.sh` keeps them in sync. What to build for each issue, step by step, is in [TEAM_GUIDE.md](TEAM_GUIDE.md).

| # | Issue | Owner | Sprint | SRS IDs | Test cases |
| --- | --- | --- | --- | --- | --- |
| 1 | Project base: app, database, login, roles, dashboards, terms example | Sathya | 1 | F-001, F-002, SR-002, SR-003, SR-005 | TC-Auth-01, TC-Auth-02, TC-Sec-03, TC-Sec-04, TC-Sec-06 |
| 2 | Lock account after 5 failed logins | Sathya | 1 | F-003 | TC-Auth-03 |
| 3 | Audit log viewer and tamper protection | Sathya | 2 | F-071, SR-006 | TC-Adm-02, TC-Sec-07 |
| 4 | Fee page and enrollment block on overdue fees | Sathya | 2 | F-060, F-061 | TC-Fee-01, TC-Fee-02 |
| 5 | Encrypt student PII and PII checklist | Sathya | 2 | SR-004, NF-003 | TC-Sec-05, TC-Sec-01 |
| 6 | Academic settings: grading scale, deadlines, fee threshold | Tanuj | 1 | F-070 | TC-Adm-01 |
| 7 | Faculty marks attendance | Tanuj | 1 | F-030 | TC-Att-01 |
| 8 | Student attendance percentage | Tanuj | 2 | F-031 | TC-Att-02 |
| 9 | Uptime check, backup and restore, retention | Tanuj | 2 | NF-002, NF-004 | TC-Ops-01, TC-Ops-02 |
| 10 | HTTPS with TLS 1.2+, security scan, final regression and reports | Tanuj | 2 | SR-001 | TC-Sec-02 + full regression |
| 11 | Admin creates students | Vaishnavi | 1 | F-010 | TC-Stu-01 |
| 12 | Update, deactivate and student self-edit | Vaishnavi | 1 | F-011, F-012 | TC-Stu-02, TC-Stu-03 |
| 13 | Search students | Vaishnavi | 1 | F-013 | TC-Stu-04 |
| 14 | Transcript and report card PDFs | Vaishnavi | 2 | F-050, F-051 | TC-Rep-01, TC-Rep-02 |
| 15 | Performance, accessibility and UI tests | Vaishnavi | 2 | NF-001, NF-005, NF-006 | TC-Perf-01, TC-Perf-02, TC-UX-01 |
| 16 | Courses, sections and prerequisites | Srujan | 1 | F-020 | TC-Enr-01 |
| 17 | Enroll and drop | Srujan | 1 | F-021, F-022 | TC-Enr-02, TC-Enr-03 |
| 18 | Marks entry with grade-lock date | Srujan | 2 | F-040 | TC-Grd-01 |
| 19 | Finalise grades, GPA/CGPA and notifications | Srujan | 2 | F-041, F-042 | TC-Grd-02, TC-Grd-03 |
