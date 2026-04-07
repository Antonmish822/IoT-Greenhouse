from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..database import get_session
from ..schemas.automation import AutomationSettingRead, AutomationSettingUpdate
from ..security import get_current_user
from ..services.automation import get_or_create_setting, update_setting

router = APIRouter(
    prefix="/greenhouses/{greenhouse_id}/automation", tags=["automation"]
)


@router.get("/", response_model=AutomationSettingRead)
def read_automation_setting(
    greenhouse_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AutomationSettingRead:
    try:
        setting = get_or_create_setting(session, greenhouse_id, current_user.id)
        return setting
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.put("/", response_model=AutomationSettingRead)
def update_automation_setting(
    greenhouse_id: int,
    payload: AutomationSettingUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AutomationSettingRead:
    try:
        return update_setting(session, greenhouse_id, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
