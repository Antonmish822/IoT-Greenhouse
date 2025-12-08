from datetime import datetime

from sqlmodel import Session

from ..models import Greenhouse
from ..repositories.greenhouses import (
    delete as delete_greenhouse_record,
    get_for_user,
    list_for_user,
    save as persist_greenhouse,
)
from ..schemas.greenhouse import GreenhouseCreate, GreenhouseRead, GreenhouseUpdate


def _to_read(greenhouse: Greenhouse) -> GreenhouseRead:
    return GreenhouseRead(
        id=greenhouse.id,
        name=greenhouse.name,
        location=greenhouse.location,
        greenhouse_metadata=greenhouse.greenhouse_metadata,
        is_active=greenhouse.is_active,
        created_at=greenhouse.created_at,
        updated_at=greenhouse.updated_at,
        user_id=greenhouse.user_id,
    )


def get_greenhouse_for_user(
    session: Session, user_id: int, greenhouse_id: int
) -> Greenhouse | None:
    return get_for_user(session, user_id, greenhouse_id)


def list_greenhouses_for_user(session: Session, user_id: int) -> list[GreenhouseRead]:
    return [_to_read(g) for g in list_for_user(session, user_id)]


def create_greenhouse(
    session: Session, user_id: int, payload: GreenhouseCreate
) -> GreenhouseRead:
    greenhouse = Greenhouse(
        name=payload.name,
        location=payload.location,
        greenhouse_metadata=payload.metadata,
        user_id=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return _to_read(persist_greenhouse(session, greenhouse))


def update_greenhouse(
    session: Session, greenhouse: Greenhouse, payload: GreenhouseUpdate
) -> GreenhouseRead:
    updated = False
    if payload.name is not None:
        greenhouse.name = payload.name
        updated = True
    if payload.location is not None:
        greenhouse.location = payload.location
        updated = True
    if payload.metadata is not None:
        greenhouse.greenhouse_metadata = payload.metadata
        updated = True
    if payload.is_active is not None:
        greenhouse.is_active = payload.is_active
        updated = True
    if updated:
        greenhouse.updated_at = datetime.utcnow()
        greenhouse = persist_greenhouse(session, greenhouse)
    return _to_read(greenhouse)


def delete_greenhouse(session: Session, greenhouse: Greenhouse) -> None:
    delete_greenhouse_record(session, greenhouse)