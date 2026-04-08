from datetime import datetime
from typing import Iterable

import httpx
from sqlmodel import Session

from ..config import Settings
from ..models import Device
from ..repositories.devices import (
    delete as delete_device_record,
    get_by_serial,
    get_for_user,
    list_for_user,
    list_for_user_and_greenhouse,
    save as persist_device,
)
from ..schemas.device import DeviceCreate, DeviceUpdate
from ..services.greenhouses import get_greenhouse_for_user

settings = Settings()


def _get_device_by_serial(session: Session, serial_number: str) -> Device | None:
    return get_by_serial(session, serial_number)


def _get_thingsboard_token() -> str:
    if settings.thingsboard_token:
        return settings.thingsboard_token

    if not all(
        [
            settings.thingsboard_url,
            settings.thingsboard_username,
            settings.thingsboard_password,
        ]
    ):
        raise RuntimeError("ThingsBoard configuration missing")

    path = settings.thingsboard_login_path
    if not path.startswith("/"):
        path = "/" + path
    url = settings.thingsboard_url.rstrip("/") + path
    payload = {
        "username": settings.thingsboard_username,
        "password": settings.thingsboard_password,
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"ThingsBoard authentication failed ({exc.response.status_code}): "
            f"{exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to authenticate against ThingsBoard") from exc

    payload = response.json()
    token = payload.get("token") or payload.get("jwt") or payload.get("accessToken")
    if not token:
        raise RuntimeError("ThingsBoard login response did not return a token")
    return token


def _verify_device_on_thingsboard(serial_number: str) -> None:
    if not settings.thingsboard_url:
        raise RuntimeError("ThingsBoard URL is not configured")

    path = settings.thingsboard_device_check_path
    if not path.startswith("/"):
        path = "/" + path
    url = settings.thingsboard_url.rstrip("/") + path.format(
        serial_number=serial_number
    )
    token = _get_thingsboard_token()
    headers = {"X-Authorization": f"Bearer {token}"}
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to contact ThingsBoard") from exc

    if response.status_code != 200:
        raise ValueError("Device not registered on ThingsBoard")


def _ensure_greenhouse_belongs_to_user(
    session: Session, user_id: int, greenhouse_id: int | None
) -> None:
    if greenhouse_id is None:
        return
    if not get_greenhouse_for_user(session, user_id, greenhouse_id):
        raise ValueError("Greenhouse not found for current user")


def get_device_for_user(
    session: Session, user_id: int, device_id: int
) -> Device | None:
    return get_for_user(session, user_id, device_id)


def get_devices_for_user(session: Session, user_id: int) -> Iterable[Device]:
    return list_for_user(session, user_id)


def list_devices_for_greenhouse(
    session: Session, user_id: int, greenhouse_id: int
) -> Iterable[Device]:
    return list_for_user_and_greenhouse(session, user_id, greenhouse_id)


def create_device(session: Session, user_id: int, payload: DeviceCreate) -> Device:
    if _get_device_by_serial(session, payload.serial_number):
        raise ValueError("Device with this serial number already exists")
    _verify_device_on_thingsboard(payload.serial_number)
    _ensure_greenhouse_belongs_to_user(session, user_id, payload.greenhouse_id)
    device = Device(
        name=payload.name,
        serial_number=payload.serial_number,
        device_metadata=payload.metadata,
        user_id=user_id,
        greenhouse_id=payload.greenhouse_id,
        last_seen=datetime.utcnow(),
    )
    return persist_device(session, device)


def update_device(session: Session, device: Device, payload: DeviceUpdate) -> Device:
    updated = False
    if payload.name is not None:
        device.name = payload.name
        updated = True
    if payload.metadata is not None:
        device.device_metadata = payload.metadata
        updated = True
    if payload.is_active is not None:
        device.is_active = payload.is_active
        updated = True
    if payload.last_seen is not None:
        device.last_seen = payload.last_seen
        updated = True
    if payload.greenhouse_id is not None:
        _ensure_greenhouse_belongs_to_user(
            session, device.user_id, payload.greenhouse_id
        )
        device.greenhouse_id = payload.greenhouse_id
        updated = True
    if updated:
        return persist_device(session, device)
    return device


def delete_device(session: Session, device: Device) -> None:
    delete_device_record(session, device)
