from sqlmodel import Session, select
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

from ..models import User
from ..schemas import UserCreate
from ..security import get_password_hash, verify_password


def _get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = _get_user_by_email(session, email)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def register_user(session: Session, payload: UserCreate) -> User:
    if _get_user_by_email(session, payload.email):
        raise ValueError("User with this email already exists")
    user = User(
        email=payload.email,
        full_name=payload.full_name or "",
        hashed_password=get_password_hash(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user



def _redirect_with_params(base_url: str, params: dict) -> str:
    parts = urlparse(base_url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q.update({k: v for k, v in params.items() if v is not None})
    new_query = urlencode(q)
    return urlunparse(
        (parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment)
    )