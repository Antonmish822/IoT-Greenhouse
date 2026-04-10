from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta
from ..config import Settings
from ..database import get_session
from ..models import User, RefreshToken, OAuthClient, AuthorizationCode, BotLinkToken
from ..schemas import UserCreate, UserRead
from ..security import create_access_token, create_refresh_token, decode_refresh_token, verify_password, get_current_user
from ..services.auth import authenticate_user, register_user, _redirect_with_params
import secrets


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


@router.get("/authorize")
def oauth_authorize_get(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Отображает страницу авторизации
    Args:
        request: запрос
    Returns:
        HTMLResponse: страница авторизации
    """
    response_type = request.query_params.get("response_type")
    client_id = request.query_params.get("client_id")
    redirect_uri = request.query_params.get("redirect_uri")
    state = request.query_params.get("state")

    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid response type",
        )
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID is required",
        )
    if not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Redirect URI is required",
        )
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    db_client_select = session.exec(
        select(OAuthClient).where(OAuthClient.client_id == client_id)
        ).first()

    if not db_client_select:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client not found",
        )
    if db_client_select.redirect_uri != redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Redirect URI mismatch",
        )
    
    hidden = f"""
    <input type="hidden" name="client_id" value="{db_client_select.client_id}" />
    <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
    """
    if state:
        hidden += f'<input type="hidden" name="state" value="{state}" />'
    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Вход</title></head>
    <body>
      <h1>Разрешить доступ: {db_client_select.name}</h1>
      <form method="post" action="/auth/authorize">
        <label>Email<br/><input name="email" type="email" required /></label><br/><br/>
        <label>Пароль<br/><input name="password" type="password" required /></label><br/><br/>
        {hidden}
        <button type="submit">Войти и выдать код</button>
      </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.post("/authorize")
async def oauth_authorize_post(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Выдает код авторизации
    Args:
        request: запрос
    Returns:
        RedirectResponse: перенаправление на redirect_uri с параметрами
    """

    form = await request.form()
    email = form.get("email")
    password = form.get("password")
    client_id = form.get("client_id")
    redirect_uri = form.get("redirect_uri")
    state = form.get("state")

    if not email or not password:
        raise HTTPException(status_code=400, detail="invalid_request")
    
    client = session.exec(
        select(OAuthClient).
        where(OAuthClient.client_id == client_id)
        ).first()

    if not client or redirect_uri != client.redirect_uri:
        raise HTTPException(status_code=400, detail="invalid_client")

    user = authenticate_user(session, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid_grant")

    code_str = secrets.token_urlsafe(32)
    code = AuthorizationCode(
        code=code_str,
        client_id=client.id,
        user_id=user.id,
        redirect_uri=redirect_uri,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.oauth_code_expire_minutes),
    )
    session.add(code)
    session.commit()

    params = {
        "code": code_str,
    }
    
    if state:
        params["state"] = state
    location = _redirect_with_params(redirect_uri, params)
    return RedirectResponse(url=location, status_code=status.HTTP_302_FOUND)

@router.post("/token")
async def oauth_token(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Обмен кода авторизации на access токен и refresh токен
    Args:
        request: запрос
    Returns:
        dict: access токен, refresh токен
    """
    form = await request.form()
    grant_type = form.get("grant_type")
    code = form.get("code")
    client_id = form.get("client_id")
    client_secret = form.get("client_secret")
    redirect_uri = form.get("redirect_uri")

    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    if not code or not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=400, detail="invalid_request")

    client = session.exec(
        select(OAuthClient).where(OAuthClient.client_id == str(client_id))
    ).first()
    if not client or not verify_password(str(client_secret), client.client_secret):
        raise HTTPException(status_code=401, detail="invalid_client")

    ac = session.exec(
        select(AuthorizationCode).where(
            AuthorizationCode.code == str(code),
            AuthorizationCode.client_id == client.id,
            AuthorizationCode.used == False,
            AuthorizationCode.expires_at > datetime.utcnow(),
        )
    ).first()
    if not ac or ac.redirect_uri != str(redirect_uri):
        raise HTTPException(status_code=400, detail="invalid_grant")

    user = session.get(User, ac.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="invalid_grant")

    ac.used = True
    session.add(ac)

    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    db_refresh = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.refresh_token_expire_minutes),
        revoked=False,
        created_at=datetime.utcnow(),
    )
    session.add(db_refresh)
    session.commit()

    return JSONResponse({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "refresh_token": refresh_token,
        "user": UserRead.from_orm(user).dict(),
    })


@router.post("/bot-link")
def create_bot_link(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Создает ссылку для бота
    Args:
        user: пользователь
    Returns:
        dict: ссылка для бота
    """
    token_str = secrets.token_urlsafe(32)
    link = BotLinkToken(
        token=token_str,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.bot_link_expire_minutes),
        used=False,
        created_at=datetime.utcnow(),
    )
    session.add(link)
    session.commit()
    return JSONResponse({
        "token": token_str,
        "link": f"https://t.me/GreenhouseBot?start={token_str}",
        "expires_in": settings.bot_link_expire_minutes * 60,
    })

@router.post("/bot-exchange")
async def bot_exchange(
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Обменивает ссылку для бота на access токен и refresh токен
    Args:
        request: запрос
    Returns:
        dict: access токен, refresh токен
    """

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_request")

    token = body.get("token")
    client_id = body.get("client_id")
    client_secret = body.get("client_secret")


    if not token or not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="invalid_request")

    client = session.exec(
        select(OAuthClient).where(OAuthClient.client_id == str(client_id))
    ).first()
    if not client or not verify_password(str(client_secret), client.client_secret):
        raise HTTPException(status_code=401, detail="invalid_client")

    link = session.exec(
        select(BotLinkToken).where(BotLinkToken.token == str(token), BotLinkToken.used == False, BotLinkToken.expires_at > datetime.utcnow())
    ).first()
    if not link:
        raise HTTPException(status_code=400, detail="invalid_request")
    

    user = session.get(User, link.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="invalid_request")
    
    link.used = True
    session.add(link)



    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    db_refresh = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow()
        + timedelta(minutes=settings.refresh_token_expire_minutes),
        revoked=False,
        created_at=datetime.utcnow(),
    )
    session.add(db_refresh)
    session.commit()

    return JSONResponse({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "refresh_token": refresh_token,
        "user": UserRead.from_orm(user).dict(),
    })





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
