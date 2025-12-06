from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from pydantic import BaseModel, Field


class TelemetrySample(BaseModel):
    ts: int
    value: Any


class TelemetryRead(BaseModel):
    device_id: int
    serial_number: str
    telemetry: Mapping[str, list[TelemetrySample]]
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)