from tests.conftest import register


def test_register_login_me_logout(client):
    r = register(client, "a@b.com")
    assert r.status_code == 201, r.text
    assert r.cookies.get("asmi_session")

    client.post("/api/v1/auth/logout")
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 401

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "a@b.com", "password": "Passw0rd!x"},
    )
    assert r.status_code == 200, r.text
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["school"]["name"] == "Test School"


def test_duplicate_email_rejected(client):
    assert register(client, "dup@x.com").status_code == 201
    assert register(client, "dup@x.com").status_code == 409


def test_terms_required(client):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "school_name": "S",
            "email": "t@x.com",
            "password": "Passw0rd!x",
            "accept_terms": False,
        },
    )
    assert r.status_code == 422


def test_short_password_rejected(client):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "school_name": "S",
            "email": "s2@x.com",
            "password": "short",
            "accept_terms": True,
        },
    )
    assert r.status_code == 422


def test_password_reset_flow(client):
    register(client, "r@x.com")
    r = client.post("/api/v1/auth/password-reset", json={"email": "r@x.com"})
    assert r.status_code == 200
    token = r.json()["message"].split(": ")[1]
    r = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "NewPassw0rd!1"},
    )
    assert r.status_code == 200, r.text
    # token is single-use
    r = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "AnotherPass!2"},
    )
    assert r.status_code == 400


def test_bad_login_rejected(client):
    register(client, "b@x.com")
    client.post("/api/v1/auth/logout")
    r = client.post(
        "/api/v1/auth/login", json={"email": "b@x.com", "password": "wrong"}
    )
    assert r.status_code == 401
