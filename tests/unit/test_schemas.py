"""Pruebas unitarias de validación para esquemas Pydantic v2 (schemas)."""

import pytest
from pydantic import ValidationError
from app.schemas import (
    UserRegister,
    OtpVerify,
    SubjectCreate,
    TaskCreate
)
from app.models import TaskPriority


def test_user_register_valid():
    """Valida que un payload correcto de registro de usuario pase satisfactoriamente."""
    data = {
        "name": "Carlos Gomez",
        "email": "carlos@universidad.edu.co",
        "password": "Password123"
    }
    user = UserRegister(**data)
    assert user.name == "Carlos Gomez"
    assert user.email == "carlos@universidad.edu.co"
    assert user.password == "Password123"


def test_user_register_invalid_email():
    """Valida que un formato incorrecto de correo electrónico arroje ValidationError."""
    with pytest.raises(ValidationError):
        UserRegister(
            name="Laura Diaz",
            email="correo-invalido-sin-arroba",
            password="Password123"
        )


def test_user_register_password_too_short():
    """Valida que una contraseña menor a 8 caracteres arroje ValidationError."""
    with pytest.raises(ValidationError):
        UserRegister(
            name="Laura Diaz",
            email="laura@universidad.edu.co",
            password="P12"
        )


def test_user_register_password_without_digit():
    """Valida que una contraseña sin números arroje ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        UserRegister(
            name="Laura Diaz",
            email="laura@universidad.edu.co",
            password="PasswordSinDigitos"
        )
    assert "dígito numérico" in str(exc_info.value)


def test_otp_verify_invalid_code():
    """Valida que códigos OTP de longitud incorrecta o con letras fallen la validación."""
    with pytest.raises(ValidationError):
        OtpVerify(email="user@test.com", code="12345")  # 5 dígitos

    with pytest.raises(ValidationError):
        OtpVerify(email="user@test.com", code="1234567")  # 7 dígitos

    with pytest.raises(ValidationError):
        OtpVerify(email="user@test.com", code="12A456")  # Contiene letras


def test_subject_create_color_validation():
    """Valida que el color de una materia deba cumplir con el formato hexadecimal #RRGGBB."""
    # Válido
    subject_valid = SubjectCreate(name="Cálculo Integral", color="#ff5733")
    assert subject_valid.color == "#ff5733"

    # Inválido: sin almohadilla
    with pytest.raises(ValidationError):
        SubjectCreate(name="Física II", color="ff5733")

    # Inválido: formato no hexadecimal
    with pytest.raises(ValidationError):
        SubjectCreate(name="Física II", color="#ZZZZZZ")

    # Inválido: longitud incorrecta
    with pytest.raises(ValidationError):
        SubjectCreate(name="Física II", color="#FFF")


def test_task_create_valid_defaults():
    """Valida la creación correcta de una tarea con valores por defecto."""
    task = TaskCreate(title="Parcial de Sistemas Operativos")
    assert task.title == "Parcial de Sistemas Operativos"
    assert task.priority == TaskPriority.medium
    assert task.subject_id is None
