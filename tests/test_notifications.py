"""In-app notifications (SRS-F-042): TC-Grd-03."""
from app.extensions import db
from app.models import Notification
from app.modules.notifications import notify


def add_note(user, message, read=False):
    row = Notification(user_id=user.id, message=message, read=read)
    db.session.add(row)
    db.session.commit()
    return row


def test_tc_grd_03_api_lists_only_my_notifications_newest_first(client, login_as):
    student, headers = login_as("student")
    other, _ = login_as("student")
    first = add_note(student, "Final grade posted for CS101: A")
    second = add_note(student, "Final grade posted for CS102: O", read=True)
    add_note(other, "Final grade posted for CS103: B")
    res = client.get("/notifications", headers=headers)
    assert res.status_code == 200
    assert [n["id"] for n in res.json["notifications"]] == [second.id, first.id]
    assert res.json["notifications"][0]["read"] is True
    assert res.json["unread"] == 1
    assert client.get("/notifications").status_code == 401


def test_tc_grd_03_user_can_mark_their_notification_as_read(client, login_as):
    student, headers = login_as("student")
    note = add_note(student, "Final grade posted for CS102: A")
    res = client.post(f"/notifications/{note.id}/read", headers=headers)
    assert res.status_code == 200 and res.json["status"] == "read"
    assert db.session.get(Notification, note.id).read is True
    assert client.post(f"/notifications/{note.id}/read",
                       headers=headers).status_code == 200      # twice is harmless
    assert client.get("/notifications", headers=headers).json["unread"] == 0


def test_tc_grd_03_nobody_else_can_mark_it_as_read(client, login_as):
    student, _ = login_as("student")
    _, other = login_as("student")
    note = add_note(student, "Final grade posted for CS102: A")
    assert client.post(f"/notifications/{note.id}/read", headers=other).status_code == 403
    assert client.post(f"/notifications/{note.id}/read").status_code == 401
    assert client.post("/notifications/9999/read", headers=other).status_code == 404
    assert db.session.get(Notification, note.id).read is False


def test_tc_grd_03_notifications_page(client, login_as):
    student, headers = login_as("student")
    unread = add_note(student, "Final grade posted for CS102: A")
    done = add_note(student, "Final grade posted for CS101: O", read=True)
    page = client.get("/ui/student/notifications", headers=headers).data
    assert b"Final grade posted for CS102: A" in page
    assert f'data-api="/notifications/{unread.id}/read"'.encode() in page   # button only if unread
    assert f'data-api="/notifications/{done.id}/read"'.encode() not in page


def test_tc_grd_03_notifications_page_when_empty_and_roles(client, login_as):
    _, student = login_as("student")
    _, faculty = login_as("faculty")
    assert b"You have no notifications yet" in client.get(
        "/ui/student/notifications", headers=student).data
    assert client.get("/ui/student/notifications", headers=faculty).status_code == 403
    assert client.get("/ui/student/notifications").status_code == 302


def test_tc_grd_03_notify_helper_keeps_messages_within_the_column_size(app, add_user):
    user = add_user("someone", "student")
    notify(user.id, "x" * 300)
    db.session.commit()
    assert len(Notification.query.one().message) == 255