from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..database import get_session
from ..schemas.device import DeviceCreate, DeviceRead, DeviceUpdate
from ..security import get_current_user
from ..services.devices import (
    create_device,
    delete_device,
    get_device_for_user,
    get_devices_for_user,
    update_device,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=list[DeviceRead])
def list_devices(
    current_user=Depends(get_current_user), session: Session = Depends(get_session)
) -> list[DeviceRead]:
    devices = get_devices_for_user(session, current_user.id)
    return devices


@router.post("/", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceCreate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DeviceRead:
    try:
        device = create_device(session, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return device


@router.put("/{device_id}", response_model=DeviceRead)
def update_device_entry(
    device_id: int,
    payload: DeviceUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DeviceRead:
    device = get_device_for_user(session, current_user.id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found for current user",
        )
    return update_device(session, device, payload)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_device(
    device_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    device = get_device_for_user(session, current_user.id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found for current user",
        )
    delete_device(session, device)
