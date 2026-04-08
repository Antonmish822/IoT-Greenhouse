from pydantic import BaseModel
from typing import Any, Dict


class RpcRequest(BaseModel):
    method: str
    params: Dict[str, Any]
