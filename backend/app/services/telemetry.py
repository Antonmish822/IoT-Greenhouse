from __future__ import annotations

from typing import Iterable

from sqlmodel import Session

from ..config import Settings
from ..repositories.devices import get_for_user
from ..schemas.telemetry import TelemetryRead, TelemetrySample
from ..services.thingsboard import fetch_device_telemetry

settings = Settings()


def get_device_telemetry(session: Session, user_id: int, device_id: int) -> TelemetryRead:
    device = get_for_user(session, user_id, device_id)
    if not device:
        raise ValueError("Device not found for current user")

    keys = [
        key.strip()
        for key in settings.thingsboard_telemetry_keys.split(",")
        if key.strip()
    ]
    telemetry_payload = fetch_device_telemetry(
        device_identifier=device.serial_number,
        keys=keys or None,
        limit=settings.thingsboard_telemetry_limit,
    )

    samples: dict[str, list[TelemetrySample]] = {}
    for key, values in telemetry_payload.items():
        if not isinstance(values, Iterable):
            continue
        normalized: list[TelemetrySample] = []
        for entry in values:
            raw_ts = entry.get("ts") or entry.get("timestamp")
            raw_value = entry.get("value")
            if raw_ts is None:
                continue
            normalized.append(
                TelemetrySample(
                    ts=int(raw_ts),
                    value=raw_value,
                )
            )
        if normalized:
            samples[key] = normalized

    return TelemetryRead(
        device_id=device.id,
        serial_number=device.serial_number,
        telemetry=samples,
    )