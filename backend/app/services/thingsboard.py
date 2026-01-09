from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import httpx

from ..config import Settings

settings = Settings()


def _normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    base_url = settings.thingsboard_url.rstrip("/")
    return base_url + path


def get_thingsboard_token() -> str:
    if settings.thingsboard_token:
        return settings.thingsboard_token

    required = [
        settings.thingsboard_url,
        settings.thingsboard_username,
        settings.thingsboard_password,
    ]
    if not all(required):
        raise RuntimeError("ThingsBoard configuration missing")

    url = _normalize_path(settings.thingsboard_login_path)
    payload = {
        "username": settings.thingsboard_username,
        "password": settings.thingsboard_password,
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.thingsboard_request_timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"ThingsBoard authentication failed ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to authenticate against ThingsBoard") from exc

    payload = response.json()
    token = payload.get("token") or payload.get("jwt") or payload.get("accessToken")
    if not token:
        raise RuntimeError("ThingsBoard login response did not return a token")
    return token


def verify_device_exists(serial_number: str) -> None:
    if not settings.thingsboard_url:
        raise RuntimeError("ThingsBoard URL is not configured")

    path = settings.thingsboard_device_check_path.format(serial_number=serial_number)
    url = _normalize_path(path)
    token = get_thingsboard_token()
    headers = {"X-Authorization": f"Bearer {token}"}
    try:
        response = httpx.get(url, headers=headers, timeout=settings.thingsboard_request_timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ValueError(
            f"Device {serial_number} not available on ThingsBoard ({exc.response.status_code})"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to contact ThingsBoard") from exc


def fetch_device_telemetry(
    device_identifier: str,
    keys: Sequence[str] | None = None,
    limit: int | None = None,
) -> Mapping[str, Iterable[Mapping[str, Any]]]:
    if not settings.thingsboard_url:
        raise RuntimeError("ThingsBoard URL is not configured")

    path = settings.thingsboard_telemetry_path.format(device_id=device_identifier)
    url = _normalize_path(path)
    token = get_thingsboard_token()
    headers = {"X-Authorization": f"Bearer {token}"}
    params: dict[str, Any] = {}
    if keys:
        params["keys"] = ",".join(keys)
    if limit is not None:
        params["limit"] = limit

    try:
        response = httpx.get(
            url, headers=headers, params=params, timeout=settings.thingsboard_request_timeout
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to read telemetry from ThingsBoard") from exc

    return response.json()


def send_rpc_request(device_id: str, method: str, params: dict[str, Any]) -> None:
    if not settings.thingsboard_url:
        raise RuntimeError("ThingsBoard URL is not configured")

    path = f"/api/plugins/rpc/oneway/{device_id}"
    url = _normalize_path(path)
    token = get_thingsboard_token()
    headers = {"X-Authorization": f"Bearer {token}"}
    payload = {"method": method, "params": params}

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=settings.thingsboard_request_timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"ThingsBoard RPC request failed ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError("Failed to send RPC request to ThingsBoard") from exc