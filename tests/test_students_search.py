def add_students(client, admin):
    people = (("Asha Rao", "S3001"), ("Ravi Kumar", "S3002"), ("Asha Menon", "S3003"))
    for name, number in people:
        res = client.post("/students", headers=admin,
                          json={"name": name, "email": f"{number.lower()}@test.edu",
                                "program": "B.Tech CSE", "semester": 3,
                                "password": "pass1234", "studentNo": number})
        assert res.status_code == 201


def search(client, headers, q):
    return client.get("/students/search", query_string={"q": q}, headers=headers)


def test_tc_stu_04_search_by_full_student_number(client, login_as):
    _, admin = login_as("admin")
    _, faculty = login_as("faculty")
    add_students(client, admin)
    res = search(client, faculty, "S3002")
    assert res.status_code == 200
    assert [s["name"] for s in res.json["students"]] == ["Ravi Kumar"]


def test_tc_stu_04_search_by_partial_name_ignores_case(client, login_as):
    _, admin = login_as("admin")
    add_students(client, admin)
    res = search(client, admin, "asha")
    assert res.status_code == 200
    assert {s["name"] for s in res.json["students"]} == {"Asha Rao", "Asha Menon"}


def test_tc_stu_04_search_by_partial_student_number(client, login_as):
    _, admin = login_as("admin")
    add_students(client, admin)
    res = search(client, admin, "S300")
    assert [s["studentNo"] for s in res.json["students"]] == ["S3001", "S3002", "S3003"]


def test_tc_stu_04_no_match_returns_empty_list(client, login_as):
    _, admin = login_as("admin")
    add_students(client, admin)
    res = search(client, admin, "zzz-nobody")
    assert res.status_code == 200
    assert res.json["students"] == []


def test_tc_stu_04_empty_query_returns_400(client, login_as):
    _, admin = login_as("admin")
    for q in ("", "   "):
        res = search(client, admin, q)
        assert res.status_code == 400
        assert res.json["error"]["code"] == "missing_field"
    assert client.get("/students/search", headers=admin).status_code == 400


def test_tc_stu_04_student_cannot_search(client, login_as):
    _, admin = login_as("admin")
    add_students(client, admin)
    _, student = login_as("student")
    assert search(client, student, "Asha").status_code == 403
    assert client.get("/students/search", query_string={"q": "Asha"}).status_code == 401


def test_tc_stu_04_results_leave_out_contact_details(client, login_as):
    _, admin = login_as("admin")
    add_students(client, admin)
    result = search(client, admin, "S3001").json["students"][0]
    assert "email" not in result and "phone" not in result and "address" not in result


def test_tc_stu_04_wildcard_characters_are_treated_as_text(client, login_as):
    _, admin = login_as("admin")
    add_students(client, admin)
    assert search(client, admin, "%").json["students"] == []
    assert search(client, admin, "_").json["students"] == []