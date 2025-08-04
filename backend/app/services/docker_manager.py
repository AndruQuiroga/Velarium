
"""Utilities for interacting with the local Docker daemon."""

from __future__ import annotations

import io
import tarfile
from typing import Dict, List

import docker
from docker.errors import APIError, BuildError


class DockerManager:
    """Thin wrapper around the Docker SDK.

    The class currently exposes a :py:meth:`build_image` method which builds a
    docker image from a given Dockerfile template.  The implementation uses the
    low level API in order to stream build logs back to the caller.
    """

    def __init__(self) -> None:  # pragma: no cover - trivial
        self.client = docker.from_env()

    def build_image(self, template: str, version: str, tag: str) -> List[Dict[str, str]]:
        """Build a docker image using a template string.

        Parameters
        ----------
        template:
            Dockerfile template containing ``{version}`` placeholder.
        version:
            Version string to substitute into the template.
        tag:
            Name of the resulting docker image tag.

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

        # Create a tar archive to use as the build context containing only the
        # Dockerfile.  The Docker SDK expects a file-like object positioned at
        # the start of the tar stream.
        fileobj = io.BytesIO()
        with tarfile.open(fileobj=fileobj, mode="w") as tar:
            data = dockerfile_contents.encode("utf-8")
            info = tarfile.TarInfo("Dockerfile")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
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

