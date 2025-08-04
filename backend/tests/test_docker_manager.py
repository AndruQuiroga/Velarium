import io
import tarfile
import zipfile
import docker
import httpx
import pytest

from backend.app.services.docker_manager import DockerManager


class DummyClient:
    def __init__(self, build_func):
        class API:
            def __init__(self, func):
                self._func = func

            def build(self, **kwargs):
                return self._func(**kwargs)

        self.api = API(build_func)


def test_build_image_success(monkeypatch):
    logs = [{"stream": "ok"}]

    def fake_build(fileobj, custom_context, tag, decode):
        assert custom_context is True
        assert tag == "test:latest"
        assert decode is True
        fileobj.seek(0)
        with tarfile.open(fileobj=fileobj, mode="r") as tar:
            dockerfile = tar.extractfile("Dockerfile").read().decode()
            assert "123" in dockerfile
        return iter(logs)

    monkeypatch.setattr(docker, "from_env", lambda: DummyClient(fake_build))

    manager = DockerManager()
    result = manager.build_image("FROM scratch\nRUN echo {version}\n", "123", "test:latest")
    assert result == logs


def test_build_image_error(monkeypatch):
    def fake_build(**kwargs):
        return iter([{ "error": "boom" }])

    monkeypatch.setattr(docker, "from_env", lambda: DummyClient(fake_build))

    manager = DockerManager()
    with pytest.raises(docker.errors.BuildError):
        manager.build_image("FROM scratch", "1", "fail")


def test_build_image_with_modpack(monkeypatch):
    logs = [{"stream": "ok"}]

    # Create an in-memory zip containing mods and config
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mods/mod.jar", b"mod")
        zf.writestr("config/conf.yml", b"cfg")
    buf.seek(0)
    archive_bytes = buf.read()

    def fake_httpx_get(url, *args, **kwargs):
        class Response:
            def __init__(self, content=None, json_data=None):
                self.content = content
                self._json = json_data

            def raise_for_status(self):
                pass

            def json(self):
                return self._json

        if url.startswith("https://api.modrinth.com"):
            return Response(json_data=[{"files": [{"url": "https://download"}]}])
        return Response(content=archive_bytes)

    monkeypatch.setattr(httpx, "get", fake_httpx_get)

    def fake_build(fileobj, custom_context, tag, decode):
        fileobj.seek(0)
        with tarfile.open(fileobj=fileobj, mode="r") as tar:
            names = tar.getnames()
            assert "mods/mod.jar" in names
            assert "config/conf.yml" in names
        return iter(logs)

    monkeypatch.setattr(docker, "from_env", lambda: DummyClient(fake_build))

    manager = DockerManager()
    result = manager.build_image(
        "FROM scratch\n", "1", "test:latest", modpack_id="abc", source="modrinth"
    )
    assert result == logs
