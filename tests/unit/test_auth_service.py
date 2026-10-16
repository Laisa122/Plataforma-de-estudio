"""Pruebas unitarias para el servicio de autenticación y tokens (auth_service)."""

from datetime import datetime, timezone, timedelta
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


def test_hash_and_verify_password():
    """Valida que una contraseña sea hasheada correctamente y verificada satisfactoriamente."""
    password = "MiPasswordSeguro123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_wrong_password_fails():
    """Valida que una contraseña incorrecta falle la verificación contra el hash."""
    password = "PasswordOriginal123"
    wrong_password = "PasswordIncorrecto123"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_generate_otp_is_six_digits():
    """Valida que el código OTP generado tenga exactamente 6 dígitos numéricos."""
    for _ in range(10):
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit() is True
        assert 100000 <= int(otp) <= 999999


def test_otp_expiry_calculation_and_validation():
    """Valida la detección de vigencia y expiración de códigos OTP con soporte para fechas naive."""
    future_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
    assert is_otp_expired(future_expiry) is False

    past_expiry = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert is_otp_expired(past_expiry) is True

    # Verificación con datetime naive (sin tzinfo, como almacena SQLite a veces)
    naive_future = datetime.utcnow() + timedelta(minutes=10)
    assert is_otp_expired(naive_future) is False

    naive_past = datetime.utcnow() - timedelta(minutes=5)
    assert is_otp_expired(naive_past) is True


def test_access_token_payload_fields():
    """Valida que el token de acceso JWT contenga los campos sub, email, type y exp correctos."""
    user_id = 42
    email = "estudiante@universidad.edu.co"

    token = create_access_token(user_id=user_id, email=email)
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == str(user_id)
    assert payload.get("email") == email
    assert payload.get("type") == "access"
    assert "exp" in payload


def test_refresh_token_payload_fields():
    """Valida la creación y decodificación correcta del token de refresco."""
    user_id = 99
    token = create_refresh_token(user_id=user_id)
    payload = decode_token(token)

    assert payload is not None
    assert payload.get("sub") == str(user_id)
    assert payload.get("type") == "refresh"
    assert "exp" in payload


def test_invalid_token_returns_none():
    """Valida que la decodificación de tokens corruptos o inválidos retorne None."""
    assert decode_token("token.invalido.falso") is None
    assert decode_token("") is None
    assert decode_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.invalidsignature") is None


def test_hash_token_deterministic_and_64_chars():
    """Valida que el hash SHA-256 del token sea determinista y tenga exactamente 64 caracteres hexadecimales."""
    token = "sample.jwt.token.string"
    hash1 = hash_token(token)
    hash2 = hash_token(token)

    assert len(hash1) == 64
    assert hash1 == hash2
    assert all(c in "0123456789abcdef" for c in hash1)
