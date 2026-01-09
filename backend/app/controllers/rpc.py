from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..database import get_session
from ..schemas.rpc import RpcRequest
from ..security import get_current_user
from ..services.devices import get_device_for_user
from ..services.thingsboard import send_rpc_request

router = APIRouter(prefix="/rpc", tags=["rpc"])


@router.post("/{device_id}", status_code=status.HTTP_202_ACCEPTED)
def send_device_rpc(
    device_id: int,
    payload: RpcRequest,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # 1. Verify device belongs to the user
    device = get_device_for_user(session, current_user.id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found for current user",
        )

    # 2. Send the RPC request via ThingsBoard service
    try:
        send_rpc_request(
            device_id=device.serial_number,
            method=payload.method,
            params=payload.params,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send RPC request: {exc}",
        ) from exc

    return {"message": "RPC request sent successfully"}
