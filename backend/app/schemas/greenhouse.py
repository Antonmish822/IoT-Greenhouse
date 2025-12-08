from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class GreenhouseBase(BaseModel):
    name: str
    location: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class GreenhouseCreate(GreenhouseBase):
    pass


class GreenhouseUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class GreenhouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    location: Optional[str]
    metadata: Optional[Dict[str, str]] = Field(alias="greenhouse_metadata")
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_id: int