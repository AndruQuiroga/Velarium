
"""Utilities for interacting with the local Docker daemon."""

from __future__ import annotations

import io
import json
import os
import tarfile
import tempfile
import zipfile
from typing import Dict, List, Optional, Tuple

import docker
import httpx
from docker.errors import APIError, BuildError, ImageNotFound


# Labels applied to images built by Velarium
PROJECT_LABEL_KEY = "velarium.project"
PROJECT_LABEL_VALUE = "velarium"
TEMPLATE_LABEL_KEY = "velarium.template"
VERSION_LABEL_KEY = "velarium.version"
BUILT_LABEL_KEY = "velarium.built"


class DockerManager:
    """Thin wrapper around the Docker SDK with simple build caching."""

    def __init__(self, metadata_path: str = "build_metadata.json") -> None:
        self.client = docker.from_env()
        self.metadata_path = metadata_path
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        else:  # pragma: no cover - trivial
            self._metadata = {}

    def _save_metadata(self) -> None:
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f)

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
    ) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
        """Build a docker image using a template string or return cached metadata.

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
        tuple
            ``(logs, metadata)`` where ``logs`` is the structured build logs and
            ``metadata`` contains information about the built image (currently
            the image id).

        Raises
        ------
        docker.errors.BuildError
            If the build fails or the API reports an error.
        """

        # Check for existing image and short-circuit if present
        if tag in self._metadata:
            try:
                self.client.images.get(tag)
                return [], self._metadata[tag]
            except ImageNotFound:
                del self._metadata[tag]
                self._save_metadata()

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

            image = self.client.images.get(tag)
            metadata = {"id": image.id}
            self._metadata[tag] = metadata
            self._save_metadata()
            return logs, metadata
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

