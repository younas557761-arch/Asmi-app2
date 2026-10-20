import os
import sys

os.environ["ASMI_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["ASMI_ENV"] = "development"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def register(client, email, school_name="Test School"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "school_name": school_name,
            "email": email,
            "password": "Passw0rd!x",
            "full_name": "Owner",
            "accept_terms": True,
        },
    )


@pytest.fixture()
def owner_client(client):
    register(client, "owner@school.com", "School A")
    yield client
    client.post("/api/v1/auth/logout")


@pytest.fixture()
def other_owner_client():
    with TestClient(app) as c:
        register(c, "owner@other.com", "School B")
        yield c
        c.post("/api/v1/auth/logout")
