from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from .config import Settings
from .database import get_session, init_db
from .models import User
from .schemas import UserCreate, UserRead, UserUpdate
from .security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

settings = Settings()
app = FastAPI(title=settings.app_name)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = _get_user_by_email(session, email)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> User:
    try:
        email = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from exc
    user = _get_user_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for provided token",
        )
    return user


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate, session: Session = Depends(get_session)
) -> UserRead:
    if _get_user_by_email(session, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    user = User(
        email=payload.email,
        full_name=payload.full_name or "",
        hashed_password=get_password_hash(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(subject=user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserRead.from_orm(user),
    }


@app.get("/profile", response_model=UserRead)
def read_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user


@app.put("/profile", response_model=UserRead)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserRead:
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


@app.on_event("startup")
def on_startup():
    init_db()