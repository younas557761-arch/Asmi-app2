DATE = "2026-10-20"


def _mk_student(c, n, class_name="Grade 1"):
    r = c.post(
        "/api/v1/students",
        json={
            "admission_number": f"ADM-{n}",
            "first_name": f"Student{n}",
            "class_name": class_name,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_mark_and_summary(owner_client):
    c = owner_client
    ids = [_mk_student(c, 1), _mk_student(c, 2), _mk_student(c, 3)]
    payload = {
        "date": DATE,
        "records": [
            {"student_id": ids[0], "status": "present"},
            {"student_id": ids[1], "status": "absent"},
            {"student_id": ids[2], "status": "late"},
        ],
    }
    r = c.post("/api/v1/attendance", json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["marked"] == 3

    # duplicate submission blocked
    assert c.post("/api/v1/attendance", json=payload).status_code == 409

    summary = c.get(f"/api/v1/attendance/summary?date={DATE}").json()
    assert summary["present"] == 1
    assert summary["absent"] == 1
    assert summary["late"] == 1
    assert summary["total"] == 3
    assert summary["marked"] is True

    listing = c.get(f"/api/v1/attendance?date={DATE}").json()
    assert listing["total"] == 3
    assert listing["items"][0]["class_name"] == "Grade 1"


def test_correction(owner_client):
    c = owner_client
    sid = _mk_student(c, 9)
    c.post(
        "/api/v1/attendance",
        json={"date": DATE, "records": [{"student_id": sid, "status": "absent"}]},
    )
    listing = c.get(f"/api/v1/attendance?date={DATE}").json()
    record_id = listing["items"][0]["id"]

    r = c.patch(
        f"/api/v1/attendance/{record_id}",
        json={"status": "excused", "note": "Medical certificate provided"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "excused"

    summary = c.get(f"/api/v1/attendance/summary?date={DATE}").json()
    assert summary["absent"] == 0 and summary["excused"] == 1


def test_other_school_cannot_mark(owner_client, other_owner_client):
    sid = _mk_student(owner_client, 5)
    r = other_owner_client.post(
        "/api/v1/attendance",
        json={"date": DATE, "records": [{"student_id": sid, "status": "present"}]},
    )
    assert r.status_code == 404
