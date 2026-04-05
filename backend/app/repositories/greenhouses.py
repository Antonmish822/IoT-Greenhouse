from typing import Iterable

from sqlmodel import Session, select

from ..models import Greenhouse


def get_for_user(
    session: Session, user_id: int, greenhouse_id: int
) -> Greenhouse | None:
    statement = select(Greenhouse).where(
        Greenhouse.id == greenhouse_id,
        Greenhouse.user_id == user_id,
    )
    return session.exec(statement).first()


def list_for_user(session: Session, user_id: int) -> Iterable[Greenhouse]:
    statement = select(Greenhouse).where(Greenhouse.user_id == user_id)
    return session.exec(statement).all()


def save(session: Session, greenhouse: Greenhouse) -> Greenhouse:
    session.add(greenhouse)
    session.commit()
    session.refresh(greenhouse)
    return greenhouse


def delete(session: Session, greenhouse: Greenhouse) -> None:
    session.delete(greenhouse)
    session.commit()
