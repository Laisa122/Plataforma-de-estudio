"""Esquemas de validación y serialización de datos con Pydantic v2.

Define las estructuras de entrada y salida para todos los endpoints de la API.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models import TaskPriority, TaskStatus, GroupRole


# ============================================================================
# Esquemas de Autenticación y Usuarios
# ============================================================================

class UserRegister(BaseModel):
    """Esquema para el registro de nuevos usuarios."""

    name: str = Field(..., min_length=2, max_length=100, description="Nombre completo del estudiante")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    password: str = Field(..., min_length=8, max_length=128, description="Contraseña de al menos 8 caracteres con dígitos")

    @field_validator("password")
    @classmethod
    def validate_password_has_digit(cls, value: str) -> str:
        """Verifica que la contraseña contenga al menos un número."""
        if not any(char.isdigit() for char in value):
            raise ValueError("La contraseña debe contener al menos un dígito numérico")
        return value


class UserLogin(BaseModel):
    """Esquema para inicio de sesión."""

    email: EmailStr = Field(..., description="Correo electrónico registrado")
    password: str = Field(..., description="Contraseña de acceso")


class OtpVerify(BaseModel):
    """Esquema para la verificación de código OTP."""

    email: EmailStr = Field(..., description="Correo electrónico registrado")
    code: str = Field(..., pattern=r"^\d{6}$", description="Código OTP numérico de 6 dígitos")


class OtpResend(BaseModel):
    """Esquema para solicitar el reenvío de un código OTP."""

    email: EmailStr = Field(..., description="Correo electrónico registrado")


class UserResponse(BaseModel):
    """Esquema de respuesta pública con datos del usuario."""

    id: int
    name: str
    email: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Esquema de respuesta tras autenticación exitosa."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Esquema para respuestas informativas estándar."""

    message: str


# ============================================================================
# Esquemas de Materias (Subjects)
# ============================================================================

class SubjectCreate(BaseModel):
    """Esquema para creación de una materia."""

    name: str = Field(..., min_length=1, max_length=100, description="Nombre de la materia")
    professor: Optional[str] = Field(None, max_length=100, description="Nombre del docente")
    color: str = Field(
        default="#6366f1",
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Color en formato hexadecimal (#RRGGBB)"
    )
    semester: Optional[str] = Field(None, max_length=20, description="Semestre lectivo actual")


class SubjectUpdate(BaseModel):
    """Esquema para actualización parcial o total de una materia."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    professor: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    semester: Optional[str] = Field(None, max_length=20)


class SubjectResponse(BaseModel):
    """Esquema de respuesta con detalles de una materia."""

    id: int
    name: str
    professor: Optional[str]
    color: str
    semester: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Esquemas de Tareas (Tasks)
# ============================================================================

class TaskCreate(BaseModel):
    """Esquema para creación de una nueva tarea."""

    title: str = Field(..., min_length=1, max_length=200, description="Título descriptivo de la tarea")
    description: Optional[str] = Field(None, description="Detalles o instrucciones adicionales")
    due_date: Optional[datetime] = Field(None, description="Fecha y hora de vencimiento")
    priority: TaskPriority = Field(default=TaskPriority.medium, description="Prioridad de la tarea")
    subject_id: Optional[int] = Field(None, description="Identificador de la materia vinculada")


class TaskUpdate(BaseModel):
    """Esquema para actualización de campos de una tarea."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    subject_id: Optional[int] = None


class TaskStatusUpdate(BaseModel):
    """Esquema exclusivo para cambio de estado en una tarea."""

    status: TaskStatus = Field(..., description="Nuevo estado de la tarea")


class TaskResponse(BaseModel):
    """Esquema de respuesta con los datos de una tarea."""

    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    priority: TaskPriority
    status: TaskStatus
    subject_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Esquemas de Grupos de Estudio (Study Groups)
# ============================================================================

class GroupCreate(BaseModel):
    """Esquema para la creación de un nuevo grupo de estudio."""

    name: str = Field(..., min_length=1, max_length=100, description="Nombre del grupo")
    description: Optional[str] = Field(None, description="Descripción del propósito del grupo")
    subject_id: Optional[int] = Field(None, description="Materia relacionada opcional")


class GroupJoin(BaseModel):
    """Esquema para unirse a un grupo mediante código de invitación."""

    invite_code: str = Field(..., min_length=1, max_length=10, description="Código de invitación de 8 caracteres")


class GroupMemberResponse(BaseModel):
    """Esquema de respuesta para miembros de un grupo."""

    user_id: int
    user_name: str
    user_email: str
    role: GroupRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    """Esquema de respuesta general para información del grupo de estudio."""

    id: int
    name: str
    description: Optional[str]
    subject_id: Optional[int]
    creator_id: int
    invite_code: str
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}
