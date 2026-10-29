from datetime import date

from app.core.settings import get_date, get_setting, set_setting
from app.extensions import db


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json == {"status": "ok", "database": "ok"}


def test_login_page_is_public(client):
    res = client.get("/ui/login")
    assert res.status_code == 200
    assert b'data-api="/auth/login"' in res.data


def test_pages_redirect_to_login_when_logged_out(client):
    res = client.get("/ui/admin/terms")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/ui/login")


def test_dashboard_shows_built_pages_and_coming_soon(client, login_as):
    _, admin = login_as("admin")
    res = client.get("/ui/admin", headers=admin)
    assert b'href="/ui/admin/terms"' in res.data
    assert b"Coming soon" in res.data


def test_wrong_role_page_shows_error_page(client, login_as):
    _, student = login_as("student")
    res = client.get("/ui/admin/terms", headers=student)
    assert res.status_code == 403
    assert b"Error 403" in res.data


def test_unknown_api_path_returns_json_404(client):
    res = client.get("/no-such-thing")
    assert res.status_code == 404
    assert res.json["error"]["code"] == "not_found"


def test_settings_have_defaults_and_can_change(app):
    assert get_setting("fee_threshold") == 5000
    set_setting("add_drop_deadline", "2026-11-01")
    db.session.commit()
    assert get_date("add_drop_deadline") == date(2026, 11, 1)
