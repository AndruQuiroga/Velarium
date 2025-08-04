import io
import tarfile
import zipfile

import docker
import httpx
import pytest

from backend.app.services.docker_manager import (
    BUILT_LABEL_KEY,
    PROJECT_LABEL_KEY,
    PROJECT_LABEL_VALUE,
    TEMPLATE_LABEL_KEY,
    VERSION_LABEL_KEY,
    DockerManager,
)


class DummyClient:
    def __init__(self, build_func, image_exists: bool = False):
        class API:
            def __init__(self, func):
                self._func = func

            def build(self, **kwargs):
                return self._func(**kwargs)

        class Images:
            def __init__(self, exists):
                self.exists = exists

            def get(self, tag):
                if self.exists:
                    return type("Image", (), {"id": "imgid"})
                raise docker.errors.ImageNotFound("not found")

        self.api = API(build_func)
        self.images = Images(image_exists)


def test_build_image_success(monkeypatch, tmp_path):
    logs = [{"stream": "ok"}]

    def fake_build(fileobj, custom_context, tag, decode):
        assert custom_context is True
        assert tag == "test:latest"
        assert decode is True
        fileobj.seek(0)
        with tarfile.open(fileobj=fileobj, mode="r") as tar:
            dockerfile = tar.extractfile("Dockerfile").read().decode()
            assert "123" in dockerfile
        client.images.exists = True
        return iter(logs)

    client = DummyClient(fake_build)
    monkeypatch.setattr(docker, "from_env", lambda: client)

    manager = DockerManager(metadata_path=tmp_path / "meta.json")
    result_logs, metadata = manager.build_image(
        "FROM scratch\nRUN echo {version}\n", "123", "test:latest"
    )
    assert result_logs == logs
    assert metadata == {"id": "imgid"}


def test_build_image_error(monkeypatch, tmp_path):
    def fake_build(**kwargs):
        return iter([{"error": "boom"}])

    monkeypatch.setattr(docker, "from_env", lambda: DummyClient(fake_build))

    manager = DockerManager(metadata_path=tmp_path / "meta.json")
    with pytest.raises(docker.errors.BuildError):
        manager.build_image("FROM scratch", "1", "fail")


def test_build_image_with_modpack(monkeypatch, tmp_path):
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
        client.images.exists = True
        return iter(logs)

    client = DummyClient(fake_build)
    monkeypatch.setattr(docker, "from_env", lambda: client)

    manager = DockerManager(metadata_path=tmp_path / "meta.json")
    result_logs, metadata = manager.build_image(
        "FROM scratch\n", "1", "test:latest", modpack_id="abc", source="modrinth"
    )
    assert result_logs == logs
    assert metadata == {"id": "imgid"}


def test_build_image_cached(monkeypatch, tmp_path):
    logs = [{"stream": "ok"}]

    def fake_build(fileobj, custom_context, tag, decode):
        client.images.exists = True
        return iter(logs)

    client = DummyClient(fake_build)
    monkeypatch.setattr(docker, "from_env", lambda: client)
    manager = DockerManager(metadata_path=tmp_path / "meta.json")
    manager.build_image("FROM scratch", "1", "test:latest")

    def fail_build(**kwargs):  # pragma: no cover - should not run
        raise AssertionError("build should not be called")

    client2 = DummyClient(fail_build, image_exists=True)
    monkeypatch.setattr(docker, "from_env", lambda: client2)
    manager2 = DockerManager(metadata_path=tmp_path / "meta.json")
    logs2, metadata2 = manager2.build_image("FROM scratch", "1", "test:latest")
    assert logs2 == []
    assert metadata2 == {"id": "imgid"}


def test_list_images(monkeypatch):
    captured_filters = {}

    class Images:
        def list(self, *, filters):
            captured_filters.update(filters)

            class Img:
                def __init__(self):
                    self.tags = ["repo:tag"]
                    self.attrs = {
                        "Config": {
                            "Labels": {
                                PROJECT_LABEL_KEY: PROJECT_LABEL_VALUE,
                                TEMPLATE_LABEL_KEY: "paper",
                                VERSION_LABEL_KEY: "1.0",
                                BUILT_LABEL_KEY: "123",
                            }
                        }
                    }

            return [Img()]

    class Dummy:
        def __init__(self):
            self.images = Images()

    monkeypatch.setattr(docker, "from_env", lambda: Dummy())

    manager = DockerManager()
    images = manager.list_images()

    assert captured_filters == {
        "label": f"{PROJECT_LABEL_KEY}={PROJECT_LABEL_VALUE}"
    }
    assert images == [
        {"tag": "repo:tag", "template": "paper", "version": "1.0", "built": "123"}
    ]

