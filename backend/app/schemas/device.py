from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    name: str
    serial_number: str
    metadata: Optional[Dict[str, Any]] = None
    greenhouse_id: Optional[int] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    last_seen: Optional[datetime] = None
    greenhouse_id: Optional[int] = None


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    serial_number: str
    is_active: bool
    last_seen: Optional[datetime]
    metadata: Optional[Dict[str, Any]] = Field(alias="device_metadata")
    greenhouse_id: Optional[int] = None
    user_id: int
