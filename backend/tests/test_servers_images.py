import os
from fastapi.testclient import TestClient

os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"

from backend.app.main import app
from backend.app.services.docker_manager import DockerManager


def test_list_images(monkeypatch):
    images = [
        {"tag": "repo:tag", "template": "paper", "version": "1.0", "built": "123"}
    ]

    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(DockerManager, "list_images", lambda self: images)

    client = TestClient(app)
    resp = client.post("/login", json={"username": "admin", "password": "secret"})
    assert resp.status_code == 200

    resp = client.get("/servers/images")
    assert resp.status_code == 200
    assert resp.json() == {"images": images}


def test_list_images_requires_auth(monkeypatch):
    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(DockerManager, "list_images", lambda self: [])
    client = TestClient(app)
    resp = client.get("/servers/images")
    assert resp.status_code == 401
