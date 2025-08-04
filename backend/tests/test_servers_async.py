import os
import pytest
from httpx import AsyncClient, ASGITransport
from docker.errors import BuildError

os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"
os.environ["ANYIO_BACKEND"] = "asyncio"

from backend.app.main import app
from backend.app.services.docker_manager import DockerManager
from backend.app.models.build_log import build_logs


@pytest.mark.anyio("asyncio")
async def test_build_and_log(monkeypatch):
    logs = [{"stream": "ok"}]

    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(
        DockerManager, "build_image", lambda self, t, v, tag: (logs, {"id": "imgid"})
    )
    build_logs.clear()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/login", json={"username": "admin", "password": "secret"}
        )
        assert resp.status_code == 200

        resp = await client.post(
            "/servers/build",
            json={"template": "FROM scratch", "version": "1", "tag": "test:1"},
        )
        assert resp.status_code == 200

        resp = await client.get("/servers/build/test:1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["log"] == logs


@pytest.mark.anyio("asyncio")
async def test_build_error_handling(monkeypatch):
    logs = [{"stream": "err"}]

    def fail_build(self, t, v, tag):
        raise BuildError("fail", build_log=logs)

    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(DockerManager, "build_image", fail_build)
    build_logs.clear()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/login", json={"username": "admin", "password": "secret"}
        )
        assert resp.status_code == 200

        resp = await client.post(
            "/servers/build",
            json={"template": "FROM scratch", "version": "1", "tag": "test:1"},
        )
        assert resp.status_code == 500

        resp = await client.get("/servers/build/test:1")
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"


@pytest.mark.anyio("asyncio")
async def test_get_build_log_not_found(monkeypatch):
    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    build_logs.clear()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/login", json={"username": "admin", "password": "secret"}
        )
        assert resp.status_code == 200

        resp = await client.get("/servers/build/missing")
        assert resp.status_code == 404


@pytest.mark.anyio("asyncio")
async def test_list_images(monkeypatch):
    images = [{"tag": "repo:tag", "template": "paper", "version": "1", "built": "123"}]

    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(DockerManager, "list_images", lambda self: images)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/login", json={"username": "admin", "password": "secret"}
        )
        assert resp.status_code == 200

        resp = await client.get("/servers/images")
        assert resp.status_code == 200
        assert resp.json() == {"images": images}


@pytest.mark.anyio("asyncio")
async def test_requires_auth(monkeypatch):
    monkeypatch.setattr(DockerManager, "__init__", lambda self: None)
    monkeypatch.setattr(DockerManager, "list_images", lambda self: [])

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/servers/images")
        assert resp.status_code == 401
