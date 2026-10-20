def _student_payload(n=1):
    return {
        "admission_number": f"ADM-{n}",
        "first_name": "Ali",
        "last_name": "Khan",
        "class_name": "Grade 1",
        "section": "A",
    }


def test_student_crud(owner_client):
    c = owner_client
    r = c.post("/api/v1/students", json=_student_payload())
    assert r.status_code == 201, r.text
    sid = r.json()["id"]

    assert c.get(f"/api/v1/students/{sid}").status_code == 200

    r = c.patch(f"/api/v1/students/{sid}", json={"last_name": "Ahmed"})
    assert r.status_code == 200 and r.json()["last_name"] == "Ahmed"

    listing = c.get("/api/v1/students?q=ali").json()
    assert listing["total"] == 1

    assert c.delete(f"/api/v1/students/{sid}").status_code == 204
    assert c.get(f"/api/v1/students/{sid}").status_code == 404


def test_duplicate_admission_number(owner_client):
    c = owner_client
    assert c.post("/api/v1/students", json=_student_payload()).status_code == 201
    assert c.post("/api/v1/students", json=_student_payload()).status_code == 409


def test_unauthenticated_blocked(client):
    assert client.get("/api/v1/students").status_code == 401
    assert client.get("/api/v1/schools/current").status_code == 401
