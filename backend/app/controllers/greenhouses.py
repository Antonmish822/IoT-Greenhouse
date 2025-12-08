from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..database import get_session
from ..schemas.greenhouse import GreenhouseCreate, GreenhouseRead, GreenhouseUpdate
from ..security import get_current_user
from ..services.greenhouses import (
    _to_read,
    create_greenhouse,
    delete_greenhouse,
    get_greenhouse_for_user,
    list_greenhouses_for_user,
    update_greenhouse,
)
from ..services.devices import list_devices_for_greenhouse

router = APIRouter(prefix="/greenhouses", tags=["greenhouses"])


@router.get("/", response_model=list[GreenhouseRead])
def list_user_greenhouses(
    current_user=Depends(get_current_user), session: Session = Depends(get_session)
) -> list[GreenhouseRead]:
    return list_greenhouses_for_user(session, current_user.id)


@router.post("/", response_model=GreenhouseRead, status_code=status.HTTP_201_CREATED)
def register_greenhouse(
    payload: GreenhouseCreate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> GreenhouseRead:
    return create_greenhouse(session, current_user.id, payload)


@router.get("/{greenhouse_id}", response_model=GreenhouseRead)
def read_greenhouse(
    greenhouse_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> GreenhouseRead:
    greenhouse = get_greenhouse_for_user(session, current_user.id, greenhouse_id)
    if not greenhouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Greenhouse not found")
    return _to_read(greenhouse)


@router.put("/{greenhouse_id}", response_model=GreenhouseRead)
def edit_greenhouse(
    greenhouse_id: int,
    payload: GreenhouseUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> GreenhouseRead:
    greenhouse = get_greenhouse_for_user(session, current_user.id, greenhouse_id)
    if not greenhouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Greenhouse not found")
    return update_greenhouse(session, greenhouse, payload)


@router.delete("/{greenhouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_greenhouse(
    greenhouse_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    greenhouse = get_greenhouse_for_user(session, current_user.id, greenhouse_id)
    if not greenhouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Greenhouse not found")
    delete_greenhouse(session, greenhouse)


@router.get("/{greenhouse_id}/devices")
def list_devices(
    greenhouse_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return list_devices_for_greenhouse(session, current_user.id, greenhouse_id)