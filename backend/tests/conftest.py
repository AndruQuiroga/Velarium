import os
import sys
import io
import zipfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def template_dir(tmp_path):
    """Create a temporary directory containing a sample Dockerfile template."""

    path = tmp_path / "templates"
    path.mkdir()
    (path / "Dockerfile").write_text("FROM scratch\nRUN echo {version}\n", encoding="utf-8")
    return path


@pytest.fixture
def modpack_metadata():
    """Return archive bytes and metadata for a dummy modpack."""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mods/mod.jar", b"mod")
        zf.writestr("config/conf.yml", b"cfg")
    buf.seek(0)
    archive = buf.read()
    metadata = [{"files": [{"url": "https://download"}]}]
    return archive, metadata


@pytest.fixture(scope="session")
def anyio_backend():  # pragma: no cover - configuration for anyio tests
    """Use asyncio backend for httpx.AsyncClient tests."""
    return "asyncio"

