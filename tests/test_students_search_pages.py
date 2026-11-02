def test_faculty_search_page_loads(client, login_as):
    _, faculty = login_as("faculty")
    res = client.get("/ui/faculty/search", headers=faculty)
    assert res.status_code == 200
    assert 'id="student-search"' in res.get_data(as_text=True)


def test_search_page_is_not_for_students(client, login_as):
    _, student = login_as("student")
    assert client.get("/ui/faculty/search", headers=student).status_code == 403
    assert client.get("/ui/faculty/search").status_code != 200


def test_admin_page_has_search_box(client, login_as):
    _, admin = login_as("admin")
    html = client.get("/ui/admin/students", headers=admin).get_data(as_text=True)
    assert 'id="student-search"' in html