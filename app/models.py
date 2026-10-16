"""Modelos ORM de SQLAlchemy para StudySync.

Define las entidades principales del dominio educativo y colaborativo.
"""

from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


class TaskPriority(str, enum.Enum):
    """Niveles de prioridad asignables a una tarea."""
    low = "low"
    medium = "medium"
    high = "high"


class TaskStatus(str, enum.Enum):
    """Estados del ciclo de vida de una tarea."""
    pending = "pending"
    in_progress = "in_progress"
    done = "done"


class GroupRole(str, enum.Enum):
    """Roles de los integrantes dentro de un grupo de estudio."""
    admin = "admin"
    member = "member"


class User(Base):
    """Modelo que representa a un estudiante o usuario del sistema."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relaciones con eliminación en cascada
    otp_codes = relationship("OtpCode", back_populates="user", cascade="all, delete-orphan")
    login_sessions = relationship("LoginSession", back_populates="user", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    created_groups = relationship(
        "StudyGroup",
        back_populates="creator",
        cascade="all, delete-orphan",
        foreign_keys="StudyGroup.creator_id"
    )
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")


class OtpCode(Base):
    """Código de un solo uso para validación de correo electrónico."""

    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="otp_codes")


class LoginSession(Base):
    """Sesión de inicio de sesión activa identificada por el hash de su token."""

    __tablename__ = "login_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="login_sessions")


class Subject(Base):
    """Materia o asignatura académica cursada por el estudiante."""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    professor = Column(String(100), nullable=True)
    color = Column(String(7), default="#6366f1", nullable=False)
    semester = Column(String(20), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="subjects")
    tasks = relationship("Task", back_populates="subject", cascade="all, delete-orphan")
    study_groups = relationship("StudyGroup", back_populates="subject")


class Task(Base):
    """Tarea, asignación o entrega académica individual."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    priority = Column(SAEnum(TaskPriority), default=TaskPriority.medium, nullable=False)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.pending, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")


class StudyGroup(Base):
    """Grupo colaborativo de estudio creado por un estudiante."""

    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invite_code = Column(String(8), unique=True, index=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    creator = relationship("User", back_populates="created_groups", foreign_keys=[creator_id])
    subject = relationship("Subject", back_populates="study_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """Membresía que vincula un estudiante con un grupo de estudio."""

    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SAEnum(GroupRole), default=GroupRole.member, nullable=False)
    joined_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    group = relationship("StudyGroup", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
