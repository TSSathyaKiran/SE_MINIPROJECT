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
| 2026-11-04 | A student cannot drop a section that already has a final grade (`DELETE /enroll/{id}` returns 403 `course_completed`); the page shows "Completed" instead of a Drop button | SRS-F-022 | Dropping would remove a graded course from the transcript and the CGPA; the SRS only mentions the add/drop deadline | #57 |
| 2026-11-08 | `POST /grades/finalize` is refused with 409 when the section has no assessments (`no_assessments`), no enrolled students (`no_students`), or an enrolled student has no mark for some assessment (`marks_missing`). Dropped students are ignored. Once a section is finalised, adding assessments and changing marks for it return 409 `already_finalised` | SRS-F-040, F-041, SAD 4.3 | The SRS and SAD only define 403 Not assigned Faculty and 409 Already finalised. Counting a missing mark as 0 would hand out wrong F grades, and editing marks after posting would leave the grade and the notification out of date | #19 |
| 2026-11-08 | Student name and student number are stored in plain text; email, phone and address are encrypted | SRS-SR-004 | Search by name or number (SRS-F-013) needs readable columns, and encrypted values cannot be searched. Only admin and faculty can search, and results leave out contact details | #5 |
