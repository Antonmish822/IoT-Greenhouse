from typing import Iterable

from sqlmodel import Session, select

from ..models import Device


def get_by_serial(session: Session, serial_number: str) -> Device | None:
    statement = select(Device).where(Device.serial_number == serial_number)
    return session.exec(statement).first()


def get_for_user(session: Session, user_id: int, device_id: int) -> Device | None:
    statement = select(Device).where(
        Device.id == device_id,
        Device.user_id == user_id,
    )
    return session.exec(statement).first()


def list_for_user(session: Session, user_id: int) -> Iterable[Device]:
    statement = select(Device).where(Device.user_id == user_id)
    return session.exec(statement).all()


def save(session: Session, device: Device) -> Device:
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


def delete(session: Session, device: Device) -> None:
    session.delete(device)
    session.commit()