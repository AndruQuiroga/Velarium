import os
from fastapi.testclient import TestClient

os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"

from backend.app.main import app


def test_token_login_and_access():
    client = TestClient(app)
    resp = client.post("/login", json={"username": "admin", "password": "secret", "use_token": True})
    assert resp.status_code == 200
    token = resp.json()["token"]
    r = client.get("/servers", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "servers" in r.json()


def test_session_login_and_access():
    client = TestClient(app)
    resp = client.post("/login", json={"username": "admin", "password": "secret"})
    assert resp.status_code == 200
    r = client.get("/servers")
    assert r.status_code == 200
    assert "servers" in r.json()


def test_requires_auth():
    client = TestClient(app)
    r = client.get("/servers")
    assert r.status_code == 401
