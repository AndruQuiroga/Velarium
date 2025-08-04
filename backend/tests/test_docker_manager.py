import tarfile
import docker
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
