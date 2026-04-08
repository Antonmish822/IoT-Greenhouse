from sqlmodel import Session

from ..schemas import UserUpdate
from ..security import get_password_hash


def update_user_profile(session: Session, current_user, payload: UserUpdate):
    updated = False
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
        updated = True
    if payload.password:
        current_user.hashed_password = get_password_hash(payload.password)
        updated = True
    if updated:
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
    return current_user
