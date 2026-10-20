def _year_payload(name="2026-2027"):
    return {"name": name, "start_date": "2026-04-01", "end_date": "2027-03-31"}


def _class_payload(name="Grade 1"):
    return {"name": name, "capacity": 40}


def test_year_crud_and_activation(owner_client):
    c = owner_client
    r = c.post("/api/v1/academic-years", json=_year_payload())
    assert r.status_code == 201, r.text
    year_id = r.json()["id"]

    # duplicate name rejected
    assert c.post("/api/v1/academic-years", json=_year_payload()).status_code == 409

    # activation sets is_current
    r = c.post(f"/api/v1/academic-years/{year_id}/activate")
    assert r.status_code == 200 and r.json()["is_current"] is True

    listing = c.get("/api/v1/academic-years").json()
    assert listing["total"] == 1


def test_class_requires_year_and_blocks_duplicates(owner_client):
    c = owner_client
    # no year exists yet -> class creation rejected with guidance
    r = c.post("/api/v1/classes", json=_class_payload())
    assert r.status_code == 422, r.text

    year_id = c.post("/api/v1/academic-years", json=_year_payload()).json()["id"]
    c.post(f"/api/v1/academic-years/{year_id}/activate")

    r = c.post("/api/v1/classes", json=_class_payload())
    assert r.status_code == 201, r.text
    class_id = r.json()["id"]
    assert r.json()["academic_year_id"] == year_id

    # same class name in same year -> 409
    assert c.post("/api/v1/classes", json=_class_payload()).status_code == 409

    # update + delete
    r = c.patch(f"/api/v1/classes/{class_id}", json={"capacity": 45})
    assert r.status_code == 200 and r.json()["capacity"] == 45
    assert c.delete(f"/api/v1/classes/{class_id}").status_code == 204


def test_class_cross_school_isolated(owner_client, other_owner_client):
    year_id = owner_client.post("/api/v1/academic-years", json=_year_payload()).json()["id"]
    owner_client.post(f"/api/v1/academic-years/{year_id}/activate")
    class_id = owner_client.post("/api/v1/classes", json=_class_payload()).json()["id"]

    assert other_owner_client.get(f"/api/v1/classes/{class_id}").status_code == 404
    assert other_owner_client.delete(f"/api/v1/classes/{class_id}").status_code == 404
    assert other_owner_client.get("/api/v1/classes").json()["total"] == 0


def test_subject_crud(owner_client):
    c = owner_client
    r = c.post("/api/v1/subjects", json={"name": "Mathematics", "code": "MATH"})
    assert r.status_code == 201, r.text
    subject_id = r.json()["id"]

    assert c.post("/api/v1/subjects", json={"name": "Mathematics"}).status_code == 409

    listing = c.get("/api/v1/subjects").json()
    assert listing["total"] == 1 and listing["items"][0]["code"] == "MATH"

    assert c.delete(f"/api/v1/subjects/{subject_id}").status_code == 204
