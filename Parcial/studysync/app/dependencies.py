"""Dependencias compartidas para FastAPI: limitador de peticiones y autenticación."""

from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, LoginSession
from app.services.auth_service import decode_token, hash_token

limiter = Limiter(key_func=get_remote_address)
bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Valida el token de acceso Bearer y devuelve el usuario autenticado.

    Verifica la firma del token, existencia y vigencia de la sesión en base de datos,
    así como el estado activo y verificado de la cuenta del usuario.
    """
    token = credentials.credentials
    payload = decode_token(token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación no válidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not payload or payload.get("type") != "access":
        raise credentials_exception

    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception

    token_hash = hash_token(token)

    # Consulta de la sesión activa
    session = (
        db.query(LoginSession)
        .filter(
            LoginSession.user_id == user_id,
            LoginSession.token_hash == token_hash,
            LoginSession.is_active.is_(True)
        )
        .first()
    )

    if not session:
        raise credentials_exception

    # Manejo de fecha naive en SQLite
    session_expiry = session.expires_at
    if session_expiry.tzinfo is None:
        session_expiry = session_expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > session_expiry:
        session.is_active = False
        db.commit()
        raise credentials_exception

    # Búsqueda del usuario activo
    user = (
        db.query(User)
        .filter(User.id == user_id, User.is_active.is_(True))
        .first()
    )

    if not user or not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no verificado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
