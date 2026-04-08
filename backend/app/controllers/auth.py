from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta
from ..config import Settings
from ..database import get_session
from ..models import User, RefreshToken
from ..schemas import UserCreate, UserRead
from ..security import create_access_token, create_refresh_token, decode_refresh_token
from ..services.auth import authenticate_user, register_user

settings = Settings()
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
    """
    Аутентифицирует пользователя
    Args:
        form_data: данные формы
    Returns:
        dict: access токен, пользователь
        рефреш токен устанавливается в куку, а также записывается в базу данных
    """
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    db_refresh_token_insert = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.refresh_token_expire_minutes),
        revoked=False,
        created_at=datetime.utcnow(),
    )
    session.add(db_refresh_token_insert)
    session.commit()

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserRead.from_orm(user).dict(),
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
        path="/auth",
    )
    return response


@router.post("/refresh")
async def refresh(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Обновляет access токен и refresh токен
    Args:
        request: запрос
    Returns:
        dict: access токен, пользователь
        рефреш токен устанавливается в куку
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
        except Exception:
            pass
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    db_refresh_token_select = session.exec(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
    ).first()

    if not db_refresh_token_select:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    email = decode_refresh_token(refresh_token)
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    db_refresh_token_select.revoked = True
    session.add(db_refresh_token_select)

    new_access = create_access_token(subject=user.email)
    new_refresh = create_refresh_token(subject=user.email)

    db_refresh_token_insert = RefreshToken(
        token=new_refresh,
        user_id=user.id,
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.refresh_token_expire_minutes),
        revoked=False,
        created_at=datetime.utcnow(),
    )
    session.add(db_refresh_token_insert)
    session.commit()

    response = JSONResponse(
        content={
            "access_token": new_access,
            "token_type": "bearer",
            "user": UserRead.from_orm(user).dict(),
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
        path="/auth",
    )
    return response


@router.post("/logout")
def logout(request: Request, session: Session = Depends(get_session)):
    """
    Выход из аккаунта
    Args:
        request: запрос
    Returns:
        dict: сообщение об успешном выходе
    """

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        db_refresh_token_select = session.exec(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow(),
            )
        ).first()
        if db_refresh_token_select:
            db_refresh_token_select.revoked = True
            session.add(db_refresh_token_select)
            session.commit()

    response = JSONResponse(content={"detail": "Logged out"})
    response.delete_cookie(key="refresh_token", path="/auth")
    return response
