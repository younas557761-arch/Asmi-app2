from datetime import datetime, timezone


def _setup(owner_client):
    c = owner_client
    year_id = c.post(
        "/api/v1/academic-years",
        json={"name": "2026-2027", "start_date": "2026-04-01", "end_date": "2027-03-31"},
    ).json()["id"]
    c.post(f"/api/v1/academic-years/{year_id}/activate")
    c.post("/api/v1/classes", json={"name": "Grade 1", "capacity": 40})
    c.post(
        "/api/v1/teachers",
        json={"employee_number": "EMP-1", "first_name": "Sara", "subject": "Math"},
    )
    r = c.post(
        "/api/v1/students",
        json={"admission_number": "ADM-1", "first_name": "Ali", "class_name": "Grade 1"},
    )
    return r.json()["id"]


def test_dashboard_summary_real_counts(owner_client):
    c = owner_client
    sid = _setup(c)
    today = datetime.now(timezone.utc).date().isoformat()
    c.post(
        "/api/v1/attendance",
        json={"date": today, "records": [{"student_id": sid, "status": "present"}]},
    )

    summary = c.get("/api/v1/dashboard/summary").json()
    assert summary["students_active"] == 1
    assert summary["teachers_active"] == 1
    assert summary["classes_count"] == 1
    assert summary["attendance_today"]["marked"] is True
    assert summary["attendance_today"]["present"] == 1
    assert summary["setup_checklist"]["attendance_marked_today"] is True


def test_dashboard_summary_empty_school(owner_client):
    summary = owner_client.get("/api/v1/dashboard/summary").json()
    assert summary["students_active"] == 0
    assert summary["attendance_today"]["marked"] is False
    assert summary["setup_checklist"]["students_added"] is False


def test_verify_email_flow(owner_client):
    c = owner_client
    r = c.post("/api/v1/auth/verify-email/request")
    assert r.status_code == 200, r.text
    code = r.json()["message"].split(": ")[1]
    assert len(code) == 6 and code.isdigit()

    # wrong code consumes an attempt
    r = c.post("/api/v1/auth/verify-email/confirm", json={"code": "000000"})
    assert r.status_code == 400 and "attempts remaining" in r.json()["detail"]

    # correct code verifies
    r = c.post("/api/v1/auth/verify-email/confirm", json={"code": code})
    assert r.status_code == 200 and r.json()["message"] == "Email verified"

    # code is single-use
    assert c.post("/api/v1/auth/verify-email/confirm", json={"code": code}).status_code == 400

    # already verified -> no new code needed
    r = c.post("/api/v1/auth/verify-email/request")
    assert r.json()["message"] == "Email already verified"
