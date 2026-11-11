"""TC-Sec-03: RBAC is enforced at the API layer (SRS-SR-002), on every route.

ACCESS is the role matrix (SAD 4.3 plus the pages); the tests check that every
route has exactly these roles and that each role is refused everywhere else. A
new route without require_role() or with different roles fails the first test.
"Any" means any logged-in user; those routes also check whose record it is.
"""
import inspect
import re

ROLES = ("student", "faculty", "admin")
PUBLIC = "public"
ACCESS = {
    "GET /": PUBLIC,
    "GET /health": PUBLIC,
    "GET /static/<path:filename>": PUBLIC,
    "POST /auth/login": PUBLIC,
    "POST /auth/logout": PUBLIC,
    "GET /ui/login": PUBLIC,
    # API
    "POST /students": "admin",
    "GET /students/<int:student_id>": "any",
    "PUT /students/<int:student_id>": "any",
    "GET /students/search": "admin faculty",
    "POST /terms": "admin",
    "GET /terms": "any",
    "POST /courses": "admin",
    "GET /courses": "any",
    "POST /courses/sections": "admin",
    "GET /courses/sections": "any",
    "POST /enroll": "student",
    "DELETE /enroll/<int:enrollment_id>": "student",
    "POST /attendance": "faculty",
    "GET /attendance/<int:student_id>/summary": "any",
    "POST /grades/assessments": "faculty",
    "POST /grades/marks": "faculty",
    "POST /grades/finalize": "faculty",
    "GET /grades/<int:student_id>": "any",
    "GET /notifications": "any",
    "POST /notifications/<int:notification_id>/read": "any",
    "GET /reports/transcript/<int:student_id>": "any",
    "GET /reports/report-card": "admin",
    "GET /fees/<int:student_id>": "any",
    "GET /admin/config": "admin",
    "PUT /admin/config": "admin",
    "GET /audit-logs": "admin",
    # pages
    "GET /ui/home": "any",
    "GET /ui/admin": "admin",
    "GET /ui/admin/audit": "admin",
    "GET /ui/admin/config": "admin",
    "GET /ui/admin/courses": "admin",
    "GET /ui/admin/report-cards": "admin",
    "GET /ui/admin/students": "admin",
    "GET /ui/admin/terms": "admin",
    "GET /ui/faculty": "faculty",
    "GET /ui/faculty/attendance": "faculty",
    "GET /ui/faculty/marks": "faculty",
    "GET /ui/faculty/search": "admin faculty",
    "GET /ui/student": "student",
    "GET /ui/student/attendance": "student",
    "GET /ui/student/courses": "student",
    "GET /ui/student/fees": "student",
    "GET /ui/student/grades": "student",
    "GET /ui/student/notifications": "student",
    "GET /ui/student/profile": "student",
}


def route_roles(app, rule):
    """The roles require_role() allows on this route (() = any login), or None if public."""
    view = app.view_functions[rule.endpoint]
    found = inspect.getclosurevars(view).nonlocals if view.__closure__ else {}
    return found["roles"] if "view" in found else None


def protected_routes(app):
    """(url, method, roles) for every route behind require_role()."""
    for rule in app.url_map.iter_rules():
        roles = route_roles(app, rule)
        if roles is None:
            continue
        url = re.sub(r"<[^>]+>", "1", rule.rule)
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            yield url, method, roles


def assert_refused(res, url, status, code):
    """API calls get a JSON error and nothing else; pages show the login or error page."""
    if url.startswith("/ui"):
        if status == 401:
            assert res.status_code == 302 and res.location.endswith("/ui/login"), url
        else:
            assert res.status_code == 403, url
    else:
        assert res.status_code == status, url
        assert list(res.json) == ["error"] and res.json["error"]["code"] == code, url


def test_tc_sec_03_every_route_has_the_expected_roles(app):
    actual = {}
    for rule in app.url_map.iter_rules():
        roles = route_roles(app, rule)
        access = PUBLIC if roles is None else " ".join(sorted(roles)) or "any"
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            actual[f"{method} {rule.rule}"] = access
    assert actual == ACCESS


def test_tc_sec_03_no_token_gets_401_and_no_data(app, client):
    routes = list(protected_routes(app))
    assert len(routes) > 40
    for url, method, _ in routes:
        assert_refused(client.open(url, method=method, json={}), url, 401, "not_logged_in")


def test_tc_sec_03_each_role_refused_outside_its_routes(app, client, login_as):
    checked = 0
    for role in ROLES:
        _, headers = login_as(role)
        for url, method, roles in protected_routes(app):
            if roles and role not in roles:
                res = client.open(url, method=method, json={}, headers=headers)
                assert_refused(res, url, 403, "forbidden")
                checked += 1
    assert checked > 50


def test_tc_sec_03_student_cannot_reach_another_students_records(client, login_as):
    _, me = login_as("student")
    other, _ = login_as("student")
    sid = other.student.id
    for method, url in [("GET", f"/students/{sid}"), ("PUT", f"/students/{sid}"),
                        ("GET", f"/fees/{sid}"), ("GET", f"/grades/{sid}"),
                        ("GET", f"/attendance/{sid}/summary"),
                        ("GET", f"/reports/transcript/{sid}")]:
        res = client.open(url, method=method, json={"phone": "9999999999"}, headers=me)
        assert res.status_code == 403, url
        assert other.student.student_no.encode() not in res.data, url
        assert other.name.encode() not in res.data, url
