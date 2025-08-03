from fastapi import APIRouter, Depends

from ..auth import require_admin

router = APIRouter(prefix="/servers", dependencies=[Depends(require_admin)])


@router.get("/")
def list_servers():
    return {"servers": []}
