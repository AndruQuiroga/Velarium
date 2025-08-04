import os
from fastapi.testclient import TestClient

os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"

from backend.app.main import app
from backend.app.services.docker_manager import DockerManager


def test_build_server(monkeypatch):
    logs = [{"stream": "ok"}]

    def fake_build(self, template, version, tag):
        assert template == "FROM scratch"
        assert version == "1"
        assert tag == "test:1"
        return logs

    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(DockerManager, "build_image", fake_build)

    client = TestClient(app)
    resp = client.post("/login", json={"username": "admin", "password": "secret"})
    assert resp.status_code == 200

    resp = client.post("/servers/build", json={"template": "FROM scratch", "version": "1", "tag": "test:1"})
    assert resp.status_code == 200
    assert resp.json() == {"logs": logs}


def test_build_requires_auth(monkeypatch):
    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(DockerManager, "build_image", lambda self, t, v, tag: [])
    client = TestClient(app)
    resp = client.post("/servers/build", json={"template": "", "version": ""})
    assert resp.status_code == 401
