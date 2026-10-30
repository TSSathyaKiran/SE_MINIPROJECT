# Team guide

Everything you need: setup, how the code works, how to commit, and exactly what to build for each of your issues, one commit per step. The base (#1) is done: login, roles, session timeout, every database table, dashboards, and a finished example (Terms) to copy.

**Roles**

| Person | Role | Also responsible for |
| --- | --- | --- |
| Sathya | Scrum Master / Repo Owner | GitHub Project board, assigning issues and reviewers, labels and milestones, sprint planning, review and retro notes, repo settings |
| Tanuj | QA Lead / Test Engineer | RTM and test case status, defect triage, final regression, Test Summary Report |
| Vaishnavi | Test Engineer | Performance, accessibility and UI tests |
| Srujan | Dev Lead | Code questions on courses, enrollment and grading; test builds and seed data |

Everyone also builds their own issues and opens their own PRs.

**Who does what**

| Person | Sprint 1 | Sprint 2 |
| --- | --- | --- |
| Sathya | #2 lockout | #3 audit log, #4 fees, #5 PII encryption |
| Tanuj | #6 academic settings, #7 mark attendance | #8 attendance %, #9 uptime + backup, #10 TLS + final regression |
| Vaishnavi | #11 create students, #12 update/deactivate/self-edit, #13 search | #14 transcript + report card PDFs, #15 performance + accessibility |
| Srujan | #16 courses + sections, #17 enroll + drop | #18 marks entry, #19 finalise + GPA/CGPA + notifications |

**When:** about 2–3 commits a day, every day. Never all at once. Each issue below lists its commits in order. Suggested pace (Day 1 = the day #1 is merged):

| Day | Sathya | Tanuj | Vaishnavi | Srujan |
| --- | --- | --- | --- | --- |
| 1 | #2 | #6 | #11 | #16 |
| 2 | #2 → PR | #6 → PR | #11 → PR | #16 → PR |
| 3 | #3 | #7 | #12 | #17 |
| 4 | #3 → PR | #7 → PR | #12 → PR | #17 → PR |
| 5 | #4 | #8 → PR | #13 → PR | #18 → PR |
| 6 | #4 → PR | #9 → PR | #15 | #19 |
| 7 | #5 | #10 | #15 → PR, #14 | #19 → PR |
| 8 | #5 → PR | #10 → PR | #14 → PR | review + regression |

---

## 1. Set up (once)

1. Accept the GitHub invite from TSSathyaKiran.
2. Clone, and set your name and the **email on your GitHub account** (otherwise your commits won't count as yours):
   ```bash
   git clone https://github.com/TSSathyaKiran/SE_MINIPROJECT.git
   cd SE_MINIPROJECT
   git config user.name "Your Name"
   git config user.email "your-github-email"
   ```
3. Install Python 3.11 or newer, then:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate            # Windows (Git Bash): source .venv/Scripts/activate
   pip install -r requirements.txt
   ```
   Activate the venv (`source ...activate`) every time you open a new terminal.
4. Windows: run every command in **Git Bash**.

## 2. Run it

```bash
python src/seed.py      # reset the database and load demo data (prints the logins)
python src/run.py       # open http://localhost:8000
pytest                  # run all tests (must pass before every commit)
```

Demo logins: `admin / admin123`, `faculty1 / faculty123`, `faculty2 / faculty123`, `student1 / student123`, `student2 / student123`, `student3 / student123`.

The database is a SQLite file (`src/instance/srs.db`), so no MySQL install is needed. If you change `models.py`, run `python src/seed.py` again. For MySQL, set `DATABASE_URL` in `.env` (see `.env.example`).

## 3. How the code works

```
src/
  run.py, seed.py
  app/
    models.py           every table (already done, add columns if you need them)
    core/
      security.py       @require_role("admin"), @require_login, current_user()
      errors.py         ApiError, get_json(), required(), as_int(), as_float()
      audit.py          audit("create", "student", student.id)
      settings.py       get_setting("fee_threshold"), get_date("add_drop_deadline")
      clock.py          clock.now(), clock.today()  (never use datetime.now())
    modules/            ONE FILE PER FEATURE: its rules, API routes and page routes
      courses.py        <- the worked example (Terms). Copy it.
      students.py ...   the top of each file lists what to build in it
    templates/<module>/ your pages (extend base.html)
    static/js/api.js    sends your forms as JSON (no JavaScript needed)
tests/
  test_<module>.py      one test file per module; copy tests/test_courses.py
```

**Open `src/app/modules/courses.py` and `tests/test_courses.py` first.** Every endpoint follows the same recipe:

```python
@bp.post("/students")
@require_role("admin")                        # 1. who may call it (401/403 automatic)
def create_student():
    data = required(get_json(), "name", "email", "program", "semester")   # 2. 400 if missing
    semester = as_int(data["semester"], "semester")                       #    400 if not a number
    if Student.query.filter_by(email=data["email"]).first():              # 3. business rules
        raise ApiError(409, "duplicate_student", "A student with this email already exists")
    student = Student(...)                                                # 4. save
    db.session.add(student)
    db.session.flush()                        #    gives student.id
    audit("create", "student", student.id)    # 5. audit every change
    db.session.commit()
    return jsonify(id=student.id, status="created"), 201                  # 6. JSON back
```

- **"Only their own record":** check it yourself, e.g.
  `if current_user().role == "student" and current_user().student.id != student_id: raise ApiError(403, "forbidden", "Not your record")`.
- **Pages** live under `/ui/...` in the same module file: `@bp.get("/ui/admin/students")` + `@require_role("admin")` + `render_template("students/admin.html", students=...)`. Use the exact path from the menu in `modules/home.py`; the dashboard link turns on by itself once your route exists.
- **Forms** need no JavaScript. Look at `templates/courses/terms.html`:
  ```html
  <form data-api="/students" data-reload data-success="Student created.">
    <label for="name" class="form-label">Name</label>
    <input id="name" name="name" class="form-control" required>
    <button class="btn btn-primary">Save</button>
    <div class="form-msg" role="alert"></div>
  </form>
  ```
  Use `data-method="PUT"` or `data-method="DELETE"` for those methods. For anything custom, call `api("POST", "/path", {...})` from a `<script>` in `{% block scripts %}`.
- **Tests:** fixtures `client`, `login_as`, `add_user` (see `tests/conftest.py`):
  ```python
  def test_tc_stu_01_admin_creates_student(client, login_as):
      _, admin = login_as("admin")
      res = client.post("/students", json={...}, headers=admin)
      assert res.status_code == 201
  ```
  Name tests after the test case (`test_tc_stu_01_...`). For deadlines and timeouts use `clock.set_now(datetime(2026, 12, 1))`.
- **Rules to keep:** never put passwords or PII (email, phone, address) in error messages; call `audit(...)` on every create, update, deactivate, grade and attendance change; read deadlines, grading scale and fee threshold from `get_setting`, never hard-code them.

## 4. Git: the same steps for every issue

```bash
git checkout main && git pull
bash scripts/g.sh start 11 create-students       # makes branch feature/11-create-students
# ...code one step, run pytest...
bash scripts/g.sh commit feat students "add POST /students with required fields"
#   -> runs tests, shows files, asks y/N, commits "feat(students): ... (#11)"
bash scripts/g.sh push                            # end of each day; prints the PR link
```

When the issue's last commit is done:

1. `bash scripts/g.sh push`, open the link it prints.
2. PR title: `<issue title> (#11)`. The description template is filled in for you; keep `Closes #11` at the top.
3. Ask your reviewer (below). Move the card to **In Review** on the Projects board. Sathya (Scrum Master) checks that every issue and PR has an owner, reviewer and milestone.
4. When it's approved and the CI check is green: **Merge pull request → Create a merge commit** (never squash). Post "#11 merged" in the group so Tanuj (QA Lead) can update the test case status in `docs/Test_Plan/Test_Cases.md` and `RTM.csv`.
5. If main changed while you worked: `bash scripts/g.sh sync`.

| Author | Reviewer |
| --- | --- |
| Sathya | Tanuj |
| Tanuj | Srujan |
| Vaishnavi | Sathya |
| Srujan | Vaishnavi |

Review within 24 hours: run it, then leave at least one real comment before approving.

---

## 5. Your issues

The commit lines are your plan. If what you actually built is different, change the message to say what you did.

### #2 Lock account after 5 failed logins (Sathya) · SRS-F-003 · TC-Auth-03

File: `modules/auth.py` (see the TODO in `login()`). Columns `failed_logins` and `locked_until` already exist.

- If `user.locked_until` is in the future → `ApiError(423, "account_locked", "Account locked. Try again in 15 minutes")`.
- Wrong password → `failed_logins += 1`; on the 5th, set `locked_until = clock.now() + timedelta(minutes=15)` and `audit("lock", "user", user.id, actor_id=user.id)`. Commit before raising the 401.
- Successful login → `failed_logins = 0`, `locked_until = None`.

```bash
bash scripts/g.sh start 2 lockout
bash scripts/g.sh commit feat auth "count failed logins on the user"
bash scripts/g.sh commit feat auth "lock account for 15 minutes after 5 failures"
bash scripts/g.sh commit feat auth "reset failed count after a successful login"
bash scripts/g.sh commit test auth "cover TC-Auth-03 lockout, audit event and unlock"
```

### #3 Audit log viewer and tamper protection (Sathya) · SRS-F-071, SR-006 · TC-Adm-02, TC-Sec-07

Files: `modules/auditlog.py`, `templates/auditlog/audit.html`, `core/audit.py`, `tests/test_auditlog.py`. Writing entries already works (`audit()`).

- `GET /audit-logs?module=&from=&to=` (admin): filter `record_type == module`, `timestamp` between the dates (YYYY-MM-DD). Return `{logs: [{actor, action, recordType, recordId, timestamp}]}`, newest first, `actor` = username.
- Protection: in `core/audit.py` add SQLAlchemy listeners that refuse changes, and database triggers:
  ```python
  from sqlalchemy import DDL, event

  @event.listens_for(AuditLog, "before_update")
  @event.listens_for(AuditLog, "before_delete")
  def _append_only(mapper, connection, target):
      raise PermissionError("audit_logs is append-only")

  for op in ("UPDATE", "DELETE"):
      event.listen(AuditLog.__table__, "after_create", DDL(
          f"CREATE TRIGGER audit_no_{op.lower()} BEFORE {op} ON audit_logs "
          "BEGIN SELECT RAISE(ABORT, 'audit_logs is append-only'); END"
      ).execute_if(dialect="sqlite"))
  ```
  (For MySQL, the same trigger uses `SIGNAL SQLSTATE '45000'`; add it with `execute_if(dialect="mysql")`.)
- Page `/ui/admin/audit`: a GET form with module/from/to and a table.

```bash
bash scripts/g.sh start 3 audit-log
bash scripts/g.sh commit feat audit "add GET /audit-logs with module and date filters"
bash scripts/g.sh commit test audit "cover TC-Adm-02 entries have actor, action and record"
bash scripts/g.sh commit feat audit "block updates and deletes of audit rows"
bash scripts/g.sh commit test audit "cover TC-Sec-07 audit rows cannot be changed"
bash scripts/g.sh commit feat audit "add admin audit log page"
```

### #4 Fee page and enrollment block (Sathya) · SRS-F-060, F-061 · TC-Fee-01, TC-Fee-02

Files: `modules/fees.py`, `templates/fees/fees.html`, `modules/enrollment.py` (one check, after #17 is merged), `tests/test_fees.py`. Seed data: student1 has a paid and a due fee; student2 is 10,000 overdue.

- `overdue_balance(student_id)`: sum of `amount_due - amount_paid` for fees with `status == "overdue"` or (`due_date < clock.today()` and not fully paid).
- `GET /fees/<student_id>` (own student or admin, else 403; 404 unknown): `{amountDue, amountPaid, balance, overdue, history: [{description, amountDue, amountPaid, dueDate, status}]}`.
- Page `/ui/student/fees`: read-only table, no buttons. Say clearly that payments happen outside the system.
- In `enroll` (enrollment.py): if `overdue_balance(...) > get_setting("fee_threshold")` → `ApiError(409, "fees_overdue", "Enrollment blocked: overdue fees above the allowed limit")`.

```bash
bash scripts/g.sh start 4 fees
bash scripts/g.sh commit feat fees "add overdue_balance() helper"
bash scripts/g.sh commit feat fees "add GET /fees/<id> for the student and admin"
bash scripts/g.sh commit test fees "cover TC-Fee-01 balance, history and 403"
bash scripts/g.sh commit feat fees "add read-only student fee page"
bash scripts/g.sh commit feat enrollment "block enrollment above the overdue fee threshold"
bash scripts/g.sh commit test fees "cover TC-Fee-02 block, allow and changed threshold"
```

### #5 Encrypt student PII (Sathya) · SRS-SR-004, NF-003 · TC-Sec-05, TC-Sec-01

Files: new `core/crypto.py`, `models.py` (Student columns), `docs/security/PII_CHECKLIST.md`, `tests/test_crypto.py`.

- `core/crypto.py`: a Fernet key from `PII_KEY` (or, if unset, derived from `SECRET_KEY` for dev), and a SQLAlchemy `TypeDecorator` `EncryptedString` that encrypts in `process_bind_param` and decrypts in `process_result_value`.
- In `models.py`: `email`, `phone`, `address` become `db.Column(EncryptedString(500))`. Nothing else changes; the app still sees plain text.
- Test: after saving a student, `db.session.execute(text("SELECT phone FROM students")).scalar()` must not contain the phone number.
- Checklist (TC-Sec-01): TLS (#10), RBAC on every route, bcrypt, encrypted PII, no PII in logs/URLs/errors, audit log. Add a test that a 409 message doesn't include the email.

```bash
bash scripts/g.sh start 5 pii-encryption
bash scripts/g.sh commit feat core "add Fernet EncryptedString column type"
bash scripts/g.sh commit feat students "store email, phone and address encrypted"
bash scripts/g.sh commit test core "cover TC-Sec-05 PII unreadable in the database"
bash scripts/g.sh commit test core "check error messages never include PII"
bash scripts/g.sh commit docs security "add PII protection checklist for TC-Sec-01"
```

### #6 Academic settings (Tanuj) · SRS-F-070 · TC-Adm-01

Files: `modules/admin.py`, `templates/admin/config.html`, `tests/test_admin.py`. The storage is done (`core/settings.py`).

- `GET /admin/config` (admin): `{gradingScale, addDropDeadline, gradeLockDate, feeThreshold}`.
- `PUT /admin/config` (admin): any of those fields. Validate: dates with `date.fromisoformat` (400 if bad); threshold a number ≥ 0; grading scale either a list `[[90,"O",10], ...]` or text with one `90,O,10` per line, highest first, ending at 0. Save with `set_setting(...)`, `audit("update", "config", key)`, commit.
- Page `/ui/admin/config`: one form; the grading scale is a `<textarea>` with one row per line; `data-method="PUT"`.

```bash
bash scripts/g.sh start 6 academic-settings
bash scripts/g.sh commit feat admin "add GET /admin/config"
bash scripts/g.sh commit feat admin "add PUT /admin/config with validation"
bash scripts/g.sh commit test admin "cover TC-Adm-01 settings saved and used"
bash scripts/g.sh commit feat admin "add academic settings page"
```

### #7 Faculty marks attendance (Tanuj) · SRS-F-030 · TC-Att-01

Files: `modules/attendance.py`, `templates/attendance/mark.html`, `tests/test_attendance.py`.

- `POST /attendance` (faculty): `{sectionId, date, records: [{studentId, status}]}`. 403 if `section.faculty_id != current_user().id`. Status must be `present`/`absent`/`late`. Every studentId needs an `Enrollment` with status `enrolled` in that section, else 400. Save or update the `Attendance` row for (enrollment, date), `audit("mark", "attendance", row.id)`. Return `{status: "saved", count}`.
- Page `/ui/faculty/attendance?sectionId=&date=`: a dropdown of *my* sections, a date, then the roster (enrolled students only) with Present/Absent/Late radio buttons. Save with a little script:
  ```html
  <script>
  document.getElementById("save").onclick = async () => {
    const records = [...document.querySelectorAll("tr[data-student]")].map(row => ({
      studentId: Number(row.dataset.student),
      status: row.querySelector("input:checked").value }));
    await api("POST", "/attendance", { sectionId: {{ section.id }}, date: "{{ date }}", records });
    alert("Saved");
  };
  </script>
  ```

```bash
bash scripts/g.sh start 7 mark-attendance
bash scripts/g.sh commit feat attendance "add POST /attendance for the assigned faculty"
bash scripts/g.sh commit feat attendance "reject students not enrolled in the section"
bash scripts/g.sh commit test attendance "cover TC-Att-01 saving, not enrolled and other faculty"
bash scripts/g.sh commit feat attendance "add faculty attendance page with roster"
bash scripts/g.sh commit feat attendance "save attendance from the page"
```

### #8 Student attendance percentage (Tanuj) · SRS-F-031 · TC-Att-02

Files: `modules/attendance.py`, `templates/attendance/student.html`.

- `attendance_summary(enrollment)` → `{present, absent, late, total, percentage}` with `percentage = round(present / total * 100, 1)` (0 if no sessions). Late does not count as present (see DEVIATIONS).
- `GET /attendance/<student_id>/summary?sectionId=` (own student, the section's faculty, admin): one section, or every current enrollment if no sectionId.
- Page `/ui/student/attendance`: a table per course.

```bash
bash scripts/g.sh start 8 attendance-percent
bash scripts/g.sh commit feat attendance "add attendance percentage helper"
bash scripts/g.sh commit test attendance "unit-test 8 present of 10 gives 80 percent"
bash scripts/g.sh commit feat attendance "add GET /attendance/<id>/summary"
bash scripts/g.sh commit test attendance "cover TC-Att-02 own student only"
bash scripts/g.sh commit feat attendance "add student attendance page"
```

### #9 Uptime, backup and restore (Tanuj) · SRS-NF-002, NF-004 · TC-Ops-01, TC-Ops-02

Files: `scripts/uptime_check.py`, `scripts/backup.py`, `docs/ops/OPERATIONS.md`, `tests/test_ops.py`.

- `uptime_check.py`: calls `/health` every 60 s, appends `time,status` to a CSV, prints availability %.
- `backup.py backup|restore <file>`: for SQLite, copy with `sqlite3.connect(...).backup(...)`; for MySQL, print the `mysqldump` / `mysql` commands.
- `OPERATIONS.md`: how to run both; retention (no job ever deletes records or audit logs; keep backups 7 years); the results of your uptime run and a restore test.

```bash
bash scripts/g.sh start 9 ops-scripts
bash scripts/g.sh commit chore ops "add uptime check script for TC-Ops-01"
bash scripts/g.sh commit chore ops "add database backup and restore script"
bash scripts/g.sh commit test ops "check a restored backup keeps students and audit logs"
bash scripts/g.sh commit docs ops "document retention, backup and restore for TC-Ops-02"
```

### #10 HTTPS, security scan, final regression (Tanuj) · SRS-SR-001 · TC-Sec-02 + all

Files: `src/run.py`, `scripts/make_cert.sh`, `docs/security/`, `docs/Test_Plan/RTM.csv`, `docs/Test_Plan/Test_Summary_Report.md`, `docs/DEVIATIONS.md`.

- `HTTPS=1 python src/run.py` serves HTTPS with TLS 1.2 minimum:
  `ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.minimum_version = ssl.TLSVersion.TLSv1_2; ctx.load_cert_chain("cert.pem", "key.pem")`, then `app.run(ssl_context=ctx)`.
- `make_cert.sh`: `openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 365 -subj "/CN=localhost"` (add `*.pem` to `.gitignore`).
- Run `testssl.sh localhost:8000` and an OWASP ZAP baseline scan; save the summaries in `docs/security/`.
- Final: run every test case, update the RTM status column, write the Test Summary Report, fill in DEVIATIONS dates and PRs, add the demo video links.

```bash
bash scripts/g.sh start 10 tls-and-final
bash scripts/g.sh commit feat core "add HTTPS mode with TLS 1.2 minimum"
bash scripts/g.sh commit chore ops "add script to make a local certificate"
bash scripts/g.sh commit docs security "add testssl and ZAP scan results"
bash scripts/g.sh commit docs tests "update RTM status after full regression"
bash scripts/g.sh commit docs tests "add Test Summary Report"
bash scripts/g.sh commit docs demo "add demo video links and final deviations"
```

### #11 Admin creates students (Vaishnavi) · SRS-F-010 · TC-Stu-01

Files: `modules/students.py`, `templates/students/admin.html`, `tests/test_students.py`.

- `POST /students` (admin): required `name, email, program, semester, password`; optional `studentNo`. Semester 1–8. If `studentNo` is given and exists → 409; if not given, make the next one (`S1004`, `S1005`, ...). Also create the login: `User(username=student_no.lower(), password_hash=hash_password(password), name=name, role="student")` and link `student.user_id`. Audit, commit, return `{id, studentNo, status: "created"}` with 201.
- Page `/ui/admin/students`: the create form and a table of all students.

```bash
bash scripts/g.sh start 11 create-students
bash scripts/g.sh commit feat students "add POST /students with required fields"
bash scripts/g.sh commit feat students "generate or check a unique student number"
bash scripts/g.sh commit feat students "create the student's login account"
bash scripts/g.sh commit test students "cover TC-Stu-01 create, missing field and duplicate"
bash scripts/g.sh commit feat students "add admin students page with create form"
```

### #12 Update, deactivate, self-edit (Vaishnavi) · SRS-F-011, F-012 · TC-Stu-02, TC-Stu-03

Files: `modules/students.py`, `templates/students/admin.html`, `templates/students/profile.html`.

- `GET /students/<id>` (admin, faculty, or that student; other student → 403; unknown → 404).
- `PUT /students/<id>`:
  - admin may change `name, email, phone, address, program, semester, status`. `status: "inactive"` = deactivate: set the student and their `User` to inactive, delete their `AuthSession` rows, `audit("deactivate", ...)`. Nothing else is deleted (history stays).
  - the student themself may send **only** `phone` and `address`; any other key → `ApiError(400, "locked_field", "You can only change phone and address")`.
  - anyone else → 403.
- Pages: Edit and Deactivate buttons on the admin page (`data-method="PUT"`, a hidden `status=inactive` input); `/ui/student/profile` shows the record with only phone/address editable.

```bash
bash scripts/g.sh start 12 update-students
bash scripts/g.sh commit feat students "add GET /students/<id> with ownership check"
bash scripts/g.sh commit feat students "let admin update and deactivate a student"
bash scripts/g.sh commit test students "cover TC-Stu-02 update, deactivate and history kept"
bash scripts/g.sh commit feat students "let students edit only phone and address"
bash scripts/g.sh commit test students "cover TC-Stu-03 locked fields return 400"
bash scripts/g.sh commit feat students "add student profile page and admin edit buttons"
```

### #13 Search students (Vaishnavi) · SRS-F-013 · TC-Stu-04

- `GET /students/search?q=` (admin, faculty; student → 403; empty `q` → 400): matches `student_no` or name containing `q` (`Student.name.ilike(f"%{q}%")`). Return `{results: [{id, studentNo, name, program, status}]}`.
- Pages: `/ui/faculty/search` (a GET form, results rendered by the server, "No results" when empty) and a search box on the admin students page.

```bash
bash scripts/g.sh start 13 search-students
bash scripts/g.sh commit feat students "add GET /students/search by number or name"
bash scripts/g.sh commit test students "cover TC-Stu-04 search, no results and student 403"
bash scripts/g.sh commit feat students "add faculty search page and admin search box"
```

### #14 Transcript and report card PDFs (Vaishnavi) · SRS-F-050, F-051 · TC-Rep-01, TC-Rep-02

Files: `modules/reports.py`, `templates/reports/report_cards.html`, `tests/test_reports.py`. Uses `gpa()` from grading.py (#19); until that's merged, compute `round(sum(credits * point) / sum(credits), 2)` yourself.

- Split each report into `transcript_data(student)` (a dict: student details, per completed term the courses with credits/grade/point, term GPA, CGPA) and a function that draws it with ReportLab. Test the dict; for the route just check `res.mimetype == "application/pdf"`.
  ```python
  from io import BytesIO
  from reportlab.lib.pagesizes import A4
  from reportlab.lib.styles import getSampleStyleSheet
  from reportlab.platypus import Paragraph, SimpleDocTemplate, Table

  buf = BytesIO()
  styles = getSampleStyleSheet()
  SimpleDocTemplate(buf, pagesize=A4).build([
      Paragraph("PES University: Unofficial Transcript", styles["Title"]),
      Table([["Code", "Course", "Credits", "Grade"], *rows])])
  return send_file(BytesIO(buf.getvalue()), mimetype="application/pdf",
                   download_name="transcript.pdf")
  ```
- `GET /reports/transcript/<student_id>`: that student or admin (else 403).
- `GET /reports/report-card?studentId=&termId=`: admin only. Institution name, student details, that term's grades and GPA.
- Page `/ui/admin/report-cards`: pick a student and a term, then download. Put the transcript link on the student grades page.

```bash
bash scripts/g.sh start 14 report-pdfs
bash scripts/g.sh commit feat reports "add transcript data and PDF builder"
bash scripts/g.sh commit feat reports "add GET /reports/transcript/<id> for owner and admin"
bash scripts/g.sh commit test reports "cover TC-Rep-01 transcript terms, GPA and 403"
bash scripts/g.sh commit feat reports "add official report card PDF for admin"
bash scripts/g.sh commit test reports "cover TC-Rep-02 report card and non-admin 403"
bash scripts/g.sh commit feat reports "add report card page for admin"
```

### #15 Performance, accessibility and UI tests (Vaishnavi) · SRS-NF-001, NF-005, NF-006 · TC-Perf-01, TC-Perf-02, TC-UX-01

Files: `tests/performance/*.jmx`, `tests/ui/`, `docs/Test_Plan/results/`.

- JMeter: one plan with 100 users (log in, open dashboard, search) for TC-Perf-01, one with 1,000 users for TC-Perf-02. Save the summary report (90th percentile, error %) as a Markdown file.
- Accessibility: run axe DevTools and Lighthouse on the login page and each dashboard; save the scores; fix what they find (labels, contrast, headings).
- Selenium: `tests/ui/test_login_flow.py` logs in as each role and checks the dashboard (run by hand, not in CI).

```bash
bash scripts/g.sh start 15 perf-and-a11y test
bash scripts/g.sh commit test performance "add JMeter plan for 100 users (TC-Perf-01)"
bash scripts/g.sh commit test performance "add JMeter plan for 1000 users (TC-Perf-02)"
bash scripts/g.sh commit docs performance "record JMeter results"
bash scripts/g.sh commit test ui "add Selenium login flow for every role"
bash scripts/g.sh commit docs ux "record axe and Lighthouse results (TC-UX-01)"
bash scripts/g.sh commit fix ui "fix accessibility issues found by axe"
```

### #16 Courses, sections, prerequisites (Srujan) · SRS-F-020 · TC-Enr-01

Files: `modules/courses.py` (below Terms), `templates/courses/admin.html`, `tests/test_courses.py`.

- `POST /courses` (admin): `{code, name, credits, prerequisites: "CS101,CS102"}`. Duplicate code → 409; credits 1–5; unknown prerequisite code → 400. Save `Prerequisite` rows.
- `GET /courses` (any): each with its prerequisite codes.
- `POST /courses/sections` (admin): `{courseId, termId, name, facultyId, capacity}`. Unknown course/term → 400; facultyId must be a faculty user; same course+term+name → 409.
- `GET /courses/sections?termId=` (any): course code/name, term, faculty name, capacity, seats taken.
- Page `/ui/admin/courses`: course form, section form (dropdowns for course, term, faculty), both lists.

```bash
bash scripts/g.sh start 16 courses-sections
bash scripts/g.sh commit feat courses "add POST and GET /courses"
bash scripts/g.sh commit feat courses "save and list course prerequisites"
bash scripts/g.sh commit feat courses "add POST and GET /courses/sections"
bash scripts/g.sh commit test courses "cover TC-Enr-01 courses, sections and duplicates"
bash scripts/g.sh commit feat courses "add admin courses and sections page"
```

### #17 Enroll and drop (Srujan) · SRS-F-021, F-022 · TC-Enr-02, TC-Enr-03, TC-Sec-03

Files: `modules/enrollment.py`, `templates/enrollment/courses.html`, `tests/test_enrollment.py`, `tests/postman/`.

- `POST /enroll` (student): `{sectionId}`. In this order: already enrolled → 409 `duplicate`; seats taken ≥ capacity → 409 `section_full`; any prerequisite course without a passing `Grade` (`grade_point > 0`) → 409 `prerequisite_unmet`. Do the seat check and the insert in one commit; load the section with `.with_for_update()`. Audit, return `{enrollmentId, status: "enrolled"}` 201.
- `DELETE /enroll/<id>` (that student; else 403; unknown 404): if `clock.today() > get_date("add_drop_deadline")` → 403 `drop_closed`. Set status `dropped` (frees the seat), audit.
- Page `/ui/student/courses`: open sections in the latest term with seats left and an Enroll button; my enrollments with a Drop button; show the add/drop deadline.
- Postman: a collection that calls admin/faculty routes with a student token and expects 403 (TC-Sec-03).

```bash
bash scripts/g.sh start 17 enroll-drop
bash scripts/g.sh commit feat enrollment "add POST /enroll with seat and duplicate checks"
bash scripts/g.sh commit feat enrollment "check prerequisites before enrolling"
bash scripts/g.sh commit test enrollment "cover TC-Enr-02 full, prerequisite and duplicate"
bash scripts/g.sh commit feat enrollment "add DELETE /enroll/<id> before add/drop deadline"
bash scripts/g.sh commit test enrollment "cover TC-Enr-03 drop before and after deadline"
bash scripts/g.sh commit feat enrollment "add student courses page with enroll and drop"
bash scripts/g.sh commit test api "add Postman collection for RBAC checks (TC-Sec-03)"
```

### #18 Marks entry with grade lock (Srujan) · SRS-F-040 · TC-Grd-01

Files: `modules/grading.py`, `templates/grading/marks.html`, `tests/test_grading.py`.

- `POST /grades/assessments` (the section's faculty): `{sectionId, name, maxMarks}`.
- `POST /grades/marks` (the section's faculty): `{assessmentId, studentId, score}`. Student not enrolled → 400; score < 0 or > max → 400; `clock.today() > get_date("grade_lock_date")` → 403 `grades_locked`. Insert or update the `Mark`, `audit("grade", "mark", mark.id)`.
- Page `/ui/faculty/marks?sectionId=`: my sections, an add-assessment form, and a marks table (one small form per cell is fine). After the lock date, show the marks read-only.

```bash
bash scripts/g.sh start 18 marks-entry
bash scripts/g.sh commit feat grading "add POST /grades/assessments for assigned faculty"
bash scripts/g.sh commit feat grading "add POST /grades/marks with max marks check"
bash scripts/g.sh commit feat grading "make marks read-only after the grade-lock date"
bash scripts/g.sh commit test grading "cover TC-Grd-01 entry, update, max and lock"
bash scripts/g.sh commit feat grading "add faculty marks page"
```

### #19 Finalise grades, GPA/CGPA, notifications (Srujan) · SRS-F-041, F-042 · TC-Grd-02, TC-Grd-03

Files: `modules/grading.py`, `modules/notifications.py`, `templates/grading/grades.html`, `templates/notifications/list.html`.

- `gpa(items)` with items `[(credits, point), ...]` → `round(sum(c * p) / sum(c), 2)`. The SRS example `[(4,9), (3,8), (4,10), (3,7)]` must give **8.64**. `grade_for(percent)` looks up `get_setting("grading_scale")`.
- `POST /grades/finalize` (the section's faculty): `{sectionId}`; already has grades → 409. For each enrolled student: percent = total score / total max × 100 → letter and point → `Grade` row → `Notification(user_id=student.user_id, message="Final grade posted for CS102: A")`. Audit. Return `{status: "finalised", count}`.
- `GET /grades/<student_id>` (that student or admin): per term the courses and term GPA, plus CGPA across all terms.
- `GET /notifications` (logged in user) and `POST /notifications/<id>/read`.
- Pages `/ui/student/grades` (link to `/reports/transcript/<id>`) and `/ui/student/notifications`; a Finalise button on the marks page.

```bash
bash scripts/g.sh start 19 finalise-gpa
bash scripts/g.sh commit feat grading "add gpa() and grade-scale lookup"
bash scripts/g.sh commit test grading "unit-test GPA 8.64 example and CGPA"
bash scripts/g.sh commit feat grading "add POST /grades/finalize"
bash scripts/g.sh commit feat notifications "notify students when grades are finalised"
bash scripts/g.sh commit test grading "cover TC-Grd-02 and TC-Grd-03 after finalise"
bash scripts/g.sh commit feat grading "add student grades page with GPA and CGPA"
bash scripts/g.sh commit feat notifications "add notifications page"
```

---

## 6. When something goes wrong

| Problem | Fix |
| --- | --- |
| `error: you're on main` | `bash scripts/g.sh start <issue> <name>` |
| `tests fail` when committing | Read the failing test's message, fix, commit again |
| `no such column` / `no such table` | `python src/seed.py` (rebuilds the database) |
| `ModuleNotFoundError: flask` | Activate the venv: `source .venv/bin/activate` |
| Push rejected | `bash scripts/g.sh sync`, then push again |
| Merge conflict after sync | Open the file, keep both people's code, remove the `<<<<<<<`/`=======`/`>>>>>>>` lines, run `pytest`, then `bash scripts/g.sh commit fix <module> "resolve merge conflict with main"` |
| Port 8000 busy | `PORT=8001 python src/run.py` |
| Anything else | Ask in the group before running any `git reset` or `--force` |
