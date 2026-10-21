def _seed(owner_client):
    c = owner_client
    year_id = c.post(
        "/api/v1/academic-years",
        json={"name": "2026-2027", "start_date": "2026-04-01", "end_date": "2027-03-31"},
    ).json()["id"]
    c.post(f"/api/v1/academic-years/{year_id}/activate")
    c.post("/api/v1/classes", json={"name": "Grade 1", "capacity": 40})
    s1 = c.post(
        "/api/v1/students",
        json={"admission_number": "ADM-1", "first_name": "Ali", "class_name": "Grade 1"},
    ).json()["id"]
    s2 = c.post(
        "/api/v1/students",
        json={"admission_number": "ADM-2", "first_name": "Sara", "class_name": "Grade 1"},
    ).json()["id"]
    c.post("/api/v1/teachers", json={"employee_number": "EMP-1", "first_name": "Sir"})
    c.post(
        "/api/v1/fees/invoices",
        json={"student_id": s1, "title": "Oct", "items": [{"description": "T", "amount": 5000}]},
    )
    c.post("/api/v1/fees/payments", json={"student_id": s1, "amount": 2000})
    return s1, s2


def test_suggestions_endpoint(owner_client):
    r = owner_client.get("/api/v1/assistant/suggestions")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 4
    assert any("outstanding" in s for s in items)


def test_summary_answer_with_live_figures(owner_client):
    c = owner_client
    _seed(c)
    r = c.post("/api/v1/assistant/ask", json={"question": "Summarise this month for me"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["engine"] == "rule"
    assert data["figures"]["students"] == 2
    assert data["figures"]["teachers"] == 1
    assert data["figures"]["outstanding"] == 3000
    assert "Students: 2" in data["text"]


def test_outstanding_fees_answer(owner_client):
    c = owner_client
    _seed(c)
    r = c.post("/api/v1/assistant/ask", json={"question": "Which classes have outstanding fees?"})
    data = r.json()
    assert "ADM-1" in data["text"]
    assert data["figures"]["items"][0]["balance"] == 3000


def test_workflow_answer(owner_client):
    r = owner_client.post(
        "/api/v1/assistant/ask",
        json={"question": "Explain how to publish examination results"},
    )
    assert r.status_code == 200
    assert "Publish results" in r.json()["text"]


def test_assistant_cross_school_isolated(owner_client, other_owner_client):
    _seed(owner_client)
    r = other_owner_client.post("/api/v1/assistant/ask", json={"question": "Summarise this month"})
    assert r.json()["figures"]["students"] == 0
