"""Pruebas de integración para el ciclo de vida de autenticación de usuarios."""

from app.models import User, OtpCode


def register_user(client, email: str, password: str = "Password123", name: str = "Estudiante Prueba"):
    """Función auxiliar para registrar un usuario mediante la API."""
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password}
    )


def get_otp_from_db(db, email: str) -> str:
    """Función auxiliar para consultar el último código OTP generado en la base de datos."""
    user = db.query(User).filter(User.email == email).first()
    assert user is not None, f"No se encontró el usuario con email {email}"
    otp_record = (
        db.query(OtpCode)
        .filter(OtpCode.user_id == user.id, OtpCode.used.is_(False))
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    assert otp_record is not None, "No se encontró ningún registro OTP activo"
    return otp_record.code


def verify_user(client, db, email: str):
    """Función auxiliar para verificar la cuenta de un usuario utilizando su OTP en base de datos."""
    code = get_otp_from_db(db, email)
    return client.post(
        "/api/auth/verify-otp",
        json={"email": email, "code": code}
    )


def login_user(client, email: str, password: str = "Password123") -> str:
    """Función auxiliar para iniciar sesión y retornar el token de acceso JWT."""
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Error en login: {response.text}"
    return response.json()["access_token"]


def test_full_auth_flow(client, db):
    """Prueba el flujo completo: registro -> verificación OTP -> login -> consulta de perfil protegido."""
    email = "camilo.torres@universidad.edu.co"
    password = "Seguridad2026!"

    # 1. Registro
    reg_resp = register_user(client, email, password, name="Camilo Torres")
    assert reg_resp.status_code == 201

    # 2. Verificación de OTP
    verify_resp = verify_user(client, db, email)
    assert verify_resp.status_code == 200

    # 3. Inicio de sesión
    token = login_user(client, email, password)
    assert token is not None

    # 4. Acceso a ruta protegida /api/auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == email
    assert data["name"] == "Camilo Torres"
    assert data["is_verified"] is True


def test_duplicate_email_rejected(client):
    """Valida que un intento de registro con un correo previamente registrado retorne error 400."""
    email = "duplicado@universidad.edu.co"
    r1 = register_user(client, email, "Pass12345")
    assert r1.status_code == 201

    r2 = register_user(client, email, "OtraPass12345")
    assert r2.status_code == 400
    assert "registrado" in r2.json()["detail"].lower()


def test_wrong_otp_rejected(client):
    """Valida que el envío de un código OTP erróneo no active la cuenta."""
    email = "otptest@universidad.edu.co"
    reg_resp = register_user(client, email, "Pass12345")
    assert reg_resp.status_code == 201

    wrong_verify = client.post(
        "/api/auth/verify-otp",
        json={"email": email, "code": "000000"}
    )
    assert wrong_verify.status_code == 400


def test_logout_invalidates_session(client, db):
    """Valida que el endpoint de logout invalide la sesión y subsecuentes llamadas sean rechazadas con 401."""
    email = "logout@universidad.edu.co"
    password = "Password123"

    register_user(client, email, password)
    verify_user(client, db, email)
    token = login_user(client, email, password)

    headers = {"Authorization": f"Bearer {token}"}

    # Verificar que el token funciona
    ok_resp = client.get("/api/auth/me", headers=headers)
    assert ok_resp.status_code == 200

    # Cerrar sesión
    logout_resp = client.post("/api/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # Verificar que el token ahora es rechazado
    after_logout_resp = client.get("/api/auth/me", headers=headers)
    assert after_logout_resp.status_code == 401
