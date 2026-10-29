# Deviations from SRS / SAD / Test Plan

Write one line per change, with the date and the PR. Explain these at the final demo.

| Date | What | Doc + section | Why | PR |
| --- | --- | --- | --- | --- |
| | 'Late' does not count as present in attendance % (assumption from SAD 4.6, confirm with team) | SRS-F-031 / SAD 4.6 | Open issue in SAD | |
| | UI pages served under `/ui/...`; API keeps the exact SAD paths | SAD 4.3 | Avoid route clashes between HTML pages and JSON API | |
| 2026-10-29 | SQLite is the default database for development and tests; MySQL is supported through `DATABASE_URL` | SRS 2.5, SAD 3.6, Test Plan 6 | Every team laptop runs the app with no database server to install | #1 |
| 2026-10-29 | Each module is one file holding its rules (plain functions), API routes and page routes | SAD 3.5 / 4.1 | Fewer files for a small team; rules are still separate functions that are unit-tested | #1 |
| 2026-10-29 | Added helper endpoints not in the SAD table: `GET /terms`, `GET /courses`, `GET /courses/sections`, `POST /grades/assessments`, `GET /grades/{studentId}`, `GET /admin/config`, `GET /notifications` | SAD 4.3 | Pages need to list data; the SAD paths are unchanged | #1 |
| 2026-10-29 | `/reports/report-card` takes `termId` instead of `term`; `/grades/finalize` returns the number of grades posted instead of a single GPA/CGPA | SAD 4.3 | A section has many students, so one GPA value does not apply; GPA/CGPA is shown per student | #1 |
| 2026-10-29 | Login sessions are stored as a SHA-256 hash of the token, not the token itself | SAD 3.9 | A leaked database cannot be used to hijack sessions | #1 |
