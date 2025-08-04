
"""Utilities for interacting with the local Docker daemon."""

from __future__ import annotations

import io
import os
import tarfile
import tempfile
import zipfile
from typing import Dict, List, Optional

import docker
import httpx
from docker.errors import APIError, BuildError


# Labels applied to images built by Velarium
PROJECT_LABEL_KEY = "velarium.project"
PROJECT_LABEL_VALUE = "velarium"
TEMPLATE_LABEL_KEY = "velarium.template"
VERSION_LABEL_KEY = "velarium.version"
BUILT_LABEL_KEY = "velarium.built"


class DockerManager:
    """Thin wrapper around the Docker SDK.

    The class currently exposes a :py:meth:`build_image` method which builds a
    docker image from a given Dockerfile template.  The implementation uses the
    low level API in order to stream build logs back to the caller.
    """

    def __init__(self) -> None:  # pragma: no cover - trivial
        self.client = docker.from_env()

    # ------------------------------------------------------------------
    def list_images(self) -> List[Dict[str, str]]:
        """Return metadata about images built by Velarium.

        The method queries the Docker daemon for images carrying the project
        label and extracts additional metadata from other labels applied to the
        image during the build process.
        """

        images = self.client.images.list(
            filters={"label": f"{PROJECT_LABEL_KEY}={PROJECT_LABEL_VALUE}"}
        )

        result: List[Dict[str, str]] = []
        for image in images:
            labels = getattr(image, "labels", None)
            if labels is None:
                labels = image.attrs.get("Config", {}).get("Labels", {})

            tag = image.tags[0] if getattr(image, "tags", None) else None
            result.append(
                {
                    "tag": tag,
                    "template": labels.get(TEMPLATE_LABEL_KEY, ""),
                    "version": labels.get(VERSION_LABEL_KEY, ""),
                    "built": labels.get(BUILT_LABEL_KEY, ""),
                }
            )

        return result

    def build_image(
        self,
        template: str,
        version: str,
        tag: str,
        modpack_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Build a docker image using a template string.

        Parameters
        ----------
        template:
            Dockerfile template containing ``{version}`` placeholder.
        version:
            Version string to substitute into the template.
        tag:
            Name of the resulting docker image tag.
        modpack_id:
            Optional identifier of a modpack to embed into the image.
        source:
            Source of the modpack. Either ``"modrinth"`` or ``"curseforge"``.

        Returns
        -------
        list of dict
            Structured build logs returned from the docker daemon.

        Raises
        ------
        docker.errors.BuildError
            If the build fails or the API reports an error.
        """

        # Assemble the Dockerfile by interpolating the provided version
        dockerfile_contents = template.format(version=version)

        # Create a tar archive to use as the build context containing the
        # Dockerfile and optional modpack contents.  The Docker SDK expects a
        # file-like object positioned at the start of the tar stream.
        fileobj = io.BytesIO()
        with tarfile.open(fileobj=fileobj, mode="w") as tar:
            data = dockerfile_contents.encode("utf-8")
            info = tarfile.TarInfo("Dockerfile")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

            if modpack_id and source:
                archive = self._download_modpack(modpack_id, source)
                with tempfile.TemporaryDirectory() as tmp:
                    archive_path = os.path.join(tmp, "modpack.zip")
                    with open(archive_path, "wb") as f:
                        f.write(archive)
                    with zipfile.ZipFile(archive_path) as zf:
                        zf.extractall(tmp)

                    # locate and add mods/config directories
                    for name in ("mods", "config"):
                        for root, dirs, _files in os.walk(tmp):
                            if os.path.basename(root) == name:
                                tar.add(root, arcname=name)
                                break
        fileobj.seek(0)

        try:
            output = self.client.api.build(
                fileobj=fileobj,
                custom_context=True,
                tag=tag,
                decode=True,
            )

            logs: List[Dict[str, str]] = []
            for chunk in output:
                logs.append(chunk)
                if "error" in chunk:
                    raise BuildError(chunk["error"], build_log=logs)
            return logs
        except APIError as exc:  # pragma: no cover - network / docker issues
            raise BuildError(str(exc), build_log=[]) from exc

    # ------------------------------------------------------------------
    def _download_modpack(self, modpack_id: str, source: str) -> bytes:
        """Download a modpack archive from the specified ``source``."""

        if source == "modrinth":
            resp = httpx.get(f"https://api.modrinth.com/v2/project/{modpack_id}/version")
            resp.raise_for_status()
            versions = resp.json()
            files = versions[0]["files"]
            download_url = files[0]["url"]
            file_resp = httpx.get(download_url)
            file_resp.raise_for_status()
            return file_resp.content
        if source == "curseforge":
            resp = httpx.get(f"https://api.curseforge.com/v1/mods/{modpack_id}/files")
            resp.raise_for_status()
            data = resp.json()["data"][0]
            download_url = data["downloadUrl"]
            file_resp = httpx.get(download_url)
            file_resp.raise_for_status()
            return file_resp.content
        raise ValueError(f"Unknown source: {source}")

