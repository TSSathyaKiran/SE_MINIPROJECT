<div align="center">

# 🎓 Student Record System (SRS-App)

**A role-based web app for a college's student records**<br>
profiles · courses · enrollment · attendance · marks · GPA/CGPA · transcripts · fees · audit log

PES University · Software Engineering mini-project · **Problem Statement No. 12**

[![CI](https://github.com/TSSathyaKiran/SE_MINIPROJECT/actions/workflows/ci.yml/badge.svg)](https://github.com/TSSathyaKiran/SE_MINIPROJECT/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/tag/TSSathyaKiran/SE_MINIPROJECT?label=release&color=blue)](https://github.com/TSSathyaKiran/SE_MINIPROJECT/tags)
[![Tests](https://img.shields.io/badge/tests-268%20passing-brightgreen)](docs/reports/Unit_Test_Report.md)
[![Coverage](https://img.shields.io/badge/coverage-97.9%25%20app%20lines-brightgreen)](docs/reports/Code_Coverage_Report.md)
[![Test cases](https://img.shields.io/badge/test%20cases-33%2F33%20passed-brightgreen)](docs/Test_Plan/Test_Cases.md)
<br>
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-3.0-000000?logo=flask&logoColor=white)
![Bootstrap](https://img.shields.io/badge/bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)
![Database](https://img.shields.io/badge/database-SQLite%20%7C%20MySQL-003B57?logo=sqlite&logoColor=white)

[Sprint board](https://github.com/users/TSSathyaKiran/projects/3) ·
[Team guide](docs/TEAM_GUIDE.md) ·
[Test reports](docs/reports/) ·
[Test cases](docs/Test_Plan/Test_Cases.md) ·
[Demo videos](#demo-videos) ·
[RTM](docs/Test_Plan/RTM.csv) ·
[Deviations](docs/DEVIATIONS.md)

<img src="docs/images/student-courses.png" alt="Student courses page: completed courses, current enrollment with a Drop button, and open sections with prerequisites and seats" width="88%">

</div>

---

## At a glance

| | |
| --- | --- |
| 📋 **Scope** | 33 requirements from the SRS: 21 functional, 6 non-functional and 6 security |
| 🏃 **Delivery** | 19 user stories (78 story points) in 2 sprints, tracked on a [GitHub Projects board](https://github.com/users/TSSathyaKiran/projects/3) |
| ✅ **Testing** | 33 of 33 test cases passed; 268 automated tests plus 9 browser tests, all run by CI on every pull request |
| 📈 **Coverage** | 97.9% of lines and 91.6% of branches in the application code ([reports](docs/reports/)) |
| 🔒 **Security** | bcrypt passwords, encrypted student PII, TLS 1.2+ with AEAD ciphers only, a strict Content-Security-Policy, role checks on every route |
| 🐞 **Defects** | 2 found during the sprints, both fixed; none open |

## Contents

- [Screenshots](#screenshots)
- [Demo videos](#demo-videos)
- [Features](#features)
- [Quick start](#quick-start)
- [Demo logins](#demo-logins)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [API](#api)
- [Security](#security)
- [Testing](#testing)
- [How we work](#how-we-work)
- [Repository structure](#repository-structure)
- [Documents](#documents)
- [Team](#team)

## Screenshots

| Grades and transcript (student) | Mark attendance (faculty) |
| --- | --- |
| <img src="docs/images/student-grades.png" alt="Student grades page with term GPA, CGPA and a transcript download button"> | <img src="docs/images/faculty-attendance.png" alt="Faculty attendance page with Present, Absent and Late choices per student"> |
| **Audit log (admin)** | **Log in** |
| <img src="docs/images/admin-audit-log.png" alt="Admin audit log filtered by module and date, showing who changed what and when"> | <img src="docs/images/login.png" alt="Login page"> |

## Demo videos

Screen recordings of the app on localhost with the demo data (`python src/seed.py`), with no sound or captions.

| Video | Length | What it shows |
| --- | --- | --- |
| 🎬 [Sprint 1](docs/demo/Sprint1_Demo.mp4) | 1:53 | Account lockout, student records, courses with prerequisites, enrollment, attendance and student search |
| 🎬 [Final (Sprint 2)](docs/demo/Final_Demo.mp4) | 1:57 | Marks and grades, GPA and CGPA, notifications, transcript and report card PDFs, the overdue-fee enrollment block and the audit log |

## Features

| | Area | What it does | SRS | Issues |
| --- | --- | --- | --- | --- |
| 🔐 | Login and roles | Login and logout, role-based dashboards for admin, faculty and student, 15-minute idle timeout, lockout after 5 failed logins | 4.1 | [#1](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/1), [#2](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/2) |
| 👤 | Student records | Admin creates, updates and deactivates students; students edit only their phone and address; search by ID or name | 4.2 | [#11](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/11), [#12](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/12), [#13](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/13) |
| 📚 | Courses and enrollment | Courses with prerequisites, sections with capacity, enroll with seat and prerequisite checks, drop before the add/drop deadline | 4.3 | [#16](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/16), [#17](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/17) |
| 🗓️ | Attendance | Faculty mark present / absent / late per session; students see their attendance percentage | 4.4 | [#7](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/7), [#8](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/8) |
| 📝 | Grades | Marks entry locked after the grade-lock date, final grades, GPA and CGPA, grade-posted notifications | 4.5 | [#18](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/18), [#19](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/19) |
| 📄 | Reports | Unofficial transcript and official report card as PDF | 4.6 | [#14](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/14) |
| 💳 | Fees | Students see dues; enrollment is blocked when overdue fees pass the threshold | 4.7 | [#4](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/4) |
| ⚙️ | Administration | Grading scale, deadlines and fee threshold settings; audit log viewer; uptime check and backup/restore | 4.8 | [#6](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/6), [#3](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/3), [#9](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/9) |
| 🛡️ | Security and quality | Encrypted student PII, HTTPS with TLS 1.2+, security scans, performance and accessibility tests | 6, 7 | [#5](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/5), [#10](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/10), [#15](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/15) |

Each row is an epic on GitHub that tracks its issues. Live progress is on the **[sprint board](https://github.com/users/TSSathyaKiran/projects/3)**.

## Quick start

Needs Python 3.11 or newer. Everything runs locally; no internet is needed once it is installed.

```bash
git clone https://github.com/TSSathyaKiran/SE_MINIPROJECT.git
cd SE_MINIPROJECT
python3 -m venv .venv
source .venv/bin/activate          # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt

python src/seed.py                 # first time: prints SECRET_KEY=... and PII_KEY=... lines;
                                   # save them in a new file .env here, then run it again
python src/seed.py                 # reset the database and load demo data (deletes all records)
python src/run.py                  # open http://localhost:8000
pytest                             # run the tests
```

> [!TIP]
> Port 8000 busy? `PORT=8001 python src/run.py`. For HTTPS, make a certificate with
> `bash scripts/make_cert.sh`, then start with `HTTPS=1 python src/run.py`.

## Demo logins

`python src/seed.py` creates two terms, five courses (CS102 needs CS101, CS201 needs CS102), past grades, fees and these accounts:

| Role | Username | Password | Try this |
| --- | --- | --- | --- |
| Admin | `admin` | `admin123` | Create a student, change the grading scale, filter the audit log, download a report card |
| Faculty | `faculty1` | `faculty123` | Mark attendance for CS102, enter marks and finalise grades |
| Faculty | `faculty2` | `faculty123` | Teaches CS201 and the past MA101 |
| Student | `student1` | `student123` | Past grades (CGPA 8.57), enrolled in CS102, transcript PDF |
| Student | `student2` | `student123` | 10,000 in overdue fees, so enrolling is blocked |
| Student | `student3` | `student123` | Has not passed CS101, so CS102 is refused; EC101 has a single seat |

> [!NOTE]
> Five wrong passwords lock an account for 15 minutes. `python src/seed.py` resets everything.

## Configuration

Settings live in `.env` (see `.env.example`), which is never committed. `SECRET_KEY` and `PII_KEY` are
required: without real values the app refuses to start and prints fresh keys to paste into `.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | none, required | Flask secret; the old example values are refused |
| `DATABASE_URL` | SQLite file `src/instance/srs.db` | e.g. `mysql+pymysql://root:password@localhost/srs_app` for MySQL |
| `PII_KEY` | none, required | Fernet key that encrypts student email, phone and address; keep a copy, the data cannot be read without it |
| `PORT` | `8000` | Port for `python src/run.py` |
| `HTTPS` | off | `HTTPS=1` serves TLS 1.2+ with `cert.pem` / `key.pem` |

## Architecture

```mermaid
flowchart LR
    B["Browser<br/>Bootstrap pages + api.js"] -->|"JSON over HTTP(S)"| F
    subgraph F["Flask app (src/app)"]
        M["modules/<br/>auth, students, courses, enrollment,<br/>attendance, grading, reports, fees,<br/>admin, auditlog, notifications"]
        C["core/<br/>security (RBAC, sessions), errors, headers,<br/>audit, settings, clock, crypto"]
        M --> C
    end
    F --> D[("SQLite or MySQL<br/>models.py")]
```

What happens when a faculty member saves attendance:

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser (api.js)
    participant R as require_role("faculty")
    participant A as attendance module
    participant DB as Database
    B->>R: POST /attendance + session token
    R->>DB: look up sha256(token), check 15-min idle timeout
    alt no session or wrong role
        R-->>B: 401 / 403 {"error": ...}
    else faculty of this section
        R->>A: mark_attendance()
        A->>DB: save rows + audit log entries (one transaction)
        A-->>B: 200 {"status": "saved", "count": n}
    end
```

- **One file per feature** in `src/app/modules/`. Each holds the business rules (plain functions), the JSON API routes and the `/ui/...` page routes.
- **Pages** are Jinja templates on Bootstrap 5, served by the app itself. Forms post JSON to the API through `static/js/api.js`.
- **Shared code** lives in `src/app/core/`: role checks, token sessions, JSON errors, security headers, the audit helper, academic settings, PII encryption and a test clock.
- **All tables** are in `src/app/models.py` and are created on startup.

## API

API paths follow the SAD (section 4.3). Every endpoint except `/auth/login` needs a session token (`Authorization: Bearer <token>` or the `srs_token` cookie), and roles are checked on the server. Errors come back as `{"error": {"code": "...", "message": "..."}}`.

<details>
<summary><b>Show all endpoints</b></summary>

| Endpoint | Method | Who | Purpose |
| --- | --- | --- | --- |
| `/auth/login` | POST | anyone | Log in → `{token, role, expiresIn}`; 401 wrong login, 423 locked |
| `/auth/logout` | POST | logged in | End the session |
| `/students` | POST | admin | Create a student |
| `/students/{id}` | GET, PUT | admin, faculty, own student | View or update a record (faculty see no contact details; students edit phone and address only) |
| `/students/search?q=` | GET | admin, faculty | Search by student ID or name |
| `/terms`, `/courses`, `/courses/sections` | GET, POST | any / admin | List or create terms, courses and sections |
| `/enroll`, `/enroll/{id}` | POST, DELETE | student | Enroll in or drop a section |
| `/attendance` | POST | faculty | Mark attendance for a session |
| `/attendance/{studentId}/summary` | GET | own student, faculty, admin | Attendance percentage |
| `/grades/assessments`, `/grades/marks`, `/grades/finalize` | POST | faculty | Add assessments, enter marks, finalise grades |
| `/grades/{studentId}` | GET | own student, admin | Grades, term GPA and CGPA |
| `/notifications`, `/notifications/{id}/read` | GET, POST | logged in | Grade-posted notifications |
| `/reports/transcript/{studentId}` | GET | own student, admin | Transcript PDF |
| `/reports/report-card?studentId=&termId=` | GET | admin | Official report card PDF |
| `/fees/{studentId}` | GET | own student, admin | Fee status |
| `/admin/config` | GET, PUT | admin | Academic settings |
| `/audit-logs` | GET | admin | Filter the audit log |
| `/health` | GET | anyone | Uptime check |

</details>

Extra helper endpoints and small changes from the SAD are listed in [DEVIATIONS.md](docs/DEVIATIONS.md).

## Security

| | Control | How |
| --- | --- | --- |
| 🔑 | Passwords | Salted **bcrypt** hashes (cost 12); never stored in plain text |
| 🎟️ | Sessions | Random tokens **stored only as SHA-256 hashes**; HttpOnly cookie; expire after **15 minutes** idle |
| 🚫 | Lockout | 15 minutes after 5 failed logins, recorded in the audit log |
| 🧭 | Access control | **Role checks on every route** on the server; a test checks every route against the role matrix |
| 🗄️ | PII at rest | Student email, phone and address **encrypted with Fernet**; faculty never see them |
| 🌐 | In transit | **TLS 1.2+**, ECDHE with AES-GCM or ChaCha20 only (no CBC) |
| 🧱 | Browser | Strict **Content-Security-Policy** with per-request nonces, `X-Frame-Options: DENY`, `nosniff`, HSTS, `no-store` on personal data, no third-party files |
| 📜 | Audit | Every create, update, deactivate, grade and attendance change is logged; the log is **append-only** in the database |

Scan results and fixes: [docs/security/](docs/security/).

## Testing

| Layer | Tool | Where |
| --- | --- | --- |
| Unit and API tests | pytest, a fresh in-memory database per test | `tests/test_<module>.py` |
| System test | pytest: the whole app over real HTTP on the demo data, one pass through the SRS 7.3 acceptance suites | `tests/test_system.py` |
| UI flows | Selenium in headless Chrome: login for each role, key flows with the keyboard only | `tests/ui/` |
| Continuous integration | GitHub Actions on every PR and on `main`: the pytest suite, then the browser tests | `.github/workflows/ci.yml` |
| API role checks | Postman collection (run with Newman) | `tests/postman/` |
| Performance | JMeter (100 and 1,000 users, P90 response time) | `tests/performance/` |
| Accessibility | axe, Lighthouse, keyboard-only flows | `docs/Test_Plan/results/` |
| Security | OWASP ZAP, testssl.sh, header and cipher tests | `docs/security/` |
| Reports | Unit test, system validation, code and branch coverage; `python scripts/make_reports.py` refreshes them | `docs/reports/` |

- Tests are named after the test case they cover, e.g. `test_tc_auth_03_lockout_after_5_failed_logins` for **TC-Auth-03**.
- All 33 test cases are in [Test_Cases.md](docs/Test_Plan/Test_Cases.md), and the [RTM](docs/Test_Plan/RTM.csv) maps each requirement to its test case and status.
- Time-based rules (session timeout, grade lock, add/drop deadline) are tested by moving a test clock (`core/clock.py`), not by waiting.
- The browser tests need `pip install selenium` and Chrome; without Selenium, `pytest` skips them.

## How we work

- **Scrum, two sprints.** Issues are grouped into epics (one per SRS section) and tracked on the [sprint board](https://github.com/users/TSSathyaKiran/projects/3): Todo → In Progress → In Review → Done, with story points per issue.
- **One branch per issue**, `feature/<n>-name`, `fix/<n>-name` or `test/<n>-name`, made from the latest `main`.
- **Small commits** in the form `type(module): what changed (#n)`. The helper script runs the tests before every commit:
  ```bash
  bash scripts/g.sh start 13 search-students
  bash scripts/g.sh commit feat students "add GET /students/search by number or name"
  bash scripts/g.sh push
  ```
- **Pull requests** start with `Closes #n`, need a green CI check and a review, and are merged with a merge commit.

The full step-by-step guide for every issue is in [docs/TEAM_GUIDE.md](docs/TEAM_GUIDE.md).

## Repository structure

<details>
<summary><b>Show the folder layout</b></summary>

```
docs/
  SRS/, SAD/, Test_Plan/     submitted documents, test cases, RTM, Test Summary Report
  reports/                   unit test, system validation, code and branch coverage reports
  security/, ops/            scan results and fixes, PII checklist, operations runbook
  images/                    screenshots used in this README
  demo/                      Sprint 1 and final demo videos
  BACKLOG.md                 the 19 issues and their requirements
  TEAM_GUIDE.md              setup, code patterns, and what to build per issue
  DEVIATIONS.md              changes from the SRS / SAD / Test Plan
scripts/
  g.sh                       git shortcuts: start, commit, push, sync
  make_reports.py            run the tests with coverage and write docs/reports/
  backup.py, uptime_check.py backup/restore and uptime monitoring
  make_cert.sh               self-signed certificate for HTTPS
src/
  run.py                     start the server
  seed.py                    reset the database with demo data (deletes every record)
  encrypt_pii.py             encrypt student PII in an older database, keeping its records
  app/
    __init__.py              app factory
    models.py                all tables
    core/                    security, errors, headers, audit, settings, clock, crypto
    modules/                 one file per feature (rules + API + pages)
    templates/, static/      Jinja pages, CSS, api.js, Bootstrap
tests/
  test_<module>.py           pytest, one file per module
  test_system.py             the whole app over real HTTP
  ui/                        Selenium browser tests
  performance/, postman/     JMeter plans and results, Postman collection
.github/                     CI workflow and PR template
```

</details>

## Documents

| Document | Contents |
| --- | --- |
| [SRS](docs/SRS/) | Software Requirements Specification: 33 requirements (functional, security, non-functional) |
| [SAD](docs/SAD/) | Software Architecture Document: components, data model, API design |
| [Test Plan](docs/Test_Plan/Student_Record_System_Test_Plan.docx) | Strategy, schedule, roles, risks, RTM |
| [Test cases](docs/Test_Plan/Test_Cases.md) and [RTM](docs/Test_Plan/RTM.csv) | Steps, expected results and status per test case; requirement traceability |
| [Test Summary Report](docs/Test_Plan/Test_Summary_Report.md) | What was tested, results by area, open items |
| [Test reports](docs/reports/) | [Unit tests](docs/reports/Unit_Test_Report.md) · [System validation](docs/reports/System_Validation_Report.md) · [Code coverage](docs/reports/Code_Coverage_Report.md) · [Branch coverage](docs/reports/Branch_Coverage_Report.md) |
| [Deviations](docs/DEVIATIONS.md) | Every change from the documents and why |

## Team

| | USN | Name | Role | Areas | GitHub |
| --- | --- | --- | --- | --- | --- |
| <img src="https://github.com/TSSathyaKiran.png?size=48" width="36" alt=""> | PES2UG24CS547 | T S Sathya Kiran | Scrum Master / Repo Owner | auth, audit log, fees, security | [@TSSathyaKiran](https://github.com/TSSathyaKiran) |
| <img src="https://github.com/Tanujn06.png?size=48" width="36" alt=""> | PES2UG24CS553 | Tanuj N | QA Lead / Test Engineer | settings, attendance, ops, final regression | [@Tanujn06](https://github.com/Tanujn06) |
| <img src="https://github.com/vaishnavii-25.png?size=48" width="36" alt=""> | PES2UG24CS517 | Sri Vaishnavi Peri | Test Engineer | students, reports, performance | [@vaishnavii-25](https://github.com/vaishnavii-25) |
| <img src="https://github.com/Srujan613.png?size=48" width="36" alt=""> | PES2UG24CS527 | Srujan Yalla | Dev Lead | courses, enrollment, grading | [@Srujan613](https://github.com/Srujan613) |

Everyone also develops their own issues. Product Owner / Course Coordinator: **Prof. Niveditha**. Role responsibilities are in the Test Plan, section 9.
