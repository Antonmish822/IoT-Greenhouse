from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Iterable

from sqlmodel import Session

from ..database import engine
from ..models import AutomationSetting, Device, Greenhouse
from ..repositories.automation import get_for_greenhouse, list_all, save
from ..repositories.devices import list_for_user_and_greenhouse
from ..schemas.automation import AutomationSettingUpdate
from ..schemas.telemetry import TelemetryRead
from ..services.greenhouses import get_greenhouse_for_user
from ..services.telemetry import get_device_telemetry
from ..services.thingsboard import send_rpc_request

logger = logging.getLogger(__name__)


def get_or_create_setting(session: Session, greenhouse_id: int, user_id: int) -> AutomationSetting:
    get_greenhouse_for_user(session, user_id, greenhouse_id)
    setting = get_for_greenhouse(session, greenhouse_id)
    if not setting:
        setting = AutomationSetting(greenhouse_id=greenhouse_id)
        setting = save(session, setting)
    return setting


def update_setting(
    session: Session, greenhouse_id: int, user_id: int, payload: AutomationSettingUpdate
) -> AutomationSetting:
    greenhouse = get_greenhouse_for_user(session, user_id, greenhouse_id)
    if not greenhouse:
        raise ValueError("Greenhouse not found")
    setting = get_or_create_setting(session, greenhouse_id, user_id)
    changed = False

    if payload.auto_mode is not None and payload.auto_mode != setting.auto_mode:
        setting.auto_mode = payload.auto_mode
        changed = True

    if (
        payload.target_temperature is not None
        and payload.target_temperature != setting.target_temperature
    ):
        setting.target_temperature = payload.target_temperature
        changed = True

    if payload.hysteresis is not None and payload.hysteresis != setting.hysteresis:
        setting.hysteresis = payload.hysteresis
        changed = True

    if changed:
        setting.updated_at = datetime.utcnow()
        setting = save(session, setting)
    return setting


def _temperature_thresholds(setting: AutomationSetting) -> tuple[float, float]:
    delta = setting.hysteresis / 2
    return (
        setting.target_temperature - delta,
        setting.target_temperature + delta,
    )


def _is_sensor(device: Device) -> bool:
    metadata = device.device_metadata or {}
    device_type = metadata.get("device_type")
    return device_type in {"telemetry", "sensor"} or metadata.get("sensor_type")


def _is_actuator(device: Device) -> bool:
    metadata = device.device_metadata or {}
    device_type = metadata.get("device_type")
    return device_type == "actuator" or metadata.get("actuator_type")


def _extract_numeric(samples: Iterable[dict]) -> float | None:
    for sample in reversed(list(samples)):
        value = sample.get("value")
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _extract_state(samples: Iterable[dict]) -> str | None:
    for sample in reversed(list(samples)):
        value = sample.get("value")
        if value is None:
            continue
        if isinstance(value, str):
            norm = value.strip().lower()
            if norm in {"true", "false"}:
                return norm
            if norm in {"open", "opened", "opening"}:
                return "true"
            if norm in {"close", "closed", "closing"}:
                return "false"
        if isinstance(value, (int, float)):
            return "true" if value else "false"
    return None


def _get_temperature_from_telemetry(
    telemetry_map: dict[int, TelemetryRead], devices: Iterable[Device]
) -> float | None:
    for device in devices:
        if not _is_sensor(device):
            continue
        record = telemetry_map.get(device.id)
        if not record or not record.telemetry:
            continue
        for _, samples in record.telemetry.items():
            if not samples:
                continue
            temperature = _extract_numeric(samples)
            if temperature is not None:
                return temperature
    return None


def _get_actuator_device(devices: Iterable[Device]) -> Device | None:
    for device in devices:
        if _is_actuator(device):
            return device
    return None


def _get_actuator_state(telemetry_map: dict[int, TelemetryRead], actuator: Device) -> str | None:
    if not actuator:
        return None
    record = telemetry_map.get(actuator.id)
    if not record or not record.telemetry:
        return None
    for key in ("actuatorOpen", "actuatorOpenState", "status"):
        samples = record.telemetry.get(key)
        if not samples:
            continue
        state = _extract_state(samples)
        if state is not None:
            return state
    return None


def _fetch_telemetry_map(
    session: Session, user_id: int, devices: Iterable[Device]
) -> dict[int, TelemetryRead]:
    telemetry_map: dict[int, TelemetryRead] = {}
    for device in devices:
        try:
            telemetry_map[device.id] = get_device_telemetry(session, user_id, device.id)
        except Exception as exc:
            logger.debug(
                "Не удалось получить телеметрию для устройства %s: %s", device.id, exc
            )
    return telemetry_map


def _process_setting(session: Session, setting: AutomationSetting) -> None:
    if not setting.auto_mode:
        return
    greenhouse = session.get(Greenhouse, setting.greenhouse_id)
    if not greenhouse:
        return
    devices = list_for_user_and_greenhouse(session, greenhouse.user_id, greenhouse.id)
    if not devices:
        return

    telemetry_map = _fetch_telemetry_map(session, greenhouse.user_id, devices)
    temperature = _get_temperature_from_telemetry(telemetry_map, devices)
    if temperature is None:
        return

    actuator = _get_actuator_device(devices)
    if not actuator:
        return

    lower, upper = _temperature_thresholds(setting)
    current_state = _get_actuator_state(telemetry_map, actuator)

    if temperature > upper and current_state != "true":
        _send_command(setting, actuator, "open", session)
    elif temperature < lower and current_state == "true":
        _send_command(setting, actuator, "close", session)


def _send_command(setting: AutomationSetting, actuator: Device, command: str, session: Session) -> None:
    try:
        send_rpc_request(
            device_id=actuator.serial_number,
            method="setActuatorState",
            params={"state": command},
        )
        setting.last_action = command
        setting.last_action_at = datetime.utcnow()
        setting.updated_at = datetime.utcnow()
        save(session, setting)
        logger.info(
            "Автоматический переход %s для теплицы %s", command, setting.greenhouse_id
        )
    except Exception as exc:
        logger.warning(
            "Не удалось отправить автоматическую команду %s для теплицы %s: %s",
            command,
            setting.greenhouse_id,
            exc,
        )


def run_automation_cycle() -> None:
    with Session(engine) as session:
        settings = [setting for setting in list_all(session) if setting.auto_mode]
        for setting in settings:
            try:
                _process_setting(session, setting)
            except Exception:
                logger.exception(
                    "Ошибка обработки автоматики для теплицы %s", setting.greenhouse_id
                )


async def start_automation_loop(interval_seconds: int = 30) -> None:
    while True:
        try:
            await asyncio.to_thread(run_automation_cycle)
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Сбой фонового цикла автоматики")
            await asyncio.sleep(interval_seconds)
