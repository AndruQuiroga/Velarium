from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import require_admin
from ..services.docker_manager import DockerManager

router = APIRouter(prefix="/servers", dependencies=[Depends(require_admin)])


class BuildPayload(BaseModel):
    template: str
    version: str
    tag: str | None = None


@router.post("/build")
def build_server(payload: BuildPayload):
    manager = DockerManager()
    tag = payload.tag or "latest"
    logs, metadata = manager.build_image(payload.template, payload.version, tag)
    return {"logs": logs, "metadata": metadata}


@router.get("/images")
def list_images():
    manager = DockerManager()
    images = manager.list_images()
    return {"images": images}


@router.get("/")
def list_servers():
    return {"servers": []}

