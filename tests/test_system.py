"""System test: the whole app over real HTTP, on the demo data from src/seed.py.

The other test files check each rule on its own through Flask's test client. This file
starts the app on a local port, loads the same demo data as `python src/seed.py`, and
runs one pass through the acceptance suites in SRS 7.3 the way the pages and Postman
call the API: log in, keep the token, make each role's calls. It checks that the modules
work together. The tests run in order and share the server; each one says which suite
it covers. Results: docs/reports/System_Validation_Report.md.
"""
import json
import threading
import urllib.error
import urllib.request
from datetime import datetime

import pytest
from werkzeug.serving import make_server

from app import create_app
from app.core import clock
from app.extensions import db
from seed import ACCOUNTS, seed  # src/seed.py

TODAY = datetime(2026, 11, 11, 10, 0)  # inside add/drop and before the grade-lock date
PASSWORDS = {username: password for username, password, _, _ in ACCOUNTS}


@pytest.fixture(scope="module")
def server():
    app = create_app("test")
    with app.app_context():
        seed()
    clock.set_now(TODAY)
    httpd = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    thread.join(timeout=5)
    clock.set_now(None)
    with app.app_context():
        db.session.remove()
        db.drop_all()


def call(base, method, path, token=None, body=None):
    """(status, JSON body or raw bytes, content type) for one HTTP request."""
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            status, raw, ctype = res.status, res.read(), res.headers.get_content_type()
    except urllib.error.HTTPError as err:
        status, raw, ctype = err.code, err.read(), err.headers.get_content_type()
    return status, json.loads(raw) if ctype == "application/json" else raw, ctype


@pytest.fixture(scope="module")
def api(server):
    """api(user, method, path, body=None): calls as that demo user (None = no token)."""
    tokens = {}

    def _api(user, method, path, body=None):
        if user and user not in tokens:
            status, res, _ = call(server, "POST", "/auth/login",
                                  body={"username": user, "password": PASSWORDS[user]})
            assert status == 200, res
            tokens[user] = res["token"]
        return call(server, method, path, tokens.get(user), body)
    return _api


@pytest.fixture(scope="module")
def ids(api):
    """Database ids of the demo students, terms and current-term sections by course code."""
    _, found, _ = api("admin", "GET", "/students/search?q=S100")
    students = {s["studentNo"]: s["id"] for s in found["students"]}
    _, terms, _ = api("admin", "GET", "/terms")
    terms = {t["name"]: t["id"] for t in terms["terms"]}
    _, sections, _ = api("admin", "GET", f"/courses/sections?termId={terms['2026-ODD']}")
    return {"students": students, "terms": terms,
            "sections": {s["courseCode"]: s["id"] for s in sections["sections"]}}


def test_system_suite_auth_and_rbac(server, api):
    for user, password, _, role in ACCOUNTS:
        status, res, _ = call(server, "POST", "/auth/login",
                              body={"username": user, "password": password})
        assert status == 200 and res["role"] == role, user
    status, res, _ = call(server, "POST", "/auth/login",
                          body={"username": "student1", "password": "wrong"})
    assert (status, res["error"]["code"]) == (401, "invalid_credentials")

    assert api(None, "GET", "/students/search?q=S")[0] == 401
    assert api("student1", "GET", "/audit-logs")[0] == 403
    assert api("student1", "GET", "/students/search?q=S")[0] == 403
    assert api("faculty1", "GET", "/reports/report-card?studentId=1&termId=1")[0] == 403
    assert api("faculty1", "PUT", "/admin/config", {"feeThreshold": 1})[0] == 403
    assert api("admin", "GET", "/audit-logs")[0] == 200

    # a logged-out token stops working
    _, res, _ = call(server, "POST", "/auth/login",
                     body={"username": "student3", "password": "student123"})
    assert call(server, "POST", "/auth/logout", res["token"])[0] == 200
    assert call(server, "GET", "/notifications", res["token"])[0] == 401


