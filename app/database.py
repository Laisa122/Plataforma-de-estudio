"""Módulo de conexión y gestión de sesiones de base de datos con SQLAlchemy."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Parámetros especiales para SQLite para permitir múltiples hilos concurrentes
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM de la aplicación."""
    pass


def get_db() -> Generator:
    """Generador de sesiones de base de datos como dependencia de FastAPI.

    Garantiza que la sesión se cierre correctamente tras procesar la solicitud.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
