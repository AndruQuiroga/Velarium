from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from docker.errors import BuildError

from ..auth import require_admin
from ..services.docker_manager import DockerManager
from ..models.build_log import BuildLog, build_logs

router = APIRouter(prefix="/servers", dependencies=[Depends(require_admin)])


class BuildPayload(BaseModel):
    template: str
    version: str
    tag: str | None = None


@router.post("/build")
def build_server(payload: BuildPayload):
    manager = DockerManager()
    tag = payload.tag or "latest"
    build_logs[tag] = BuildLog(tag=tag, status="building", log=[])
    try:
        logs, metadata = manager.build_image(payload.template, payload.version, tag)
        build_logs[tag].status = "success"
        build_logs[tag].log = logs
        return {"logs": logs, "metadata": metadata}
    except BuildError as exc:
        build_logs[tag].status = "error"
        build_logs[tag].log = exc.build_log if hasattr(exc, "build_log") else None
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/build/{tag}")
def get_build_log(tag: str):
    entry = build_logs.get(tag)
    if entry is None:
        raise HTTPException(status_code=404, detail="Build tag not found")
    return entry


@router.get("/images")
def list_images():
    manager = DockerManager()
    images = manager.list_images()
    return {"images": images}


@router.get("/")
def list_servers():
    return {"servers": []}

