def test_profile_page_shows_own_record_with_locked_fields(client, login_as):
    user, headers = login_as("student")
    res = client.get("/ui/student/profile", headers=headers)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert user.student.student_no in html
    assert 'name="phone"' in html and 'name="address"' in html
    assert 'name="program"' not in html and 'name="name"' not in html


def test_profile_page_is_student_only(client, login_as):
    _, admin = login_as("admin")
    assert client.get("/ui/student/profile", headers=admin).status_code == 403
    assert client.get("/ui/student/profile").status_code != 200


def test_admin_page_has_edit_and_deactivate_buttons(client, login_as):
    _, admin = login_as("admin")
    user, _ = login_as("student")
    html = client.get("/ui/admin/students", headers=admin).get_data(as_text=True)
    assert f'data-api="/students/{user.student.id}"' in html
    assert "Deactivate" in html