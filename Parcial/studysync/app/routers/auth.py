"""Enrutador de autenticación: registro, verificación OTP, login, refresh y cierre de sesión."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks, Header
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import limiter, bearer_scheme, get_current_user
from app.models import User, OtpCode, LoginSession
from app.schemas import (
    UserRegister,
    UserLogin,
    OtpVerify,
    OtpResend,
    UserResponse,
    TokenResponse,
    MessageResponse
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    generate_otp,
    get_otp_expiry,
    is_otp_expired,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token
)
from app.services.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(
    request: Request,
    payload: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Registra un nuevo usuario en la plataforma y envía un código OTP por correo."""
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_verified=False,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    otp_code = generate_otp()
    otp_entry = OtpCode(
        user_id=user.id,
        code=otp_code,
        expires_at=get_otp_expiry(),
        used=False
    )
    db.add(otp_entry)
    db.commit()

    background_tasks.add_task(send_otp_email, user.email, otp_code, user.name)

    return MessageResponse(
        message="Usuario registrado exitosamente. Se ha enviado un código de verificación a tu correo."
    )


@router.post("/verify-otp", response_model=MessageResponse)
def verify_otp(
    payload: OtpVerify,
    db: Session = Depends(get_db)
):
    """Valida el código OTP recibido por correo y activa la cuenta del usuario."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    otp_entry = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == user.id,
            OtpCode.code == payload.code,
            OtpCode.used.is_(False)
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )

    if not otp_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código OTP inválido o ya utilizado"
        )

    if is_otp_expired(otp_entry.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código OTP ha expirado"
        )

    otp_entry.used = True
    user.is_verified = True
    db.commit()

    return MessageResponse(message="Cuenta verificada exitosamente")


@router.post("/resend-otp", response_model=MessageResponse)
@limiter.limit("3/minute")
def resend_otp(
    request: Request,
    payload: OtpResend,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Invalida códigos OTP previos no usados y genera uno nuevo."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta ya está verificada"
        )

    # Invalidar OTPs previos pendientes
    active_otps = (
        db.query(OtpCode)
        .filter(OtpCode.user_id == user.id, OtpCode.used.is_(False))
        .all()
    )
    for otp in active_otps:
        otp.used = True

    new_code = generate_otp()
    new_otp = OtpCode(
        user_id=user.id,
        code=new_code,
        expires_at=get_otp_expiry(),
        used=False
    )
    db.add(new_otp)
    db.commit()

    background_tasks.add_task(send_otp_email, user.email, new_code, user.name)

    return MessageResponse(message="Nuevo código OTP enviado a tu correo.")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: UserLogin,
    db: Session = Depends(get_db)
):
    """Autentica las credenciales del estudiante e inicia una sesión con tokens JWT."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta no verificada. Por favor verifica tu correo."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta se encuentra inactiva"
        )

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    settings = get_settings()
    token_h = hash_token(access_token)
    session_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    session = LoginSession(
        user_id=user.id,
        token_hash=token_h,
        expires_at=session_expiry,
        is_active=True
    )
    db.add(session)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Renueva el token de acceso utilizando un refresh token válido enviado en el encabezado Authorization."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Encabezado Authorization ausente o formato incorrecto"
        )

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuario no presente en el token"
        )

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuario no válido"
        )

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o no autorizado"
        )

    new_access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id)

    settings = get_settings()
    token_h = hash_token(new_access_token)
    session_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    new_session = LoginSession(
        user_id=user.id,
        token_hash=token_h,
        expires_at=session_expiry,
        is_active=True
    )
    db.add(new_session)
    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invalida la sesión activa correspondiente al token de acceso presentado."""
    token = credentials.credentials
    token_h = hash_token(token)

    session = (
        db.query(LoginSession)
        .filter(
            LoginSession.token_hash == token_h,
            LoginSession.user_id == current_user.id
        )
        .first()
    )

    if session:
        session.is_active = False
        db.commit()

    return MessageResponse(message="Sesión cerrada exitosamente")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna la información del perfil del usuario actualmente autenticado."""
    return UserResponse.model_validate(current_user)
