from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..database import get_session
from ..schemas.telemetry import TelemetryRead
from ..security import get_current_user
from ..services.telemetry import get_device_telemetry

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/{device_id}", response_model=TelemetryRead)
def read_device_telemetry(
    device_id: int,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> TelemetryRead:
    try:
        return get_device_telemetry(session, current_user.id, device_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch telemetry from ThingsBoard",
        ) from exc
