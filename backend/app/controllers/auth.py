from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from ..database import get_session
from ..schemas import UserCreate, UserRead
from ..security import create_access_token
from ..services.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.options("/register")
def register_options():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    try:
        user = register_user(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return user


@router.options("/login")
def login_options():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
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
