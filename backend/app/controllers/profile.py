from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..database import get_session
from ..schemas import UserRead, UserUpdate
from ..security import get_current_user
from ..services.profile import update_user_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=UserRead)
def read_profile(current_user=Depends(get_current_user)) -> UserRead:
    return current_user


@router.put("/", response_model=UserRead)
def update_profile(
    payload: UserUpdate,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserRead:
    return update_user_profile(session, current_user, payload)