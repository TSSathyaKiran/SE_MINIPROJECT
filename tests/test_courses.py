"""Terms are the worked example. Add your course/section tests (issue #16) below."""
from app.models import AuditLog, Term


def test_admin_creates_and_lists_terms(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    assert res.status_code == 201
    assert res.json == {"termId": 1, "status": "created"}

    _, student = login_as("student")
    res = client.get("/terms", headers=student)
    assert res.json["terms"] == [{"id": 1, "name": "2026-ODD"}]


def test_create_term_rejects_missing_name(client, login_as):
    _, admin = login_as("admin")
    res = client.post("/terms", json={"name": "  "}, headers=admin)
    assert res.status_code == 400
    assert res.json["error"]["code"] == "missing_field"


def test_create_term_rejects_duplicate(client, login_as):
    _, admin = login_as("admin")
    client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    res = client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    assert res.status_code == 409
    assert Term.query.count() == 1


def test_create_term_is_audited(client, login_as):
    admin_user, admin = login_as("admin")
    client.post("/terms", json={"name": "2026-ODD"}, headers=admin)
    log = AuditLog.query.one()
    assert (log.user_id, log.action, log.record_type, log.record_id) == \
        (admin_user.id, "create", "term", "1")
