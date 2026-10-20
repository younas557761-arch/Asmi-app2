SCHEME = {
    "name": "Standard A-F",
    "pass_mark": 40,
    "bands": [
        {"grade": "A", "min_percentage": 80},
        {"grade": "B", "min_percentage": 60},
        {"grade": "F", "min_percentage": 0},
    ],
}


def _mk_student(c, n):
    r = c.post(
        "/api/v1/students",
        json={"admission_number": f"ADM-{n}", "first_name": f"Student{n}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_scheme_exam_results_and_publish(owner_client):
    c = owner_client
    r = c.post("/api/v1/exams/schemes", json=SCHEME)
    assert r.status_code == 201, r.text
    assert len(r.json()["bands"]) == 3
    assert c.post("/api/v1/exams/schemes", json=SCHEME).status_code == 409

    exam = c.post(
        "/api/v1/exams",
        json={"name": "Midterm", "start_date": "2026-10-01", "end_date": "2026-10-10"},
    )
    assert exam.status_code == 201, exam.text
    exam_id = exam.json()["id"]
    assert c.post(
        "/api/v1/exams",
        json={"name": "Midterm", "start_date": "2026-10-01", "end_date": "2026-10-10"},
    ).status_code == 409

    s1 = _mk_student(c, 1)
    s2 = _mk_student(c, 2)
    marks = {
        "records": [
            {"student_id": s1, "subject": "Math", "max_marks": 100, "marks_obtained": 85},
            {"student_id": s1, "subject": "English", "max_marks": 100, "marks_obtained": 70},
            {"student_id": s2, "subject": "Math", "max_marks": 100, "marks_obtained": 50},
            {"student_id": s2, "subject": "English", "max_marks": 100, "marks_obtained": 40},
        ]
    }
    r = c.post(f"/api/v1/exams/{exam_id}/marks", json=marks)
    assert r.status_code == 201, r.text

    # marks above max rejected
    bad = {"records": [{"student_id": s1, "subject": "Urdu", "max_marks": 50, "marks_obtained": 60}]}
    assert c.post(f"/api/v1/exams/{exam_id}/marks", json=bad).status_code == 422

    results = c.get(f"/api/v1/exams/{exam_id}/results").json()
    by_id = {r["student_id"]: r for r in results["items"]}
    assert by_id[s1]["percentage"] == 77.5 and by_id[s1]["grade"] == "B" and by_id[s1]["passed"] is True
    assert by_id[s2]["percentage"] == 45 and by_id[s2]["grade"] == "F" and by_id[s2]["passed"] is False

    # publish gate
    r = c.post(f"/api/v1/exams/{exam_id}/publish")
    assert r.status_code == 200 and r.json()["published"] is True

    # marks locked after publishing
    assert c.post(f"/api/v1/exams/{exam_id}/marks", json=marks).status_code == 409


def test_exams_cross_school_isolated(owner_client, other_owner_client):
    exam = owner_client.post(
        "/api/v1/exams",
        json={"name": "Finals", "start_date": "2026-12-01", "end_date": "2026-12-10"},
    ).json()
    assert other_owner_client.get(f"/api/v1/exams/{exam['id']}").status_code == 404
    assert other_owner_client.get("/api/v1/exams").json()["total"] == 0
