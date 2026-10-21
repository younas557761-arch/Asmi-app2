from app.services import builder as builder_service


def _setup(owner_client):
    c = owner_client
    year_id = c.post(
        "/api/v1/academic-years",
        json={"name": "2026-2027", "start_date": "2026-04-01", "end_date": "2027-03-31"},
    ).json()["id"]
    c.post(f"/api/v1/academic-years/{year_id}/activate")


def test_parse_command_variants():
    p = builder_service.parse_command("Add a new Grade 6 class")
    assert p["action"] == "create_class" and p["params"]["name"] == "Grade 6" and p["confidence"] == "high"

    p = builder_service.parse_command("create subject Physics")
    assert p["action"] == "create_subject" and p["params"]["name"] == "Physics"

    p = builder_service.parse_command("Add a monthly fee category Transport 1500")
    assert p["action"] == "create_fee_category" and p["params"]["amount"] == 1500

    p = builder_service.parse_command("academic year 2027-2028")
    assert p["action"] == "create_academic_year"
    assert p["params"]["start_date"] == "2027-04-01"

    p = builder_service.parse_command("fly me to the moon")
    assert p["action"] is None


def test_plan_approve_apply_flow(owner_client):
    c = owner_client
    _setup(c)

    r = c.post("/api/v1/builder/plan", json={"command": "Add a new Grade 6 class"})
    assert r.status_code == 201, r.text
    plan = r.json()
    assert plan["status"] == "pending"
    assert plan["plan"]["action"] == "create_class"
    assert plan["plan"]["validation"]["ok"] is True

    # approve applies the action
    r = c.post("/api/v1/builder/approve", json={"plan_id": plan["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "applied"

    # idempotent: second approve returns stored result
    r = c.post("/api/v1/builder/approve", json={"plan_id": plan["id"]})
    assert r.status_code == 200 and r.json()["status"] == "applied"

    # class actually exists
    classes = c.get("/api/v1/classes").json()["items"]
    assert any(cls["name"] == "Grade 6" for cls in classes)

    # plan history recorded
    plans = c.get("/api/v1/builder/plans").json()
    assert plans["total"] >= 1
    applied = [p for p in plans["items"] if p["status"] == "applied"]
    assert len(applied) == 1


def test_reject_plan(owner_client):
    c = owner_client
    _setup(c)
    plan = c.post("/api/v1/builder/plan", json={"command": "add subject Chemistry"}).json()
    r = c.post(f"/api/v1/builder/reject/{plan['id']}")
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    assert c.post(f"/api/v1/builder/reject/{plan['id']}").status_code == 409


def test_duplicate_detected_at_plan_time(owner_client):
    c = owner_client
    _setup(c)
    assert c.post("/api/v1/classes", json={"name": "Grade 1", "capacity": 40}).status_code == 201
    plan = c.post("/api/v1/builder/plan", json={"command": "Add a new Grade 1 class"}).json()
    assert plan["status"] == "rejected"
    assert any("already exists" in p for p in plan["plan"]["validation"]["problems"])
    # approval of a rejected plan is blocked
    assert c.post("/api/v1/builder/approve", json={"plan_id": plan["id"]}).status_code == 409


def test_arbitrary_sql_never_executed():
    """The registry only contains typed actions — no raw execution path exists."""
    import inspect

    from app.services import builder
    src = inspect.getsource(builder)
    for banned in ["execute(", "exec(", "subprocess", "os.system"]:
        assert banned not in src, f"unsafe construct found: {banned}"
    assert set(builder.ACTIONS.keys()) == {
        "create_class", "create_subject", "create_fee_category",
        "create_academic_year", "enroll_student", "add_teacher",
    }
