# Student Record System (SRS-App)

Problem Statement No. 12: a web-based system to manage student profiles, courses, enrollment, attendance, marks, GPA/CGPA, transcripts, fee visibility, and audit logs.

## Team

| USN | Name | Role | GitHub username |
| --- | --- | --- | --- |
| PES2UG24CS553 | Tanuj N | Scrum Master / QA Lead (settings, attendance, ops) |  |
| PES2UG24CS547 | T S Sathya Kiran | Repo owner, Developer + Test Engineer (auth, audit, fees, security) | TSSathyaKiran |
| PES2UG24CS517 | Sri Vaishnavi Peri | Developer + Test Engineer (students, reports, performance) |  |
| PES2UG24CS527 | Srujan Yalla | Developer (courses, enrollment, grading) |  |

**Start here: [docs/TEAM_GUIDE.md](docs/TEAM_GUIDE.md)** (setup, how the code works, and every issue step by step).

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
python src/seed.py        # demo data; prints the demo logins
python src/run.py         # http://localhost:8000
pytest                    # all tests
```

Uses a SQLite file by default; set `DATABASE_URL` in `.env` for MySQL (see `.env.example`).

## Repository structure

```
docs/
  SRS/, SAD/, Test_Plan/     submitted documents, test cases, RTM
  BACKLOG.md                 the 19 issues
  TEAM_GUIDE.md              what to build and how
  DEVIATIONS.md              changes from the SRS/SAD/Test Plan
scripts/
  g.sh                       git shortcuts: start, commit, push, sync
  sync_issues.sh             make GitHub issues match BACKLOG.md
src/
  run.py, seed.py
  app/
    models.py                all tables
    core/                    security, errors, audit, settings, clock
    modules/                 one file per feature (routes + rules + pages)
    templates/, static/
tests/                       pytest (one file per module); ui/, performance/ for manual tools
```

## Tech stack

Python Flask, Flask-SQLAlchemy (SQLite or MySQL), bcrypt, Fernet encryption, ReportLab PDFs, Bootstrap 5 pages. Tests: pytest (CI on every PR), Selenium, Postman, JMeter, OWASP ZAP, testssl.sh, axe/Lighthouse.
