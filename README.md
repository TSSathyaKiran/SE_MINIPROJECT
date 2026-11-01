# Student Record System (SRS-App)

[![CI](https://github.com/TSSathyaKiran/SE_MINIPROJECT/actions/workflows/ci.yml/badge.svg)](https://github.com/TSSathyaKiran/SE_MINIPROJECT/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0-lightgrey)
![Database](https://img.shields.io/badge/database-SQLite%20%7C%20MySQL-orange)

A web-based student record system for a college: student profiles, courses and sections, enrollment, attendance, marks, GPA/CGPA, transcripts, fee visibility and an audit log, with separate views for admins, faculty and students.

PES University · Software Engineering mini-project · **Problem Statement No. 12**

**Quick links:** [Sprint board](https://github.com/users/TSSathyaKiran/projects/3) · [Team guide](docs/TEAM_GUIDE.md) · [Backlog](docs/BACKLOG.md) · [Test cases](docs/Test_Plan/Test_Cases.md) · [RTM](docs/Test_Plan/RTM.csv) · [Deviations](docs/DEVIATIONS.md)

---

## Contents

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

---

## Features

| Area | What it does | SRS | Issues |
| --- | --- | --- | --- |
| Login and roles | Login and logout, role-based dashboards for admin, faculty and student, 15-minute idle timeout, lockout after 5 failed logins | 4.1 | [#1](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/1), [#2](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/2) |
| Student records | Admin creates, updates and deactivates students; students edit only their phone and address; search by ID or name | 4.2 | [#11](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/11), [#12](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/12), [#13](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/13) |
| Courses and enrollment | Courses with prerequisites, sections with capacity, enroll with seat and prerequisite checks, drop before the add/drop deadline | 4.3 | [#16](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/16), [#17](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/17) |
| Attendance | Faculty mark present / absent / late per session; students see their attendance percentage | 4.4 | [#7](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/7), [#8](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/8) |
| Grades | Marks entry locked after the grade-lock date, final grades, GPA and CGPA, grade-posted notifications | 4.5 | [#18](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/18), [#19](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/19) |
| Reports | Unofficial transcript and official report card as PDF | 4.6 | [#14](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/14) |
| Fees | Students see dues; enrollment is blocked when overdue fees pass the threshold | 4.7 | [#4](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/4) |
| Administration | Grading scale, deadlines and fee threshold settings; audit log viewer; uptime check and backup/restore | 4.8 | [#6](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/6), [#3](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/3), [#9](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/9) |
| Security and quality | Encrypted student PII, HTTPS with TLS 1.2+, security scans, performance and accessibility tests | 6, 7 | [#5](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/5), [#10](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/10), [#15](https://github.com/TSSathyaKiran/SE_MINIPROJECT/issues/15) |

Live progress for every issue is on the **[sprint board](https://github.com/users/TSSathyaKiran/projects/3)**. Each row above is an epic on GitHub that tracks its issues.

## Quick start

Needs Python 3.11 or newer.

```bash
git clone https://github.com/TSSathyaKiran/SE_MINIPROJECT.git
cd SE_MINIPROJECT
python3 -m venv .venv
source .venv/bin/activate          # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt

python src/seed.py                 # reset the database and load demo data
python src/run.py                  # open http://localhost:8000
pytest                             # run all tests
```

Port 8000 busy? `PORT=8001 python src/run.py`

## Demo logins

`python src/seed.py` creates these accounts and sample data: two terms, five courses (CS102 requires CS101, CS201 requires CS102), a section with only one seat, past grades, and fees, with an overdue balance for student2.

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin123` |
| Faculty | `faculty1`, `faculty2` | `faculty123` |
| Student | `student1`, `student2`, `student3` | `student123` |

## Configuration

Copy `.env.example` to `.env` to change settings. Everything works without it.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | `dev-only-change-me` | Flask secret; set a real one outside development |
| `DATABASE_URL` | SQLite file `src/instance/srs.db` | e.g. `mysql+pymysql://root:password@localhost/srs_app` for MySQL |
| `PII_KEY` | none | Fernet key for encrypting student PII |
| `PORT` | `8000` | Port for `python src/run.py` |

## Architecture

```mermaid
flowchart LR
    B["Browser<br/>Bootstrap pages + api.js"] -->|"JSON over HTTP(S)"| F
    subgraph F["Flask app (src/app)"]
        M["modules/<br/>auth, students, courses, enrollment,<br/>attendance, grading, reports, fees,<br/>admin, auditlog, notifications"]
        C["core/<br/>security (RBAC, sessions), errors,<br/>audit, settings, clock"]
        M --> C
    end
    F --> D[("SQLite or MySQL<br/>models.py")]
```

- **One file per feature** in `src/app/modules/`. Each holds the business rules (plain functions), the JSON API routes and the `/ui/...` page routes.
- **Pages** are Jinja templates on Bootstrap 5. Forms post JSON to the API through `static/js/api.js`.
- **Shared code** lives in `src/app/core/`: role checks, token sessions, JSON errors, the audit helper, academic settings and a test clock.
- **All tables** are in `src/app/models.py` and are created on startup.

## API

API paths follow the SAD (section 4.3). Every endpoint except `/auth/login` needs a session token (`Authorization: Bearer <token>` or the `srs_token` cookie), and roles are checked on the server. Errors come back as `{"error": {"code": "...", "message": "..."}}`.

| Endpoint | Method | Who | Purpose |
| --- | --- | --- | --- |
| `/auth/login` | POST | anyone | Log in → `{token, role, expiresIn}`; 401 wrong login, 423 locked |
| `/auth/logout` | POST | logged in | End the session |
| `/students` | POST | admin | Create a student |
| `/students/{id}` | GET, PUT | admin, faculty, own student | View or update a record (students: phone and address only) |
| `/students/search?q=` | GET | admin, faculty | Search by student ID or name |
| `/courses`, `/courses/sections` | GET, POST | any / admin | List or create courses and sections |
| `/enroll`, `/enroll/{id}` | POST, DELETE | student | Enroll in or drop a section |
| `/attendance` | POST | faculty | Mark attendance for a session |
| `/attendance/{studentId}/summary` | GET | own student, faculty, admin | Attendance percentage |
| `/grades/marks`, `/grades/finalize` | POST | faculty | Enter marks, finalise grades |
| `/reports/transcript/{studentId}` | GET | own student, admin | Transcript PDF |
| `/fees/{studentId}` | GET | own student, admin | Fee status |
| `/admin/config` | GET, PUT | admin | Academic settings |
| `/audit-logs` | GET | admin | Filter the audit log |
| `/health` | GET | anyone | Uptime check |

Extra helper endpoints and small changes from the SAD are listed in [DEVIATIONS.md](docs/DEVIATIONS.md).

## Security

- Passwords hashed with **bcrypt** (salted).
- Session tokens are random and **stored only as SHA-256 hashes**. Sessions expire after **15 minutes** idle, and the cookie is HttpOnly.
- **Account lockout** for 15 minutes after 5 failed logins, recorded in the audit log.
- **Role checks on every route** on the server, not only in the menu.
- Every create, update, deactivate, grade and attendance change writes an **audit log** entry.
- Student PII **encrypted at rest** with Fernet, and **HTTPS with TLS 1.2+** (issues #5 and #10).

## Testing

| Layer | Tool | Where |
| --- | --- | --- |
| Unit and API tests | pytest, a fresh in-memory database per test | `tests/test_<module>.py` |
| Continuous integration | GitHub Actions runs every test on each PR and on `main` | `.github/workflows/ci.yml` |
| API role checks | Postman collection | `tests/postman/` |
| UI flows | Selenium | `tests/ui/` |
| Performance | JMeter (100 and 1,000 users, P90 response time) | `tests/performance/` |
| Accessibility | axe / Lighthouse | `docs/Test_Plan/results/` |
| Security | OWASP ZAP, testssl.sh | `docs/security/` |

- Tests are named after the test case they cover, e.g. `test_tc_auth_03_lockout_after_5_failed_logins` for **TC-Auth-03**.
- All 33 test cases are in [Test_Cases.md](docs/Test_Plan/Test_Cases.md), and the [RTM](docs/Test_Plan/RTM.csv) maps each requirement to its test case and status.
- Time-based rules (session timeout, grade lock, add/drop deadline) are tested by moving a test clock (`core/clock.py`), not by waiting.

## How we work

- **Scrum, two sprints.** Issues are grouped into epics (one per SRS section) and tracked on the [sprint board](https://github.com/users/TSSathyaKiran/projects/3): Todo → In Progress → In Review → Done.
- **One branch per issue**, `feature/<n>-name` or `fix/<n>-name`, made from the latest `main`.
- **Small commits** in the form `type(module): what changed (#n)`. The helper script runs the tests before every commit:
  ```bash
  bash scripts/g.sh start 13 search-students
  bash scripts/g.sh commit feat students "add GET /students/search by number or name"
  bash scripts/g.sh push
  ```
- **Pull requests** start with `Closes #n`, need one approval and a green CI check, and are merged with a merge commit.

The full step-by-step guide for every issue is in [docs/TEAM_GUIDE.md](docs/TEAM_GUIDE.md).

## Repository structure

```
docs/
  SRS/, SAD/, Test_Plan/     submitted documents, test cases, RTM
  BACKLOG.md                 the 19 issues and their requirements
  TEAM_GUIDE.md              setup, code patterns, and what to build per issue
  DEVIATIONS.md              changes from the SRS / SAD / Test Plan
scripts/
  g.sh                       git shortcuts: start, commit, push, sync
  sync_issues.sh             make GitHub issues match BACKLOG.md
src/
  run.py                     start the server
  seed.py                    reset the database with demo data
  app/
    __init__.py              app factory
    models.py                all tables
    core/                    security, errors, audit, settings, clock
    modules/                 one file per feature (rules + API + pages)
    templates/, static/      Jinja pages, CSS, api.js
tests/                       pytest, one file per module
.github/                     CI workflow and PR template
```

## Documents

| Document | Contents |
| --- | --- |
| [SRS](docs/SRS/) | Software Requirements Specification: 33 requirements (functional, security, non-functional) |
| [SAD](docs/SAD/) | Software Architecture Document: components, data model, API design |
| [Test Plan](docs/Test_Plan/Student_Record_System_Test_Plan.docx) | Strategy, schedule, roles, risks |
| [Test cases](docs/Test_Plan/Test_Cases.md) and [RTM](docs/Test_Plan/RTM.csv) | Steps and expected results per test case; requirement traceability |
| [Deviations](docs/DEVIATIONS.md) | Every change from the documents and why |

## Team

| USN | Name | Role | Areas | GitHub |
| --- | --- | --- | --- | --- |
| PES2UG24CS547 | T S Sathya Kiran | Scrum Master / Repo Owner | auth, audit log, fees, security | [@TSSathyaKiran](https://github.com/TSSathyaKiran) |
| PES2UG24CS553 | Tanuj N | QA Lead / Test Engineer | settings, attendance, ops, final regression | [@Tanujn06](https://github.com/Tanujn06) |
| PES2UG24CS517 | Sri Vaishnavi Peri | Test Engineer | students, reports, performance | [@vaishnavii-25](https://github.com/vaishnavii-25) |
| PES2UG24CS527 | Srujan Yalla | Dev Lead | courses, enrollment, grading | [@Srujan613](https://github.com/Srujan613) |

Everyone also develops their own issues. Product Owner / Course Coordinator: **Prof. Niveditha**. Role responsibilities are in the Test Plan, section 9.
