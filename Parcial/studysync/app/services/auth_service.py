"""Servicio de autenticación, hashing de contraseñas y gestión de tokens JWT y OTP."""

from datetime import datetime, timezone, timedelta
import hashlib
import random
from typing import Optional, Dict, Any
import bcrypt
from jose import jwt, JWTError
from app.config import get_settings


def hash_password(password: str) -> str:
    """Genera un hash seguro utilizando el algoritmo bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano contra su hash almacenado."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def generate_otp() -> str:
    """Genera un código numérico aleatorio de 6 dígitos para verificación."""
    return f"{random.randint(100000, 999999)}"


def get_otp_expiry() -> datetime:
    """Calcula la fecha de expiración para un OTP (15 minutos a partir de ahora en UTC)."""
    return datetime.now(timezone.utc) + timedelta(minutes=15)


def is_otp_expired(expires_at: datetime) -> bool:
    """Verifica si la fecha de expiración del código OTP ya ha pasado.

    Maneja datetimes 'naive' (sin zona horaria) de SQLite asignándoles UTC.
    """
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expires_at


def create_access_token(user_id: int, email: str) -> str:
    """Crea un token JWT de acceso con tiempo de expiración estándar."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Crea un token JWT de refresco con mayor duración temporal."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida un token JWT.

    Retorna el diccionario con los claims o None si el token es inválido o expiró.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Calcula el hash SHA-256 de una cadena de texto (token JWT).

    Permite identificar sesiones activas sin almacenar el token en texto plano.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