def test_system_suite_student_records(server, api):
    status, new, _ = api("admin", "POST", "/students",
                         {"name": "Kiran Rao", "email": "kiran@example.edu",
                          "program": "B.Tech CSE", "semester": 3, "password": "kiran1234"})
    assert status == 201
    status, res, _ = api("admin", "POST", "/students",
                         {"name": "Kiran Rao", "email": "k@example.edu", "program": "B.Tech CSE",
                          "semester": 3, "password": "x", "studentNo": new["studentNo"]})
    assert (status, res["error"]["code"]) == (409, "duplicate_student")

    status, found, _ = api("faculty1", "GET", "/students/search?q=kiran")
    assert status == 200 and [s["studentNo"] for s in found["students"]] == [new["studentNo"]]
    assert "kiran@example.edu" not in json.dumps(found)

    # the new student logs in and edits only phone and address
    login = {"username": new["studentNo"].lower(), "password": "kiran1234"}
    _, session, _ = call(server, "POST", "/auth/login", body=login)
    token = session["token"]
    path = f"/students/{new['id']}"
    status, res, _ = call(server, "PUT", path, token, {"phone": "9845012345"})
    assert status == 200
    status, res, _ = call(server, "PUT", path, token, {"program": "B.Tech ECE"})
    assert (status, res["error"]["code"]) == (400, "locked_field")

    # deactivated: cannot log in, record kept
    assert api("admin", "PUT", path, {"status": "inactive"})[0] == 200
    status, res, _ = call(server, "POST", "/auth/login", body=login)
    assert (status, res["error"]["code"]) == (403, "account_inactive")
    status, res, _ = api("admin", "GET", path)
    assert status == 200 and res["status"] == "inactive" and res["phone"] == "9845012345"

    actions = {(log["action"], log["recordId"])
               for log in api("admin", "GET", "/audit-logs?module=student")[1]["logs"]}
    assert {("create", str(new["id"])), ("deactivate", str(new["id"]))} <= actions


def test_system_suite_course_and_enrollment(api, ids):
    cs102, ec101 = ids["sections"]["CS102"], ids["sections"]["EC101"]
    # student3 has not passed CS101, which CS102 needs
    status, res, _ = api("student3", "POST", "/enroll", {"sectionId": cs102})
    assert (status, res["error"]["code"]) == (409, "prerequisite_unmet")

    # EC101 has one seat
    status, taken, _ = api("student3", "POST", "/enroll", {"sectionId": ec101})
    assert status == 201
    status, res, _ = api("student1", "POST", "/enroll", {"sectionId": ec101})
    assert (status, res["error"]["code"]) == (409, "section_full")

    # dropping before the add/drop deadline frees the seat
    status, res, _ = api("student3", "DELETE", f"/enroll/{taken['enrollmentId']}")
    assert (status, res["status"]) == (200, "dropped")
    assert api("student1", "POST", "/enroll", {"sectionId": ec101})[0] == 201
    assert api("student3", "DELETE", f"/enroll/{taken['enrollmentId']}")[0] == 409


def test_system_suite_fee_visibility(api, ids):
    s1, s2 = ids["students"]["S1001"], ids["students"]["S1002"]
    status, fees, _ = api("student2", "GET", f"/fees/{s2}")
    assert status == 200
    assert (fees["balance"], fees["overdue"]) == (10000, 10000)
    assert [f["status"] for f in fees["history"]] == ["overdue"]
    status, fees, _ = api("student1", "GET", f"/fees/{s1}")
    assert (fees["balance"], fees["overdue"]) == (25000, 0)

    assert api("student1", "GET", f"/fees/{s2}")[0] == 403
    assert api("faculty1", "GET", f"/fees/{s2}")[0] == 403
    assert api("admin", "GET", f"/fees/{s2}")[0] == 200

    # 10,000 overdue is above the 5,000 limit, so student2 cannot enroll
    status, res, _ = api("student2", "POST", "/enroll", {"sectionId": ids["sections"]["CS201"]})
    assert (status, res["error"]["code"]) == (409, "fees_overdue")


def test_system_suite_attendance(api, ids):
    s1, s2 = ids["students"]["S1001"], ids["students"]["S1002"]
    cs102 = ids["sections"]["CS102"]
    for day, s2_status in [("2026-11-09", "late"), ("2026-11-10", "absent")]:
        status, _, _ = api("faculty1", "POST", "/attendance",
                           {"sectionId": cs102, "date": day,
                            "records": [{"studentId": s1, "status": "present"},
                                        {"studentId": s2, "status": s2_status}]})
        assert status in (200, 201)
    status, res, _ = api("faculty2", "POST", "/attendance",
                         {"sectionId": cs102, "date": "2026-11-10",
                          "records": [{"studentId": s1, "status": "absent"}]})
    assert status == 403

    by_course = {s["courseCode"]: s for s in
                 api("student1", "GET", f"/attendance/{s1}/summary")[1]["sections"]}
    assert (by_course["CS102"]["present"], by_course["CS102"]["percentage"]) == (2, 100.0)
    mine = api("student2", "GET", f"/attendance/{s2}/summary?sectionId={cs102}")[1]
    assert (mine["sections"][0]["late"], mine["sections"][0]["percentage"]) == (1, 0)
    assert api("student1", "GET", f"/attendance/{s2}/summary")[0] == 403
    assert len(api("admin", "GET", "/audit-logs?module=attendance")[1]["logs"]) == 4


