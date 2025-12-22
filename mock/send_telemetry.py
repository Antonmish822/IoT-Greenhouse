#!/usr/bin/env python3
"""Мок-датчик, отправляющий телеметрию на бекенд через HTTP POST."""

from __future__ import annotations

import json
import os
import pathlib
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Iterable, Sequence

DEFAULT_API_BASE_URL = "http://81.177.135.202:5010/api/v1"
DEFAULT_INTERVAL = 10.0
DEFAULT_TIMEOUT = 5.0
DEFAULT_CONFIG_FILE = pathlib.Path(__file__).resolve().parent / "config.json"


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(level: str, message: str) -> None:
    print(f"{iso_timestamp()} {level} {message}", flush=True)


def load_config(path: pathlib.Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"config file not found at {path}")
    try:
        raw = path.read_text()
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"unable to parse {path}: {exc}") from exc


def ensure_devices(tokens: Sequence[str]) -> Sequence[str]:
    cleaned = [str(token).strip() for token in tokens if str(token).strip()]
    if not cleaned:
        raise ValueError("config must expose a non-empty 'devices' list")
    return tuple(cleaned)


def ensure_positive(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def build_payload() -> dict:
    return {
        "temperature": round(22 + random.uniform(-0.4, 0.4), 1),
        "humidity": round(27 + random.uniform(-0.8, 0.8), 1),
    }


def loop(tokens: Sequence[str], api_base: str, interval: float, timeout: float) -> None:
    index = 0
    token_count = len(tokens)
    while True:
        token = tokens[index]
        index = (index + 1) % token_count
        payload = build_payload()
        url = f"{api_base}/{token}/telemetry"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        log("INFO", f"sending payload for {token}: {payload}")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
            log("INFO", f"request succeeded for {token}: {body}")
        except urllib.error.HTTPError as exc:
            log("ERROR", f"request failed for {token}: HTTP {exc.code} {exc.reason}")
        except urllib.error.URLError as exc:
            log("ERROR", f"request failed for {token}: {exc.reason}")
        except Exception as exc:  # pragma: no cover - safety net
            log("ERROR", f"unexpected error for {token}: {exc}")
        time.sleep(interval)


def main() -> int:
    config_path = pathlib.Path(os.environ.get("MOCK_CONFIG_FILE", DEFAULT_CONFIG_FILE))
    try:
        raw = load_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        log("ERROR", str(exc))
        return 1

    api_base_url = str(raw.get("api_base_url", DEFAULT_API_BASE_URL)).rstrip("/")
    interval = ensure_positive(float(raw.get("interval", DEFAULT_INTERVAL)), "interval")
    request_timeout = ensure_positive(float(raw.get("request_timeout_seconds", DEFAULT_TIMEOUT)), "request_timeout_seconds")

    try:
        tokens = ensure_devices(raw.get("devices", []))
    except ValueError as exc:
        log("ERROR", str(exc))
        return 1

    loop(tokens, api_base_url, interval, request_timeout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
