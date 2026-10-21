def test_templates_catalogue(owner_client):
    r = owner_client.get("/api/v1/onboarding/templates")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 9
    keys = [t["key"] for t in items]
    for expected in ["primary", "secondary", "international", "custom"]:
        assert expected in keys
    primary = next(t for t in items if t["key"] == "primary")
    assert "Grade 1" in primary["grades"]


def test_modules_catalogue(owner_client):
    r = owner_client.get("/api/v1/onboarding/modules")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 10


def test_create_workspace_seeds_from_template(owner_client):
    c = owner_client
    r = c.post(
        "/api/v1/onboarding/create-workspace",
        json={
            "template_key": "primary",
            "school_name": "Sunrise Primary",
            "country": "Pakistan",
            "city": "Karachi",
            "timezone": "Asia/Karachi",
            "currency": "PKR",
            "language": "en",
            "academic_year": "2026-2027",
            "modules": ["students", "classes", "attendance", "fees", "exams"],
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["classes_created"] == 5        # Grade 1..5
    assert data["subjects_created"] == 5         # default subjects
    assert data["fee_categories_created"] == 3
    assert data["school"]["name"] == "Sunrise Primary"

    # everything actually landed in the database
    assert c.get("/api/v1/classes").json()["total"] == 5
    assert c.get("/api/v1/subjects").json()["total"] == 5
    fees = c.get("/api/v1/fees/categories").json()["total"]
    assert fees == 3
    year = c.get("/api/v1/academic-years").json()["items"][0]
    assert year["is_current"] is True

    # idempotent: running again creates nothing new
    r2 = c.post(
        "/api/v1/onboarding/create-workspace",
        json={
            "template_key": "primary",
            "school_name": "Sunrise Primary",
            "academic_year": "2026-2027",
            "modules": ["students", "classes", "fees"],
        },
    )
    assert r2.status_code == 201
    assert r2.json()["classes_created"] == 0
    assert c.get("/api/v1/classes").json()["total"] == 5


def test_custom_template_seeds_nothing(owner_client):
    c = owner_client
    r = c.post(
        "/api/v1/onboarding/create-workspace",
        json={
            "template_key": "custom",
            "school_name": "Blank Slate",
            "academic_year": "2026-2027",
            "modules": ["students"],
        },
    )
    assert r.status_code == 201
    assert r.json()["classes_created"] == 0
    assert c.get("/api/v1/classes").json()["total"] == 0


def test_unknown_template_rejected(owner_client):
    r = owner_client.post(
        "/api/v1/onboarding/create-workspace",
        json={"template_key": "hogwarts", "school_name": "X", "modules": []},
    )
    assert r.status_code == 404


def test_onboarding_isolated_per_school(owner_client, other_owner_client):
    owner_client.post(
        "/api/v1/onboarding/create-workspace",
        json={"template_key": "small", "school_name": "A", "modules": ["students"]},
    )
    assert other_owner_client.get("/api/v1/classes").json()["total"] == 0
