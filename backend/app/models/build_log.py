from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class BuildLog(BaseModel):
    """Record of a server build."""

    tag: str
    status: str
    log: Optional[List[Dict[str, str]]] = None


# In-memory store of build logs keyed by tag
build_logs: dict[str, BuildLog] = {}
