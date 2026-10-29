"""Academic settings: TC-Adm-01 (issue #6)."""
from datetime import date

from app.core.settings import get_date, get_setting
from app.models import AuditLog

DEFAULT_SCALE = [[90, "O", 10], [80, "A+", 9], [70, "A", 8], [60, "B+", 7],
                 [55, "B", 6], [50, "C", 5], [40, "P", 4], [0, "F", 0]]
NEW_SCALE = [[90, "O", 10], [75, "A", 8], [50, "P", 4], [0, "F", 0]]


def test_tc_adm_01_admin_reads_current_config(client, login_as):
    _, admin = login_as("admin")
    res = client.get("/admin/config", headers=admin)
    assert res.status_code == 200
    assert res.json == {
        "gradingScale": DEFAULT_SCALE,
        "addDropDeadline": "2026-12-31",
        "gradeLockDate": "2026-12-31",
        "feeThreshold": 5000,
    }


def test_tc_adm_01_saved_settings_are_used(client, login_as):
    _, admin = login_as("admin")
    res = client.put("/admin/config", json={
        "gradingScale": NEW_SCALE,
        "addDropDeadline": "2026-11-15",
        "gradeLockDate": "2026-12-20",
        "feeThreshold": 7500,
    }, headers=admin)
    assert res.status_code == 200
    assert res.json["feeThreshold"] == 7500

    # the same values come back from GET ...
    res = client.get("/admin/config", headers=admin)
    assert res.json["gradingScale"] == NEW_SCALE
    assert res.json["addDropDeadline"] == "2026-11-15"
    assert res.json["gradeLockDate"] == "2026-12-20"

    # ... and the rest of the app reads them through core/settings.py
    assert get_setting("fee_threshold") == 7500
    assert get_setting("grading_scale") == NEW_SCALE
    assert get_date("add_drop_deadline") == date(2026, 11, 15)


def test_tc_adm_01_grading_scale_accepts_text_lines(client, login_as):
    _, admin = login_as("admin")
    res = client.put("/admin/config",
                     json={"gradingScale": "90,O,10\n75,A,8\n50,P,4\n0,F,0"},
                     headers=admin)
    assert res.status_code == 200
    assert res.json["gradingScale"] == NEW_SCALE


def test_tc_adm_01_updates_one_field_only(client, login_as):
    _, admin = login_as("admin")
    res = client.put("/admin/config", json={"feeThreshold": 0}, headers=admin)
    assert res.status_code == 200
    assert res.json["feeThreshold"] == 0
    assert res.json["addDropDeadline"] == "2026-12-31"  # untouched


def test_tc_adm_01_changes_are_audited(client, login_as):
    admin_user, admin = login_as("admin")
    client.put("/admin/config", json={"addDropDeadline": "2026-10-01",
                                      "feeThreshold": 100}, headers=admin)
    logs = AuditLog.query.order_by(AuditLog.id).all()
    assert [(log.action, log.record_type, log.record_id) for log in logs] == [
        ("update", "config", "add_drop_deadline"),
        ("update", "config", "fee_threshold"),
    ]
    assert all(log.user_id == admin_user.id for log in logs)


def test_tc_adm_01_rejects_bad_date(client, login_as):
    _, admin = login_as("admin")
    res = client.put("/admin/config", json={"addDropDeadline": "15/11/2026"}, headers=admin)
    assert res.status_code == 400
    assert res.json["error"]["code"] == "invalid_field"


def test_tc_adm_01_rejects_negative_fee_threshold(client, login_as):
    _, admin = login_as("admin")
    res = client.put("/admin/config", json={"feeThreshold": -1}, headers=admin)
    assert res.status_code == 400
    assert res.json["error"]["code"] == "invalid_field"


def test_tc_adm_01_rejects_scale_wrong_order_or_no_zero(client, login_as):
    _, admin = login_as("admin")
    res = client.put("/admin/config", json={"gradingScale": [[50, "P", 4], [90, "O", 10]]},
                     headers=admin)
    assert res.status_code == 400  # not highest first
    res = client.put("/admin/config", json={"gradingScale": [[90, "O", 10], [40, "F", 0]]},
                     headers=admin)
    assert res.status_code == 400  # does not end at 0


def test_tc_adm_01_rejects_empty_body(client, login_as):
    _, admin = login_as("admin")
    res = client.put("/admin/config", json={}, headers=admin)
    assert res.status_code == 400
    assert res.json["error"]["code"] == "missing_field"


def test_tc_adm_01_config_is_admin_only(client, login_as):
    _, student = login_as("student")
    assert client.get("/admin/config", headers=student).status_code == 403
    res = client.put("/admin/config", json={"feeThreshold": 1}, headers=student)
    assert res.status_code == 403
    assert client.get("/admin/config").status_code == 401  # not logged in


def test_tc_adm_01_rejects_non_finite_threshold(client, login_as):
    _, admin = login_as("admin")
    for bad in ("inf", "-inf", "nan"):
        res = client.put("/admin/config", json={"feeThreshold": bad}, headers=admin)
        assert res.status_code == 400, bad
        assert res.json["error"]["code"] == "invalid_field"