def test_system_suite_grades_and_gpa(api, ids):
    s1, s2 = ids["students"]["S1001"], ids["students"]["S1002"]
    cs102 = ids["sections"]["CS102"]
    status, exam, _ = api("faculty1", "POST", "/grades/assessments",
                          {"sectionId": cs102, "name": "Final exam", "maxMarks": 100})
    assert status == 201
    for student, score in [(s1, 85), (s2, 58)]:
        status, res, _ = api("faculty1", "POST", "/grades/marks",
                             {"assessmentId": exam["assessmentId"], "studentId": student,
                              "score": score})
        assert status in (200, 201), res
    assert api("faculty2", "POST", "/grades/finalize", {"sectionId": cs102})[0] == 403
    status, res, _ = api("faculty1", "POST", "/grades/finalize", {"sectionId": cs102})
    assert (status, res["count"]) == (200, 2)
    status, res, _ = api("faculty1", "POST", "/grades/marks",
                         {"assessmentId": exam["assessmentId"], "studentId": s1, "score": 99})
    assert (status, res["error"]["code"]) == (409, "already_finalised")

    # 85% is A+ (9), 58% is B (6) on the default scale; GPA = sum(credits x point) / credits
    grades = api("student1", "GET", f"/grades/{s1}")[1]
    assert [(t["term"], t["gpa"]) for t in grades["terms"]] == [("2025-EVEN", 8.57),
                                                                 ("2026-ODD", 9.0)]
    assert grades["cgpa"] == 8.73                     # (4*9 + 3*8 + 4*9) / 11
    assert api("student2", "GET", f"/grades/{s2}")[1]["cgpa"] == 4.73  # (28 + 0 + 24) / 11
    assert api("student1", "GET", f"/grades/{s2}")[0] == 403

    notes = api("student1", "GET", "/notifications")[1]
    posted = [n for n in notes["notifications"]
              if n["message"] == "Final grade posted for CS102: A+"]
    assert len(posted) == 1 and not posted[0]["read"]
    assert api("student1", "POST", f"/notifications/{posted[0]['id']}/read")[0] == 200
    assert api("student2", "POST", f"/notifications/{posted[0]['id']}/read")[0] == 403

    grade_logs = api("admin", "GET", "/audit-logs?module=grade")[1]["logs"]
    assert [log["action"] for log in grade_logs] == ["finalise", "finalise"]
    assert {log["actor"] for log in grade_logs} == {"faculty1"}


def test_system_suite_reports_and_transcripts(api, ids):
    s1, s2 = ids["students"]["S1001"], ids["students"]["S1002"]
    status, pdf, ctype = api("student1", "GET", f"/reports/transcript/{s1}")
    assert (status, ctype) == (200, "application/pdf") and pdf.startswith(b"%PDF")
    assert api("student1", "GET", f"/reports/transcript/{s2}")[0] == 403

    term = ids["terms"]["2026-ODD"]
    status, pdf, ctype = api("admin", "GET", f"/reports/report-card?studentId={s1}&termId={term}")
    assert (status, ctype) == (200, "application/pdf") and pdf.startswith(b"%PDF")
    assert api("student1", "GET", f"/reports/report-card?studentId={s1}&termId={term}")[0] == 403


def test_system_suite_security(server, api, ids):
    # the API never hands out PII to the wrong person, and errors carry no data
    s2 = ids["students"]["S1002"]
    for path in [f"/students/{s2}", f"/grades/{s2}", f"/fees/{s2}",
                 f"/reports/transcript/{s2}"]:
        status, res, _ = api("student1", "GET", path)
        assert status == 403 and list(res) == ["error"], path
        assert "Ravi" not in json.dumps(res) and "S1002" not in json.dumps(res), path

    # five wrong passwords lock the account, even for the right password after that
    for _ in range(5):
        call(server, "POST", "/auth/login", body={"username": "faculty2", "password": "bad"})
    status, res, _ = call(server, "POST", "/auth/login",
                          body={"username": "faculty2", "password": "faculty123"})
    assert (status, res["error"]["code"]) == (423, "account_locked")

    # every change made in the earlier suites is in the audit log, with who made it
    logs = api("admin", "GET", "/audit-logs")[1]["logs"]
    kinds = {log["recordType"] for log in logs}
    assert {"student", "enrollment", "attendance", "assessment", "mark", "grade"} <= kinds
    assert all(log["actor"] != "system" for log in logs if log["recordType"] != "user")
