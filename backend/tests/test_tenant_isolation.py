from tests.conftest import register


def test_cross_school_access_denied(owner_client, other_owner_client):
    r = owner_client.post(
        "/api/v1/students",
        json={
            "admission_number": "ADM-1",
            "first_name": "Secret",
            "last_name": "Student",
        },
    )
    sid = r.json()["id"]

    # Different school owner cannot read the student even with the id
    assert other_owner_client.get(f"/api/v1/students/{sid}").status_code == 404
    assert other_owner_client.patch(
        f"/api/v1/students/{sid}", json={"first_name": "Hacked"}
    ).status_code == 404
    assert other_owner_client.delete(f"/api/v1/students/{sid}").status_code == 404

    # Other school's listing does not leak the record
    listing = other_owner_client.get("/api/v1/students").json()
    assert listing["total"] == 0


def test_admission_numbers_unique_per_school(owner_client, other_owner_client):
    payload = {"admission_number": "ADM-1", "first_name": "A"}
    assert owner_client.post("/api/v1/students", json=payload).status_code == 201
    # Same admission number is fine in another school
    assert other_owner_client.post("/api/v1/students", json=payload).status_code == 201


def test_school_settings_isolated(owner_client, other_owner_client):
    owner_client.patch("/api/v1/schools/current", json={"name": "Renamed A"})
    mine = owner_client.get("/api/v1/schools/current").json()
    theirs = other_owner_client.get("/api/v1/schools/current").json()
    assert mine["name"] == "Renamed A"
    assert theirs["name"] == "School B"
